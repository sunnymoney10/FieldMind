# Proposed manager authorization and suppression scope — B2A

Manager authorization, suppression/release, list membership and AI research remain separate, auditable record types. Scope interpretation is a pure, synthetic policy preview in `domain/scope-policy.mjs`; it is not connected to existing storage or app contact decisions.

## Scope is explicit, not inherited by address or name

| Scoped subject | Meaning of an exact directive | What it does not automatically include |
|---|---|---|
| Building | The named structure / explicitly stated building-level activity | Every suite, premise, operator or account |
| Suite | The identified unit within its building | Neighboring suites or all occupants/accounts |
| Premise | The identified operational location | Same-address premises, prior businesses or all service points |
| Utility service location | The provider-scoped service point | Every co-located premise or utility account |
| Utility account | The exact provider-scoped account | Previous/later/parallel accounts or the business generally |
| Business | The specifically identified business | Every similarly named branch, trading name or property owner |
| Occupancy | That business-at-premise relationship | Past/future occupants or the business's other locations |

A known physical relationship alone is not evidence that the manager intended restriction propagation. An ambiguous physical/identity relationship never becomes an accepted relationship as a side effect of policy evaluation. Inputs include explicitly reviewed related candidates only; same-address/name similarity belongs in identity review, not suppression expansion.

## Scope statements

Proposed manager-attested scope annotations reference an existing directive ID, workspace, source row, manager issuer, issue time, reason and one of:

- **exact:** source/manager confirms the directive applies only to its named subject. Do not restrict neighboring candidates.
- **explicit_targets:** source/manager explicitly supports the named additional subjects. Only those IDs and the original subject are covered, never all present/future descendants by default.
- **ambiguous:** source or manager intent is unresolved. Hold relevant candidates for review; do not call them suppressed without evidence.

Without an annotation, the directive applies to its exact subject. If a target's explicitly supplied related candidate has an unclassified directive, return a **review hold**, not inherited suppression. Never silently treat that hold as approval. Two competing scope annotations reject interpretation and require manager review; there is no convenient last-writer-wins default. The annotations are preview inputs only in B2A, not new persisted collections. Future storage must give them immutable event IDs/provenance and bind issuers to authenticated sessions.

## Control rules

- Approval must be a manager-issued ProspectAuthorization with source, exact subject, reason and timestamp. Being on an “approved” CSV is list membership, not a new authenticated approval event.
- AI findings cannot authorize a prospect, expand a scope, release a restriction or establish enrollment eligibility. Representatives can record observations; they cannot issue manager directives through the repository proof.
- Evaluate authorization per scoped root as of issue time. Same-time contradictory decisions are disputed. A relevant withdrawal prevents a positive recommendation; authorization on one scope does not override a relevant suppression or scope hold.
- Suppression has no age expiry. An Active row, changed name, new occupant, new account, later research, or fresh manager approval does not release it.
- A release is a separately recorded manager event referencing exactly one suppression, with source/reason/time. Releasing one does not release others. A released building directive stays in audit history.
- `hold` means do not proceed on the assumption of permission; it is not a new eligibility/status label. `eligibility` always remains `not_established`.

## Identity, role and operational limits

B2A annotations and actor registries are synthetic inputs. Their source text/actual authority cannot be proved by shape validation. The future application service must bind manager sessions, scope privileges, role changes and source attestations to durable events. Workspace-wide manager privileges are a **test assumption**, not an approved organization-level delegation policy.

Do not expose a user-controlled `relatedCandidates` or scope-annotation payload as a permission bypass. The future server must derive/review candidate relationships and block use while relevant scope remains unresolved. This policy is independent from the current live interface, which remains unchanged.
