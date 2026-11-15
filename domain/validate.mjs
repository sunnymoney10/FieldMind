import { CONTRACTS, COLLECTIONS, SNAPSHOT_SCHEMA } from "./contracts.mjs";
const own = (o, k) => Object.hasOwn(o, k);
const plain = (v) =>
  v !== null &&
  typeof v === "object" &&
  !Array.isArray(v) &&
  (Object.getPrototypeOf(v) === Object.prototype ||
    Object.getPrototypeOf(v) === null);
export function validDate(v) {
  return (
    typeof v === "string" &&
    /^\d{4}-\d{2}-\d{2}$/.test(v) &&
    Number.isFinite(Date.parse(v)) &&
    new Date(v).toISOString().slice(0, 10) === v
  );
}
export function validTimestamp(v) {
  return (
    typeof v === "string" &&
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/.test(v) &&
    validDate(v.slice(0, 10)) &&
    Number.isFinite(Date.parse(v)) &&
    new Date(v).toISOString() ===
      v.replace(/Z$/, v.includes(".") ? "Z" : ".000Z")
  );
}
export function safeSourceUrl(v) {
  try {
    if (typeof v !== "string" || /[\u0000-\u0020\u007f]/.test(v)) return false;
    const u = new URL(v);
    return (
      ["http:", "https:"].includes(u.protocol) && !u.username && !u.password
    );
  } catch {
    return false;
  }
}
function check(v, s, path, errors) {
  const fail = (message) => errors.push({ path, code: "shape", message });
  if (s.kind === "nullable") {
    if (v !== null) check(v, s.of, path, errors);
    return;
  }
  if (s.kind === "string") {
    if (typeof v !== "string") fail("Expected string");
    return;
  }
  if (s.kind === "id") {
    if (
      typeof v !== "string" ||
      !v.length ||
      v.length > 128 ||
      !/^[A-Za-z0-9_-]+$/.test(v) ||
      ["__proto__", "constructor", "prototype"].includes(v)
    )
      fail("Expected opaque safe ID");
    return;
  }
  if (s.kind === "timestamp" || s.kind === "date") {
    if (!(s.kind === "date" ? validDate(v) : validTimestamp(v)))
      fail("Expected valid " + s.kind);
    return;
  }
  if (s.kind === "integer") {
    if (!Number.isSafeInteger(v) || v < s.min)
      fail("Expected nonnegative safe integer");
    return;
  }
  if (s.kind === "enum") {
    if (!s.values.includes(v)) fail("Unrecognized value");
    return;
  }
  if (s.kind === "ref") {
    check(
      v,
      {
        kind: "object",
        fields: { type: { kind: "enum", values: s.types }, id: { kind: "id" } },
      },
      path,
      errors,
    );
    return;
  }
  if (s.kind === "array") {
    if (!Array.isArray(v)) {
      fail("Expected array");
      return;
    }
    v.forEach((x, i) => check(x, s.of, `${path}[${i}]`, errors));
    return;
  }
  if (!plain(v)) {
    fail("Expected plain object");
    return;
  }
  for (const k of Object.keys(v))
    if (!own(s.fields, k))
      errors.push({
        path: path + "." + k,
        code: "unknown_field",
        message: "Unknown field; preserve raw payload separately",
      });
  for (const [k, field] of Object.entries(s.fields)) {
    if (!own(v, k))
      errors.push({
        path: path + "." + k,
        code: "required",
        message: "Missing field",
      });
    else check(v[k], field, path + "." + k, errors);
  }
}
export function validateRecord(collection, record) {
  const errors = [];
  if (!own(CONTRACTS, collection))
    return {
      ok: false,
      errors: [
        { path: collection, code: "collection", message: "Unknown collection" },
      ],
    };
  check(record, CONTRACTS[collection], collection, errors);
  return { ok: !errors.length, errors };
}
/** Actors come from a trusted boundary, never from research/import payloads. No authentication is implemented here. */
export function validateWorkspace(w, { actors = {} } = {}) {
  const errors = [],
    warnings = [];
  check(w, SNAPSHOT_SCHEMA, "workspace", errors);
  if (errors.length) return { ok: false, errors, warnings };
  const error = (path, code, message) => errors.push({ path, code, message });
  const index = new Map();
  for (const [collection, records] of Object.entries(CONTRACTS).map(([k]) => [
    k,
    w[k],
  ]))
    for (const r of records) {
      if (r.workspaceId !== w.workspaceId)
        error(`${collection}.${r.id}`, "workspace", "Cross-workspace record");
      if (index.has(r.id))
        error(
          `${collection}.${r.id}`,
          "duplicate_id",
          "IDs must be unique across entity types",
        );
      else index.set(r.id, { collection, r });
    }
  function target(id, collection, path) {
    const found = index.get(id);
    if (!found || found.collection !== collection) {
      error(path, "reference", "Missing or incorrectly typed reference: " + id);
      return null;
    }
    return found.r;
  }
  function subject(s, path) {
    return target(s.id, COLLECTIONS[s.type], path);
  }
  function actor(id, role, path) {
    const a = own(actors, id) ? actors[id] : null;
    if (!a || a.workspaceId !== w.workspaceId || !a.roles?.includes(role))
      error(path, "actor", `Trusted ${role} actor required`);
  }
  function support(ids, path) {
    for (const id of ids) target(id, "claims", path);
  }
  function period(p, path) {
    if (p.from && p.to && p.from > p.to)
      error(path, "period", "Period is reversed");
  }
  function supportedLink(ids, predicate, entity, expected, path) {
    support(ids, path);
    if (!ids.length)
      error(
        path,
        "support",
        "Accepted relationship needs explicit supporting claim",
      );
    if (
      !ids.some((id) => {
        const c = index.get(id)?.r;
        return (
          c?.subject?.id === entity &&
          c.predicate === predicate &&
          c.value === expected
        );
      })
    )
      error(path, "support", "No claim establishes this relationship");
  }
  for (const [collection] of Object.entries(CONTRACTS))
    for (const r of w[collection]) {
      const path = `${collection}.${r.id}`;
      if (r.subject) subject(r.subject, path + ".subject");
      if (r.period) period(r.period, path + ".period");
      for (const key of [
        "premiseIds",
        "serviceLocationIds",
        "supportClaimIds",
        "claimIds",
        "sourceRowIds",
        "fieldObservationIds",
        "derivedFrom",
        "conflictsWith",
      ])
        if (r[key] && new Set(r[key]).size !== r[key].length)
          error(
            path + "." + key,
            "duplicate_reference",
            "Repeated relationship reference",
          );
      if (r.externalRefs)
        for (const x of r.externalRefs) {
          if (!x.issuer.trim() || !x.kind.trim() || !x.value.trim())
            error(
              path,
              "external_reference",
              "External identifiers require issuer, kind and exact value",
            );
          for (const row of x.sourceRowIds) target(row, "sourceRows", path);
          if (!x.sourceRowIds.length)
            error(path, "provenance", "External references need source rows");
        }
      if (collection === "suites") {
        target(r.buildingId, "buildings", path);
        if (!r.label.trim()) error(path, "suite", "Suite label required");
      }
      if (collection === "premises") {
        const suite = r.suiteId ? target(r.suiteId, "suites", path) : null;
        if (r.buildingId) target(r.buildingId, "buildings", path);
        if (suite && suite.buildingId !== r.buildingId)
          error(path, "location", "Suite and premise building disagree");
      }
      if (collection === "serviceLocations") {
        if (
          r.reference !== null &&
          (!r.reference.trim() || !r.provider?.trim())
        )
          error(
            path,
            "provider",
            "A service reference needs an explicit provider",
          );
        support(r.supportClaimIds, path);
        for (const id of r.premiseIds) {
          target(id, "premises", path);
          supportedLink(r.supportClaimIds, "serves_premise", r.id, id, path);
        }
      }
      if (collection === "occupancies") {
        target(r.premiseId, "premises", path);
        target(r.businessId, "businesses", path);
        supportedLink(
          r.supportClaimIds,
          "occupies",
          r.businessId,
          r.premiseId,
          path,
        );
      }
      if (collection === "utilityAccounts") {
        if (!r.reference.trim())
          error(path, "account", "Exact account reference required");
        if (r.provider !== null && !r.provider.trim())
          error(path, "provider", "Provider is nonempty or null");
        support(r.supportClaimIds, path);
        for (const id of r.serviceLocationIds) {
          target(id, "serviceLocations", path);
          supportedLink(r.supportClaimIds, "served_at", r.id, id, path);
        }
      }
      if (collection === "importBatches") {
        const a = own(actors, r.importedBy) ? actors[r.importedBy] : null;
        if (!a || a.workspaceId !== w.workspaceId)
          error(path, "actor", "Trusted importing actor required");
      }
      if (collection === "sourceRows") {
        target(r.batchId, "importBatches", path);
        if (r.cells.length !== r.headers.length)
          error(
            path,
            "row_width",
            "Headers and cells must retain ordered columns",
          );
      }
      if (collection === "researchRuns") {
        for (const id of r.requestedPremiseIds) target(id, "premises", path);
        for (const c of r.coverage) subject(c.subject, path);
        if (
          r.completedAt &&
          Date.parse(r.completedAt) < Date.parse(r.createdAt)
        )
          error(path, "time", "Completion precedes research run");
      }
      if (collection === "fieldObservations") {
        actor(r.observerId, "representative", path);
        if (!r.note.trim() || !r.predicate.trim())
          error(path, "observation", "Observation note and predicate required");
      }
      if (collection === "claims") {
        for (const id of r.sourceRowIds) target(id, "sourceRows", path);
        for (const id of r.fieldObservationIds)
          target(id, "fieldObservations", path);
        support(r.derivedFrom, path);
        support(r.conflictsWith, path);
        for (const id of r.conflictsWith) {
          const other = index.get(id)?.r;
          if (
            other?.subject?.id !== r.subject.id ||
            other?.subject?.type !== r.subject.type ||
            other?.predicate !== r.predicate
          )
            error(
              path,
              "conflict_scope",
              "Conflicts must describe the same subject and predicate",
            );
        }
        if (r.researchRunId) target(r.researchRunId, "researchRuns", path);
        if (!r.predicate.trim() || !r.value.trim())
          error(path, "claim", "Claim predicate and value required");
        if (
          [
            "approval",
            "eligibility",
            "suppression",
            "unsuppress",
            "list_membership",
          ].includes(r.predicate)
        )
          error(
            path,
            "control_plane",
            "Use audited manager directives; claims cannot authorize or establish eligibility",
          );
        for (const c of r.citations) {
          subject(c.scope, path);
          if (!safeSourceUrl(c.url) || !c.title.trim() || !c.excerpt.trim())
            error(
              path,
              "citation",
              "Citation needs HTTP(S) URL, title and excerpt",
            );
          if (c.scope.type !== r.subject.type || c.scope.id !== r.subject.id)
            error(
              path,
              "scope",
              "Source scope must match claim subject; use an explicit derived claim for transfer",
            );
        }
        if (
          !r.sourceRowIds.length &&
          !r.citations.length &&
          !r.fieldObservationIds.length &&
          !r.derivedFrom.length
        )
          error(path, "provenance", "Claim needs evidence");
        if (r.basis === "inferred" && !r.derivedFrom.length)
          error(path, "inference", "Inference needs claim dependencies");
        if (r.origin === "ai" && !r.researchRunId)
          error(path, "research", "AI claim needs research run");
        if (r.origin === "manager_list" && !r.sourceRowIds.length)
          error(path, "provenance", "List claim needs source row");
        if (r.origin === "field" && !r.fieldObservationIds.length)
          error(path, "provenance", "Field claim needs observation");
        if (
          ["public_record", "public_source"].includes(r.origin) &&
          !r.citations.length
        )
          error(path, "provenance", "Public claim needs citation");
        if (r.temporal === "as_of" && !r.period.from)
          error(path, "time", "Current-as-of claim needs an effective date");
        if (
          r.predicate === "historical_participation" ||
          r.predicate === "historical_equipment"
        ) {
          if (
            r.temporal !== "historical" ||
            r.subject.type !== "utilityAccount"
          )
            error(
              path,
              "mimo",
              "MIMO history belongs to a historical account assertion",
            );
        }
        if (r.review === "verified") {
          const obs = r.verificationObservationId
            ? target(r.verificationObservationId, "fieldObservations", path)
            : null;
          if (
            !obs ||
            !r.fieldObservationIds.includes(obs.id) ||
            !["direct_observation", "record_review"].includes(obs.kind) ||
            obs.subject.type !== r.subject.type ||
            obs.subject.id !== r.subject.id ||
            obs.predicate !== r.predicate ||
            obs.value !== r.value ||
            Date.parse(obs.observedAt) < Date.parse(r.observedAt)
          )
            error(
              path,
              "verification",
              "Verified needs matching direct observation or record review",
            );
          if (r.basis === "inferred")
            error(
              path,
              "verification",
              "Inference cannot be promoted to verified",
            );
        } else if (r.verificationObservationId)
          error(
            path,
            "verification",
            "Verification observation only applies to verified review",
          );
        if (r.derivedFrom.includes(r.id) || r.conflictsWith.includes(r.id))
          error(
            path,
            "self_reference",
            "Claim cannot depend on or conflict with itself",
          );
      }
      if (collection === "authorityAssertions") {
        if (r.holder) subject(r.holder, path);
        support(r.claimIds, path);
        const targets = {
          business_ownership: ["business"],
          business_operations: ["occupancy"],
          utility_account: ["utilityAccount"],
          property: ["building", "suite", "premise"],
          hvac_facilities: ["building", "suite", "premise", "serviceLocation"],
        };
        if (!targets[r.kind].includes(r.subject.type))
          error(path, "authority_scope", "Wrong subject for authority kind");
        if (r.holder && !r.claimIds.length)
          error(path, "authority_evidence", "Named holder requires evidence");
        for (const id of r.claimIds) {
          const c = index.get(id)?.r;
          if (
            c?.subject?.id !== r.subject.id ||
            c?.subject?.type !== r.subject.type ||
            c?.predicate !== `authority.${r.kind}` ||
            c?.value !== r.holder?.id
          )
            error(
              path,
              "authority_evidence",
              "Authority claim must match subject, kind and holder",
            );
        }
      }
      if (
        [
          "listMemberships",
          "prospectAuthorizations",
          "suppressions",
          "suppressionReleases",
        ].includes(collection)
      ) {
        target(r.sourceRowId, "sourceRows", path);
        if (collection !== "listMemberships") {
          actor(r.issuedBy, "manager", path);
          if (!r.reason.trim())
            error(path, "reason", "Manager directive needs reason");
        }
        if (collection === "suppressionReleases") {
          const s = target(r.suppressionId, "suppressions", path);
          if (s && Date.parse(r.issuedAt) < Date.parse(s.issuedAt))
            error(path, "time", "Release predates suppression");
        }
      }
    }
  // Duplicate account/service references are review warnings, never implicit identity merges.
  for (const collection of ["utilityAccounts", "serviceLocations"]) {
    const seen = new Map();
    for (const r of w[collection])
      if (r.provider && r.reference) {
        const key = JSON.stringify([r.provider, r.reference]);
        if (seen.has(key))
          warnings.push({
            path: collection,
            code: "duplicate_external_reference",
            ids: [seen.get(key), r.id],
            message: "Review identity; records remain separate",
          });
        else seen.set(key, r.id);
      }
  }
  const positions = new Set();
  for (const r of w.sourceRows) {
    const key = JSON.stringify([r.batchId, r.rowIndex]);
    if (positions.has(key))
      error(
        "sourceRows." + r.id,
        "duplicate_row_position",
        "One row per index within a batch",
      );
    positions.add(key);
  }
  const visiting = new Set(),
    done = new Set();
  function visit(id) {
    if (visiting.has(id)) {
      error("claims." + id, "cycle", "Cyclic inference dependencies");
      return;
    }
    if (done.has(id)) return;
    visiting.add(id);
    const c = index.get(id);
    if (c?.collection === "claims")
      for (const dep of c.r.derivedFrom) visit(dep);
    visiting.delete(id);
    done.add(id);
  }
  for (const c of w.claims) visit(c.id);
  return { ok: !errors.length, errors, warnings };
}
export function assertWorkspace(w, context) {
  const result = validateWorkspace(w, context);
  if (!result.ok) {
    const e = new Error("Invalid FieldMind domain workspace");
    e.diagnostics = result.errors;
    throw e;
  }
  return result;
}
