# Proposed Stage B2 — review required

B1 does not authorize B2, data migration, deployment or main merge. Keep all work on the development branch until separately approved. Existing migration plan's dry-run and cutover gates remain in force.

## Compatibility bridge design first

Specify an explicit legacy-to-domain **preview** contract without changing existing `S.accounts`, `S.notes`, localStorage or cloud collections. Classify every legacy field as mapped, retained raw or unresolved. In particular, never equate `acct` with premise/account/service location without source semantics; never convert legacy imported verified flags into representative attestations. Produce synthetic preview fixtures and diagnostics, not an executable migration against user data.

Acceptance: the bridge cannot write storage; mismatched suites/accounts are unresolved; raw fields survive the preview; all legacy entities/notes are reconciled. Existing research JSON v2 remains accepted by the legacy UI until a separately reviewed protocol upgrade.

## Resolve scope, time and verification policy

Approve how manager directives scope to buildings, suites, service locations, businesses and occupancies; flag ambiguous scope conservatively. Define claim-type freshness windows, authority record-review standards, overlapping occupancy reviews, supersession/conflict resolution and manager suppression-release procedure. B1's same-day default remains until a policy is approved.

Acceptance: tests cover parent/child scope, historical occupants, shared meters and restrictions issued by multiple managers; evidence never broadens scope or confers eligibility implicitly. No CRM/enrollment/routing functionality added.

## Select and prove one canonical persistence approach

Review [storage options](storage-options-b2.md). Approve the storage/auth environment before implementation. Prefer one authenticated service plus relational store for the multi-rep future; avoid dual-authority local/cloud sync. If approved, implement only an isolated synthetic test workspace first, not replacement of the current live adapter.

Acceptance: authenticated cross-workspace denial; representative cannot issue manager directives; AI cannot mutate control records; expected revision conflicts; failures leave old data readable; no global Synced status while any write is pending/failed. Prove startup, quota, retry and partial-commit behavior by fault injection.

## Integrate only after isolated proof and review

Build a repository boundary around approved contracts and a read-only domain projection before enabling writes. Keep UI design and existing useful workflows. Show authority distinctions/unknowns without turning the product into a sales-script tool. Add exact app-version compatibility tests, export/restore preview and audit inspection.

Acceptance: legacy workflows and security tests remain green, no automatic identity merge, normalized facts link to raw sources, disputed dependencies cease to support current intelligence, historical MIMO never appears as current equipment/eligibility.

## Migration remains a separate authorization

After the bridge and storage design are approved, prepare a concrete dry-run report only if explicitly authorized. Review mapping decisions and reconciliations; then request separate approval before any existing-data migration or cutover. Keep original data read-only, no silent overwrite/deletion and no production deploy in B2 unless explicitly authorized later.
