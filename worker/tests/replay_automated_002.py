"""Replay the automated-002 live captures (SearXNG + Crawl4AI, Nov 15 2026 03:42 UTC) through the merged worker.

Usage: python3 -I tests/replay_automated_002.py <path to automated-002 run folder>
Reads that run's retrieval JSON and raw HTML (untrusted data; nothing in it is executed), normalizes each
page with worker/blocks.py, checks the SHA-256 against the original run, drafts claims with worker/rules.py,
then runs the normal worker checks and brief. Raw HTML is not copied into this repository.
"""
import json, os, sys, shutil, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "worker"))
import fmworker as W, blocks, rules  # noqa: E402

SRC = os.path.abspath(sys.argv[1])
OUT = os.path.join(ROOT, "runs", "replay-automated-002")
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
prospect = {"ref": "r1kedpv", "listed_name": "Videri Chocolate Factory", "synthetic": False,
            "address": {"number": "327", "street": "W Davie St", "suite": None, "city": "Raleigh", "state": "NC", "zip": "27601"}}
json.dump(prospect, open(os.path.join(OUT, "prospect.json"), "w"), indent=1)

disc = json.load(open(os.path.join(SRC, "discovery.json")))
summary = json.load(open(os.path.join(SRC, "summary.json")))
orig = json.load(open(os.path.join(SRC, "evidence.json")))
orig_sha = {c["source_id"]: c["normalized_sha256"] for c in orig["claims"]}

recs = []
for i, q in enumerate(disc["queries"], 1):
    res = (q.get("response") or {})
    unresp = res.get("unresponsive_engines") or []
    recs.append({"id": f"Q{i}", "kind": "search", "query": q["query"], "outcome": "ok" if q.get("result_count") else ("failed" if q.get("error") else "no_results"),
                 "error": q.get("error") or (f"engines blocked: {unresp}" if unresp else None), "source_type": "search_results",
                 "captured_text": "\n".join(f"{r.get('title','')} | {r.get('url','')}" for r in res.get("results", [])[:10]),
                 "started_at": q.get("retrieved_at"), "completed_at": q.get("retrieved_at"), "adapter": "searxng (automated-002)"})

sha_checks = {}
for f in ("retrieval-initial.json", "retrieval-follow.json"):
    path = os.path.join(SRC, f)
    if not os.path.exists(path):
        continue
    for s in json.load(open(path))["sources"]:
        raw = os.path.join(SRC, "raw-local-only", s["source_id"] + ".html")
        html = open(raw, encoding="utf-8", errors="replace").read() if os.path.exists(raw) else ""
        ok = s.get("success") and s.get("http_status") == 200 and len(html) > 500 and not blocks.looks_like_challenge(html)
        text, sha = blocks.normalize(html) if ok else ("", None)
        if s["source_id"] in orig_sha:
            sha_checks[s["source_id"]] = (sha == orig_sha[s["source_id"]])
        host = (s.get("final_url") or "").split("/")[2] if "//" in (s.get("final_url") or "") else ""
        stype = "business_site" if rules.is_primary_host(s.get("final_url"), prospect["listed_name"]) else ("listing" if "visitraleigh" in host or "downtownraleigh" in host else "news")
        recs.append({"id": s["source_id"], "kind": "fetch", "url": s.get("final_url") or s.get("requested_url"), "title": host,
                     "outcome": "ok" if ok else ("blocked" if s.get("http_status") in (401, 403, 429) else "failed"),
                     "error": None if ok else f"HTTP {s.get('http_status')} (not usable as evidence)", "source_type": stype,
                     "captured_text": text, "normalized_sha256": sha, "started_at": s.get("retrieved_at"),
                     "completed_at": s.get("finished_at") or s.get("retrieved_at"), "adapter": "crawl4ai (automated-002)"})

with open(os.path.join(OUT, "retrieval.jsonl"), "w") as fh:
    for r in recs:
        fh.write(json.dumps(r) + "\n")

t0 = dt.datetime.now(dt.timezone.utc)
claims = rules.extract(prospect, recs)
json.dump(claims, open(os.path.join(OUT, "claims.json"), "w"), indent=1)
start = dt.datetime.fromisoformat(summary["started_at"]); retr_end = start + dt.timedelta(seconds=summary["stage_cumulative_seconds"]["retrieval_finished_seconds"])
marks = [{"phase": "prepare", "at": start.isoformat()}, {"phase": "retrieve", "at": start.isoformat()}, {"phase": "extract", "at": retr_end.isoformat()}]
local = (dt.datetime.now(dt.timezone.utc) - t0)
marks += [{"phase": "check", "at": (retr_end + local).isoformat()}, {"phase": "done", "at": (retr_end + local).isoformat()},
          {"checked_profile": ["hours", "hvac", "owner"], "not_found": ["Official registry, permit and property records (not in this run's selection)"]}]
with open(os.path.join(OUT, "marks.jsonl"), "w") as fh:
    for m in marks:
        fh.write(json.dumps(m) + "\n")
brief, research, report = W.build(prospect, W.plan(prospect), recs, claims, W.timing_from(os.path.join(OUT, "marks.jsonl")), dt.date(2026, 11, 14))
for name, obj in (("brief.json", brief), ("research.v2.json", research), ("run-report.json", report)):
    json.dump(obj, open(os.path.join(OUT, name), "w"), indent=1)

result = {"sha256_matches_original": sha_checks, "searches": sum(r["kind"] == "search" for r in recs),
          "fetches": sum(r["kind"] == "fetch" for r in recs), "usable_pages": sum(r["kind"] == "fetch" and r["outcome"] == "ok" for r in recs),
          "draft_claims": len(claims), "accepted": report["claims"]["accepted"], "rejected": report["claims"]["rejected_by_reason"],
          "labels": report["claims"]["accepted_by_label"], "elapsed_seconds": report["timing"]["elapsed_seconds"],
          "q1": brief["q1_current_operator"]["summary"], "q5": brief["q5_verify_first"]["question"],
          "owner_row": brief["q2_decision_authority"]["business_ownership"]["summary"]}
json.dump(result, open(os.path.join(OUT, "replay-result.json"), "w"), indent=1)
print(json.dumps(result, indent=1))
