# Read-only legacy compatibility preview — B2A

Implementation: `domain/legacy-preview.mjs`. Reviewable synthetic output: [`examples/b2a-legacy-preview.json`](../examples/b2a-legacy-preview.json). Regenerate examples with `node benchmarks/examples.mjs` using synthetic data only.

The API accepts exact JSON text, an optional validated reference domain workspace and trusted synthetic validation context. It accepts **no storage handle** and emits `kind: legacy_preview`, `writable: false`. It does not return an append command, accepted domain snapshot, new identity ID, migration routine or writable record. It cannot modify localStorage, the Claude adapter, the live `S` object or a repository workspace.

Preservation:

- Original JSON text including indentation/newlines is retained exactly, even if parsing fails.
- The complete parsed source is retained, including unknown root fields, meta, all account fields, source rows, brief/history, evidence, contacts, visits and unrecognized nested data.
- Each legacy account key/raw record and associated raw notes remain inspectable. Orphan notes and malformed account values are retained as unresolved, never discarded.
- Prototype-shaped JSON keys remain ordinary data. No assignment into a shared object prototype occurs.

Diagnostics:

- `acct` remains an unclassified external reference; header provenance must distinguish premise, utility account and service point.
- Exact normalized name/address matches are **candidates only**. Even one candidate never becomes an accepted identity. Duplicate and large shared-address groups include total counts; at most twenty candidate IDs are shown per item.
- Device/MIMO strings remain historical with unresolved account/occupancy association. Suppression/list status requires manager provenance and scope review; AI brief/decision-maker text is not verified authority.
- Legacy verified flags without actor/method/time attestation remain flagged as unattested. Existing source history may already be incomplete; preview cannot reconstruct overwritten rows or duplicate CSV headers lost by old parsing.
- Unknown fields are classified as raw/unresolved, not silently normalized or truncated. Candidate lists may be capped but original data never is.

Proposed bounds: 16 MiB UTF-8 JSON and 10,000 legacy accounts per preview. Over-budget inputs reject before parsing/expansion; original input remains with the caller. Invalid JSON/structure yields diagnostics and retained source text rather than a partial migration. This bound applies to this pure API; future upload limits must also be enforced at the network boundary.

Compatibility: the existing app, research JSON v2, `fieldmind:1` backup interpretation and persistence keys remain unchanged. The preview is not loaded by `index.html`. Importing a preview into the old app or domain repository is neither supported nor authorized. Future mapping would require separate model/policy approval, a concrete dry-run reconciliation and explicit migration authorization.
