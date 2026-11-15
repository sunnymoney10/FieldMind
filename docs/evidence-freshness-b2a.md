# Proposed evidence freshness policy — B2A

Status: proposed, exercised with synthetic data only. Approval of B2A work does not make these day limits live product rules. Version `b2a-proposed-1` is implemented in `domain/intelligence.mjs`, separately from the retained B1 resolver. Do not wire the older same-day resolver into the interface as the universal freshness policy.

“Decisions don’t take time. They take information.” Stale evidence is information with limits, not no information. The projection retains original value, dates, dependencies, contradictions and source provenance even when current status cannot be established.

## Proposed maximum age in calendar days

| Claim type / decision risk | Direct representative evidence | Public record | Other public source | Manager list assertion |
|---|---:|---:|---:|---:|
| Operating status | 14 | 30 | 7 | 7 |
| Occupant identity | 30 | 90 | 14 | 14 |
| Business hours | 30 | 14 | 14 | 7 |
| Business ownership authority | 90 | 180 | 30 | 14 |
| Business operations authority | 30 | 60 | 14 | 7 |
| Utility-account authority | 30 | 30 | 7 | 7 |
| Property authority | 180 | 365 | 30 | 14 |
| HVAC/facilities authority | 60 | 180 | 14 | 7 |
| HVAC context | 180 | 365 | 90 | 30 |
| Energy experience / comfort context | 90 | 180 | 30 | 14 |

These windows reflect different change rates and consequences of error; they are initial hypotheses for review and the real-world intelligence benchmark. A fact inside its window can still be wrong. A property record establishes only its stated scope, not current equipment or all decision rights. Staff statements are capped at seven days and cannot become representative verification. More granular source reliability (official business site versus listing/review, public record authority by jurisdiction) needs a reviewed source registry; B2A intentionally uses the coarser B1 origin/observation categories rather than pretending those distinctions are already proven.

Manager prospect authorization, suppression and suppression-release events are **not evidence-age claims**. Suppression persists until its specifically referenced manager release. Age never turns a restriction into permission. Withdrawal/authorization applies as of issue time under the separate scope policy; authorization never establishes eligibility.

## Dates, source and dependency rules

- Caller supplies an explicit `asOf` date. Compare at UTC calendar-day granularity; a future observation is not available evidence. The validity boundary is inclusive.
- Conservatively anchor age to the oldest known observation/publication date. A new retrieval of an old published statement does not refresh the underlying fact. An explicit new direct observation is a distinct Claim with its own provenance, not an edit to the old source.
- Current facts require explicit temporal `as_of` scope and effective start, no elapsed effective end, available support, and no unresolved contradiction.
- Historical participation/equipment and ended claims remain historical regardless of age. Unknown effective dates remain unknown. No rule for a predicate/source means no current establishment, while useful source information remains visible.
- AI is a producer, not an authoritative evidence source. AI-retrieved reported facts with valid citations default to the conservative public-source window and remain `source_supported`, never representative-verified. AI cannot self-designate an authoritative record class through this projection.
- An inference inherits all supporting evidence dates and the earliest dependency expiry, **also capped by its own target claim/source-risk window**. Fresh-looking inference cannot launder an old or lower-risk source into current high-risk authority. Disputed dependencies propagate disputes.
- Scope cannot be borrowed: building evidence is not a directly observed suite fact. An explicit inference may reference building evidence but must show its assumptions and remain qualified.

## Display states and their distinct meanings

| Status | What the rep sees |
|---|---|
| `current_verified` | Matched representative direct observation/record review, within policy and temporal scope; verify method is visible |
| `source_supported` | A cited source reports it within policy; not independent confirmation or verified authority |
| `inferred` | A qualified hypothesis with usable current dependencies; not a fact or automatic eligibility/authority decision |
| `disputed` | Explicit correction/conflict, competing current single-valued facts, or disputed dependency; show alternatives |
| `historical` | Historical, expired or superseded evidence retained as useful context; distinguish stale from historical in `freshness` |
| `unknown` | Current conclusion not established; can still have `usefulContext: true`, provenance and a qualified hypothesis |

Independent axes include `freshness`, `epistemic`, `authorityState`, source origin, support grade and `usefulContext`. “Unknown current authority” must not hide a useful source-reported owner or a qualified hypothesis. No single numeric confidence score is emitted. `supportGrade` is a descriptive label (confirmed/documented/reasoned/unresolved), not a probability or ranking score.

Approval questions for B2B: confirm/adjust these windows, acceptable record-review standards and source classes; decide how a new observation can explicitly supersede a conflict without deleting history. No automatic conflict-clearing operation is implemented in B2A.
