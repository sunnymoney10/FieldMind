const { test } = require("node:test");
const assert = require("node:assert/strict");
const f = require("./fixtures/domain-b1.cjs");
const load = Promise.all([
  import("../domain/contracts.mjs"),
  import("../domain/intelligence.mjs"),
  import("../domain/scope-policy.mjs"),
  import("../domain/limits.mjs"),
  import("../domain/legacy-preview.mjs"),
]).then((ms) => Object.assign({}, ...ms));
async function setup() {
  const d = await load;
  return { d, w: f.fixture(d.emptyWorkspace), ctx: structuredClone(f.context) };
}
function verify(
  w,
  id,
  predicate,
  value = "Synthetic fact",
  subject = f.ref("business", "business-a"),
) {
  const v = f.verified(id, subject, predicate, value);
  w.fieldObservations.push(v.observation);
  w.claims.push(v.claim);
  return v.claim;
}
function project(d, w, ctx, asOf = "2026-12-15") {
  return d.createIntelligenceProjection(w, { asOf }, ctx);
}
function directive(w, id, subject, kind = "suppression") {
  const d = {
    ...f.base(id),
    subject,
    sourceRowId: "row-old",
    issuedBy: "manager",
    reason: "Synthetic source-supported manager directive",
    issuedAt: f.AT,
  };
  if (kind === "authorization") {
    d.decision = "authorized";
    w.prospectAuthorizations.push(d);
  } else w.suppressions.push(d);
  return d;
}
function statement(d, mode, targets = []) {
  return {
    id: "scope-" + d.id + "-" + mode,
    directiveId: d.id,
    workspaceId: d.workspaceId,
    issuedBy: "manager",
    issuedAt: f.AT,
    sourceRowId: "row-old",
    mode,
    targets,
    reason: "Synthetic explicit scope attestation",
  };
}
test("B2A freshness differs by claim type: ownership survives months while hours becomes historical context", async () => {
  const { d, w, ctx } = await setup();
  verify(w, "ownership", "authority.business_ownership", "owner");
  verify(w, "hours", "hours", "9–5");
  let p = project(d, w, ctx, "2027-01-15");
  assert.equal(p.finding("ownership").status, "current_verified");
  assert.equal(p.finding("hours").freshness, "stale");
  assert.equal(p.finding("hours").status, "historical");
  assert.equal(p.finding("hours").usefulContext, true);
  assert.equal(p.finding("hours").value, "9–5");
});
test("B2A source and risk affect validity; public records last longer but are not representative authority", async () => {
  const { d, w, ctx } = await setup();
  w.claims.push(
    f.claim("public-owner", {
      predicate: "authority.business_ownership",
      origin: "public_record",
      value: "owner",
    }),
    f.claim("listing-owner", {
      predicate: "authority.business_ownership",
      value: "owner",
    }),
    f.claim("account-authority", {
      predicate: "authority.utility_account",
      subject: f.ref("utilityAccount", "account-old"),
      value: "owner",
      citations: [
        {
          ...f.claim("x").citations[0],
          scope: f.ref("utilityAccount", "account-old"),
        },
      ],
    }),
  );
  const p = project(d, w, ctx, "2027-01-15");
  assert.equal(p.finding("public-owner").status, "source_supported");
  assert.equal(p.finding("public-owner").authorityState, "unknown");
  assert.equal(p.finding("listing-owner").freshness, "stale");
  assert.equal(p.finding("account-authority").freshness, "stale");
});
test("B2A old published evidence is not refreshed by a new retrieval", async () => {
  const { d, w, ctx } = await setup();
  w.claims.push(
    f.claim("old-publication", {
      predicate: "hours",
      sourcePublishedOn: "2020-01-01",
    }),
  );
  const p = project(d, w, ctx);
  assert.equal(p.finding("old-publication").status, "historical");
  assert.ok(p.finding("old-publication").provenance.citations.length);
});
test("B2A qualified hypotheses stay visible; fresh source-backed support is not verified authority", async () => {
  const { d, w, ctx } = await setup();
  w.claims.push(
    f.claim("source", {
      predicate: "occupant_identity",
      value: "Synthetic Operator",
    }),
  );
  w.claims.push(
    f.claim("hypothesis", {
      predicate: "authority.business_ownership",
      value: "owner",
      origin: "ai",
      basis: "inferred",
      derivedFrom: ["source"],
      researchRunId: "run",
      citations: [],
    }),
  );
  const p = project(d, w, ctx, "2026-11-20");
  const h = p.finding("hypothesis");
  assert.equal(h.status, "inferred");
  assert.equal(h.authorityState, "inferred");
  assert.equal(h.provenance.origin, "ai");
  assert.deepEqual(h.dependencyIds, ["source"]);
  assert.equal(p.finding("source").status, "source_supported");
  assert.equal(h.confidenceIsProbability, false);
});
test("B2A contradictions and dependency disputes are retained and selected for verification first", async () => {
  const { d, w, ctx } = await setup();
  verify(w, "open", "operating_status", "Open");
  verify(w, "closed", "operating_status", "Closed");
  w.claims.push(
    f.claim("inferred", {
      predicate: "authority.business_ownership",
      value: "owner",
      basis: "inferred",
      origin: "ai",
      researchRunId: "run",
      derivedFrom: ["open"],
      citations: [],
    }),
  );
  const p = project(d, w, ctx, "2026-11-16");
  assert.equal(p.finding("open").status, "disputed");
  assert.equal(p.finding("closed").status, "disputed");
  assert.equal(p.finding("inferred").status, "disputed");
  assert.ok(p.brief(f.ref("business", "business-a")).verifyFirst.claimId);
  assert.equal(
    p.brief(f.ref("business", "business-a")).eligibility,
    "not_established",
  );
});
test("B2A historical MIMO, unknown policy and future observations remain distinct", async () => {
  const { d, w, ctx } = await setup();
  w.claims.push(f.claim("unknown-type", { predicate: "unclassified_signal" }));
  verify(w, "future", "hours", "9–5");
  w.claims.find((c) => c.id === "future").observedAt =
    "2027-01-01T12:00:00.000Z";
  w.fieldObservations.find((o) => o.id === "observation-future").observedAt =
    "2027-01-01T12:00:00.000Z";
  const p = project(d, w, ctx);
  assert.equal(p.finding("history-device").status, "historical");
  assert.equal(p.finding("unknown-type").status, "unknown");
  assert.equal(p.finding("unknown-type").usefulContext, true);
  assert.equal(p.finding("future").freshness, "future");
  assert.equal(p.finding("future").value, null);
  assert.equal(p.finding("missing"), null);
});
test("B2A projection snapshots and returned findings cannot mutate source or cached results", async () => {
  const { d, w, ctx } = await setup();
  verify(w, "v", "hours", "9–5");
  const p = project(d, w, ctx, "2026-11-16");
  w.claims.find((c) => c.id === "v").value = "modified";
  const out = p.finding("v");
  out.value = "also modified";
  assert.equal(p.finding("v").value, "9–5");
});
test("B2A graph depth, edges, cycles and bytes fail before unbounded recursive validation", async () => {
  const { d, w, ctx } = await setup();
  assert.throws(
    () => d.graphBudget(w, { ...d.DOMAIN_LIMITS, maxBytes: 1 }),
    /byte budget/,
  );
  for (let i = 0; i < 70; i++)
    w.claims.push(
      f.claim("chain-" + i, {
        basis: i ? "inferred" : "reported",
        derivedFrom: i ? ["chain-" + (i - 1)] : [],
      }),
    );
  assert.throws(() => project(d, w, ctx), /depth/);
  const x = f.fixture(d.emptyWorkspace);
  x.claims[0].derivedFrom = [x.claims[1].id];
  x.claims[1].derivedFrom = [x.claims[0].id];
  assert.throws(() => project(d, x, ctx), /cycle/);
});
test("B2A building restriction does not silently suppress a suite: unknown scope holds for review", async () => {
  const { d, w, ctx } = await setup();
  const root = f.ref("building", "building"),
    target = f.ref("suite", "suite-101");
  directive(w, "building-restriction", root);
  let r = d.evaluateScope(
    w,
    { target, relatedCandidates: [root], asOf: f.AT },
    ctx,
  );
  assert.equal(r.suppressed, false);
  assert.equal(r.reviewRequired, true);
  assert.equal(r.hold, true);
  r = d.evaluateScope(
    w,
    {
      target,
      relatedCandidates: [root],
      statements: [statement(w.suppressions[0], "exact")],
      asOf: f.AT,
    },
    ctx,
  );
  assert.equal(r.reviewRequired, false);
  assert.equal(r.suppressed, false);
});
test("B2A explicit manager targets suppress only named suites; scope annotations require manager and source", async () => {
  const { d, w, ctx } = await setup();
  const root = f.ref("building", "building"),
    a = f.ref("suite", "suite-101"),
    b = f.ref("suite", "suite-102");
  const s = directive(w, "building-restriction", root),
    annotation = statement(s, "explicit_targets", [a]);
  assert.equal(
    d.evaluateScope(
      w,
      {
        target: a,
        relatedCandidates: [root],
        statements: [annotation],
        asOf: f.AT,
      },
      ctx,
    ).suppressed,
    true,
  );
  assert.equal(
    d.evaluateScope(
      w,
      {
        target: b,
        relatedCandidates: [root],
        statements: [annotation],
        asOf: f.AT,
      },
      ctx,
    ).suppressed,
    false,
  );
  assert.throws(() =>
    d.evaluateScope(
      w,
      {
        target: a,
        statements: [{ ...annotation, issuedBy: "ai" }],
        asOf: f.AT,
      },
      ctx,
    ),
  );
});
test("B2A all seven target types support exact scope without name/address inheritance", async () => {
  const { d, w, ctx } = await setup();
  const occupancyClaim = verify(w, "occupies", "occupies", "premise-101");
  w.occupancies.push({
    ...f.base("occ"),
    premiseId: "premise-101",
    businessId: "business-a",
    period: { from: null, to: null },
    supportClaimIds: [occupancyClaim.id],
  });
  w.serviceLocations.push({
    ...f.base("service"),
    provider: null,
    reference: null,
    premiseIds: [],
    supportClaimIds: [],
    externalRefs: [],
  });
  for (const [type, id] of [
    ["building", "building"],
    ["suite", "suite-101"],
    ["premise", "premise-101"],
    ["serviceLocation", "service"],
    ["utilityAccount", "account-old"],
    ["business", "business-a"],
    ["occupancy", "occ"],
  ]) {
    const target = f.ref(type, id);
    directive(w, "s-" + type, target);
    assert.equal(
      d.evaluateScope(w, { target, asOf: f.AT }, ctx).suppressed,
      true,
    );
  }
});
test("B2A approval never releases suppression; restrictions persist until an explicit referenced release", async () => {
  const { d, w, ctx } = await setup();
  const target = f.ref("premise", "premise-101");
  directive(w, "restriction", target);
  directive(w, "approval", target, "authorization");
  assert.equal(
    d.evaluateScope(w, { target, asOf: "2027-11-15T12:00:00.000Z" }, ctx)
      .suppressed,
    true,
  );
  w.suppressionReleases.push({
    ...f.base("release"),
    suppressionId: "restriction",
    sourceRowId: "row-old",
    issuedBy: "manager",
    reason: "Explicit release",
    issuedAt: f.AT,
  });
  const result = d.evaluateScope(w, { target, asOf: f.AT }, ctx);
  assert.equal(result.suppressed, false);
  assert.equal(result.authorization, "authorized");
  assert.equal(result.eligibility, "not_established");
});
test("B2A scope conflicts and ambiguous statements hold instead of selecting a convenient restriction", async () => {
  const { d, w, ctx } = await setup();
  const target = f.ref("premise", "premise-101"),
    s = directive(w, "s", target),
    annotation = statement(s, "ambiguous", [target]);
  const result = d.evaluateScope(
    w,
    { target, statements: [annotation], asOf: f.AT },
    ctx,
  );
  assert.equal(result.reviewRequired, true);
  assert.equal(result.hold, true);
  assert.throws(
    () =>
      d.evaluateScope(
        w,
        { target, statements: [annotation, annotation], asOf: f.AT },
        ctx,
      ),
    /Conflicting/,
  );
});
test("B2A preview preserves raw JSON, unknown fields, orphans and unclassified IDs without writable output", async () => {
  const { d, w, ctx } = await setup();
  const input = {
    fieldmind: 1,
    unknownRoot: { kept: true },
    accounts: {
      legacy: {
        name: "Synthetic Shared Name",
        addr: "100 Fictional Plaza",
        acct: "000-01",
        custom: { deep: ["value"] },
        device: "Historical device",
        suppressed: true,
      },
    },
    notes: {
      legacy: {
        evidence: [{ verified: true }],
        brief: { occupant: { name: "AI owner" } },
      },
      orphan: { unknown: "retained" },
    },
    meta: { custom: "kept" },
  };
  const text = JSON.stringify(input, null, 3) + "\n";
  const report = d.previewLegacy(text, { referenceWorkspace: w, context: ctx });
  assert.equal(report.rawText, text);
  assert.deepEqual(report.source, input);
  assert.equal(report.writable, false);
  assert.deepEqual(report.items[0].raw.custom, input.accounts.legacy.custom);
  assert.equal(report.items[0].acceptedIdentity, null);
  assert.equal(report.items[0].proposedDomainRecords.length, 0);
  assert.equal(report.orphanNotes.length, 1);
  assert.ok(
    report.items[0].diagnostics.includes("legacy_verification_unattested"),
  );
});
test("B2A even a single apparent reference match is never automatically accepted; huge groups are bounded", async () => {
  const { d, w, ctx } = await setup();
  w.businesses = w.businesses.slice(0, 1);
  const accounts = Object.fromEntries(
    Array.from({ length: 50 }, (_, i) => [
      "item-" + i,
      { name: "Synthetic Shared Name", addr: "100 Fictional Plaza" },
    ]),
  );
  const report = d.previewLegacy(JSON.stringify({ accounts }), {
    referenceWorkspace: w,
    context: ctx,
  });
  assert.equal(report.items[0].relationships[1].total, 1);
  assert.equal(report.items[0].acceptedIdentity, null);
  assert.equal(report.items[0].relationships[0].ids.length, 20);
  assert.equal(report.items[0].relationships[0].total, 49);
});
test("B2A malformed and prototype-shaped legacy values remain raw and never mutate object prototypes", async () => {
  const { d } = await setup();
  const raw =
    '{"accounts":{"__proto__":{"name":"Synthetic","mystery":1},"bad":null},"notes":{"constructor":{"kept":true}}}';
  const report = d.previewLegacy(raw);
  assert.equal(report.items[0].legacyKey, "__proto__");
  assert.equal(report.items[1].raw, null);
  assert.equal({}.mystery, undefined);
  assert.equal(report.orphanNotes[0].legacyKey, "constructor");
  assert.equal(d.previewLegacy("not json").rawText, "not json");
  assert.throws(
    () =>
      d.previewLegacy(raw, {
        limits: { maxBytes: 1, maxAccounts: 1, maxCandidatesPerItem: 1 },
      }),
    /byte budget/,
  );
});
test("B2A AI-retrieved cited facts remain source-backed information, never verified authority", async () => {
  const { d, w, ctx } = await setup();
  w.claims.push(
    f.claim("ai-retrieved", {
      origin: "ai",
      researchRunId: "run",
      predicate: "authority.business_ownership",
      value: "owner",
    }),
  );
  const finding = project(d, w, ctx, "2026-11-20").finding("ai-retrieved");
  assert.equal(finding.status, "source_supported");
  assert.equal(finding.authorityState, "unknown");
  assert.equal(finding.provenance.origin, "ai");
  assert.deepEqual(finding.supportOrigins, ["public_source"]);
});
test("B2A an inference cannot borrow a low-risk source freshness window for high-risk authority", async () => {
  const { d, w, ctx } = await setup();
  w.claims.push(
    f.claim("property-record", {
      origin: "public_record",
      predicate: "authority.property",
      value: "owner",
    }),
    f.claim("account-inference", {
      origin: "ai",
      researchRunId: "run",
      basis: "inferred",
      predicate: "authority.utility_account",
      value: "owner",
      derivedFrom: ["property-record"],
      citations: [],
    }),
  );
  const p = project(d, w, ctx, "2027-01-15");
  assert.equal(p.finding("property-record").freshness, "current");
  assert.equal(p.finding("account-inference").freshness, "stale");
  assert.equal(p.finding("account-inference").authorityState, "unknown");
  assert.equal(p.finding("account-inference").usefulContext, true);
});
test("B2A a future-published source or later-recorded attestation cannot become available verified knowledge", async () => {
  const { d, w, ctx } = await setup();
  const c = verify(w, "late-review", "hours", "9–5");
  w.fieldObservations.find(
    (o) => o.id === c.verificationObservationId,
  ).createdAt = "2027-01-01T12:00:00.000Z";
  assert.notEqual(
    project(d, w, ctx, "2026-11-20").finding(c.id).status,
    "current_verified",
  );
  w.claims.push(
    f.claim("future-published", {
      predicate: "hours",
      sourcePublishedOn: "2027-01-01",
    }),
  );
  assert.equal(
    project(d, w, ctx, "2026-11-20").finding("future-published").usefulContext,
    false,
  );
});
