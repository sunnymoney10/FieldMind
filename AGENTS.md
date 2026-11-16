# FieldMind project instructions

FieldMind is an AI-native opportunity intelligence tool for B2B energy acquisition field reps working Duke EnergyWise Business MIMO lists. It gives reps available public data to understand a business's operation — the brains of the operation — before they walk in.

## Product center

The rep is the expert. FieldMind arms them with signal — not scripts or scores. Research surfaces what's publicly findable about a business; the rep decides what it means and what to do next.

The app is one self-contained HTML page (`index.html`). It runs in any browser, offline or online. The research engine (`research/`) runs locally or as a hosted service and is called from the app or from the Claude research skill.

## Data rules (non-negotiable)

- **No real prospect records, premise IDs, or account numbers in this repo.** Ever.
- Test data is synthetic. Public businesses may be used as research examples.
- Research sends only a business name and address to external sources.
- Research imports must never auto-approve prospects or remove suppression flags.
- Do not open, process, or commit real MIMO lists or customer data.
- Do not print secrets, tokens, or customer identifiers to logs or test output.

## Working rules

- Run `npm test` before pushing any JS change to main.
- Run `cd research && python3 -m unittest discover -s tests` before pushing any Python change.
- The app must work fully offline (no CDN dependency for core function).
- Keep synthetic and real data paths clearly separated in code and in tests.
- Security and policy tests (`tests/security.test.cjs`, `tests/policy-b2a.test.cjs`) must always pass.

## Key paths

| Path | What it is |
|---|---|
| `index.html` | The app |
| `research/` | Research engine: source retrieval, brief generation, tests |
| `worker/` | Merged research worker and pilot tools |
| `tests/` | App tests (Node) |
| `design-system/` | Brand book, tokens, logos (brain mark, app icon, favicon) |
| `skills/fieldmind-research/` | Claude skill for phone-based research flow |

## Brand

The mark is a bold continuous brain line with a citron signal point — "the brains of the operation." Colors: Daylight (`#F1EBDF` background, `#1C2022` ink, `#FF3D8C` accent, `#DCEF55` citron). Type: Inter. Full system in `design-system/README.md`.
