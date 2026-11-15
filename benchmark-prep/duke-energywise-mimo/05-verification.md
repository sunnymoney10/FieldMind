# Independent source-verification and evidence-quality rubric

Reviewer is independent of the researcher and must not grade an AI answer by asking the same model to confirm itself. Hide arm/researcher/timing metadata where feasible, randomize brief order and use a stable blinded brief ID. Record possible unblinding. Complete review before comparing timing or usefulness outcomes. The reviewer form uses a blinded brief reference, not an arm label. Keep `blind-map.blank.csv` with the study coordinator and unblind only after verdicts/adjudication freeze.

For the synthetic rehearsal only, give the reviewer the separate expected-distinction key after their initial source review. It tests protocol restraint; it is not external ground truth. For the future real study, there is no fabricated key: verify from permitted original sources and separately authorized observations. No business contact or private utility access is authorized by this package.

## Source verification sequence

1. Confirm the record's permission and suppression gate was passed before any research; otherwise mark blocked and stop.
2. Inspect the original permitted source, not just a search snippet, model citation or summary. Log source URL/title/issuer, publication/effective/retrieval dates, access success and a permitted excerpt/location. Preserve a capture only if storage terms allow it.
3. Match exact subject/suite/account/provider scope. A building record does not establish suite equipment. An old account or former business must not become the current operator/account by implication.
4. Compare each assertion to what the source actually says, including qualifiers and missing dates. Trace an inference to its premises; label assumptions and rival explanations.
5. Look for contradictory/current sources under the same allowed search/time policy, not only confirming sources. Log failed searches and access restrictions. No result means not found under those conditions, not proof of absence.
6. Assess current fact independently where feasible using an appropriately authoritative record or a separately authorized representative observation. A faithful quote of a possibly stale listing is **not** confirmed current reality. If verification is unavailable, mark unverifiable; do not guess.

## Per-dimension rubric (0 / 1 / 2)

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Source access/authenticity | Missing, fabricated or not inspected | Accessible excerpt/secondary report with limits | Original source inspected, issuer/location recorded |
| Exact scope / identity | Wrong or unsupported business/suite/account association | Ambiguity explicitly retained | Source clearly covers the claimed exact scope; acceptance separately reviewed |
| Claim faithfulness | Contradicts/overstates source | Accurate but incomplete/qualifier needs repair | Accurate text/qualifiers and no unsupported extension |
| Temporal handling | History/stale statement presented as current | Dates missing but uncertainty explicit | Dates/scope/freshness handled correctly; old context retained |
| Authority basis | Ownership/operator/property/account/HVAC conflated | Qualified role hypothesis; verified authority unknown | Correctly scoped attestation, or appropriately explicit unknown with source limitations |
| Contradiction handling | Conflicts hidden or cherry-picked | Conflict acknowledged but dependencies incomplete | Alternatives, implications and verification need documented |
| Provenance/dependencies | Untraceable or invented | Partial source/dependency trail | Every material finding traceable, with uncertainty and scope |

These dimensions are diagnostics, **not an averaged confidence probability or automatic opportunity score**. Use `N/A` for authority basis on nonauthority claims. An appropriate unknown may score well on restraint/handling, but never counts as a correct positive fact for accuracy. A qualified hypothesis is scored for support/logic, not counted as independently verified reality.

## Verdicts and denominators

For each material factual assertion, classify `correct / incorrect / unverifiable` for documentary accuracy: correct requires a faithful statement, correct scope and appropriate temporal/epistemic qualifiers. If a source is unavailable and cannot be independently checked, mark unverifiable rather than assume correct. For explicitly inferred statements, use the separate `supported / unsupported / N/A` inference verdict.

For a claimed current fact, separately classify `confirmed correct / confirmed incorrect / not verifiable / N/A` using the recorded independent verification method/reference. Report this actual-current-fact accuracy separately from source faithfulness. Do not convert “a listing reports X” into “X is confirmed true today.”

Do not count absent citations, fabricated sources or known wrong-scope assertions as harmless unverifiable cases: they are evidence defects/critical errors. Explicit unknown answers are coverage outcomes, not assertions added to the correct/incorrect denominator. Report unverifiable rates and coverage so the study cannot improve its percentage by hiding difficult cases.

## Critical errors and adjudication

Stop/review for: real processing without release; unauthorized transfer/access/contact; accepted wrong business/suite association; MIMO history presented as current installation/account succession/eligibility; fabricated evidence; or unsupported verified authority. Retain the original brief and record correction separately; do not silently edit away the failure.

A second independent reviewer adjudicates every critical error and material disagreement. Report initial verdicts, disagreements and resolution, including still-unverifiable facts. Ordinary scoring disagreements do not justify contacting businesses; that remains separately gated. Review a sample of unknowns and all unsupported-inference flags to assess whether research stopped reasonably or missed accessible evidence.
