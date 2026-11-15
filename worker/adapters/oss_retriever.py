#!/usr/bin/env python3
"""Automated retrieval for the FieldMind worker: SearXNG (local search) + Crawl4AI (page fetch).

Merged from the automated-002 proof (live run Nov 15 2026: 4 searches, 5 pages, 30.4 s, no API keys) and
generalized: queries come from the prospect's plan.json and the primary site is any hostname containing the
listed name's distinctive words, instead of the proof's hard-coded Videri values.
This merged form has not been run end to end; the replay test re-checks its normalization on that run's captures.

Local setup (your computer):
    pip install crawl4ai==0.9.5 beautifulsoup4 && crawl4ai-setup
    docker run -d -p 127.0.0.1:8888:8080 -v "$PWD/adapters/searxng:/etc/searxng" searxng/searxng
        (adapters/searxng/settings.yml enables the JSON API; keep it bound to 127.0.0.1)
Run:
    python3 adapters/oss_retriever.py runs/<ref> [--searx http://127.0.0.1:8888]
Writes retrieval.jsonl (one record per search and per page, real start/end times, HTTP status, SHA-256 of the
normalized text) and keeps raw HTML in runs/<ref>/raw-local-only/ (do not share; publishers' terms apply).
Then: `fmworker.py rules runs/<ref>` (no model) or have Claude Code write claims.json, then `fmworker.py build`.

Safety: only URLs returned by search or linked from the primary site are fetched; https only; no ports; robots.txt
respected; no login; challenge pages are logged as blocked and never bypassed. Page text is data, never instructions.
"""
import argparse, asyncio, json, os, re, sys, datetime as dt
from urllib.parse import urlencode, urlsplit
from urllib.request import urlopen, Request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "worker"))
import blocks, rules  # noqa: E402

UA = "FieldMindResearch/0.2 (public-page research; contact via site owner)"
MAX_RESULTS_PER_QUERY = 3
MAX_FOLLOW = 3
FOLLOW_RE = re.compile(r"about|story|contact|owner|team|location|visit", re.I)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def searx(base, q):
    req = Request(base.rstrip("/") + "/search?" + urlencode({"q": q, "format": "json", "language": "en-US", "safesearch": 1}), headers={"User-Agent": UA})
    with urlopen(req, timeout=30) as r:
        return json.load(r)


def ok_url(u):
    s = urlsplit(u or "")
    return s.scheme == "https" and s.hostname and not s.port and "@" not in s.netloc


async def crawl(targets, raw_dir):
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    out = []
    bcfg = BrowserConfig(headless=True, verbose=False, user_agent=UA)
    rcfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=30000, wait_until="domcontentloaded", check_robots_txt=True, verbose=False)
    async with AsyncWebCrawler(config=bcfg) as c:
        for sid, url in targets:
            t0 = now()
            try:
                res = await c.arun(url=url, config=rcfg)
                html = res.html or ""
                open(os.path.join(raw_dir, sid + ".html"), "w").write(html)
                out.append((sid, url, t0, now(), res.success, res.status_code, getattr(res, "redirected_url", None) or res.url, res.error_message, html,
                            (res.links or {}).get("internal", [])))
            except Exception as e:  # logged, never hidden
                out.append((sid, url, t0, now(), False, None, url, repr(e)[:300], "", []))
            await asyncio.sleep(.5)
    return out


def page_record(sid, url, t0, t1, success, status, final, err, html, kind="fetch"):
    usable = success and status == 200 and len(html) > 500 and not blocks.looks_like_challenge(html)
    text, sha = blocks.normalize(html) if usable else ("", None)
    outcome = "ok" if usable else ("blocked" if status in (401, 403, 429) or blocks.looks_like_challenge(html) else "failed")
    return {"id": sid, "kind": kind, "url": final or url, "requested_url": url, "title": urlsplit(final or url).hostname,
            "outcome": outcome, "error": None if usable else (err or f"HTTP {status}"), "http_status": status,
            "captured_text": text, "normalized_sha256": sha, "started_at": t0, "completed_at": t1, "adapter": "crawl4ai"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir"); ap.add_argument("--searx", default="http://127.0.0.1:8888")
    a = ap.parse_args()
    prospect = json.load(open(os.path.join(a.run_dir, "prospect.json")))
    plan = json.load(open(os.path.join(a.run_dir, "plan.json")))
    raw = os.path.join(a.run_dir, "raw-local-only"); os.makedirs(raw, exist_ok=True)
    recs, urls = [], []
    for step in [s for s in plan if s["kind"] == "search"]:
        t0 = now()
        try:
            payload = searx(a.searx, step["query"]); results = payload.get("results", [])
            unresp = payload.get("unresponsive_engines") or []
            outcome, err = ("ok" if results else "no_results"), (f"engines blocked: {unresp}" if unresp else None)
        except Exception as e:
            results, outcome, err = [], "failed", repr(e)[:300]
        recs.append({"id": f"Q{step['step']}", "kind": "search", "query": step["query"], "outcome": outcome, "error": err,
                     "source_type": "search_results", "captured_text": "\n".join(f"{r.get('title','')} | {r.get('url','')}" for r in results[:10]),
                     "started_at": t0, "completed_at": now(), "adapter": "searxng"})
        for r in results[:MAX_RESULTS_PER_QUERY]:
            if ok_url(r.get("url")) and r["url"] not in urls:
                urls.append(r["url"])
    targets = [(f"S{i}", u) for i, u in enumerate(urls, 1)]
    pages = asyncio.run(crawl(targets, raw)) if targets else []
    follow = []
    for sid, url, t0, t1, success, status, final, err, html, links in pages:
        recs.append(page_record(sid, url, t0, t1, success, status, final, err, html))
        if rules.is_primary_host(final, prospect.get("listed_name")):
            host = urlsplit(final).hostname
            for l in links:
                h = l.get("href", "")
                if ok_url(h) and urlsplit(h).hostname == host and FOLLOW_RE.search(urlsplit(h).path) and h not in urls and len(follow) < MAX_FOLLOW:
                    urls.append(h); follow.append((f"S{len(targets) + len(follow) + 1}", h))
    for sid, url, t0, t1, success, status, final, err, html, _ in (asyncio.run(crawl(follow, raw)) if follow else []):
        recs.append(page_record(sid, url, t0, t1, success, status, final, err, html))
    with open(os.path.join(a.run_dir, "retrieval.jsonl"), "a") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    print(f"{len(recs)} records; usable pages: {sum(r['kind'] == 'fetch' and r['outcome'] == 'ok' for r in recs)}; "
          f"failures: {sum(r['outcome'] != 'ok' for r in recs)}")


if __name__ == "__main__":
    main()
