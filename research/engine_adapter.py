"""Run the merged FieldMind research engine on a finished retrieval job and project it for the app.

The retrieval worker (worker/fmworker.py: SearXNG + Crawl4AI) is unchanged. This adapter reads that job's
captures, normalizes each page (engine/blocks.py), drafts claims with the model-free rules (engine/rules.py) and
runs the engine's checks and six-question brief (engine/fmworker.py): identity/suite merge rejection, authority
limits, historical vs current, contradictions.

The app's attach rule is kept as is: the draft never sets the occupant, decision route or profile fields, and
claims are only "found" or "historical". What the engine concluded (candidate operator, disputes, suite
mismatches, sources not merged) reaches the rep as the six answers and the first question to verify.
"""
import json, os, re, sys, datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "engine"))
import fmworker as W, rules, blocks  # noqa: E402

SUITE_RE = re.compile(r"\b(?:STE|SUITE|UNIT|APT|#)\s*\.?\s*([0-9A-Z-]+)\b", re.I)
QUESTIONS = ["Who appears to operate here?", "Who makes the decisions?", "What's the energy and HVAC picture?",
             "What's old or uncertain?", "What should I check first?", "Does this change my priority?"]
ROLE_LABEL = {"business_ownership": "Owner", "business_operations": "Manager", "utility_account": "Utility account",
              "property": "Property owner", "hvac_facilities": "HVAC contact"}


def prospect_from(target):
    addr = target["addr"].strip()
    m = SUITE_RE.search(addr)
    suite = f"Ste {m.group(1)}" if m else None
    base = addr[:m.start()].strip(" ,") if m else addr
    parts = base.split(None, 1)
    number, street = (parts[0], parts[1]) if len(parts) == 2 and parts[0][:1].isdigit() else ("", base)
    if not number:
        raise ValueError("street address needs a number")
    return W.check_prospect({"ref": "r" + re.sub(r"[^0-9a-z]", "", target["ref"].lower())[:8], "listed_name": target["name"],
                             "synthetic": False, "address": {"number": number, "street": street, "suite": suite, "city": target["city"]}})


def records(run):
    run = Path(run)
    out = []
    disc = json.loads((run / "discovery.json").read_text())
    for i, q in enumerate(disc.get("queries", []), 1):
        res = q.get("response") or {}
        unresp = res.get("unresponsive_engines") or []
        out.append({"id": f"Q{i}", "kind": "search", "query": q.get("query"), "source_type": "search_results",
                    "outcome": "ok" if q.get("result_count") else ("failed" if q.get("error") else "no_results"),
                    "error": q.get("error") or (f"engines blocked: {unresp}" if unresp else None),
                    "captured_text": "\n".join(f"{r.get('title','')} | {r.get('url','')}" for r in res.get("results", [])[:10]),
                    "started_at": q.get("retrieved_at"), "completed_at": q.get("retrieved_at")})
    for name in ("retrieval-initial.json", "retrieval-follow.json"):
        f = run / name
        if not f.exists():
            continue
        for s in json.loads(f.read_text()).get("sources", []):
            raw = run / "raw-local-only" / f"{s['source_id']}.html"
            html = raw.read_text(errors="replace") if raw.exists() else ""
            usable = bool(s.get("success")) and s.get("http_status") == 200 and len(html) > 500 and not blocks.looks_like_challenge(html)
            text, sha = blocks.normalize(html) if usable else ("", None)
            url = s.get("final_url") or s.get("requested_url")
            out.append({"id": s["source_id"], "kind": "fetch", "url": url, "title": (url or "").split("/")[2] if "//" in (url or "") else "",
                        "outcome": "ok" if usable else ("blocked" if s.get("http_status") in (401, 403, 429) else "failed"),
                        "error": None if usable else (s.get("error") or f"HTTP {s.get('http_status')}"), "http_status": s.get("http_status"),
                        "source_type": "web", "captured_text": text, "normalized_sha256": sha,
                        "started_at": s.get("retrieved_at"), "completed_at": s.get("finished_at") or s.get("retrieved_at")})
    return out


ROLE_ORDER = ["business_ownership", "business_operations", "property", "hvac_facilities"]
TIE = {"match": "a public source lists this exact address", "suite_unconfirmed": "a public source lists this address; the suite isn't confirmed"}


def _year(f):
    d = f.get("effective_date") or f.get("published") or ""
    return str(d)[:4] if d else ""


def _who(f):
    who = f.get("person") or f.get("subject") or f.get("text")
    if f["label"] == "historical":
        return f"{who} ({_year(f) + ', ' if _year(f) else ''}may be out of date)"
    if f["label"] == "disputed":
        return f"{who} (sources disagree)"
    return who


def answers(brief, report):
    """Plain-language six answers for the rep, built from the findings (no internal IDs or status codes)."""
    q1, find = brief["q1_current_operator"], brief["findings"]
    occ = [f for f in find if f.get("claim_type") in ("occupant_identity", "operating_status")]
    listed = q1.get("listed_name_historical")
    if q1["state"] == "disputed":
        a1 = "Sources disagree: " + "; ".join(f"{f['text']}{' (' + _year(f) + ')' if _year(f) else ''}" for f in occ if f["label"] == "disputed") + ". Who operates here now isn't confirmed."
    elif q1["state"] == "unknown":
        a1 = "No public source ties a business to this exact address."
    else:
        cur = next((f for f in occ if f["label"] in ("source_supported", "verified") and f["temporal"] == "current"), None)
        closed = next((f for f in occ if f.get("claim_type") == "operating_status" and f["temporal"] == "current"), None)
        if cur and cur.get("claim_type") == "occupant_identity":
            a1 = f"Likely {cur['subject']}: a public source lists this address" + ("." if " Suite " not in q1["summary"] and "suite not confirmed" not in q1["summary"] else "; the suite isn't confirmed.")
        elif closed:
            a1 = f"{closed['text']}. Who operates here now isn't confirmed."
        else:
            a1 = "No public source ties a business to this exact address."
        if listed and cur and W.name_key(listed) != W.name_key(cur["subject"]):
            a1 += f" Your list says {listed}."
    alts = q1.get("alternatives_not_merged") or []
    if alts:
        a1 += " Also found, but not at this address or suite: " + "; ".join(x.split(" (")[0] for x in alts[:3]) + "."
    rows, missing = [], []
    for role in ROLE_ORDER:
        fs = [f for f in find if f.get("authority_role") == role]
        if fs:
            rows.append(f"{ROLE_LABEL[role]}: " + "; ".join(_who(f) for f in fs) + ".")
        else:
            missing.append(ROLE_LABEL[role].lower().replace("hvac", "HVAC"))
    if not rows:
        rows.append("No owner or manager found.")
    rows.append("Ask who signs for the utility account.")
    a2 = " ".join(rows)
    hvac = [f["text"] for f in find if f.get("claim_type") == "hvac" and f["label"] != "inferred"]
    prod = list(dict.fromkeys(re.search(r"mentions '([^']+)'", f["text"]).group(1) for f in find if re.search(r"mentions '([^']+)'", f.get("text") or "") and (f.get("text") or "").startswith("On-site production")))
    a3 = ("; ".join(hvac) + ". " if hvac else "No HVAC information found. ")
    if prod:
        a3 += f"Its own site mentions on-site production ({', '.join(prod)}), which is process equipment, not HVAC. "
    a3 += "Eligibility not confirmed."
    parts = []
    dis = [f["text"] for f in find if f["label"] == "disputed"]
    old = [f"{f['text']}" for f in find if f["label"] == "historical" and not f.get("authority_role")]
    inf = [f["text"] for f in find if f["label"] == "inferred"]
    if dis: parts.append("Sources disagree: " + "; ".join(dis[:3]) + ".")
    if old: parts.append("Older information: " + "; ".join(old[:3]) + ".")
    if inf: parts.append("Inferred, not stated by a source: " + "; ".join(inf[:3]) + ".")
    a4 = " ".join(parts) or "Nothing flagged."
    q5 = brief["q5_verify_first"]
    a5 = q5["question"]
    a6 = "FieldMind doesn't score this. Use your own judgment; nothing here sets eligibility or priority."
    return [{"question": q, "answer": a[:1200]} for q, a in zip(QUESTIONS, (a1, a2, a3, a4, a5, a6))]


def project_run(run, target, summary):
    prospect = prospect_from(target)
    recs = records(run)
    claims = rules.extract(prospect, recs)
    timing = {"elapsed_seconds": round(summary.get("elapsed_seconds") or 0), "started_at": summary.get("started_at"), "finished_at": summary.get("finished_at")}
    brief, research, report = W.build(prospect, W.plan(prospect), recs, claims, timing, dt.date.today())
    Path(run, "engine-brief.json").write_text(json.dumps(brief, indent=1))
    Path(run, "engine-report.json").write_text(json.dumps(report, indent=1))
    by_id = {r["id"]: r for r in recs}
    out_claims = []
    for f in brief["findings"]:
        if f["label"] == "inferred" or not W.safe_url(f.get("url")):
            continue  # inferences stay in the answers; only sourced excerpts become claims
        hist = f["label"] == "historical"
        prefix = "Sources disagree: " if f["label"] == "disputed" else ("Older information: " if hist else "")
        r = by_id.get(f["source_id"], {})
        out_claims.append({"id": f["claim_id"], "claim": (prefix + f["text"])[:300], "claim_type": f.get("claim_type") or "other", "about": "other",
                           "status": "historical" if hist else "found", "basis": "observed",
                           "source": {"name": r.get("title") or "Source", "type": "website", "url": f["url"]},
                           "observed_at": (f.get("retrieved_at") or "")[:10], "excerpt": f.get("excerpt"), "retrieved_at": f.get("retrieved_at"),
                           "normalized_sha256": r.get("normalized_sha256"), "time_state": "historical" if hist else "unknown",
                           "current_verified": False, **({"conflicts_with": f["conflicts_with"]} if f.get("conflicts_with") else {})})
    q = answers(brief, report)
    metrics = dict(summary)
    metrics.update(engine_policy=W.POLICY, engine_accepted=report["claims"]["accepted"], engine_rejected=report["claims"]["rejected_by_reason"],
                   engine_unresolved=report["unresolved_questions"][:6])
    premise = {"match": {"ref": target["ref"]}, "researched_at": dt.date.today().isoformat(),
               "occupant": {"name": None, "status": "unknown"}, "decision_route": {"route": "unknown"},
               "profile": {"owner": {"status": "not_checked"}, "hvac": {"status": "not_checked"}}, "claims": out_claims,
               "summary": (q[0]["answer"][:400] + f" {len(out_claims)} findings from public sources. Check who operates here and who decides on site.")[:600],
               "find_out_first": brief["q5_verify_first"]["question"][:200],
               "cannot_conclude": ["Current HVAC equipment", "Program eligibility", "Who signs for the utility account", "Permission to contact"],
               "research_questions": q, "research_method": "public_sources+" + W.POLICY, "research_metrics": metrics}
    return {"schema": "fieldmind.research", "version": 2, "generated": dt.datetime.now(dt.timezone.utc).isoformat(), "premises": [premise]}
