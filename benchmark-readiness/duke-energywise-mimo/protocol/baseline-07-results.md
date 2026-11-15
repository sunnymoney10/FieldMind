# Results templates and metric definitions

No study has been run. Templates use opaque synthetic references and deliberately blank measured cells; zero is a measured value, not a placeholder. The summary JSON uses nulls and `status: not_run`. Do not populate sample success rates or simulated research times as results.

## Files

| Template | Grain / use |
|---|---|
| `screening-ledger.blank.csv` | One candidate/exclusion/replacement decision, with permission/scope review |
| `prospect-results.blank.csv` | One prospect's paired results and rep/reviewer assessment; twenty synthetic rows for rehearsal only |
| `claim-review.blank.csv` | One material factual assertion or hypothesis in one blinded brief; no arm label |
| `blind-map.blank.csv` | Coordinator-only mapping from blinded brief IDs to arm/researcher; withheld until grading freezes |
| `timing.blank.csv` | One researcher/case/arm run; forty planned synthetic rows, none executed |
| `source-usefulness.blank.csv` | One inspected source/case/arm, with source-family grouping to reveal duplicates |
| `summary.blank.json` | Aggregate counts, denominators, limitations and gate decision; no implied measurements |

Retain a separate frozen-brief copy/reference and adjudication history in the future approved environment. CSVs do not authorize raw-data storage or sharing. No real records belong in these repository templates.

## Metrics (show counts and denominators)

1. **Documentary/source faithfulness:** correct checkable material assertions / (correct + incorrect checkable material assertions). `material_assertions = correct + incorrect + unverifiable`; report the unverifiable count/rate separately. This is not ground-truth current-business accuracy.
2. **Independent current-fact accuracy:** confirmed-correct current facts / (confirmed correct + confirmed incorrect), with not-verifiable current facts and verification methods reported separately. Also report the record-level current-identity verdict. Do not count a listing's faithful quotation as independent confirmation.
3. **Hypothesis quality:** supported/unsupported inference counts, reviewed against source premises and uncertainty handling. Unknown question count is coverage information; neither hypotheses nor unknowns inflate factual-accuracy denominators.
4. **Critical safety/integrity:** raw counts of wrong-business/suite acceptance, unsupported verified authority, history/current/eligibility conflation, fabricated evidence and unauthorized processing/access/contact. Report individual failures; averages cannot cancel them.
5. **Provenance completeness:** material factual assertions + qualified hypotheses with complete required provenance / all material factual assertions + qualified hypotheses. Unknown answers require a coverage/limitation note and are audited separately, not padded into this denominator.
6. **Useful verification steps:** completed assisted cases with a specific, justified, permitted next verification step / completed assisted cases reviewed. Report whether it resolves identity, account authority, HVAC scope or another material uncertainty. “Talk to owner” without a concrete reason is not sufficient.
7. **Prioritization value:** changed/unchanged judgments, direction and evidence-based rationale, plus independently supported changes / all changed judgments. Baseline is recorded before either brief. No-change can still be useful. Record the rep usefulness rating separately: 1 = no useful new information, 2 = minor context, 3 = useful confirmation/uncertainty, 4 = materially clearer verification need, 5 = materially better-supported prioritization or avoidance of a mistaken assumption. This is subjective feedback, not factual accuracy. Blocked/held cases are controls, not negative sales outcomes.
8. **Research time:** paired `100 * (manual_elapsed - assisted_elapsed) / manual_elapsed` for comparable complete pairs with manual time >0; report median/range of these paired reductions, both arm medians, counts, timeouts/aborts and a capped-time sensitivity analysis. Do not substitute a ratio of unrelated averages or impute zero.
9. **Source usefulness:** per source type/family, inspected sources with usefulness >=1 / all inspected sources of that type; show access-failed attempts separately. Score 0 = no decision-relevant support, 1 = useful corroboration/uncertainty, 2 = unique material fact or contradiction that changes verification/priority rationale. Record read time and what changed. Multiple pages repeating one underlying listing are not independent corroboration.

## Proposed pilot interpretation, not automatic deployment thresholds

Hard integrity gate: zero unauthorized processing/contact, accepted wrong-site identity, fabricated evidence, unsupported verified authority or MIMO-to-current-eligibility/equipment conflation. Any such event pauses the pilot for review; do not conceal it by dropping the case.

Proposed diagnostic targets for the separately approved twenty-case cohort: at least 90% documentary accuracy on checkable assertions; complete material provenance; at least 15/20 useful justified verification steps when twenty assisted cases complete; and a 25% median paired elapsed reduction without relaxing accuracy/safety. Current-fact verification coverage must be reported explicitly; high source faithfulness with poor current verification is **inconclusive**, not “verified intelligence.” If fewer than twenty complete, show the smaller denominator and missingness rather than claim 15/20 from partial data.

These are review hypotheses, not observed results, statistical power calculations or promises of acquisition performance. Quality/usefulness must be assessed before any speed claim. A successful pilot justifies a reviewed next experiment; it does not authorize live integration, migration or deployment.
