# Manual-versus-assisted timing protocol

Prospective design: twenty cleared real prospects, two researchers, forty research runs. Each prospect is researched once manually and once with approved AI assistance by **different people**. No real runs are authorized now. Synthetic controls rehearse gates only; their not-run/time cells remain blank.

## Freeze comparable conditions

- Same exact task, six-question form, approved initial data, historical MIMO context, permitted public sources, cutoff date and output expectations in both arms. Manual means no generative AI; assisted means approved AI plus the human source checking/correction needed for a usable brief. No bonus internal/private sources for either arm.
- Fix the proposed per-run cap at **1,200 seconds (20 minutes)** before the future pilot, or document a reviewed alternative before starting. Unknowns are valid outcomes when the cap is reached.
- Record researcher experience, approved model/version/tool configuration, date, connectivity/source-access conditions and prior familiarity. Use the same source-access rules; log failed pages and limitations rather than quietly replace cases.
- Complete permission screening before starting the research timer; record its timestamp separately. Model prompt preparation, permitted data entry, source verification and final human correction **are timed**.

## Assignment and leakage control

Use ten matched pairs with A manual/B assisted for one case and the opposite for the partner. Each researcher has ten runs per arm; odd stratum counts balance across researchers. Neither person researches the same prospect twice. Randomize case order with a recorded seed; alternate order blocks to reduce fatigue/tool learning. Keep related sites in the same arm for a given researcher. Do not let either researcher see the other's findings, sources, reviewer key or independent verdicts until both runs are frozen.

The synthetic plan demonstrates the constraint: S02 and S05 share a fictional site cluster and are both assisted for A/manual for B. Pair/cluster identity is an exposure-control device, not accepted business/account identity. Future real cluster membership can require redesign; record cluster imbalance rather than force an invalid crossover. Reviewers should not supply corrective answers during a timed run.

## Clock definitions

- `wall_seconds = timer_finished_at - timer_started_at` using the same clock/timezone.
- Primary `elapsed_seconds = wall_seconds - pause_seconds`. Pause only for prespecified external interruptions (e.g. researcher pulled away), never for slow tools, source access, model latency, checking or corrections. Log pause reason; report raw wall time as derivable from timestamps.
- Track nonoverlapping phases: request/data preparation; source search/read; model/browser/tool wait; human verification/correction; final brief completion. Their sum should reconcile to elapsed time. No concurrent case processing.
- `active_seconds = elapsed_seconds - model_or_tool_wait_seconds`. Record it as a secondary measure; primary elapsed time includes waiting. Manual browser waiting belongs in the same wait field.
- Independent grading/adjudication time is not researcher brief-production time; log/review it separately and report overall study effort when relevant. A rep's final usefulness/priority assessment also has a separate timing note.

Stop when a review-ready six-question brief is frozen, at the cap, or immediately upon discovering a permission/suppression problem. Keep the unfinished brief and exact abort reason; do not record a blocked/aborted case as a zero-second success. A timeout records actual elapsed up to the cap, completion status and unresolved fields. Unexpected long waits are logged, not silently excluded.

## Analysis and fairness

Compute a paired per-prospect elapsed difference and relative reduction only for comparable, completed, positive-time runs. Report median and range, plus arm-specific medians and raw case counts. Report all timeouts, aborts and missing pairs separately. Show a capped-time sensitivity view including timed-out runs; do not claim speed based solely on successful easy cases. Never impute missing times as zero.

Two researchers and twenty prospects are a diagnostic pilot, not a causal productivity trial. Counterbalancing reduces familiarization/skill bias but cannot eliminate source changes, cluster imbalance or researcher differences. Report results by arm/researcher/stratum, retain disagreements and do not claim conversion, enrollment or production improvements from research timing.
