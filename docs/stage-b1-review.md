# Stage B1 review package

Accepted Stage A base: `d10969d30c8477319a6c0aa39ebfb204baab7322`. Branch: `codex/stage-a-foundation`. B1 implements only synthetic, persistence-free domain contracts/functions/validation/tests and documentation.

## Delivered

- [Amended entity model](entity-model.md): five independent authority concepts; distinct buildings/suites/premises/utility service locations; separate manager controls, memberships and research; historical MIMO; immutable raw source preservation.
- [Domain API](../domain/README.md): complete runtime contracts, strict structural and cross-record validation, candidate-only identity review, independent authority evaluation, explicit manager control decisions, historical MIMO projection and atomic in-memory append/replay.
- [Compatibility assessment](stage-b1-compatibility.md): new modules are not loaded by the legacy app; existing input/storage formats remain unchanged.
- [Storage comparison](storage-options-b2.md): local-first versus authenticated cloud, with multi-representative implications.
- [Proposed B2 plan](stage-b2-plan.md): policy/compatibility preview first, approved storage direction next, then isolated proof before integration. Migration remains separately gated.

## Results

Test command: `FIELDMIND_CHROMIUM=/usr/bin/chromium npm test` (Node 24.22.1 and managed Chromium). For domain-only review: `npm run test:domain`. Standard setup remains `npm ci` and `npx playwright install chromium` where managed Chromium is unavailable.

| Suite | Passed | Failed |
|---|---:|---:|
| B1 domain tests | 29 | 0 |
| Retained Stage A baseline/security/browser tests | 19 | 0 |
| Total | 48 | 0 |

No skipped tests. Domain scenarios cover shared addresses/names, suites/buildings, successive and concurrent accounts, shared service points, five independent authorities in all four states, source scope, impossible dates, typed/cross-workspace references, observation verification, stale/future knowledge, claim conflicts/dependencies/cycles, independent list/approval/suppression audit, manager-only releases, caller spoofing, raw imports/duplicate headers, exact replay, conflicting-ID refusal and nonmutation on failure.

The three retained KNOWN RISK legacy tests still reproduce old defects. They are not acceptance tests claiming those bugs have been fixed in the app. The app blob remains exactly `86593fcd00885758c91ef0d7f2fd0f5a594b4454`, identical to Stage A. No user data was used, read, converted or migrated.

## Remaining risks and boundaries

1. Legacy app defects remain until separately approved integration. No production benefit from new domain logic is implied yet.
2. Actor roles are supplied by a trusted caller context for synthetic tests. This is not authentication, a signed audit log, server-side enforcement or proof of tenant isolation. B2 must bind identities to real sessions/permissions and enforce constraints durably.
3. Same-day freshness is a conservative default, not a business-approved policy. Broader freshness windows and parent/child suppression scopes require review. `prospectDecision` uses explicitly supplied scopes; uncertain scope is not automatically resolved.
4. A source excerpt's truth, source authority and parsing fidelity cannot be established by shape validation. Representative record review and field observation are distinct; no synthetic test establishes actual acquisition accuracy.
5. Strict normalized validation does not parse/migrate legacy CSV, research v2 or backups. Malformed/unknown legacy data must stay raw and be quarantined/reviewed, never silently discarded.
6. Append replay is idempotent for stable IDs, not automatic content-based deduplication across freshly generated IDs. The future importer must assign stable command IDs and preserve upload events without duplicating accepted assertions.
7. All-or-nothing append is an in-memory clone operation, not a storage transaction. No deletion/update/migration API exists. Storage failure, cross-device concurrency, limits and rollback remain unimplemented.
8. Snapshot validation traverses full graphs and recursively resolves dependencies. Production graph/depth/input-size budgets and performance testing remain necessary; tests cover synthetic correctness only.
9. There is no automatic conflict resolution or accepted-identity linking operation. Explicit conflicts remain disputed until a later reviewed resolution mechanism exists.

## Review decision requested

Approve B1 and review the B2 plan plus cloud-versus-local direction before additional implementation. Recommendation: authenticated cloud canonical storage for the multi-representative future, with online commits first and explicit unsaved/offline states. Do not implement replacement before this choice is approved. No main merge, deployment or existing-user-data migration is authorized. A migration dry run and actual cutover remain distinct future approvals.
