# Isolated repository/storage proof — B2A

`proof/repository.mjs` uses Node's built-in SQLite **in memory**, with synthetic fixtures only. SQLite is a disposable local transaction test engine, not a selected cloud vendor, production backend or replacement app adapter. No service listens on a port. Closing the proof loses its data deliberately.

## Proposed request surface

- `read({credential, workspaceId})` returns a detached snapshot and revision after workspace/role checks. Researchers receive no full-workspace read.
- `commit({credential, workspaceId, expectedRevision, commandId, additions})` appends validated records atomically, with an expected revision, actor-bound command identity and audit entry. It returns revision/command status, not a full data dump.
- No update, merge, delete, restore, migration, deployment or implicit identity-acceptance endpoint exists.

`testOnly.seed/inspect` are privileged fixture harness helpers, **not** part of the proposed transport surface. They must never be exposed by a future service.

## Authentication assumptions — not real authentication

A trusted verifier callback maps synthetic credentials to a subject and expiry. A separate trusted membership callback supplies current workspace roles; historical actor provenance is retained separately for domain validation. Requests cannot supply roles, actor registries, principals or validation context. Identity and current membership are checked at request entry and again before commit. A future service must replace these test doubles with a real verified session boundary and durable role/attestation history. No B2A test establishes OAuth/JWT/session security, real tenant isolation or database network security.

Manager/representative members may read the synthetic workspace. Only the issuing manager can append directives; only the observing representative can append observations. Researchers may append unreviewed AI Claims/ResearchRuns only. Manager-only and observation checks occur on current session roles, not historical privileges. Revoked permissions cannot be restored by client-provided context. Existing historical records remain auditable; role-history validation must include legitimate new grants as well as past attestations.

B1's pure append function gained a backward-compatible trusted `callerRoles` option so current permissions and historical provenance do not need to be conflated. It is an internal boundary input, not a request field. The legacy application does not call it.

## Atomicity, isolation and recovery

The local relational proof has workspace revisions, immutable entity rows, actor-bound idempotency commands and audit rows. Composite keys include workspace IDs; JSON record workspace/ID checks and workspace foreign keys enforce basic consistency. Full typed-relationship validation happens in the domain before commit. This is a generic entity-envelope test schema, **not the final normalized relational schema**; production must enforce approved typed foreign keys/constraints as well.

- Parameterized SQL; query scope always includes the authorized workspace.
- `BEGIN IMMEDIATE` wraps record inserts, revision change, command acknowledgement and audit entry. Conditional revision update detects stale clients. The test interleaves two stale client revisions; it is not a distributed load test.
- Exact same command/actor/payload retry returns the original revision. A changed payload or actor cannot reuse the command ID to write something different. IDs are not inferred/deduplicated from business data.
- Faults after entity writes, after revision update or before commit roll back **all** changes, including command and audit entries. The caller's rejected draft is unchanged.
- A failure after commit returns `outcome_unknown`, not “not saved.” The caller retries the same command ID/payload; the original successful revision is recovered without duplicate observations.
- Payload/graph bounds are checked before recursive domain validation. Commands cap at 16 MiB; candidate snapshots use the documented domain budgets. Real network parsing limits must be enforced earlier by a future HTTP boundary.

Errors use stable codes without internal data or SQL leakage: unauthenticated, forbidden, invalid_request, revision_conflict, command_conflict, validation_failed, write_failed, outcome_unknown. No global Synced indicator or optimistic live-state mutation is implemented here.

## Executed test matrix

Twelve repository tests cover forged/expired credentials; request-injected roles; cross-workspace read/write/record attempts; researcher restrictions; detached reads; invalid-batch rollback; stale-client conflict and retained draft; three transaction fault points and retry recovery; lost acknowledgement and idempotent retry; changed-command rejection; revoked/downgraded role checks; and rechecking permissions before commit. Domain, policy and retained browser tests run alongside these.

## Not proven

Real authentication, HTTP/CSRF controls, persistence across process/device loss, filesystem/database crash durability, encryption, managed backups, database server isolation, distributed concurrent sessions, malicious database clients and mobile performance are outside this in-memory proof. They are explicit gates for a separately approved backend implementation. Existing localStorage/Claude storage code is unchanged.
