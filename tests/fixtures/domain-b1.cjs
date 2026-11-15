// Entirely synthetic domain snapshot. IDs are fixture labels, never address/name/account hashes.
const AT = "2026-11-15T12:00:00.000Z",
  DAY = "2026-11-15";
const base = (id) => ({
  id,
  workspaceId: "synthetic-workspace",
  createdAt: AT,
});
const ref = (type, id) => ({ type, id });
const context = {
  actorId: "rep",
  actors: {
    rep: { workspaceId: "synthetic-workspace", roles: ["representative"] },
    manager: { workspaceId: "synthetic-workspace", roles: ["manager"] },
    ai: { workspaceId: "synthetic-workspace", roles: ["researcher"] },
  },
};
function fixture(emptyWorkspace) {
  const w = emptyWorkspace("synthetic-workspace");
  w.buildings = [
    {
      ...base("building"),
      addressRaw: "100 Fictional Plaza",
      externalRefs: [],
    },
  ];
  w.suites = [101, 102].map((n) => ({
    ...base("suite-" + n),
    buildingId: "building",
    label: String(n),
    addressRaw: "100 Fictional Plaza",
    externalRefs: [],
  }));
  w.premises = [101, 102].map((n) => ({
    ...base("premise-" + n),
    buildingId: "building",
    suiteId: "suite-" + n,
    addressRaw: "100 Fictional Plaza",
    externalRefs: [],
  }));
  w.businesses = [
    {
      ...base("business-a"),
      name: "Synthetic Shared Name",
      aliases: [],
      externalRefs: [],
    },
    {
      ...base("business-b"),
      name: "Synthetic Shared Name",
      aliases: [],
      externalRefs: [],
    },
  ];
  w.parties = [
    "owner",
    "operator",
    "account-agent",
    "landlord",
    "facilities",
  ].map((n) => ({ ...base(n), displayName: "Synthetic " + n, kind: "person" }));
  w.importBatches = [
    {
      ...base("batch-old"),
      fileName: "synthetic-mimo.csv",
      rawText:
        'Name,Name,Account,Device,Status\r\n"Synthetic, Former",Other,000-OLD,Synthetic Device,DNC\r\n',
      declaredSource: "Synthetic manager list",
      importedBy: "manager",
      listType: "mimo",
      parserVersion: "fixture-1",
      mappingVersion: "fixture-1",
    },
  ];
  w.sourceRows = [
    {
      ...base("row-old"),
      batchId: "batch-old",
      rowIndex: 0,
      headers: ["Name", "Name", "Account", "Device", "Status"],
      cells: [
        "Synthetic, Former",
        "Other",
        "000-OLD",
        "Synthetic Device",
        "DNC",
      ],
    },
  ];
  w.researchRuns = [
    {
      ...base("run"),
      requestedPremiseIds: ["premise-101"],
      protocolVersion: "synthetic-1",
      rawRequest: "Synthetic request",
      rawResponse: "Synthetic response",
      completedAt: AT,
      coverage: [],
    },
  ];
  w.utilityAccounts = ["old", "new", "parallel"].map((n) => ({
    ...base("account-" + n),
    provider: "Synthetic Utility",
    reference:
      n === "old" ? "000-OLD" : n === "new" ? "000-NEW" : "000-PARALLEL",
    serviceLocationIds: [],
    period: { from: null, to: null },
    supportClaimIds: [],
  }));
  w.claims = [
    claim("history-participation", {
      subject: ref("utilityAccount", "account-old"),
      predicate: "historical_participation",
      value: "Participated in synthetic historic program",
      origin: "manager_list",
      temporal: "historical",
      sourceRowIds: ["row-old"],
      citations: [],
    }),
    claim("history-device", {
      subject: ref("utilityAccount", "account-old"),
      predicate: "historical_equipment",
      value: "Synthetic Device",
      origin: "manager_list",
      temporal: "historical",
      sourceRowIds: ["row-old"],
      citations: [],
    }),
  ];
  return w;
}
function claim(id, overrides = {}) {
  return {
    ...base(id),
    subject: ref("business", "business-a"),
    predicate: "operating_status",
    value: "Operating",
    origin: "public_source",
    basis: "reported",
    review: "unreviewed",
    temporal: "as_of",
    period: { from: DAY, to: null },
    observedAt: AT,
    sourcePublishedOn: null,
    sourceRowIds: [],
    citations: [
      {
        url: "https://example.com/synthetic",
        title: "Synthetic public source",
        excerpt: "Synthetic fact",
        retrievedAt: AT,
        publishedOn: null,
        scope: ref("business", "business-a"),
      },
    ],
    fieldObservationIds: [],
    derivedFrom: [],
    conflictsWith: [],
    researchRunId: null,
    verificationObservationId: null,
    ...overrides,
  };
}
function verified(id, subject, predicate, value) {
  const observation = {
    ...base("observation-" + id),
    observerId: "rep",
    subject,
    predicate,
    value,
    kind: "direct_observation",
    note: "Synthetic verification",
    observedAt: AT,
  };
  const c = claim(id, {
    subject,
    predicate,
    value,
    origin: "field",
    basis: "observed",
    review: "verified",
    citations: [],
    fieldObservationIds: [observation.id],
    verificationObservationId: observation.id,
  });
  return { observation, claim: c };
}
module.exports = { AT, DAY, base, ref, context, fixture, claim, verified };
