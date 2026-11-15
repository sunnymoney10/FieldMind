# Storage decision before Stage B2

No persistence replacement implemented. Comparison is vendor-neutral; no provider, account or credentials are provisioned.

| Concern | Local-first canonical storage | Authenticated cloud canonical storage |
|---|---|---|
| Single rep, intermittent connectivity | Immediate offline reads/writes with IndexedDB transactions | Offline reads need an explicit cached snapshot; offline writes need an outbox or deferred-draft policy |
| Multi-representative future | Team sharing requires a sync service, identity, permissions, reconciliation and global suppression distribution | Shared workspace, manager roles, team-wide suppression and audit history are natural server responsibilities |
| Authority and suppression | A device can hold stale approval/suppression; cannot guarantee that another rep sees a restriction | Server can enforce issuing roles, scope, revisions and current restrictions atomically |
| Conflicts | Multi-device sync needs carefully designed revisions and conflict resolution; append-only events reduce but do not eliminate semantic conflicts | Optimistic revisions and database transactions prevent silent lost updates; identity conflicts still need review |
| Recovery | Browser clearing, device loss and storage quota require deliberate backup; recovery is user-dependent | Central backups, retention and restoration possible, but must be configured and tested |
| Privacy/security | Data remains on device; same-origin code and device access still matter; local actor roles are not real team authentication | Requires authentication, workspace isolation, least privilege, secure exports, service operations and access tests |
| Complexity | Lowest complexity only while intentionally single-device; reliable team sync makes it significantly more complex | One service plus relational store is a manageable team foundation; full offline sync should be deferred until justified |

**Recommendation for the intended multi-representative product:** authenticated cloud as the future source of truth, with one service and relational database enforcing workspace and manager/representative roles. Begin with explicit online commits and unsaved drafts, not a simultaneous two-authority sync system. Add a clearly labeled read cache, then an offline outbox only after conflict and suppression freshness rules are approved. A stale cached approval must never override a newer server restriction.

Local-first remains viable for a deliberate single-rep pilot, but would defer the hardest multi-rep questions rather than resolve them. Do not treat the current localStorage fallback as a sync solution. Existing Claude storage could be retained only if its transaction, revision, tenant-isolation and operational guarantees are demonstrated; repository code alone does not establish them.

**Decisions requested before replacement:** canonical store direction; hosting/authentication environment; workspace/team boundaries; manager privilege assignment; whether offline edits are necessary initially; maximum tolerated age of cached restrictions; backup/retention requirements. No provider-specific implementation or existing-data migration is authorized by this proposal.
