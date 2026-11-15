/** Persistence-free B1 contracts. All objects are strict; nullable dates express unknown bounds. */
const text = { kind: "string" },
  id = { kind: "id" },
  timestamp = { kind: "timestamp" },
  date = { kind: "date" };
const list = (of) => ({ kind: "array", of }),
  nullable = (of) => ({ kind: "nullable", of });
const shape = (fields) => ({ kind: "object", fields });
const oneOf = (...values) => ({ kind: "enum", values });
const ref = (...types) => ({ kind: "ref", types });
export const SUBJECT_TYPES = Object.freeze([
  "building",
  "suite",
  "premise",
  "serviceLocation",
  "business",
  "occupancy",
  "utilityAccount",
  "party",
]);
export const AUTHORITY_KINDS = Object.freeze([
  "business_ownership",
  "business_operations",
  "utility_account",
  "property",
  "hvac_facilities",
]);
export const COLLECTIONS = Object.freeze({
  building: "buildings",
  suite: "suites",
  premise: "premises",
  serviceLocation: "serviceLocations",
  business: "businesses",
  occupancy: "occupancies",
  utilityAccount: "utilityAccounts",
  party: "parties",
  importBatch: "importBatches",
  sourceRow: "sourceRows",
  claim: "claims",
  researchRun: "researchRuns",
  fieldObservation: "fieldObservations",
  authorityAssertion: "authorityAssertions",
  listMembership: "listMemberships",
  prospectAuthorization: "prospectAuthorizations",
  suppression: "suppressions",
  suppressionRelease: "suppressionReleases",
});
const subject = ref(...SUBJECT_TYPES);
const period = shape({ from: nullable(date), to: nullable(date) });
const citation = shape({
  url: text,
  title: text,
  excerpt: text,
  retrievedAt: timestamp,
  publishedOn: nullable(date),
  scope: subject,
});
const externalRef = shape({
  issuer: text,
  kind: text,
  value: text,
  sourceRowIds: list(id),
});
const common = { id, workspaceId: id, createdAt: timestamp };
const record = (fields) => shape({ ...common, ...fields });
// Complete records are required. Optional domain facts use explicit null/empty arrays, not inferred defaults.
export const CONTRACTS = Object.freeze({
  buildings: record({ addressRaw: text, externalRefs: list(externalRef) }),
  suites: record({
    buildingId: id,
    label: text,
    addressRaw: text,
    externalRefs: list(externalRef),
  }),
  premises: record({
    buildingId: nullable(id),
    suiteId: nullable(id),
    addressRaw: text,
    externalRefs: list(externalRef),
  }),
  serviceLocations: record({
    provider: nullable(text),
    reference: nullable(text),
    premiseIds: list(id),
    supportClaimIds: list(id),
    externalRefs: list(externalRef),
  }),
  businesses: record({
    name: text,
    aliases: list(text),
    externalRefs: list(externalRef),
  }),
  parties: record({
    displayName: text,
    kind: oneOf("person", "organization", "unknown"),
  }),
  occupancies: record({
    premiseId: id,
    businessId: id,
    period,
    supportClaimIds: list(id),
  }),
  utilityAccounts: record({
    provider: nullable(text),
    reference: text,
    serviceLocationIds: list(id),
    period,
    supportClaimIds: list(id),
  }),
  importBatches: record({
    fileName: text,
    rawText: text,
    declaredSource: text,
    importedBy: id,
    listType: oneOf("approved", "mimo", "other"),
    parserVersion: text,
    mappingVersion: text,
  }),
  sourceRows: record({
    batchId: id,
    rowIndex: { kind: "integer", min: 0 },
    headers: list(text),
    cells: list(text),
  }),
  researchRuns: record({
    requestedPremiseIds: list(id),
    protocolVersion: text,
    rawRequest: text,
    rawResponse: text,
    completedAt: nullable(timestamp),
    coverage: list(
      shape({
        subject,
        dimension: text,
        result: oneOf("found", "not_found", "not_checked"),
        checked: text,
      }),
    ),
  }),
  fieldObservations: record({
    observerId: id,
    subject,
    predicate: text,
    kind: oneOf(
      "direct_observation",
      "staff_statement",
      "representative_inference",
      "record_review",
    ),
    value: text,
    note: text,
    observedAt: timestamp,
  }),
  claims: record({
    subject,
    predicate: text,
    value: text,
    origin: oneOf(
      "public_record",
      "public_source",
      "manager_list",
      "ai",
      "field",
    ),
    basis: oneOf("reported", "observed", "inferred"),
    review: oneOf("unreviewed", "verified", "disputed", "superseded"),
    temporal: oneOf("historical", "as_of", "unknown"),
    period,
    observedAt: timestamp,
    sourcePublishedOn: nullable(date),
    sourceRowIds: list(id),
    citations: list(citation),
    fieldObservationIds: list(id),
    derivedFrom: list(id),
    conflictsWith: list(id),
    researchRunId: nullable(id),
    verificationObservationId: nullable(id),
  }),
  authorityAssertions: record({
    kind: oneOf(...AUTHORITY_KINDS),
    subject,
    holder: nullable(ref("party", "business")),
    claimIds: list(id),
  }),
  listMemberships: record({
    subject,
    sourceRowId: id,
    listType: oneOf("approved", "mimo", "other"),
  }),
  prospectAuthorizations: record({
    subject,
    sourceRowId: id,
    issuedBy: id,
    decision: oneOf("authorized", "withdrawn"),
    reason: text,
    issuedAt: timestamp,
  }),
  suppressions: record({
    subject,
    sourceRowId: id,
    issuedBy: id,
    reason: text,
    issuedAt: timestamp,
  }),
  suppressionReleases: record({
    suppressionId: id,
    sourceRowId: id,
    issuedBy: id,
    reason: text,
    issuedAt: timestamp,
  }),
});
export const SNAPSHOT_SCHEMA = shape({
  schemaVersion: oneOf(1),
  workspaceId: id,
  ...Object.fromEntries(
    Object.entries(CONTRACTS).map(([k, v]) => [k, list(v)]),
  ),
});
export function emptyWorkspace(workspaceId) {
  return {
    schemaVersion: 1,
    workspaceId,
    ...Object.fromEntries(Object.keys(CONTRACTS).map((k) => [k, []])),
  };
}
