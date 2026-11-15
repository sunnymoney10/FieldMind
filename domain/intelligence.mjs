import { assertWorkspace, validDate } from "./validate.mjs";
import { graphBudget } from "./limits.mjs";
// Proposed policy, not a live product setting. Days are maximum ages, not guarantees of truth.
const deepFreeze = (o) => {
  for (const v of Object.values(o))
    if (v && typeof v === "object") deepFreeze(v);
  return Object.freeze(o);
};
export const FRESHNESS_POLICY = deepFreeze({
  version: "b2a-proposed-1",
  rules: Object.freeze({
    operating_status: {
      field: 14,
      public_record: 30,
      public_source: 7,
      manager_list: 7,
    },
    occupant_identity: {
      field: 30,
      public_record: 90,
      public_source: 14,
      manager_list: 14,
    },
    hours: { field: 30, public_record: 14, public_source: 14, manager_list: 7 },
    "authority.business_ownership": {
      field: 90,
      public_record: 180,
      public_source: 30,
      manager_list: 14,
    },
    "authority.business_operations": {
      field: 30,
      public_record: 60,
      public_source: 14,
      manager_list: 7,
    },
    "authority.utility_account": {
      field: 30,
      public_record: 30,
      public_source: 7,
      manager_list: 7,
    },
    "authority.property": {
      field: 180,
      public_record: 365,
      public_source: 30,
      manager_list: 14,
    },
    "authority.hvac_facilities": {
      field: 60,
      public_record: 180,
      public_source: 14,
      manager_list: 7,
    },
    hvac_context: {
      field: 180,
      public_record: 365,
      public_source: 90,
      manager_list: 30,
    },
    energy_experience: {
      field: 90,
      public_record: 180,
      public_source: 30,
      manager_list: 14,
    },
  }),
});
const key = (s) => JSON.stringify([s.type, s.id]);
/** One validated immutable snapshot -> indexed findings. Not imported by the live app. */
export function createIntelligenceProjection(
  workspace,
  { asOf, policy = FRESHNESS_POLICY },
  context,
) {
  policy = structuredClone(policy);
  if (
    !policy ||
    typeof policy.version !== "string" ||
    !policy.rules ||
    Object.values(policy.rules).some(
      (rule) =>
        !rule ||
        typeof rule !== "object" ||
        Object.values(rule).some(
          (days) => !Number.isSafeInteger(days) || days < 0 || days > 3650,
        ),
    )
  )
    throw new TypeError("Invalid freshness policy");
  if (!validDate(asOf))
    throw new TypeError("Explicit valid asOf date required");
  const budget = graphBudget(workspace);
  assertWorkspace(workspace, context);
  const w = structuredClone(workspace),
    claims = new Map(w.claims.map((c) => [c.id, c])),
    observations = new Map(w.fieldObservations.map((o) => [o.id, o])),
    rows = new Map(w.sourceRows.map((r) => [r.id, r])),
    batches = new Map(w.importBatches.map((b) => [b.id, b])),
    states = new Map(),
    conflicts = new Map(),
    bySubject = new Map();
  for (const c of w.claims) {
    if (!bySubject.has(key(c.subject))) bySubject.set(key(c.subject), []);
    bySubject.get(key(c.subject)).push(c.id);
    for (const id of c.conflictsWith) {
      if (!conflicts.has(c.id)) conflicts.set(c.id, new Set());
      if (!conflicts.has(id)) conflicts.set(id, new Set());
      conflicts.get(c.id).add(id);
      conflicts.get(id).add(c.id);
    }
  }
  for (const id of budget.order) {
    const c = claims.get(id),
      parents = c.derivedFrom.map((p) => states.get(p));
    const citations = c.citations.filter(
        (s) =>
          s.retrievedAt.slice(0, 10) <= asOf &&
          (!s.publishedOn || s.publishedOn <= asOf),
      ),
      sourceRows = c.sourceRowIds.filter(
        (id) =>
          batches.get(rows.get(id)?.batchId)?.createdAt.slice(0, 10) <= asOf,
      ),
      obs = c.fieldObservationIds
        .map((id) => observations.get(id))
        .filter(
          (o) =>
            o.observedAt.slice(0, 10) <= asOf &&
            o.createdAt.slice(0, 10) <= asOf,
        );
    const known =
      c.createdAt.slice(0, 10) <= asOf &&
      c.observedAt.slice(0, 10) <= asOf &&
      (!c.sourcePublishedOn || c.sourcePublishedOn <= asOf);
    const directSupport = !!(
        citations.length ||
        sourceRows.length ||
        obs.length
      ),
      dependencyContext =
        parents.length > 0 && parents.every((p) => p.usefulContext);
    const usefulContext = known && (directSupport || dependencyContext);
    const reasons = [];
    let origin =
      c.origin === "ai" && c.basis !== "inferred" && citations.length
        ? "public_source"
        : c.origin;
    const supportOrigins =
      c.basis === "inferred"
        ? [...new Set(parents.flatMap((p) => p.supportOrigins))]
        : [origin];
    // AI has no intrinsic freshness. Inference inherits the earliest expiry of its support.
    const rule = policy.rules[c.predicate];
    let maxDays = rule?.[origin] ?? null;
    if (c.basis === "inferred" && parents.length) {
      const caps = supportOrigins.map((source) => rule?.[source]);
      maxDays =
        caps.length && caps.every((x) => Number.isSafeInteger(x))
          ? Math.min(...caps)
          : null;
    }
    const isVerified =
      c.review === "verified" &&
      obs.some((o) => o.id === c.verificationObservationId);
    const observationDays = obs.filter((o) => o.kind === "staff_statement")
      .length
      ? 7
      : null;
    if (maxDays !== null && observationDays !== null)
      maxDays = Math.min(maxDays, observationDays);
    // Old published records do not become current merely because they were retrieved today.
    const dates = [
      c.observedAt.slice(0, 10),
      c.sourcePublishedOn,
      ...citations.map((s) => s.publishedOn),
      ...(c.basis === "inferred" ? parents.map((p) => p.supportAnchor) : []),
    ].filter(Boolean);
    const anchor = dates.sort()[0];
    let expiresOn =
      maxDays === null
        ? null
        : new Date(Date.parse(anchor) + maxDays * 86400000)
            .toISOString()
            .slice(0, 10);
    const periodCurrent =
      c.temporal === "as_of" &&
      c.period.from &&
      c.period.from <= asOf &&
      (!c.period.to || c.period.to >= asOf);
    let freshness = !known
      ? "future"
      : c.temporal === "historical" || (c.period.to && c.period.to < asOf)
        ? "historical"
        : !periodCurrent
          ? "unknown"
          : expiresOn === null
            ? "unknown"
            : asOf <= expiresOn
              ? "current"
              : "stale";
    if (c.basis === "inferred" && parents.length) {
      const expiries = [expiresOn, ...parents.map((p) => p.expiresOn)]
        .filter(Boolean)
        .sort();
      expiresOn = maxDays === null ? null : expiries[0] || null;
    }
    if (c.basis === "inferred" && parents.length && periodCurrent && known)
      freshness =
        expiresOn === null
          ? "unknown"
          : parents.every((p) => p.freshness === "current") && asOf <= expiresOn
            ? "current"
            : parents.some((p) => p.freshness === "future")
              ? "unknown"
              : "stale";
    let status = "unknown";
    const opposed = [...(conflicts.get(id) || [])].filter(
      (other) =>
        claims.get(other)?.observedAt.slice(0, 10) <= asOf &&
        claims.get(other)?.createdAt.slice(0, 10) <= asOf,
    );
    if (!known) {
      status = "unknown";
      reasons.push("Not available as of requested date");
    } else if (
      c.review === "disputed" ||
      opposed.length ||
      parents.some((p) => p.status === "disputed")
    ) {
      status = "disputed";
      reasons.push("Unresolved contradiction or disputed dependency");
    } else if (c.review === "superseded") {
      status = "historical";
      reasons.push("Superseded; retained as context");
    } else if (
      freshness === "current" &&
      usefulContext &&
      parents.every(
        (p) =>
          p.freshness === "current" &&
          p.status !== "unknown" &&
          p.status !== "historical",
      )
    )
      status =
        c.basis === "inferred"
          ? "inferred"
          : isVerified
            ? "current_verified"
            : "source_supported";
    else if (usefulContext && ["historical", "stale"].includes(freshness)) {
      status = "historical";
      reasons.push(
        freshness === "stale"
          ? "Too old to establish a current fact; useful context retained"
          : "Historical context; not evidence of present conditions",
      );
    } else
      reasons.push(
        !known
          ? "Not available as of requested date"
          : !rule && c.basis !== "inferred"
            ? "No approved freshness rule for this claim type"
            : "Current fact not established",
      );
    if (c.basis === "inferred")
      reasons.push("Qualified hypothesis; inspect supporting claims");
    const authority = c.predicate.startsWith("authority.");
    const authorityState = !authority
      ? "not_applicable"
      : status === "disputed"
        ? "disputed"
        : status === "current_verified"
          ? "verified"
          : status === "inferred"
            ? "inferred"
            : "unknown";
    states.set(id, {
      claimId: id,
      subject: c.subject,
      predicate: c.predicate,
      value: known ? c.value : null,
      status,
      freshness,
      usefulContext,
      epistemic:
        c.basis === "inferred"
          ? "inference"
          : isVerified
            ? "representative_verified"
            : "source_reported",
      authorityState,
      supportGrade:
        status === "current_verified"
          ? "confirmed"
          : status === "source_supported"
            ? "documented"
            : status === "inferred"
              ? "reasoned"
              : "unresolved",
      confidenceIsProbability: false,
      supportOrigins,
      supportAnchor: anchor,
      observedAt: c.observedAt,
      effectivePeriod: c.period,
      expiresOn,
      policyVersion: policy.version,
      dependencyIds: [...c.derivedFrom],
      conflictIds: opposed,
      reasons,
      provenance: {
        origin: c.origin,
        citations,
        sourceRowIds: sourceRows,
        fieldObservationIds: obs.map((o) => o.id),
        researchRunId: c.researchRunId,
      },
    });
  }
  // Detect competing current single-valued facts without inventing a winner.
  const singleValued = new Set([
    "operating_status",
    "occupant_identity",
    "hours",
  ]);
  const alternatives = new Map();
  for (const f of states.values())
    if (
      (singleValued.has(f.predicate) || f.predicate.startsWith("authority.")) &&
      ["current_verified", "source_supported", "inferred"].includes(f.status)
    ) {
      const k = key(f.subject) + "|" + f.predicate;
      if (!alternatives.has(k)) alternatives.set(k, []);
      alternatives.get(k).push(f);
    }
  for (const group of alternatives.values())
    if (new Set(group.map((f) => f.value)).size > 1) {
      const candidateIds = group.slice(0, 21).map((f) => f.claimId);
      for (const f of group) {
        f.status = "disputed";
        f.authorityState = f.predicate.startsWith("authority.")
          ? "disputed"
          : "not_applicable";
        f.conflictIds = [
          ...new Set([
            ...f.conflictIds,
            ...candidateIds.filter((id) => id !== f.claimId).slice(0, 20),
          ]),
        ];
        f.conflictAlternativeCount = group.length - 1;
        f.reasons.push("Competing current values require review");
        f.supportGrade = "unresolved";
      }
    }
  for (const id of budget.order) {
    const f = states.get(id);
    if (f.dependencyIds.some((id) => states.get(id).status === "disputed")) {
      f.status = "disputed";
      f.authorityState = f.predicate.startsWith("authority.")
        ? "disputed"
        : "not_applicable";
      f.supportGrade = "unresolved";
      f.reasons.push("Supporting claim is disputed");
    }
  }
  function finding(id) {
    return states.has(id) ? structuredClone(states.get(id)) : null;
  }
  function forSubject(subject) {
    return (bySubject.get(key(subject)) || []).map(finding);
  }
  function brief(subject) {
    const findings = forSubject(subject),
      disputes = findings.filter((f) => f.status === "disputed"),
      unknownAuthority = findings.filter((f) => f.authorityState === "unknown");
    const first =
      disputes[0] ||
      unknownAuthority[0] ||
      findings.find((f) => f.freshness !== "current") ||
      findings.find((f) => f.status === "inferred");
    return {
      subject: structuredClone(subject),
      findings,
      verifyFirst: first
        ? {
            claimId: first.claimId,
            reason:
              first.reasons[0] ||
              "Confirm scoped authority before relying on it",
          }
        : {
            claimId: null,
            reason:
              "Confirm current occupant and utility-account authority; these are not established by absence of findings",
          },
      priorityRecommendation: "human_review",
      eligibility: "not_established",
      policyVersion: policy.version,
    };
  }
  return {
    finding,
    forSubject,
    brief,
    all: () => [...states.keys()].map(finding),
    stats: () => ({
      ...budget,
      order: undefined,
      policyVersion: policy.version,
    }),
  };
}
