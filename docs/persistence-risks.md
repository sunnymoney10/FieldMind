# Persistence assessment and proposed resolution — no replacement in Stage A

Current adapter: Claude capability-backed document collections (`chunks`, `notes`, workspace metadata), otherwise one localStorage JSON value. Repository contains no server authorization rules. Current privacy claims cannot be verified from client code alone.

| Risk | Current behavior | Proposed acceptance gate |
|---|---|---|
| Startup race | 10-second fallback may load local state before a late cloud response replaces it; app permits edits during initialization | Explicit loading/ready/degraded state machine; one selected store per session, no replacement of dirty state; delay/failure tests preserve edits |
| Save acknowledgement | In-memory mutation precedes write; saveLocal catches quota errors without failing caller | Stage validated change, commit, then acknowledge; quota/network failure preserves recoverable draft and reports unsaved |
| Partial operations | Account chunks, metadata, notes, wipe and restore use multiple independent writes | Transaction or versioned snapshot with final atomic active-version pointer; injected failures at every boundary leave old state readable |
| Concurrent writers | Per-key queues coordinate one client only; whole-document writes overwrite other devices | Expected-revision checks and actionable conflict recovery; two-client tests show no silent lost update |
| Sync indicator | Any successful write can show Synced despite another failed/pending operation | Track pending/failed operations globally; show Synced only after all durable acknowledgements |
| Validation | Loaded state and backups have minimal structural validation; empty workspace handling is inconsistent | Versioned schema validation before activation; invalid/empty/orphan fixtures handled intentionally |
| Storage size | 60-account chunks do not bound bytes; growing notes/source history may exceed limits | Validate provider limits, enforce byte budgets, avoid unbounded history per document; retain full history in normalized storage |
| Authorization | Client path includes user ID, but access policy is not in repository | Prove cross-workspace denial with authenticated integration tests before trusting cloud isolation |
| Recovery | Clipboard backup is plaintext; failures can leave partial delete/restore | Deliberate export, strict restore preview, pre-restore backup and atomic commit; test exact recovery |

## Recommended approach after identity-model approval

Keep one repository API (`loadWorkspace`, `commitChange(expectedRevision)`, `exportSnapshot`, `validateRestore`, `commitRestore`) and explicit result types. Domain operations own integrity; storage must enforce the approved relationships rather than perpetuate account-as-premise keys.

For an intentional local-only release, IndexedDB transactions are adequate, with explicit local-only status and export recovery. For a cloud/shared release, prefer a single authenticated service and relational store with workspace-scoped constraints, transactions and optimistic revisions. Do not introduce both new paths at once. First verify whether current capability storage supports equivalent transactions, revisions, size limits and tenant isolation; retaining it is acceptable only if guarantees can be demonstrated. IndexedDB should not silently become a competing cloud authority.

Select one canonical store and migration plan after reviewing the entity model and intended hosting environment. No service selection, new credentials, backend implementation or production deployment is authorized by Stage A.

## Test plan for Stage B

Fault injection: timeout then late cloud success; edit before startup completes; local quota exceeded; permission denial; failure on every chunk/note/meta step; out-of-order completion; concurrent edits; restore empty workspace; malformed backup; interrupted migration and rollback. Model review and explicit implementation approval precede these persistence changes.
