#!/usr/bin/env python3
"""FieldMind research worker (isolated prototype).

Pipeline: intake guard -> plan -> retrieval log -> claims -> deterministic checks
-> six-question brief + FieldMind research v2 file + run report.

Retrieval and claim extraction are pluggable. In this prototype they are done by an
agent with live web search/fetch tools that writes `retrieval.jsonl` and `claims.json`;
a Claude API adapter can write the same two files. Everything after that is plain code:
no model decides whether a claim is accepted.

Standard library only.
"""
import json, re, sys, os, datetime as dt, argparse, unicodedata
from urllib.parse import urlparse

POLICY = "fm-research-policy-v0"
FRESH_MONTHS = 24          # proposed freshness window; older reports are marked historical
CAP_SECONDS = 1200         # per-run cap from the readiness timing protocol
OFFICIAL = {"registry", "property_record", "permit"}
AUTH_ROLES = ["business_ownership", "business_operations", "utility_account", "property", "hvac_facilities"]
PHASES = ["prepare", "retrieve", "extract", "check", "assemble"]

# ---------------------------------------------------------------- intake guard
ALLOWED = {"ref", "listed_name", "address", "synthetic", "list_context"}
ADDR_KEYS = {"number", "street", "suite", "city", "state", "zip"}
CTX_KEYS = {"historical_participation", "listed_names_historical"}
FORBIDDEN_KEY = re.compile(r"account|premise|itron|device|meter|serial|customer|contact|phone|email|ssn", re.I)


class IntakeError(ValueError):
    pass


def check_prospect(p):
    """Minimum-necessary guard: only a ref, the listed name and the exact address go out."""
    if not isinstance(p, dict):
        raise IntakeError("prospect must be an object")
    extra = set(p) - ALLOWED
    if extra:
        raise IntakeError("fields not allowed in a research request: " + ", ".join(sorted(extra)))
    if not re.fullmatch(r"r[0-9a-z]{1,8}", str(p.get("ref", ""))):
        raise IntakeError("ref must be a FieldMind code like r1a2b3c, not a utility or premise ID")
    a = p.get("address")
    if not isinstance(a, dict) or not a.get("number") or not a.get("street") or not a.get("city"):
        raise IntakeError("address needs number, street and city")
    if set(a) - ADDR_KEYS:
        raise IntakeError("address fields not allowed: " + ", ".join(sorted(set(a) - ADDR_KEYS)))
    ctx = p.get("list_context") or {}
    if set(ctx) - CTX_KEYS:
        raise IntakeError("list_context fields not allowed: " + ", ".join(sorted(set(ctx) - CTX_KEYS)))

    def walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if FORBIDDEN_KEY.search(k):
                    raise IntakeError(f"field looks like an identifier that must not leave FieldMind: {path}{k}")
                walk(v, f"{path}{k}.")
        elif isinstance(o, list):
            for v in o:
                walk(v, path)
        elif isinstance(o, str) and re.search(r"\d{8,}", o):
            raise IntakeError(f"long digit string in {path.rstrip('.') or 'value'} looks like an account or premise ID")
    walk(p)
    return p


def addr_line(a):
    s = f"{a['number']} {a['street']}"
    if a.get("suite"):
        s += f", {a['suite']}"
    return f"{s}, {a['city']}, {a.get('state', '')} {a.get('zip', '')}".strip().rstrip(",")


# ---------------------------------------------------------------- plan
def plan(p):
    a, name = p["address"], p.get("listed_name") or ""
    street = f"{a['number']} {a['street']}"
    city = f"{a['city']} {a.get('state', '')}".strip()
    steps = [
        ("search", f"\"{street}\" {city}", "who operates at the exact address now", "business"),
        ("search", f"{name} {street} {city}", "is the listed name still operating here", "business"),
        ("search", f"{name} owner founder {a['city']}", "ownership / operator people", "people"),
        ("search", f"{name} North Carolina Secretary of State business registration", "legal entity, registered agent, officers", "people"),
        ("search", f"{street} {a['city']} property owner parcel Wake County", "property owner (landlord route)", "infrastructure"),
        ("search", f"{street} {a['city']} permit HVAC mechanical", "HVAC / mechanical permits", "energy"),
        ("fetch", "business's own website (from results)", "hours, about page, address confirmation", "business"),
        ("fetch", "best independent source (from results)", "corroboration, dates, history", "business"),
    ]
    return [{"step": i + 1, "kind": k, "query": q, "goal": g, "dimension": d} for i, (k, q, g, d) in enumerate(steps)]


# ---------------------------------------------------------------- helpers
def norm(s):
    s = unicodedata.normalize("NFKC", str(s or ""))
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


STREET_ABBR = {"street": "st", "avenue": "ave", "boulevard": "blvd", "road": "rd", "drive": "dr", "west": "w",
               "east": "e", "north": "n", "south": "s", "suite": "ste", "lane": "ln", "court": "ct", "place": "pl", "parkway": "pkwy"}


def canon_addr(s):
    s = norm(s).replace(".", "").replace(",", " ").replace("#", " ste ")
    return " ".join(STREET_ABBR.get(w, w) for w in s.split())


def addr_parts(s):
    """number, street core, suite from a free-text address"""
    c = canon_addr(s)
    m = re.match(r"(\d+[a-z]?)\s+(.*)", c)
    if not m:
        return None, c, None
    num, rest = m.group(1), m.group(2)
    suite = None
    sm = re.search(r"\b(?:ste|unit|apt|bldg|sweet)\s*([0-9][0-9a-z-]*)", rest)
    if sm:
        suite = sm.group(1)
        rest = rest[:sm.start()]
    core = rest.split(" raleigh")[0].strip()
    core = re.split(r"\b(?:nc|north carolina)\b", core)[0].strip()
    return num, core, suite


def address_match(prospect_addr, source_addr):
    """'match' | 'suite_mismatch' | 'suite_unconfirmed' | 'different' | 'none'"""
    if not source_addr:
        return "none"
    num, core, suite = addr_parts(source_addr)
    p_core = canon_addr(prospect_addr["street"])
    if num != canon_addr(prospect_addr["number"]) or not core or not (core.startswith(p_core) or p_core.startswith(core)):
        return "different"
    p_suite = canon_addr(prospect_addr.get("suite") or "").replace("ste", "").strip() or None
    if p_suite and suite and suite != p_suite:
        return "suite_mismatch"
    if p_suite and not suite:
        return "suite_unconfirmed"
    if suite and not p_suite:
        return "suite_unconfirmed"
    return "match"


def name_key(s):
    s = norm(s)
    s = re.sub(r"\b(llc|inc|incorporated|corp|corporation|co|company|ltd|pllc|pa|the)\b", " ", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def safe_url(u):
    if not isinstance(u, str) or re.search(r"[\x00-\x20\x7f]", u):
        return ""
    try:
        p = urlparse(u)
    except Exception:
        return ""
    return u if p.scheme in ("http", "https") and p.netloc and "@" not in p.netloc else ""


def parse_date(s):
    if not s:
        return None
    m = re.match(r"(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", str(s))
    if not m:
        return None
    return dt.date(int(m.group(1)), int(m.group(2) or 1), int(m.group(3) or 1))


def months_between(a, b):
    return (b.year - a.year) * 12 + (b.month - a.month)


def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def load_jsonl(path):
    out = []
    with open(path) as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


# ---------------------------------------------------------------- checks
def check_claims(prospect, retrievals, claims, as_of):
    """Deterministic acceptance. Returns (accepted, rejected, notes)."""
    R = {r["id"]: r for r in retrievals}
    pa = prospect["address"]
    accepted, rejected, notes = [], [], []

    def reject(c, reason, detail=""):
        rejected.append({"id": c.get("id"), "text": c.get("text"), "reason": reason, "detail": detail,
                         "subject": c.get("subject"), "about": c.get("about"), "address_in_source": c.get("address_in_source"),
                         "retrieval": c.get("retrieval")})

    observed = [c for c in claims if c.get("basis") != "inferred"]
    inferred = [c for c in claims if c.get("basis") == "inferred"]

    # pass 1: provenance + address tie for observed claims
    tied_names = set()
    stage = []
    for c in observed:
        r = R.get(c.get("retrieval"))
        if not r:
            reject(c, "source_missing", "no retrieval with that id"); continue
        if r.get("outcome") != "ok":
            reject(c, "source_failed", f"retrieval {r['id']} outcome {r.get('outcome')}"); continue
        if not safe_url(r.get("url")):
            reject(c, "unsafe_or_missing_url"); continue
        ex = c.get("excerpt") or ""
        if len(norm(ex)) < 8:
            reject(c, "excerpt_missing"); continue
        if norm(ex) not in norm(r.get("captured_text")):
            reject(c, "excerpt_not_in_source", "quoted text is not in what was retrieved"); continue
        if c.get("address_in_source"):
            if norm(c["address_in_source"]) not in norm(r.get("captured_text")):
                reject(c, "address_not_in_source"); continue
        m = address_match(pa, c.get("address_in_source"))
        c = dict(c, _addr=m, _r=r)
        if m == "different":
            reject(c, "identity_merge_rejected", f"source address '{c['address_in_source']}' is not {addr_line(pa)}"); continue
        if m == "suite_mismatch":
            reject(c, "identity_merge_rejected", "source names a different suite"); continue
        if (m == "suite_unconfirmed" and not pa.get("suite") and c.get("about") == "occupant"
                and name_key(c.get("subject")) != name_key(prospect.get("listed_name"))):
            reject(c, "identity_merge_rejected", "the list gives no suite and this source names a different business in a specific suite"); continue
        if m in ("match", "suite_unconfirmed") and c.get("about") == "occupant" and c.get("subject"):
            tied_names.add(name_key(c["subject"]))
        stage.append(c)

    # pass 2: claims with no address must tie to an address-matched occupant name
    for c in stage:
        if c["_addr"] == "none":
            needs_tie = c.get("about") in ("occupant", "premises", "landlord", "equipment")
            if c.get("about") in ("premises", "landlord", "equipment") and c.get("claim_type") in ("property", "hvac", "electrical", "occupancy_change"):
                reject(c, "identity_merge_rejected", "building or property facts need the exact address in the source"); continue
            if needs_tie and name_key(c.get("subject")) not in tied_names:
                reject(c, "identity_merge_rejected", "no address in source and the name is not tied to this address by another accepted source"); continue
            if needs_tie:
                c["_name_tied"] = True

        # authority rules
        role = c.get("authority_role")
        if role == "utility_account":
            reject(c, "authority_rejected", "public sources cannot establish utility-account authority"); continue
        st = c.get("proposed_status", "found")
        if st == "verified":
            src_type = c["_r"].get("source_type")
            why = None
            if src_type not in OFFICIAL:
                why = f"verified needs an official record (registry, property record, permit); source is {src_type}"
            elif role and (not c.get("person") or norm(c["person"]) not in norm(c["_r"].get("captured_text"))):
                why = "verified authority needs the named person in the official record"
            elif c["_addr"] != "match" and not c.get("_name_tied"):
                why = "verified needs the record tied to this exact address"
            if why:
                rejected.append({"id": c["id"], "text": c.get("text"), "reason": "verified_label_rejected", "detail": why + "; kept as source-supported"})
                st = "found"
        if c.get("_addr") == "suite_unconfirmed" and st == "verified":
            st = "found"
        # temporal
        d = parse_date(c.get("effective_date")) or parse_date(c["_r"].get("published"))
        current = c.get("temporal", "current")
        aged = bool(d and months_between(d, as_of) > FRESH_MONTHS)
        if current == "historical" or aged:
            st = "historical"
            current = "historical"
        c["_aged"] = aged
        c["status"], c["temporal"] = st, current
        accepted.append(c)

    # contradictions among current claims with the same value_key
    groups = {}
    for c in accepted:
        if c.get("value_key") and c["temporal"] == "current":
            groups.setdefault(c["value_key"], []).append(c)
    for key, cs in groups.items():
        vals = {name_key(c.get("value")) for c in cs}
        if len(vals) > 1:
            ids = [c["id"] for c in cs]
            for c in cs:
                c["status"] = "conflicting"
                c["conflicts_with"] = [i for i in ids if i != c["id"]]
            notes.append(f"Sources disagree on {key}: " + "; ".join(f"{c['id']}={c.get('value')}" for c in cs))

    # inferred claims need accepted, non-rejected parents
    ok_ids = {c["id"] for c in accepted}
    for c in inferred:
        parents = c.get("derived_from") or []
        if not parents or not all(pid in ok_ids for pid in parents):
            reject(c, "inference_unsupported", "inferences need accepted parent claims"); continue
        if c.get("proposed_status") == "verified":
            rejected.append({"id": c["id"], "text": c.get("text"), "reason": "verified_label_rejected", "detail": "an inference cannot be verified"})
        if c.get("authority_role") == "utility_account":
            reject(c, "authority_rejected", "utility-account authority is not inferred from ownership"); continue
        if c.get("authority_role"):
            reject(c, "authority_rejected", "decision authority is never inferred; it needs a source"); continue
        pc = [x for x in accepted if x["id"] in parents]
        if c.get("subject") and not any(name_key(x.get("subject")) == name_key(c["subject"]) for x in pc):
            reject(c, "identity_merge_rejected", "an inference cannot move facts from one business or place to another"); continue
        temporal = "historical" if all(x["temporal"] == "historical" for x in pc) else c.get("temporal", "current")
        c = dict(c, status="inferred", temporal=temporal)
        accepted.append(c)
    return accepted, rejected, notes


# ---------------------------------------------------------------- assemble
STATE_OF = {"verified": "verified", "found": "source_supported", "inferred": "inferred", "historical": "historical", "conflicting": "disputed"}


def pick(accepted, **kw):
    return [c for c in accepted if all(c.get(k) == v for k, v in kw.items())]


def first_current(cs):
    cur = [c for c in cs if c["temporal"] == "current"]
    order = ["verified", "found", "conflicting", "inferred"]
    cur.sort(key=lambda c: order.index(c["status"]) if c["status"] in order else 9)
    return cur[0] if cur else None


def build(prospect, plan_steps, retrievals, claims, timing, as_of=None):
    as_of = as_of or dt.date.today()
    accepted, rejected, notes = check_claims(prospect, retrievals, claims, as_of)
    pa = prospect["address"]
    scope = addr_line(pa)
    listed = prospect.get("listed_name")

    occ_claims = [c for c in accepted if c.get("claim_type") in ("occupant_identity", "operating_status") and c.get("about") == "occupant"]
    occ = first_current(occ_claims)
    disputed_occ = [c for c in occ_claims if c["status"] == "conflicting"]
    closed = [c for c in accepted if c.get("claim_type") == "operating_status" and c["temporal"] == "current" and norm(c.get("value")) in ("closed", "permanently closed", "moved")]

    if disputed_occ:
        q1_state, occ_name = "disputed", None
        def _d(c):
            r = R_by(retrievals, c.get("retrieval")) or {}
            return c.get("effective_date") or r.get("published") or "undated"
        q1_summary = "Sources disagree: " + "; ".join(f"{c.get('subject')} {c.get('value')} ({c['id']}, {_d(c)})" for c in disputed_occ) + ". Current operator not established."
    elif closed:
        q1_state, occ_name = "source_supported", None
        q1_summary = f"A current source reports {closed[0].get('subject')} as {closed[0].get('value')} at this address ({closed[0]['id']}). Current operator unknown."
    elif occ:
        q1_state, occ_name = STATE_OF[occ["status"]], occ.get("subject")
        tie = "exact address in source" if occ.get("_addr") == "match" else "address in source, suite not confirmed" if occ.get("_addr") == "suite_unconfirmed" else "name tied by another source"
        q1_summary = f"Candidate operator: {occ_name} ({tie}; {occ['id']}). A candidate until a reviewer accepts the identity."
    else:
        q1_state, occ_name = "unknown", None
        q1_summary = "No accepted source ties a business to this exact address."
    alternatives = [r for r in rejected if r["reason"] == "identity_merge_rejected" and r.get("about") == "occupant" and r.get("address_in_source")]
    listed_elsewhere = [r for r in alternatives if listed and name_key(r.get("subject")) == name_key(listed)]
    if listed_elsewhere and q1_state == "unknown":
        q1_summary += " The listed business appears at other addresses or suites: " + "; ".join(f"{r['address_in_source']} ({r['id']})" for r in listed_elsewhere) + "."
    if listed and occ_name and name_key(listed) != name_key(occ_name):
        q1_summary += f" Listed name '{listed}' kept as list information, not assumed current."

    # Q2 rows
    def row(role):
        cs = [c for c in accepted if c.get("authority_role") == role and c["temporal"] == "current"]
        hist = [c for c in accepted if c.get("authority_role") == role and c["temporal"] == "historical"]
        if role == "utility_account":
            return {"summary": "Not established. Public sources cannot show who holds or can sign for the utility account.", "state": "unknown",
                    "claim_refs": [], "what_is_not_established": "Account holder and signing authority; needs authorized confirmation"}
        if not cs:
            return {"summary": "Not found in permitted public sources." + (" Historical: " + "; ".join(f"{c.get('person') or c.get('value')} ({c.get('effective_date') or 'undated'}, {c['id']})" for c in hist) if hist else ""),
                    "state": "unknown", "claim_refs": [c["id"] for c in hist],
                    "what_is_not_established": "Who holds this authority now"}
        best = sorted(cs, key=lambda c: ["verified", "found", "conflicting", "inferred"].index(c["status"]))[0]
        dispute = any(c["status"] == "conflicting" for c in cs)
        st = "disputed" if dispute else ("verified" if best["status"] == "verified" else "inferred" if best["status"] == "inferred" else "source_supported")
        limits = {"business_ownership": "Ownership is not utility-account or HVAC authority",
                  "business_operations": "Running the business is not authority over the account or equipment",
                  "property": "Property ownership does not show who controls tenant HVAC or the account",
                  "hvac_facilities": "Who approves thermostat or HVAC changes is not established"}[role]
        return {"summary": "; ".join(f"{c.get('person') or c.get('value')} ({c['id']}, {STATE_OF[c['status']]})" for c in cs),
                "state": st, "claim_refs": [c["id"] for c in cs], "what_is_not_established": limits}
    q2 = {r: row(r) for r in AUTH_ROLES}

    hvac = [c for c in accepted if c.get("claim_type") in ("hvac", "electrical")]
    ctx = prospect.get("list_context") or {}
    q3 = {
        "historical_participation": {"summary": ctx.get("historical_participation") or "None supplied with this request", "claim_refs": []},
        "historical_equipment": {"summary": "Not sent to the research worker (device fields stay in FieldMind)", "claim_refs": []},
        "current_account": {"summary": "Unknown. Not researchable from public sources.", "state": "unknown", "claim_refs": []},
        "current_hvac": {"summary": "; ".join(f"{c['text']} ({c['id']}, {STATE_OF[c['status']]})" for c in hvac) or "No current HVAC or controls facts found in permitted sources",
                         "state": ("source_supported" if any(c["temporal"] == "current" and c["status"] in ("found", "verified") for c in hvac) else "inferred" if hvac else "unknown"),
                         "claim_refs": [c["id"] for c in hvac]},
        "current_eligibility": {"state": "not_established", "summary": "Not established by MIMO history or this research brief", "official_review_ref": None},
    }

    failures = [r for r in retrievals if r.get("outcome") != "ok"]
    not_found = [s for s in (timing.get("not_found") or [])]
    q4 = {
        "historical": [f"{c['id']}: {c['text']}" for c in accepted if c["temporal"] == "historical"],
        "stale": [f"{c['id']}: source dated more than {FRESH_MONTHS} months before {as_of.isoformat()}" for c in accepted if c.get("_aged")],
        "inferred": [f"{c['id']}: {c['text']} (from {', '.join(c.get('derived_from') or [])})" for c in accepted if c["status"] == "inferred"],
        "unknown": [f"{r.replace('_', ' ')}: not established" for r, v in q2.items() if v["state"] == "unknown"] + not_found,
        "contradicted": notes,
    }

    # Q5: ranked by the spec's order: operator/suite risk, then account authority, then device hypotheses
    same_street = [r for r in listed_elsewhere if address_match(dict(pa, suite=None), r["address_in_source"]) in ("match", "suite_unconfirmed")]
    if same_street and q1_state == "unknown":
        q5 = (f"Sources put {listed} at {same_street[0]['address_in_source']}, not {pa.get('suite')}. Is the list's suite out of date, or is a different business in {pa.get('suite')}?",
              "The list suite does not match where public sources place the business", "Briefing on the wrong suite or attaching another tenant's history")
    elif q1_state in ("unknown", "disputed") or closed:
        q5 = ("Who operates at " + scope + " today?", "The current operator is not established", "Briefing the rep on the wrong business")
    elif occ and occ.get("_addr") == "suite_unconfirmed" and not pa.get("suite"):
        seen = sorted({addr_parts(c["address_in_source"])[2] for c in accepted if c.get("address_in_source") and addr_parts(c["address_in_source"])[2]})
        q5 = (f"The list has no suite. Sources put {occ_name} in Suite {addr_parts(occ['address_in_source'])[2] or '?'}" + (f" of a building with suites {', '.join(seen)}" if len(seen) > 1 else "") + ". Is this premises that suite?",
              "The list address covers more than one tenant" if len(seen) > 1 else "The list gives no suite and sources name one", "Attaching another tenant's facts or account history to this premises")
    elif occ and occ.get("_addr") == "suite_unconfirmed":
        q5 = (f"Is {occ_name} in the exact suite on the list?", "Sources give the building but not the suite", "Attaching a neighbouring tenant's facts to this premises")
    elif q2["business_ownership"]["state"] in ("unknown", "inferred"):
        q5 = (f"Who owns {occ_name}, and do they decide on the utility account?", "Ownership and account authority are not established", "Pitching someone who can't approve enrollment")
    else:
        owner = q2["business_ownership"]["summary"].split(" (")[0]
        q5 = (f"Does {owner} hold the Duke account for this location, or does a landlord or manager?", "Utility-account authority is never established by public sources", "Pitching someone who can't sign for the account")
    q5d = {"question": q5[0], "reason": q5[1], "risk_avoided": q5[2],
           "evidence_refs": ([occ["id"]] if occ else []) + q2["business_ownership"]["claim_refs"][:2],
           "requires_separate_contact_permission": True}

    findings = []
    for c in accepted:
        r = R_by(retrievals, c.get("retrieval"))
        findings.append({"claim_id": c["id"], "text": c["text"], "subject": c.get("subject"), "person": c.get("person"), "scope": scope if c.get("_addr") == "match" else (c.get("address_in_source") or "entity (name-tied)"),
                         "label": STATE_OF[c["status"]], "temporal": c["temporal"], "claim_type": c.get("claim_type"),
                         "authority_role": c.get("authority_role"), "retrieved_at": r.get("completed_at") if r else None,
                         "published": r.get("published") if r else None, "effective_date": c.get("effective_date"),
                         "source_id": c.get("retrieval"), "url": safe_url(r.get("url")) if r else None, "excerpt": c.get("excerpt"),
                         "derived_from": c.get("derived_from") or [], "conflicts_with": c.get("conflicts_with") or []})

    unresolved = [q5d["question"]] + [f"{r.replace('_', ' ')}: {v['what_is_not_established']}" for r, v in q2.items() if v["state"] in ("unknown", "inferred", "disputed")]
    if q3["current_hvac"]["state"] == "unknown":
        unresolved.append("Current HVAC and thermostat setup at this premises")

    brief = {
        "schema": "fieldmind.precontact-benchmark-brief/v1", "record_ref": prospect["ref"], "arm": "assisted", "researcher_ref": "fmworker-prototype",
        "research_as_of": as_of.isoformat(), "policy_version": POLICY, "synthetic": bool(prospect.get("synthetic")),
        "program_context": {"label": "Duke EnergyWise Business MIMO opportunity research", "official_rule_version": None, "current_eligibility": "not_established"},
        "q1_current_operator": {"summary": q1_summary, "subject_and_suite": scope, "state": q1_state,
                                "candidate_identity_refs": [c["id"] for c in occ_claims], "accepted_identity_reference": None,
                                "claim_refs": [c["id"] for c in occ_claims], "listed_name_historical": listed,
                                "alternatives_not_merged": [f"{r['subject']} at {r['address_in_source']} ({r['id']}): {r['detail']}" for r in alternatives]},
        "q2_decision_authority": q2, "q3_energy_hvac_context": q3, "q4_uncertainty": q4, "q5_verify_first": q5d,
        "q6_priority_judgment": {"before": None, "after": None, "changed": None, "rationale": None, "evidence_refs": [], "human_judgment_not_eligibility": True,
                                 "note": "Left for the rep. The worker does not score or rank."},
        "findings": findings,
        "source_register_refs": [{"id": r["id"], "kind": r["kind"], "query": r.get("query"), "url": safe_url(r.get("url")) or None, "outcome": r.get("outcome"),
                                  "source_type": r.get("source_type"), "retrieved_at": r.get("completed_at"), "error": r.get("error")} for r in retrievals],
        "research_limitations": [f"{r['id']} {r.get('url') or r.get('query')}: {r.get('outcome')} ({r.get('error') or 'no detail'})" for r in failures]
                                + [f"Searched, not found: {s}" for s in not_found]
                                + ["Captured text is the retrieval tool's extract of each page, not the raw page",
                                   "Identity is a candidate until a reviewer accepts it"],
    }

    research = to_fieldmind(prospect, accepted, q1_state, occ, occ_name, q2, q5d, as_of, timing, retrievals)
    report = run_report(prospect, plan_steps, retrievals, claims, accepted, rejected, notes, timing, unresolved)
    return brief, research, report


def R_by(retrievals, rid):
    for r in retrievals:
        if r["id"] == rid:
            return r
    return None


SOURCE_NAMES = {"business_site": "Business website", "registry": "NC Secretary of State", "property_record": "County property record",
                "permit": "Permit record", "listing": "Business listing", "news": "News article", "review": "Review site", "search_results": "Search results"}


def to_fieldmind(prospect, accepted, q1_state, occ, occ_name, q2, q5d, as_of, timing, retrievals):
    status_map = {"source_supported": "found", "verified": "verified", "inferred": "inferred", "disputed": "conflicting", "unknown": "unknown", "historical": "unknown"}
    occupant = {"status": status_map[q1_state], "name": occ_name if q1_state in ("verified", "source_supported", "inferred") else None,
                "evidence": [occ["id"]] if occ else []}
    if occupant["status"] in ("verified", "found") and not occupant["name"]:
        occupant = {"status": "unknown", "name": None, "evidence": []}

    claims = []
    for c in accepted:
        r = R_by(retrievals, c.get("retrieval")) or {}
        cl = {"id": c["id"], "claim": c["text"][:300], "claim_type": c.get("claim_type", "other"), "about": c.get("about", "other"),
              "status": c["status"], "basis": "inferred" if c["status"] == "inferred" else "observed",
              "observed_at": (r.get("completed_at") or as_of.isoformat())[:10], "effective_date": c.get("effective_date"),
              "dimension": c.get("dimension", "business")}
        if cl["basis"] == "observed":
            cl["source"] = {"name": r.get("title") or SOURCE_NAMES.get(r.get("source_type"), "Source"), "type": r.get("source_type", "web"), "url": safe_url(r.get("url"))}
            cl["excerpt"] = (c.get("excerpt") or "")[:800]
        if c.get("conflicts_with"):
            cl["conflicts_with"] = c["conflicts_with"]
        if c.get("derived_from"):
            cl["derived_from"] = c["derived_from"]
        claims.append(cl)

    own = q2["business_ownership"]
    route = {"route": "unknown", "status": "unknown"}
    if own["state"] in ("verified", "source_supported") and occupant["status"] in ("found", "verified"):
        route = {"route": "owner_operator", "status": "inferred", "who": own["summary"].split(" (")[0],
                 "basis": "A source names this person as owner of the business operating at this address. Account authority is not established.",
                 "evidence": own["claim_refs"]}

    def prof(claim_type, key):
        cs = [c for c in accepted if c.get("claim_type") == claim_type and c["temporal"] == "current" and c["status"] != "inferred"]
        if not cs:
            return {"status": "not_found"} if key in timing.get("checked_profile", []) else {"status": "not_checked"}
        c = cs[0]
        r = R_by(retrievals, c.get("retrieval")) or {}
        st = "conflict" if c["status"] == "conflicting" else "found"
        return {"status": st, "value": str(c.get("value") or c["text"])[:200], "evidence": [x["id"] for x in cs], "source": r.get("title") or SOURCE_NAMES.get(r.get("source_type"), "Source"),
                "link": safe_url(r.get("url")), "date": (r.get("completed_at") or "")[:10]}
    profile = {"hours": prof("hours", "hours"), "owner": prof("ownership", "owner"), "structure": prof("structure", "structure"),
               "property": prof("property", "property"), "occupancy": prof("occupancy_change", "occupancy"), "hvac": prof("hvac", "hvac"),
               "electrical": prof("electrical", "electrical")}
    profile = {k: {kk: vv for kk, vv in v.items() if vv not in ("", None)} for k, v in profile.items()}

    found_dims = {c.get("dimension") for c in accepted}
    coverage = [{"dimension": d, "checked": "planned searches for " + d, "result": "found" if d in found_dims else "not_found"}
                for d in ("business", "people", "infrastructure", "energy")]

    premise = {"match": {"ref": prospect["ref"]}, "researched_at": as_of.isoformat(), "occupant": occupant,
               "summary": (f"{occ_name}: " if occ_name else "") + f"{len(accepted)} accepted claims from {sum(1 for r in retrievals if r.get('outcome') == 'ok')} sources. Utility-account authority and eligibility not established."[:600],
               "find_out_first": q5d["question"][:200], "can_infer": [c["text"] for c in accepted if c["status"] == "inferred"][:5],
               "cannot_conclude": ["Who holds or can sign for the utility account", "Current program eligibility", "Installed thermostats or HVAC controls"]
                                  if q2["hvac_facilities"]["state"] == "unknown" else ["Who holds or can sign for the utility account", "Current program eligibility"],
               "decision_route": route, "profile": profile, "coverage": coverage, "claims": claims}
    return {"schema": "fieldmind.research", "version": 2, "generated": now_iso(), "researcher": "fmworker-prototype",
            "run": {"minutes": round((timing.get("elapsed_seconds") or 0) / 60, 1), "searches": sum(1 for r in retrievals if r["kind"] == "search"),
                    "pages_read": sum(1 for r in retrievals if r["kind"] == "fetch" and r.get("outcome") == "ok")},
            "premises": [premise]}


def run_report(prospect, plan_steps, retrievals, claims, accepted, rejected, notes, timing, unresolved):
    by_reason = {}
    for r in rejected:
        by_reason[r["reason"]] = by_reason.get(r["reason"], 0) + 1
    el = timing.get("elapsed_seconds")
    return {"ref": prospect["ref"], "policy_version": POLICY, "synthetic": bool(prospect.get("synthetic")),
            "timing": {"elapsed_seconds": el, "cap_seconds": CAP_SECONDS, "within_cap": (el is not None and el <= CAP_SECONDS),
                       "phases": timing.get("phases", {}), "started_at": timing.get("started_at"), "finished_at": timing.get("finished_at")},
            "retrieval": {"planned_steps": len(plan_steps), "searches": sum(1 for r in retrievals if r["kind"] == "search"),
                          "fetches": sum(1 for r in retrievals if r["kind"] == "fetch"),
                          "ok": sum(1 for r in retrievals if r.get("outcome") == "ok"),
                          "failures": [{"id": r["id"], "kind": r["kind"], "target": r.get("url") or r.get("query"), "outcome": r.get("outcome"), "error": r.get("error")}
                                       for r in retrievals if r.get("outcome") != "ok"]},
            "claims": {"proposed": len(claims), "accepted": len(accepted),
                       "accepted_by_label": {s: sum(1 for c in accepted if c["status"] == s) for s in ("verified", "found", "inferred", "historical", "conflicting")},
                       "rejected": rejected, "rejected_by_reason": by_reason, "contradictions": notes},
            "unresolved_questions": unresolved}


# ---------------------------------------------------------------- timing
def timing_from(marks_path):
    """marks.jsonl rows: {"phase": "...", "at": iso}. Phase time runs until the next mark."""
    if not os.path.exists(marks_path):
        return {}
    rows = load_jsonl(marks_path)
    extra = {}
    for r in rows:
        for k in ("not_found", "checked_profile"):
            if k in r:
                extra.setdefault(k, []).extend(r[k])
    marks = [r for r in rows if "phase" in r]
    ts = [dt.datetime.fromisoformat(r["at"]) for r in marks]
    phases = {}
    for i in range(len(marks) - 1):
        phases[marks[i]["phase"]] = phases.get(marks[i]["phase"], 0) + round((ts[i + 1] - ts[i]).total_seconds())
    out = {"phases": phases, **extra}
    if len(ts) >= 2:
        out.update(started_at=marks[0]["at"], finished_at=marks[-1]["at"], elapsed_seconds=round((ts[-1] - ts[0]).total_seconds()))
    return out


# ---------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("plan"); s.add_argument("run_dir")
    s = sub.add_parser("mark"); s.add_argument("run_dir"); s.add_argument("phase", choices=PHASES + ["done"])
    s = sub.add_parser("log"); s.add_argument("run_dir"); s.add_argument("record_json", help="retrieval record; '-' reads stdin")
    s = sub.add_parser("build"); s.add_argument("run_dir"); s.add_argument("--as-of")
    s = sub.add_parser("rules", help="draft claims.json with the model-free rule extractor"); s.add_argument("run_dir")
    a = ap.parse_args(argv)
    d = a.run_dir
    if a.cmd == "plan":
        p = check_prospect(json.load(open(os.path.join(d, "prospect.json"))))
        steps = plan(p)
        json.dump(steps, open(os.path.join(d, "plan.json"), "w"), indent=1)
        print(json.dumps(steps, indent=1))
    elif a.cmd == "mark":
        with open(os.path.join(d, "marks.jsonl"), "a") as f:
            f.write(json.dumps({"phase": a.phase, "at": now_iso()}) + "\n")
    elif a.cmd == "log":
        rec = json.loads(sys.stdin.read() if a.record_json == "-" else a.record_json)
        rec.setdefault("completed_at", now_iso())
        with open(os.path.join(d, "retrieval.jsonl"), "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(rec["id"], rec.get("outcome"))
    elif a.cmd == "rules":
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import rules
        p = check_prospect(json.load(open(os.path.join(d, "prospect.json"))))
        claims = rules.extract(p, load_jsonl(os.path.join(d, "retrieval.jsonl")))
        json.dump(claims, open(os.path.join(d, "claims.json"), "w"), indent=1)
        print(f"{len(claims)} draft claims written by the rule extractor")
    elif a.cmd == "build":
        p = check_prospect(json.load(open(os.path.join(d, "prospect.json"))))
        steps = json.load(open(os.path.join(d, "plan.json"))) if os.path.exists(os.path.join(d, "plan.json")) else plan(p)
        retr = load_jsonl(os.path.join(d, "retrieval.jsonl"))
        claims = json.load(open(os.path.join(d, "claims.json")))
        timing = timing_from(os.path.join(d, "marks.jsonl"))
        as_of = parse_date(a.as_of) if a.as_of else dt.date.today()
        brief, research, report = build(p, steps, retr, claims, timing, as_of)
        for name, obj in (("brief.json", brief), ("research.v2.json", research), ("run-report.json", report)):
            json.dump(obj, open(os.path.join(d, name), "w"), indent=1)
        print(json.dumps({"accepted": report["claims"]["accepted"], "rejected": report["claims"]["rejected_by_reason"],
                          "elapsed_seconds": report["timing"]["elapsed_seconds"], "failures": len(report["retrieval"]["failures"])}))


if __name__ == "__main__":
    main()
