"""Model-free claim extractor (fallback when no model is available).

Generalized from the automated-002 proof's keyword rules: nothing here is specific to one business.
It writes claims.json drafts in the worker's format, with excerpts taken verbatim from the captured
text, so every draft still goes through fmworker.check_claims. Low recall by design: it finds
address lines, owner/founder mentions, production signals and explicit HVAC words, and never proposes
"verified", decision authority beyond ownership, utility-account authority or eligibility.
"""
import re
from urllib.parse import urlparse

STOP = {"the", "and", "of", "inc", "llc", "co", "company", "pllc", "corp"}
OWNER = re.compile(r"\b(owner|co-owner|founder|co-founder)\b", re.I)
PERSON = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b")
PROCESS = re.compile(r"\b(roast|roaster|roasting|manufacture|manufacturing|bakery ovens?|brew(?:ery|house|ing)|kitchen|production)\b", re.I)
HVAC = re.compile(r"\b(HVAC|thermostats?|heat pumps?|air[- ]conditioning|rooftop units?|chillers?|boilers?)\b", re.I)
WE = re.compile(r"\b(we|our)\b", re.I)
YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
NOT_PEOPLE = {"Chocolate Factory", "North Carolina", "United States", "Raleigh North", "Did You"}


def name_tokens(name):
    return [t for t in re.findall(r"[a-z0-9]+", (name or "").lower()) if t not in STOP and len(t) > 2]


def is_primary_host(url, listed_name):
    """A hostname that contains the listed name's distinctive words (a candidate, never an identity)."""
    host = (urlparse(url or "").hostname or "").replace("-", "").lower()
    toks = name_tokens(listed_name)
    return bool(toks) and sum(t in host for t in toks) >= min(2, len(toks))


def mentions_name(text, listed_name):
    toks = name_tokens(listed_name)
    low = (text or "").lower()
    return bool(toks) and sum(t in low for t in toks) >= min(2, len(toks))


def window(line, m, width=240):
    """Short verbatim excerpt around a match (always a substring of the line)."""
    a = max(0, m.start() - width // 2)
    b = min(len(line), m.end() + width // 2)
    return line[a:b].strip()


def address_regex(prospect):
    a = prospect["address"]
    street_word = re.escape(re.findall(r"[A-Za-z]{3,}", a["street"])[0]) if re.findall(r"[A-Za-z]{3,}", a["street"]) else ""
    return re.compile(r"\b" + re.escape(a["number"]) + r"\s+[^\n]{0,40}?" + street_word + r"[^\n]{0,80}", re.I)


def extract(prospect, retrievals):
    listed = prospect.get("listed_name") or ""
    addr_re = address_regex(prospect)
    claims, n = [], 0

    def add(**c):
        nonlocal n
        n += 1
        c.setdefault("basis", "observed"); c.setdefault("proposed_status", "found")
        c["id"] = f"R{n:02d}"; c["extractor"] = "rules"
        claims.append(c)

    for r in retrievals:
        if r.get("outcome") != "ok" or not r.get("captured_text") or r.get("kind") == "search":  # result lists have no single source
            continue
        primary = is_primary_host(r.get("url"), listed)
        page_about_listed = primary or mentions_name(r.get("title"), listed) or mentions_name(r.get("captured_text", "")[:600], listed)
        for line in r["captured_text"].splitlines():
            m = addr_re.search(line)
            if m and page_about_listed:
                addr = m.group(0).strip(" .,;")
                add(text=f"{listed} is listed at {addr}", claim_type="occupant_identity", about="occupant", subject=listed,
                    value=listed, value_key="occupant_name", retrieval=r["id"], excerpt=addr, address_in_source=addr, dimension="business")
            m = OWNER.search(line)
            if m and (primary or mentions_name(line, listed)):
                people = [p for p in PERSON.findall(line) if p not in NOT_PEOPLE and not mentions_name(p, listed)]
                if people:
                    years = sorted(set(YEAR.findall(line)))
                    add(text=f"{people[0]} named as {m.group(1).lower()}" + (f" ({years[-1]})" if years else " (undated)"),
                        claim_type="ownership", about="occupant", subject=listed, person=people[0], value=people[0],
                        authority_role="business_ownership", retrieval=r["id"], excerpt=window(line, m, 300),
                        temporal="historical" if years else "current", effective_date=years[-1] if years else None, dimension="people")
            if primary and WE.search(line):
                m = PROCESS.search(line)
                if m:
                    add(text=f"On-site production: the business's own site mentions '{m.group(0).lower()}'. Process equipment, not HVAC.", claim_type="other",
                        about="occupant", subject=listed, retrieval=r["id"], excerpt=window(line, m), dimension="energy")
                m = HVAC.search(line)
                if m:
                    add(text=f"The business's own site mentions {m.group(0)}", claim_type="hvac", about="occupant", subject=listed,
                        retrieval=r["id"], excerpt=window(line, m), dimension="energy")
    return claims
