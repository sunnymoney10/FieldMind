# Migration plan — gated on explicit approval

Stage A ships no new identity model, persistence replacement or migration code. Development approval is not migration approval. No existing records are changed by these documents or fixtures.

## 1. Preserve the source and establish inventory

After approval, take a user-controlled versioned export and digest before any write. Validate it without normalization or mutation; inventory accounts, notes, raw rows, brief/history, visits, evidence, suppression flags, unknown fields and malformed/orphaned records. Keep original bytes and legacy IDs. Do not request or place real customer data in repository tests.

The existing app may already have overwritten history. A migration cannot recover missing rows: mark history incomplete and allow separately reviewed reimports of original files. Do not invent historical dates or associations.

## 2. Dry-run mapping only

Generate a report with a migration-run ID, source digest, counts and a mapping from each legacy ID to proposed records. Treat `acct` as an unclassified external reference until column provenance distinguishes premise IDs from utility accounts. Preserve exact original formatting. Manual edits that changed an address/account without changing its legacy key must be flagged.

Default to independent provisional records, even when names/addresses are identical. Shared buildings, omitted suites, conflicting identifiers, simultaneous meters, account succession and business aliases require explicit review. No automatic merging of ambiguous identities. Separate candidate links from accepted relationships.

Map source rows to immutable batches/rows where possible. Missing batch metadata becomes `legacy_unknown` provenance; don't manufacture a filename, authority or timestamp. Preserve legacy source-row objects, including their limitations, alongside reconstructed ordered cells. Prior backups may already have lost duplicate header columns.

Convert legacy evidence conservatively: retain original status and raw payload, but do not reinterpret imported `verified` as a representative attestation without actor/basis evidence. Brief/profile claims without traceable support remain unreviewed. Preserve unknown fields in a legacy envelope. Keep visits and corrections linked to legacy context where occupant attribution is uncertain.

## 3. Review gate

Present entity counts, all ambiguous candidate relationships, suppression conflicts, unsupported verification and field-level transformations. Require explicit approval of both the model and concrete dry-run report. The reviewer may accept individual links, keep records separate or defer them. No silent destructive defaults.

## 4. Shadow conversion and reconciliation

Write to a separate versioned workspace/database namespace, never over the current store. Use idempotent migration keys based on source digest, legacy record key and transformation version. Re-running the same conversion must produce the same mapping, not duplicate records. Track every original record/field as mapped or retained opaque; no unexplained omissions. Retain suppression regardless of membership changes until explicitly resolved.

Validate workspace-scoped foreign keys, source retention, evidence dependencies, record counts, temporal unknowns, duplicate/overlap warnings and export round-trip equality of retained originals. Compare old and proposed brief views without presenting unapproved links as fact.

## 5. Controlled cutover, only after separate approval

Freeze or reconcile changes since the snapshot using explicit revisions; abort if the source digest/revision changed. Commit the new workspace atomically and switch a version pointer only after verification. Leave legacy data read-only and available for rollback. Do not dual-write two identity models without a reconciliation contract.

Rollback switches back to the untouched legacy snapshot; new observations made after cutover must be exported/reconciled before reversal so they are not lost. Never delete the old workspace as part of migration. Cleanup and retention are a later explicit decision.

## Future acceptance gates (not passing tests yet)

- Two businesses at one address and two suites remain distinct unless a reviewer accepts a link.
- One premise retains successive accounts and simultaneous meters without inferring false succession.
- Every import preserves prior source rows, raw formatting and batch context; retries are idempotent.
- DNC/hold cannot disappear because a later row says Active, research says eligible, or a business changes name.
- Disputed evidence cannot continue to support an established derived conclusion.
- A failed or interrupted migration leaves the active workspace unchanged; rollback preserves original bytes.
- Every legacy field is reconciled or explicitly retained as unresolved, including orphans and malformed data.
