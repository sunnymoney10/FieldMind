# B1 domain API

Pure ES modules, no runtime dependencies, DOM, storage, network or clocks. Not loaded by `index.html`.

```js
import {emptyWorkspace} from './contracts.mjs';
import {validateWorkspace} from './validate.mjs';
import {appendRecords} from './functions.mjs';
const workspace = emptyWorkspace('synthetic-workspace');
const context = {
  actorId: 'synthetic-manager',
  actors: {'synthetic-manager': {workspaceId: workspace.workspaceId, roles: ['manager']}}
};
const validation = validateWorkspace(workspace, context);
// Append complete records only; caller generates stable IDs. No writes happen here.
const next = appendRecords(workspace, {}, context).workspace;
```

`CONTRACTS` and `SNAPSHOT_SCHEMA` are the executable normalized format. All fields required; unknowns are explicit null/empty arrays as described by each contract. Diagnostics contain `{path, code, message}`. Cross-record validation applies workspace, typed reference, provenance, verification, authority-scope, temporal and graph checks. External duplicate references warn rather than merge. Supply trusted actor registry when validating imported historical directives and observations; the registry must come from an authenticated boundary in any future live integration.

- `appendRecords(workspace, {collection: [record]}, context)`: validates input and proposed result; returns a clone with added/replayed IDs. Exact same-ID replay is idempotent. Different content under an existing ID throws without modifying the input. It does not deduplicate new IDs by text or normalize original imports. Stable command/entity IDs must be assigned by the future importer. This is not a durable transaction or migration routine.
- `identityCandidates(workspace, query, context)`: exact normalized address/name or exact typed external reference -> review candidates; always `acceptedId: null`, even for one candidate. Does not strip suites or attempt fuzzy identity resolution.
- `claimState(workspace, claimId, {asOf, maxAgeDays}, context)`: conservative current support state. Reports unknown for unreviewed public findings; the actual Claim remains available with its provenance. Missing claim returns unknown.
- `authorityFor(workspace, {kind, subject, asOf, maxAgeDays}, context)`: independent authority states plus supporting assertion/claim IDs; conflicting holders are never chosen arbitrarily.
- `prospectDecision(workspace, explicitSubjects, utcTimestamp, context)`: manager authorization, active restrictions, memberships and full directive IDs; eligibility remains not established. No implicit ancestor/occupant suppression mapping.
- `mimoHistory(workspace, accountId, context)`: cloned historical Claims with explicit no-current-equipment/no-eligibility/no-sequence conclusions.

The functions validate the snapshot first. They are designed for correctness in synthetic workloads, not high-volume production use. No caching/index/storage service is introduced. Do not pass real data or wire this into the running app before the integration and authorization plan is reviewed.
