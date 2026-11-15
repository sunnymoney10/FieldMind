# Merged worker (Nov 14, 2026, 22:46–23:10 ET)

Combines this worker (rules, brief, pilot tools, test list 001) with the separate automated-002 proof (SearXNG + Crawl4AI automation, menu/footer filter, 9 regression tests). The proof had been built without this worker, so the two had drifted apart.

## What came from where

| Piece | Source | State |
|---|---|---|
| Acceptance rules, six-question brief, FieldMind v2 file, run report | this worker | 24 tests pass |
| Pilot helper: prepare, merge, summary, intake guard | this worker | 6 tests pass |
| Menu, footer and form filter (`worker/blocks.py`) | automated-002, ported unchanged | 3 ported tests pass. Replay reproduces the original SHA-256 on all 4 usable pages. |
| Model-free rule extractor (`worker/rules.py`, `fmworker.py rules`) | automated-002 keyword rules, generalized (no Videri values) | 6 ported tests pass. Replay reproduces the original run's 5 leads. |
| SearXNG + Crawl4AI connector (`adapters/oss_retriever.py`) | automated-002 settings, generalized to any prospect | The merged form hasn't been run (no network here). The original ran live in 30.4 s. |
| `adapters/searxng/settings.yml`, `adapters/requirements-proof.lock` | automated-002 | Local-only search configuration; pinned to Crawl4AI 0.9.5 |

## Replay of automated-002 through the merged worker
- **Input:** that run's real captures from Nov 15, 03:42 UTC: 4 searches and 5 pages (1 was a redirect and wasn't used).
- **Normalization:** 4 of 4 page hashes match the original run.
- **Rule extractor:** 5 draft claims (2 address, 2 production signal, 1 owner mention). All 5 were accepted. The 2023 owner mention is marked historical, not current.
- **Brief:**
  - Operator: Videri is a candidate.
  - First question: "The list has no suite. Sources put Videri Chocolate Factory in Suite 100. Is this premises that suite?"
  - Ownership row: current owner not found; one historical mention.
- **App import (isolated copy):** schema valid, 1 of 1 matched, 5 source links shown, label "Decision route unknown". The original proof imported an empty claim list; this one carries the sourced claims.

## Bugs found while merging (fixed)
- A broader challenge-page pattern I added ("captcha") rejected 3 good pages because the word appears in ordinary page scripts. Reverted to the original pattern.
- The rule extractor drafted claims from search-result lists, which have no single source. The worker rejected them; the extractor now skips them.
- The business's own site writes the suite as "Sweet 100". The address matcher now reads it as Suite 100.

## Still open
- Signed-in Claude Code hasn't run model extraction yet. The rule extractor is a low-recall fallback and doesn't understand meaning.
- The generalized connector needs one live run on your computer.
- Crawl4AI requires attribution: "This product includes software developed by UncleCode (https://x.com/unclecode) as part of the Crawl4AI project (https://github.com/unclecode/crawl4ai)." SearXNG is AGPL-3.0: run it unmodified and local only.
