# B1 compatibility assessment

`index.html`, its styles, legacy global state, research v2 parser, CSV workflow, localStorage keys, Claude capability adapter and backup format are unchanged from accepted Stage A. The new ES modules are not imported by the app. No production behavior claims are made based on the isolated domain tests.

| Current behavior | B1 domain equivalent / gap | Future integration rule |
|---|---|---|
| Account-keyed combined premise/business/account | Distinct locations, business, occupancy and account references | Legacy `acct` stays unclassified until original headers establish semantics; no automatic conversion |
| Name/address-prefix research match | Candidate-only exact normalized lookups | Single candidate still requires accepted linkage; don't break current workflow silently |
| One decision route | Five scoped authority concepts, separate Party identity | Existing owner_operator/corporate/landlord route is research context, not sufficient utility/facilities authority |
| List selected as approved or MIMO | Independent memberships, manager authorization and suppression events | Membership is never approval; legacy suppression cannot disappear during mapping |
| Imported evidence verified flag | Evidence origin, review and matching representative observation | Unattested legacy verified flag remains raw/unreviewed; no fabricated observation |
| Historical equipment/device strings | Historical account Claims with immutable rows | Missing account association becomes unresolved; don't attach it to a current occupant automatically |
| Mutable brief and field corrections | Evidence dependencies and dispute propagation in pure resolution | UI brief must eventually become a traceable projection; B1 does not change the legacy brief |
| Replace-style list import and backup restore | Append-only in-memory operations; raw imports retained | Requires separately reviewed repository/restore design; B1 append is not a storage transaction |
| Research JSON v2 and fieldmind:1 backups | New domain snapshot schemaVersion:1 | Formats are intentionally different; no implicit upgrade, parser rerouting or migration |

The retained Stage A KNOWN RISK tests still reproduce legacy suite ambiguity, historical-row replacement/suppression loss, and account-as-premise identity splitting. Passing B1 tests demonstrate proposed domain behavior only. Current users receive none of those domain corrections until an approved integration occurs.

Validation is stricter than the app: complete normalized records, real dates, typed references and explicit provenance. This must be introduced through an import preview/quarantine flow, never by dropping invalid legacy fields. Original raw import text is preserved separately; malformed rows can be diagnosed without discarding originals.

Tests cover representative mobile navigation and DOM injection, not visual screenshot equivalence, authenticated cloud authorization, actual customer datasets or offline multi-device sync. Existing markup and CSS remain byte-identical because the app file is unchanged.
