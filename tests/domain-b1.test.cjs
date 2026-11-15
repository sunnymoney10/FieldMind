const { test } = require("node:test");
const assert = require("node:assert/strict");
const f = require("./fixtures/domain-b1.cjs");
const load = Promise.all([
  import("../domain/contracts.mjs"),
  import("../domain/validate.mjs"),
  import("../domain/functions.mjs"),
]).then((ms) => Object.assign({}, ...ms));
async function setup() {
  const d = await load;
  return { d, w: f.fixture(d.emptyWorkspace), ctx: structuredClone(f.context) };
}
function good(d, w, ctx) {
  const result = d.validateWorkspace(w, ctx);
  assert.equal(result.ok, true, JSON.stringify(result.errors));
}
function bad(d, w, ctx, code) {
  const result = d.validateWorkspace(w, ctx);
  assert.equal(result.ok, false);
  if (code)
    assert.ok(
      result.errors.some((e) => e.code === code),
      JSON.stringify(result.errors),
    );
}
function verified(w, id, subject, predicate, value) {
  const v = f.verified(id, subject, predicate, value);
  w.fieldObservations.push(v.observation);
  w.claims.push(v.claim);
  return v.claim;
}
function authority(w, kind, subject, holder, id = kind) {
  verified(w, "claim-" + id, subject, "authority." + kind, holder.id);
  w.authorityAssertions.push({
    ...f.base("authority-" + id),
    kind,
    subject,
    holder,
    claimIds: ["claim-" + id],
  });
}
const at = f.AT,
  day = f.DAY;
test("B1 synthetic snapshot validates without mutating raw import or duplicate headers", async () => {
  const { d, w, ctx } = await setup();
  const before = JSON.stringify(w);
  good(d, w, ctx);
  assert.equal(JSON.stringify(w), before);
  assert.equal(w.sourceRows[0].headers[0], w.sourceRows[0].headers[1]);
  assert.ok(w.importBatches[0].rawText.includes("\r\n"));
});
test("B1 strict contracts reject unknown fields, invalid types and impossible dates without throwing", async () => {
  const { d, w, ctx } = await setup();
  for (const change of [
    (x) => (x.premises[0].madeUp = true),
    (x) => (x.claims[0].period.from = "2026-02-30"),
    (x) => (x.sourceRows[0].cells = {}),
    (x) => (x.claims[0].observedAt = "2026-11-15T25:00:00Z"),
    (x) => (x.claims[0].value = null),
  ]) {
    const copy = structuredClone(w);
    change(copy);
    bad(d, copy, ctx);
  }
  assert.equal(d.validateWorkspace(null).ok, false);
  assert.equal(d.validateRecord("not-a-table", {}).ok, false);
});
test("B1 cross-workspace, duplicate IDs, missing and wrong-typed references fail", async () => {
  const { d, w, ctx } = await setup();
  for (const change of [
    (x) => (x.suites[0].workspaceId = "other"),
    (x) => (x.suites[0].id = "building"),
    (x) => (x.premises[0].suiteId = "missing"),
    (x) => (x.premises[0].suiteId = "business-a"),
  ]) {
    const copy = structuredClone(w);
    change(copy);
    bad(d, copy, ctx);
  }
});
test("B1 buildings, suites, premises and service locations stay distinct; inconsistent suite parent fails", async () => {
  const { d, w, ctx } = await setup();
  w.buildings.push({
    ...f.base("another-building"),
    addressRaw: "100 Fictional Plaza",
    externalRefs: [],
  });
  w.premises[0].buildingId = "another-building";
  bad(d, w, ctx, "location");
});
test("B1 shared names/addresses and exact external IDs only return review candidates", async () => {
  const { d, w, ctx } = await setup();
  const before = JSON.stringify(w);
  let result = d.identityCandidates(
    w,
    { type: "premise", addressRaw: "100 Fictional Plaza" },
    ctx,
  );
  assert.equal(result.candidates.length, 2);
  assert.equal(result.acceptedId, null);
  assert.equal(result.status, "review_required");
  assert.equal(
    d.identityCandidates(
      w,
      { type: "business", name: "Synthetic Shared Name" },
      ctx,
    ).candidates.length,
    2,
  );
  w.premises[0].externalRefs = [
    {
      issuer: "Synthetic Utility",
      kind: "premise",
      value: "000-01",
      sourceRowIds: ["row-old"],
    },
  ];
  result = d.identityCandidates(
    w,
    { type: "premise", externalReference: w.premises[0].externalRefs[0] },
    ctx,
  );
  assert.equal(result.acceptedId, null);
  w.premises[0].externalRefs = [];
  assert.equal(JSON.stringify(w), before);
});
test("B1 accepted occupancy/service relationships require typed evidence, allow multiple occupancies", async () => {
  const { d, w, ctx } = await setup();
  for (const [business, id] of [
    ["business-a", "occupancy-a"],
    ["business-b", "occupancy-b"],
  ]) {
    const c = verified(
      w,
      "claim-" + id,
      f.ref("business", business),
      "occupies",
      "premise-101",
    );
    w.occupancies.push({
      ...f.base(id),
      premiseId: "premise-101",
      businessId: business,
      period: { from: null, to: null },
      supportClaimIds: [c.id],
    });
  }
  good(d, w, ctx);
  w.occupancies[0].supportClaimIds = [];
  bad(d, w, ctx, "support");
});
test("B1 successive and simultaneous utility accounts can serve one service location without inferred succession", async () => {
  const { d, w, ctx } = await setup();
  const link = verified(
    w,
    "service-claim",
    f.ref("serviceLocation", "service"),
    "serves_premise",
    "premise-101",
  );
  w.serviceLocations.push({
    ...f.base("service"),
    provider: "Synthetic Utility",
    reference: "SYN-SERVICE",
    premiseIds: ["premise-101"],
    supportClaimIds: [link.id],
    externalRefs: [],
  });
  for (const [i, a] of w.utilityAccounts.entries()) {
    a.serviceLocationIds = ["service"];
    a.period =
      i === 0
        ? { from: "2020-01-01", to: "2022-12-31" }
        : { from: "2023-01-01", to: null };
    a.supportClaimIds = [
      verified(
        w,
        "account-link-" + i,
        f.ref("utilityAccount", a.id),
        "served_at",
        "service",
      ).id,
    ];
  }
  good(d, w, ctx);
  assert.equal(w.utilityAccounts.length, 3);
  assert.equal(
    d.mimoHistory(w, "account-old", ctx).accountSequence,
    "not_inferred",
  );
});
test("B1 account references preserve punctuation/leading zeros and unknown providers, duplicates produce warnings", async () => {
  const { d, w, ctx } = await setup();
  w.utilityAccounts.push({ ...w.utilityAccounts[0], id: "account-duplicate" });
  const result = d.validateWorkspace(w, ctx);
  assert.equal(result.ok, true);
  assert.equal(result.warnings[0].code, "duplicate_external_reference");
  assert.equal(w.utilityAccounts[0].reference, "000-OLD");
  w.utilityAccounts[0].provider = null;
  good(d, w, ctx);
});
test("B1 five authority concepts resolve independently with no ownership shortcut", async () => {
  const { d, w, ctx } = await setup();
  const scopes = {
    business_ownership: f.ref("business", "business-a"),
    business_operations: f.ref("occupancy", "occupancy"),
    utility_account: f.ref("utilityAccount", "account-new"),
    property: f.ref("building", "building"),
    hvac_facilities: f.ref("premise", "premise-101"),
  };
  const c = verified(
    w,
    "occupies",
    f.ref("business", "business-a"),
    "occupies",
    "premise-101",
  );
  w.occupancies.push({
    ...f.base("occupancy"),
    premiseId: "premise-101",
    businessId: "business-a",
    period: { from: null, to: null },
    supportClaimIds: [c.id],
  });
  for (const [kind, holder] of [
    ["business_ownership", "owner"],
    ["business_operations", "operator"],
    ["utility_account", "account-agent"],
    ["property", "landlord"],
    ["hvac_facilities", "facilities"],
  ])
    authority(w, kind, scopes[kind], f.ref("party", holder));
  good(d, w, ctx);
  for (const kind of d.AUTHORITY_KINDS) {
    const result = d.authorityFor(
      w,
      { kind, subject: scopes[kind], asOf: day },
      ctx,
    );
    assert.equal(result.state, "verified");
  }
  w.authorityAssertions = w.authorityAssertions.filter(
    (a) => a.kind === "business_ownership",
  );
  assert.equal(
    d.authorityFor(
      w,
      { kind: "hvac_facilities", subject: scopes.hvac_facilities, asOf: day },
      ctx,
    ).state,
    "unknown",
  );
});
test("B1 authority can be unknown, inferred, disputed or verified, with traceable support", async () => {
  const { d, w, ctx } = await setup();
  const subject = f.ref("business", "business-a"),
    holder = f.ref("party", "owner");
  w.authorityAssertions.push({
    ...f.base("auth"),
    kind: "business_ownership",
    subject,
    holder: null,
    claimIds: [],
  });
  assert.equal(
    d.authorityFor(w, { kind: "business_ownership", subject, asOf: day }, ctx)
      .state,
    "unknown",
  );
  const parent = verified(w, "parent", subject, "owner_named", "owner");
  w.claims.push(
    f.claim("inference", {
      subject,
      predicate: "authority.business_ownership",
      value: "owner",
      origin: "ai",
      basis: "inferred",
      derivedFrom: [parent.id],
      researchRunId: "run",
    }),
  );
  w.authorityAssertions[0].holder = holder;
  w.authorityAssertions[0].claimIds = ["inference"];
  assert.equal(
    d.authorityFor(w, { kind: "business_ownership", subject, asOf: day }, ctx)
      .state,
    "inferred",
  );
  w.claims.find((c) => c.id === "parent").review = "disputed";
  w.claims.find((c) => c.id === "parent").verificationObservationId = null;
  assert.equal(
    d.authorityFor(w, { kind: "business_ownership", subject, asOf: day }, ctx)
      .state,
    "disputed",
  );
});
test("B1 competing authority holders dispute resolution rather than picking first", async () => {
  const { d, w, ctx } = await setup();
  const subject = f.ref("business", "business-a");
  authority(w, "business_ownership", subject, f.ref("party", "owner"), "one");
  authority(
    w,
    "business_ownership",
    subject,
    f.ref("party", "operator"),
    "two",
  );
  assert.equal(
    d.authorityFor(w, { kind: "business_ownership", subject, asOf: day }, ctx)
      .state,
    "disputed",
  );
});
test("B1 research cannot self-verify and observation must match exact subject/predicate/value", async () => {
  const { d, w, ctx } = await setup();
  const c = verified(
    w,
    "verify",
    f.ref("business", "business-a"),
    "operating_status",
    "Open",
  );
  c.value = "Closed";
  bad(d, w, ctx, "verification");
  c.value = "Open";
  c.basis = "inferred";
  c.derivedFrom = ["history-device"];
  bad(d, w, ctx, "verification");
});
test("B1 disputed dependencies and asymmetric conflicts propagate; dependency cycles rejected", async () => {
  const { d, w, ctx } = await setup();
  verified(
    w,
    "fact",
    f.ref("business", "business-a"),
    "operating_status",
    "Open",
  );
  w.claims.push(
    f.claim("opposite", {
      predicate: "operating_status",
      value: "Closed",
      conflictsWith: ["fact"],
    }),
  );
  w.claims.push(
    f.claim("derived", {
      predicate: "decision_context",
      basis: "inferred",
      origin: "ai",
      derivedFrom: ["fact"],
      researchRunId: "run",
    }),
  );
  assert.equal(d.claimState(w, "fact", { asOf: day }, ctx), "disputed");
  assert.equal(d.claimState(w, "derived", { asOf: day }, ctx), "disputed");
  w.claims.find((c) => c.id === "fact").derivedFrom = ["derived"];
  bad(d, w, ctx, "cycle");
});
test("B1 building citations cannot establish suite facts without explicit inference; dangling evidence rejected", async () => {
  const { d, w, ctx } = await setup();
  w.claims.push(f.claim("scope", { subject: f.ref("premise", "premise-101") }));
  bad(d, w, ctx, "scope");
  w.claims.pop();
  w.claims[0].derivedFrom = ["missing"];
  bad(d, w, ctx, "reference");
});
test("B1 freshness, future observations, historical facts and unknown time do not become current verified authority", async () => {
  const { d, w, ctx } = await setup();
  authority(
    w,
    "property",
    f.ref("building", "building"),
    f.ref("party", "landlord"),
  );
  const q = {
    kind: "property",
    subject: f.ref("building", "building"),
    asOf: "2026-11-16",
  };
  assert.equal(d.authorityFor(w, q, ctx).state, "unknown");
  assert.equal(
    d.authorityFor(w, { ...q, maxAgeDays: 1 }, ctx).state,
    "verified",
  );
  assert.equal(
    d.authorityFor(w, { ...q, asOf: "2026-11-14" }, ctx).state,
    "unknown",
  );
});
test("B1 list membership, manager approval and suppression are independent audit records", async () => {
  const { d, w, ctx } = await setup();
  const subject = f.ref("premise", "premise-101");
  w.listMemberships.push({
    ...f.base("membership"),
    subject,
    sourceRowId: "row-old",
    listType: "approved",
  });
  let result = d.prospectDecision(w, [subject], at, ctx);
  assert.equal(result.authorization, "unknown");
  assert.equal(result.eligibility, "not_established");
  w.prospectAuthorizations.push({
    ...f.base("approval"),
    subject,
    sourceRowId: "row-old",
    issuedBy: "manager",
    decision: "authorized",
    reason: "Synthetic authorization",
    issuedAt: at,
  });
  w.suppressions.push({
    ...f.base("dnc"),
    subject,
    sourceRowId: "row-old",
    issuedBy: "manager",
    reason: "Synthetic DNC",
    issuedAt: at,
  });
  result = d.prospectDecision(w, [subject], at, ctx);
  assert.equal(result.authorization, "authorized");
  assert.equal(result.suppressed, true);
  assert.equal(result.mayResearch, false);
  assert.equal(result.memberships.length, 1);
  assert.deepEqual(result.activeSuppressionIds, ["dnc"]);
});
test("B1 generic Active rows and AI findings cannot release suppression or confer eligibility", async () => {
  const { d, w, ctx } = await setup();
  const subject = f.ref("premise", "premise-101");
  w.suppressions.push({
    ...f.base("dnc"),
    subject,
    sourceRowId: "row-old",
    issuedBy: "manager",
    reason: "DNC",
    issuedAt: at,
  });
  w.sourceRows.push({
    ...f.base("row-new"),
    batchId: "batch-old",
    rowIndex: 1,
    headers: ["Status"],
    cells: ["Active"],
  });
  w.claims.push(
    f.claim("ai-opinion", {
      origin: "ai",
      researchRunId: "run",
      predicate: "opportunity_context",
      value: "Appears promising",
    }),
  );
  assert.equal(d.prospectDecision(w, [subject], at, ctx).suppressed, true);
  w.claims[2].predicate = "eligibility";
  bad(d, w, ctx, "control_plane");
});
test("B1 only explicit manager release clears its referenced suppression and retains both records", async () => {
  const { d, w, ctx } = await setup();
  const subject = f.ref("premise", "premise-101");
  for (const id of ["dnc", "hold"])
    w.suppressions.push({
      ...f.base(id),
      subject,
      sourceRowId: "row-old",
      issuedBy: "manager",
      reason: "Synthetic restriction",
      issuedAt: at,
    });
  w.suppressionReleases.push({
    ...f.base("release"),
    suppressionId: "dnc",
    sourceRowId: "row-old",
    issuedBy: "manager",
    reason: "Explicit release",
    issuedAt: at,
  });
  assert.deepEqual(
    d.prospectDecision(w, [subject], at, ctx).activeSuppressionIds,
    ["hold"],
  );
  assert.equal(w.suppressions.length, 2);
  w.suppressionReleases[0].issuedBy = "ai";
  bad(d, w, ctx, "actor");
});
test("B1 ambiguous control scope requires explicit subjects; future directives do not apply", async () => {
  const { d, w, ctx } = await setup();
  const subject = f.ref("premise", "premise-101");
  w.prospectAuthorizations.push({
    ...f.base("future"),
    subject,
    sourceRowId: "row-old",
    issuedBy: "manager",
    decision: "authorized",
    reason: "Synthetic",
    issuedAt: "2026-11-16T12:00:00.000Z",
  });
  assert.equal(
    d.prospectDecision(w, [subject], at, ctx).authorization,
    "unknown",
  );
  assert.throws(() => d.prospectDecision(w, [], at, ctx));
});
test("B1 MIMO preserves original history without current equipment or sequential-account assumptions", async () => {
  const { d, w, ctx } = await setup();
  const before = JSON.stringify(w);
  const result = d.mimoHistory(w, "account-old", ctx);
  assert.equal(result.claims.length, 2);
  assert.equal(result.currentEquipment, "unknown");
  assert.equal(result.currentEligibility, "not_established");
  assert.equal(result.accountSequence, "not_inferred");
  result.claims[0].value = "Changed";
  assert.equal(JSON.stringify(w), before);
  w.claims[0].temporal = "as_of";
  bad(d, w, ctx, "mimo");
});
test("B1 append preserves history and exact replays; conflicting IDs never overwrite; failure is atomic", async () => {
  const { d, w, ctx } = await setup();
  ctx.actorId = "manager";
  const before = JSON.stringify(w);
  const batch = { ...w.importBatches[0], id: "batch-repeat" };
  const row = { ...w.sourceRows[0], id: "row-repeat", batchId: batch.id };
  const result = d.appendRecords(
    w,
    { importBatches: [batch], sourceRows: [row] },
    ctx,
  );
  assert.equal(result.workspace.sourceRows.length, 2);
  assert.equal(result.workspace.sourceRows[0].cells[3], "Synthetic Device");
  assert.equal(JSON.stringify(w), before);
  const replay = d.appendRecords(result.workspace, { sourceRows: [row] }, ctx);
  assert.equal(replay.replayed.length, 1);
  assert.throws(
    () =>
      d.appendRecords(
        result.workspace,
        { sourceRows: [{ ...row, cells: ["different"] }] },
        ctx,
      ),
    /Identity conflict/,
  );
  assert.throws(() =>
    d.appendRecords(w, { sourceRows: [{ ...row, batchId: "missing" }] }, ctx),
  );
  assert.equal(JSON.stringify(w), before);
});
test("B1 AI caller cannot spoof manager/observer or append verified claims", async () => {
  const { d, w, ctx } = await setup();
  ctx.actorId = "ai";
  const directive = {
    ...f.base("forged"),
    subject: f.ref("premise", "premise-101"),
    sourceRowId: "row-old",
    issuedBy: "manager",
    reason: "Spoof",
    issuedAt: at,
    decision: "authorized",
  };
  assert.throws(() =>
    d.appendRecords(w, { prospectAuthorizations: [directive] }, ctx),
  );
  assert.throws(() =>
    d.appendRecords(
      w,
      {
        fieldObservations: [
          f.verified(
            "forged",
            f.ref("business", "business-a"),
            "status",
            "Open",
          ).observation,
        ],
      },
      ctx,
    ),
  );
  assert.throws(() =>
    d.appendRecords(
      w,
      {
        claims: [
          {
            ...f.claim("forged"),
            origin: "ai",
            researchRunId: "run",
            review: "verified",
          },
        ],
      },
      ctx,
    ),
  );
  const result = d.appendRecords(
    w,
    { claims: [f.claim("valid-ai", { origin: "ai", researchRunId: "run" })] },
    ctx,
  );
  assert.equal(result.added[0], "valid-ai");
});
test("B1 public source evidence alone does not imply representative verification", async () => {
  const { d, w, ctx } = await setup();
  w.claims.push(f.claim("public"));
  assert.equal(d.claimState(w, "public", { asOf: day }, ctx), "unknown");
});
test("B1 a service location may serve multiple premises; account-to-service links remain explicit", async () => {
  const { d, w, ctx } = await setup();
  const links = [101, 102].map(
    (n) =>
      verified(
        w,
        "shared-service-" + n,
        f.ref("serviceLocation", "shared-service"),
        "serves_premise",
        "premise-" + n,
      ).id,
  );
  w.serviceLocations.push({
    ...f.base("shared-service"),
    provider: "Synthetic Utility",
    reference: "Shared",
    premiseIds: ["premise-101", "premise-102"],
    supportClaimIds: links,
    externalRefs: [],
  });
  good(d, w, ctx);
  w.serviceLocations[0].supportClaimIds.pop();
  bad(d, w, ctx, "support");
});
test("B1 all five authority kinds retain verified, inferred, disputed and unknown states independently", async () => {
  const { d, w, ctx } = await setup();
  w.occupancies.push({
    ...f.base("ops"),
    premiseId: "premise-101",
    businessId: "business-a",
    period: { from: null, to: null },
    supportClaimIds: [
      verified(
        w,
        "ops-link",
        f.ref("business", "business-a"),
        "occupies",
        "premise-101",
      ).id,
    ],
  });
  const subjects = [
    f.ref("business", "business-a"),
    f.ref("occupancy", "ops"),
    f.ref("utilityAccount", "account-old"),
    f.ref("building", "building"),
    f.ref("premise", "premise-101"),
  ];
  for (const [i, kind] of d.AUTHORITY_KINDS.entries()) {
    const subject = subjects[i],
      query = { kind, subject, asOf: day };
    assert.equal(d.authorityFor(w, query, ctx).state, "unknown");
    authority(w, kind, subject, f.ref("party", "owner"), "kind-" + i);
    assert.equal(d.authorityFor(w, query, ctx).state, "verified");
    const parentId = "claim-kind-" + i;
    w.claims.push(
      f.claim("inferred-kind-" + i, {
        subject,
        predicate: "authority." + kind,
        value: "owner",
        origin: "ai",
        basis: "inferred",
        researchRunId: "run",
        derivedFrom: [parentId],
        citations: [],
      }),
    );
    const assertion = w.authorityAssertions.find(
      (a) => a.id === "authority-kind-" + i,
    );
    assertion.claimIds = ["inferred-kind-" + i];
    assert.equal(d.authorityFor(w, query, ctx).state, "inferred");
    w.claims.find((c) => c.id === parentId).review = "disputed";
    w.claims.find((c) => c.id === parentId).verificationObservationId = null;
    assert.equal(d.authorityFor(w, query, ctx).state, "disputed");
  }
});
test("B1 unsafe citation URLs, wrong observation actors and arbitrary unknown predicates cannot issue controls", async () => {
  const { d, w, ctx } = await setup();
  w.claims.push(
    f.claim("unsafe", {
      citations: [
        {
          url: "javascript:alert(1)",
          title: "Synthetic",
          excerpt: "Synthetic",
          retrievedAt: at,
          publishedOn: null,
          scope: f.ref("business", "business-a"),
        },
      ],
    }),
  );
  bad(d, w, ctx, "citation");
  w.claims.pop();
  const v = f.verified(
    "bad-actor",
    f.ref("business", "business-a"),
    "ownership",
    "owner",
  );
  v.observation.observerId = "ai";
  w.fieldObservations.push(v.observation);
  w.claims.push(v.claim);
  bad(d, w, ctx, "actor");
});
test("B1 approval ties dispute, withdrawal blocks, releases respect asOf and explicit suppression IDs", async () => {
  const { d, w, ctx } = await setup();
  const subject = f.ref("premise", "premise-101");
  for (const [id, decision] of [
    ["yes", "authorized"],
    ["no", "withdrawn"],
  ])
    w.prospectAuthorizations.push({
      ...f.base(id),
      subject,
      sourceRowId: "row-old",
      issuedBy: "manager",
      decision,
      reason: "Synthetic manager decision",
      issuedAt: at,
    });
  assert.equal(
    d.prospectDecision(w, [subject], at, ctx).authorization,
    "disputed",
  );
  w.prospectAuthorizations[1].issuedAt = "2026-11-15T13:00:00.000Z";
  assert.equal(
    d.prospectDecision(w, [subject], "2026-11-15T14:00:00.000Z", ctx)
      .authorization,
    "withdrawn",
  );
  w.suppressions.push({
    ...f.base("restriction"),
    subject,
    sourceRowId: "row-old",
    issuedBy: "manager",
    reason: "DNC",
    issuedAt: at,
  });
  w.suppressionReleases.push({
    ...f.base("future-release"),
    suppressionId: "restriction",
    sourceRowId: "row-old",
    issuedBy: "manager",
    reason: "Explicit release",
    issuedAt: "2026-11-16T12:00:00.000Z",
  });
  assert.equal(d.prospectDecision(w, [subject], at, ctx).suppressed, true);
  assert.equal(
    d.prospectDecision(w, [subject], "2026-11-17T12:00:00.000Z", ctx)
      .suppressed,
    false,
  );
});
test("B1 later verification cannot rewrite earlier as-of knowledge; freshness uses observation date", async () => {
  const { d, w, ctx } = await setup();
  const c = verified(
    w,
    "dated",
    f.ref("business", "business-a"),
    "operating_status",
    "Open",
  );
  c.period.from = "2020-01-01";
  assert.equal(d.claimState(w, c.id, { asOf: day }, ctx), "verified");
  w.fieldObservations.find(
    (o) => o.id === c.verificationObservationId,
  ).observedAt = "2026-11-16T12:00:00.000Z";
  assert.equal(d.claimState(w, c.id, { asOf: day }, ctx), "unknown");
});
test("B1 equivalent UTC timestamps compare chronologically regardless of fractional seconds", async () => {
  const { d, w, ctx } = await setup();
  const subject = f.ref("premise", "premise-101");
  for (const [id, decision, issuedAt] of [
    ["fractional", "authorized", at],
    ["whole", "withdrawn", "2026-11-15T12:00:00Z"],
  ])
    w.prospectAuthorizations.push({
      ...f.base(id),
      subject,
      sourceRowId: "row-old",
      issuedBy: "manager",
      decision,
      reason: "Synthetic equal-time directive",
      issuedAt,
    });
  assert.equal(
    d.prospectDecision(w, [subject], at, ctx).authorization,
    "disputed",
  );
  const v = f.verified(
    "whole-time",
    f.ref("business", "business-a"),
    "status",
    "Open",
  );
  v.observation.observedAt = "2026-11-15T12:00:00Z";
  w.claims.push(v.claim);
  w.fieldObservations.push(v.observation);
  good(d, w, ctx);
});
