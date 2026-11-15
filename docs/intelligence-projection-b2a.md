# Source-backed precontact intelligence projection — B2A

Implementation: `createIntelligenceProjection` in `domain/intelligence.mjs`. Reviewable synthetic output: [`examples/b2a-intelligence.json`](../examples/b2a-intelligence.json). Neither is connected to the live interface.

## Evidence -> finding, without inventing authority

1. Enforce snapshot bytes/count/depth/edge budgets before recursive B1 validation. Reject broken/cyclic references rather than silently dropping them.
2. Validate typed identity, exact source scope, provenance, observation verification and workspace references. Clone one validated snapshot; build subject/claim/observation/source indexes once, not one whole-workspace scan per card.
3. Evaluate dependencies in topological order. Apply the versioned claim/source/risk freshness policy. A qualified hypothesis inherits its source clocks and its target decision-risk cap; new AI text cannot reset evidence age.
4. Keep a Claim's exact value and citations/rows/observations plus original dates. Display origin (AI/public/field/list) independently from source support and verification. Reported source claims are useful even when authority is unknown.
5. Preserve explicit contradictions bidirectionally. Also flag competing current values for single-valued operating status, occupant identity, hours and each authority predicate. Multiple HVAC/energy facts may coexist; differing HVAC statements are not automatically mutually exclusive. Dependency disputes propagate to conclusions.
6. Return structured data, **not HTML**. Future rendering must retain Stage A escaping and safe-link rules. Do not interpolate raw preview text into HTML.

Finding fields include value, status, freshness, usefulContext, epistemic basis, authorityState, observed/effective/expiry dates, policy version, qualitative support grade, dependency/conflict IDs, reason and provenance. Qualitative grades describe support; `confidenceIsProbability` is always false. No confidence percentage, opportunity score or eligibility claim is invented.

A retrieval-produced AI claim with a valid cited report uses a conservative public-source window and remains source-supported, not verified authority. A citation alone cannot prove its truth or authoritative source class. Representative direct observation and record review are distinguishable through referenced FieldObservations. Inferences retain assumptions through their dependencies; they do not make a business owner a utility-account or HVAC decision-maker.

## Useful older information

Stale/historical/superseded records remain visible with qualifiers. “Not sufficiently recent to establish current fact” is not “nothing useful was found.” Unknown current status may still have useful context, exact source value and a verification prompt. Future evidence is not displayed as available as-of knowledge. Historical MIMO context never becomes a current equipment inventory, account succession or eligibility.

No automatic conflict-clearing or supersession workflow is introduced. B2A can report conflicts and retain the evidence; resolving them requires a separately reviewed event model and representative/manager workflow.

## Brief construction and verification first

`brief(subject)` returns findings for **that exact subject**, a reason to verify first and no automatic opportunity ranking. It prioritizes a disputed finding, then unestablished authority, then stale/unknown evidence or an inference. With no useful findings it asks to establish current occupant and utility-account authority. `priorityRecommendation: human_review` and `eligibility: not_established` prevent findings from becoming a disguised enrollment decision.

A future prospect brief must join only **explicitly reviewed** Business/Occupancy/Premise/account references; B2A intentionally does not traverse same addresses, chain names or legacy `acct` fields to fabricate a complete business story. It should answer:

| Rep question | Evidence to show |
|---|---|
| Who appears to operate here? | Occupancy/occupant identity, exact location/suite, source date, alternatives and unresolved identity |
| Who likely controls the decisions? | Five separate authority rows: ownership, operations, account, property, HVAC/facilities; source-reported hypotheses remain visible |
| Energy/HVAC context? | Scoped permits, public comfort/energy reports and explicit inferences; historical equipment separately |
| What is old/uncertain/contradicted? | Temporal and epistemic qualifiers, conflicts and unsupported dependencies |
| What should I verify first? | Highest material identity/authority uncertainty or contradiction with its reason |
| Does this change priority? | Rep records a before/after judgment and evidence-based rationale in the benchmark; no automatic route/sales script |

## Performance and output bounds

One projection compiles all claims once, then exact-subject/claim lookups use indexes. Contradictory single-valued groups retain total alternative count and at most twenty displayed alternative IDs per finding to avoid quadratic output. Raw Claims remain intact. Large result sets must be paginated at a future service/UI boundary, not rendered all at once. The current benchmark measures server-side computation, not mobile main-thread responsiveness or end-to-end LLM research latency.
