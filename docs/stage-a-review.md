# Stage A review package

Baseline: `25ed230b694a892ff18dd22543a8d87e3e4b78df` (main), application `index.html`, originally requested as FieldMind.html. Development branch: `codex/stage-a-foundation`.

## Scope

Implemented: automated Node test harness over the actual inline production script (boot skipped for pure-function tests), synthetic identity/history/research fixtures, Chromium smoke test, isolated rendering/link/CSV protections. No CSS, static markup or navigation redesign. No identity/persistence replacement, data migration, production deployment or main merge.

Review [entity model](entity-model.md), [migration plan](migration-plan.md), and [persistence risks](persistence-risks.md) before authorizing Stage B. The documents propose relationships; they do not implement tables or modify stored records.

## Security changes

- Escape source metadata, change field labels, legacy evidence class attributes, restored visit minutes and import counts at HTML boundaries. Existing finding/excerpt/identifier escaping is regression-tested.
- Render source/profile links only when parsed as absolute HTTP(S), without controls/whitespace or embedded credentials. Apply this to current and legacy evidence/profile renderers, including restored records. Unsafe stored values are retained but not linked; no data rewrite. Observed-claim import source checks also use the URL validator.
- Neutralize formula-leading CSV values with an apostrophe, including whitespace/control prefixes; then perform CSV quoting including carriage returns. Safe normal values and quoted text retain conventional export formatting. Formula-like negative values export as text intentionally. This protects the FieldMind export; users should not strip the protection before spreadsheet import.

## Reproduce

Node 22+ (validated with 24.22.1):

```sh
npm ci
npx playwright install chromium
npm test
```

On a machine with managed Chromium, set `FIELDMIND_CHROMIUM=/usr/bin/chromium`. Tests use no credentials or real customer data. Browser intercepts its synthetic page origin and blocks external requests, including fonts. This is workflow/DOM validation, not a pixel screenshot comparison or live cloud integration test. Production app remains a standalone HTML file with no runtime npm dependencies.

`FIELDMIND_TEST_HTML=/path/to/baseline.html` allows regression checks against another revision. Against the original application, all six original security groups failed (four exposed behavior failures and two missing-new-helper failures); this is expected, not a failure of the final branch.

## Results

Final command: `FIELDMIND_CHROMIUM=/usr/bin/chromium npm test`.

| Group | Pass | Fail | Interpretation |
|---|---:|---:|---|
| Baseline / fixture tests | 11 | 0 | Includes three explicitly labeled KNOWN RISK characterizations, not corrected identity guarantees |
| Isolated security tests | 7 | 0 | HTML, safe/unsafe URLs, legacy paths, backup-derived display fields and CSV protections |
| Chromium workflow/security smoke | 1 | 0 | Mobile navigation, search, brief tabs, sources, visit form, malicious synthetic source data, no page errors |
| Total | 19 | 0 | No skipped tests |

Known-risk characterizations intentionally reproduce first-suite ambiguity, source-history replacement/suppression removal on reimport, and successive/simultaneous account identity splitting. They must be replaced with desired-behavior regression tests during approved Stage B work. Green status does not mean those defects are fixed.

## Remaining risks

Identity collisions, prefix matching, historical overwrites and suppression removal remain. Research can accept unsupported profiles/imported verification, stale briefs and unresolved derived dependencies. Storage still risks startup replacement, partial writes, local false acknowledgement and concurrent lost updates. Backup schema validation, prototype-sensitive dictionary keys, resource-size limits and authenticated cloud isolation require subsequent hardening. The focused security changes are not a claim of complete security certification.

No real dataset migration or live cloud test was attempted. No customer evidence was uploaded. Review entity boundaries, account issuer/identity semantics, temporal uncertainty, suppression authority and the migration approval gates before Stage B. Stop here pending explicit approval; do not merge or deploy automatically.
