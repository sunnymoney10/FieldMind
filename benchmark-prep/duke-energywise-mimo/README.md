# FieldMind: Duke EnergyWise Business MIMO benchmark preparation

**SYNTHETIC ONLY — real-record processing is not authorized.** This package prepares a future benchmark using a separately authorized subset of Brian's approved MIMO list. It contains no actual list records, customer accounts, public-source research, business contacts or current Duke eligibility determinations.

The program name is the requested benchmark context, not a claim that the fictional sites participated or qualify. No current Duke terms, equipment requirements, incentive values or account/territory rules were researched or validated for this preparation. Confirm current official program context separately before a real run.

## Start here

1. [Permission checklist](01-permissions.md): canvassing, AI, enrichment, storage, access and retention are separate decisions.
2. [Balanced cohort protocol](02-cohort.md): twenty eligible research seats; suppressed/ambiguous cases stay outside active research until resolved.
3. [Synthetic fixture guide](03-fixtures.md): twenty rehearsal records, sixty fictional source snippets and a separate reviewer key.
4. [Six-question brief](04-brief.md), [blank JSON brief](templates/intelligence-brief.blank.json) and [synthetic illustration](templates/intelligence-brief.synthetic-example.json) (not a benchmark result).
5. [Independent verification rubric](05-verification.md): source faithfulness and independently checked current accuracy are distinct.
6. [Manual/assisted timing protocol](06-timing.md): counterbalanced, separate researchers; same task, time cap and source access.
7. [Results definitions/templates](07-results.md): all result cells remain blank; no benchmark outcome is claimed.
8. [Go/no-go checklist](08-go-no-go.md): current decision is **NO GO for real records**.

Use [authorization-review.json](templates/authorization-review.json) for the future permission review. It is pending/unconfirmed; editing the form does not grant authority or release processing.

## Rehearsal materials

- [Researcher fixtures](fixtures/prospects.synthetic.json)
- [Fictional source packets](fixtures/source-packets.synthetic.json) — URLs use `.invalid`; do not fetch them.
- [Reviewer-only key](fixtures/reviewer-key.synthetic.json) — withhold during a blind rehearsal; synthetic expectations, not real-world ground truth.
- [Planned synthetic cohort/arms](templates/cohort-plan.synthetic.csv) — four blocked gate controls, sixteen hypothetical research candidates. All permissions for real processing remain ungranted.
- [Prospect results](templates/prospect-results.blank.csv), [claim review](templates/claim-review.blank.csv), [timing](templates/timing.blank.csv), [source usefulness](templates/source-usefulness.blank.csv), [screening ledger](templates/screening-ledger.blank.csv), [summary](templates/summary.blank.json).

The twenty-record rehearsal is **not** twenty authorized real research cases. Its four gate controls test stopping behavior. A future real cohort must fill twenty cleared seats with stratum-matched replacements and keep exclusions in a separate ledger.

## Integrity checks

From this directory, run `python tools/validate_package.py`. It checks fixture balance, separation of history/current state, source references, blocked controls, counterbalanced assignments, cluster leakage, untouched blank results and pending permission gates. It reads only these local synthetic package files. `generate_synthetic.py` regenerates known fictional fixtures/templates; it accepts no prospect input and is not an importer.

Current status: [validation report](VALIDATION.md). None of the prep checks establishes real research accuracy, real authentication, program eligibility or permission to process real records.

No live app, domain/persistence adapter or production infrastructure is changed by this package. No contact, real-data upload, research, transformation, migration, deployment or main merge is authorized. Stop after reviewing the package and permissions.
