# FieldMind

AI-native opportunity intelligence for B2B energy acquisition representatives. FieldMind gives field reps the available public data to understand a business's operation the way a brain would, and to find the brains behind it, before they walk in.

## What's here

| Path | What it is |
|---|---|
| `index.html` | The app: one self-contained page. It runs in the browser on its own, or as the hosted artifact with cloud sync and research from the phone. |
| `research/` | The research engine and local research server: source retrieval, evidence checks, brief generation, tests. See `ENGINE-INTEGRATION.md` and `RESEARCH-INTEGRATION.md`. |
| `worker/` | The merged research worker (retrieval adapters, rules, pilot tools, test list 001). See `worker/MERGE.md` and `worker/REPORT.md`. |
| `tests/` | App tests (Node). |
| `design-system/` | The FieldMind design system: `README.md` (brand book), `tokens.json` (Daylight and Night colors, type, spacing), components and logos (brain mark, app icon, Research button, favicon). |
| `skills/fieldmind-research/` | The Claude skill that runs FieldMind research, including the "Run my FieldMind research" phone flow. |
| `docs/`, `domain/`, `benchmarks/`, `proof/` | Specs, domain notes and evaluation material. |

## Run the tests

```sh
npm install
FIELDMIND_CHROMIUM=/path/to/chrome node --test --experimental-test-isolation=none tests/*.test.cjs
cd research && python3 -m unittest discover -s tests
python3 research/tests/e2e_replay.py
python3 research/tests/e2e_phone_research.py
```

## Data rules

- No real prospect records, account numbers or premise IDs belong in this repo.
- Test data is synthetic, plus public businesses used as research examples.
- Research sends only a business's name and address to public sources.
