# Stage B2A review package

Base: accepted B1 commit `d236985fd1637f138a94068686d20a44b711aa11`. Development branch: `codex/stage-a-foundation`. Scope: proposed policy, read-only compatibility preview, isolated relational repository proof, structured intelligence projection and synthetic performance evidence. No live integration or real prospect research occurred.

## Deliverables

- [Evidence freshness policy](evidence-freshness-b2a.md): claim/source/decision-risk windows, useful older context, qualified hypotheses, explicit unknowns and disputes. The day limits remain proposed, not active product rules.
- [Authorization/suppression scope](suppression-authorization-b2a.md): seven exact subject kinds, manager-supported target expansion and ambiguous-scope review holds, without inherited suppression through shared names/addresses.
- [Read-only compatibility preview](compatibility-preview-b2a.md) and [synthetic preview output](../examples/b2a-legacy-preview.json): exact source text, every raw field, unknown metadata and orphan notes retained; zero accepted identities/writable domain records.
- [Repository boundary/test results](repository-boundary-b2a.md): disposable in-memory relational proof, synthetic verifier/current-role directory, workspace checks, revision conflicts, transactional rollback, command audit and lost-acknowledgement retry. Not real authentication or production storage.
- [Intelligence projection specification](intelligence-projection-b2a.md) and [synthetic findings](../examples/b2a-intelligence.json): source-backed information remains useful separately from representative verification/authority; dependencies, contradiction alternatives, provenance, dates and verify-first rationale stay inspectable.
- [Performance results](performance-b2a.md) and [raw measurements](../benchmarks/results-b2a.json).
- [Stage B2B proposal](stage-b2b-proposal.md), led by the [small authorized real-world intelligence benchmark](real-world-benchmark-proposal.md), not by a test-count milestone.

## Verification

`FIELDMIND_CHROMIUM=/usr/bin/chromium npm test`: **79 passed, 0 failed, 0 skipped**. Retained Stage A/B1 tests: 48; B2A policy/preview/projection: 19; isolated repository: 12. Standard setup: Node >=22.13 (tested 24.22.1), `npm ci`, `npx playwright install chromium`; omit the environment override when using Playwright-managed Chromium. Node's SQLite engine is used only by the proof/bench tests, not the standalone app.

`npm run bench`: **nine timing budgets and one whole-process memory smoke budget passed**. Measurements and methodology are in the linked report. 1,000 prospects/8,000 claims projected at about 486 ms p95; 5,000/40,000 at about 1,438 ms. The 10,000-record preview took about 230 ms. Whole benchmark process peak RSS was about 743 MiB; this is an explicit full-snapshot/batch constraint, not a mobile performance claim.

`index.html` remains byte-identical to Stage A/B1 (Git blob `86593fcd00885758c91ef0d7f2fd0f5a594b4454`). Existing interface, design, workflows, localStorage/Claude adapter and input formats are unchanged. New modules are not loaded by the app. B1 pure append gained only a trusted internal current-role option to separate current permissions from historical provenance; it is not a request-provided auth context. No new npm dependency was added. Development Node minimum was narrowed to 22.13 for built-in SQLite test availability.

The retained three legacy KNOWN RISK tests still reproduce unresolved app identity/history defects. Green tests do not mean the legacy app is integrated or safe for real migration.

## Remaining risks and decisions

1. Synthetic credentials and in-memory transactions do not prove real authentication, network/session controls, multi-process concurrency, database crash durability, managed backups or real tenant isolation. The generic proof table layout is not the final normalized production schema.
2. Proposed freshness windows and coarse source classes require review/calibration. Neither shape validation nor a source URL proves the source is true or authoritative. No actual research accuracy/usefulness result is claimed.
3. Scope statements are manager-attested preview inputs, not persisted production events. Current role delegation, ambiguity resolution, historical grants and safe server-derived relationship scopes need approved service design. Do not let callers omit candidate scopes to bypass a review hold.
4. Legacy overwrites may already have lost history; the preview cannot reconstruct missing records or silently reinterpret legacy IDs/verification. It provides no migration API.
5. Full-snapshot validation/cloning has significant memory cost. The measured large batch is suitable only as isolated server/batch evidence; paging, concurrency profiling and low-end mobile checks remain necessary before integration.
6. The new policy projection is separate from B1's old same-day resolver. Future integration must explicitly select the approved policy version, not accidentally inherit the old fallback. Conflict/supersession resolution and accepted-identity events remain unimplemented.
7. Existing storage/startup/save/recovery risks remain in the live app because replacing that adapter is outside B2A.

## Approval requested

Approve or amend the proposed policies and bounded B2B plan. Recommended next product milestone: a separately authorized twenty-prospect benchmark that produces inspectable six-question briefs and measures accuracy, usefulness, priority judgment and elapsed research/review time.

The exact list/research permissions, participants and approved working environment must be confirmed before using real data. This is not approval to run real records through the new proof store. Live integration, vendor selection/provisioning, persistence replacement, migration, deployment and main merge remain separately gated. Stop here pending review.
