import { CONTRACTS, COLLECTIONS, AUTHORITY_KINDS } from "./contracts.mjs";
import { assertWorkspace, validDate, validTimestamp } from "./validate.mjs";
const same = (a, b) => a.type === b.type && a.id === b.id;
const canonical = (v) =>
  Array.isArray(v)
    ? "[" + v.map(canonical).join(",") + "]"
    : v && typeof v === "object"
      ? "{" +
        Object.keys(v)
          .sort()
          .map((k) => JSON.stringify(k) + ":" + canonical(v[k]))
          .join(",") +
        "}"
      : JSON.stringify(v);
/** All-or-nothing append in memory. No delete, update, merge, identity resolution or persistence. */
export function appendRecords(workspace, additions, context) {
  assertWorkspace(workspace, context);
  const registeredCaller =
    context?.actors && Object.hasOwn(context.actors, context.actorId)
      ? context.actors[context.actorId]
      : null;
  const caller = registeredCaller && {
    ...registeredCaller,
    roles: context.callerRoles ?? registeredCaller.roles,
  };
  if (
    !caller ||
    !Array.isArray(caller.roles) ||
    caller.workspaceId !== workspace.workspaceId
  )
    throw new Error("Trusted calling actor required");
  if (!additions || typeof additions !== "object" || Array.isArray(additions))
    throw new TypeError("Expected collection additions");
  const next = structuredClone(workspace),
    existing = new Map(
      Object.keys(CONTRACTS).flatMap((k) =>
        next[k].map((r) => [r.id, { collection: k, record: r }]),
      ),
    );
  const added = [],
    replayed = [];
  for (const [collection, records] of Object.entries(additions)) {
    if (!Object.hasOwn(CONTRACTS, collection) || !Array.isArray(records))
      throw new TypeError("Unknown collection or non-array additions");
    for (const record of records) {
      const prev = existing.get(record?.id);
      if (prev) {
        if (
          prev.collection !== collection ||
          canonical(prev.record) !== canonical(record)
        )
          throw new Error(
            "Identity conflict; existing record retained: " + record?.id,
          );
        replayed.push(record.id);
        continue;
      }
      const managerCollections = [
        "prospectAuthorizations",
        "suppressions",
        "suppressionReleases",
      ];
      if (
        managerCollections.includes(collection) &&
        (!caller.roles.includes("manager") ||
          record.issuedBy !== context.actorId)
      )
        throw new Error("Only the issuing manager can append directives");
      if (
        collection === "fieldObservations" &&
        (!caller.roles.includes("representative") ||
          record.observerId !== context.actorId)
      )
        throw new Error(
          "Only the observing representative can append observations",
        );
      if (
        collection === "importBatches" &&
        record.importedBy !== context.actorId
      )
        throw new Error("Import actor must match caller");
      if (
        !caller.roles.some((r) => r === "manager" || r === "representative")
      ) {
        if (
          !caller.roles.includes("researcher") ||
          !["researchRuns", "claims"].includes(collection) ||
          (collection === "claims" &&
            (record.origin !== "ai" || record.review !== "unreviewed"))
        )
          throw new Error(
            "Research can append unreviewed AI claims and runs only",
          );
      }
      const copy = structuredClone(record);
      next[collection].push(copy);
      existing.set(copy.id, { collection, record: copy });
      added.push(copy.id);
    }
  }
  const validation = assertWorkspace(next, context);
  return { workspace: next, added, replayed, warnings: validation.warnings };
}
/** Normalized names/addresses produce review candidates, never accepted matches. */
export function identityCandidates(
  workspace,
  { type, addressRaw, name, externalReference },
  context,
) {
  assertWorkspace(workspace, context);
  if (!Object.hasOwn(COLLECTIONS, type))
    throw new TypeError("Unknown entity type");
  const normalize = (s) =>
    typeof s === "string"
      ? s
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, " ")
          .trim()
      : "";
  const candidates = [];
  for (const r of workspace[COLLECTIONS[type]]) {
    const reasons = [];
    if (
      normalize(addressRaw) &&
      normalize(r.addressRaw) === normalize(addressRaw)
    )
      reasons.push("same_address");
    if (
      normalize(name) &&
      [r.name, ...(r.aliases || [])].some(
        (v) => normalize(v) === normalize(name),
      )
    )
      reasons.push("same_name");
    if (
      externalReference &&
      (r.externalRefs || []).some(
        (x) =>
          x.issuer === externalReference.issuer &&
          x.kind === externalReference.kind &&
          x.value === externalReference.value,
      )
    )
      reasons.push("same_external_reference");
    if (reasons.length) candidates.push({ id: r.id, reasons });
  }
  return {
    status: candidates.length ? "review_required" : "unresolved",
    candidates,
    acceptedId: null,
  };
}
function claimEvaluator(w, { asOf, maxAgeDays = 0 }) {
  if (!validDate(asOf) || !Number.isSafeInteger(maxAgeDays) || maxAgeDays < 0)
    throw new TypeError("Valid asOf date and nonnegative maxAgeDays required");
  const claims = new Map(w.claims.map((c) => [c.id, c]));
  const conflicts = new Set(
    w.claims.flatMap((c) => c.conflictsWith.flatMap((id) => [c.id, id])),
  );
  const cache = new Map();
  function evaluate(id) {
    if (cache.has(id)) return cache.get(id);
    const c = claims.get(id);
    if (!c) return "unknown";
    if (c.review === "disputed" || conflicts.has(id)) return "disputed";
    if (
      c.review === "superseded" ||
      c.temporal !== "as_of" ||
      !c.period.from ||
      c.period.from > asOf ||
      (c.period.to && c.period.to < asOf) ||
      c.observedAt.slice(0, 10) > asOf
    )
      return "unknown";
    const age =
      (Date.parse(asOf) - Date.parse(c.observedAt.slice(0, 10))) / 86400000;
    if (age > maxAgeDays) return "unknown";
    if (
      c.verificationObservationId &&
      w.fieldObservations
        .find((o) => o.id === c.verificationObservationId)
        ?.observedAt.slice(0, 10) > asOf
    )
      return "unknown";
    // Workspace validation rejects cycles before evaluation.
    const parents = c.derivedFrom.map(evaluate);
    const state = parents.includes("disputed")
      ? "disputed"
      : parents.includes("unknown")
        ? "unknown"
        : c.review === "verified"
          ? "verified"
          : c.basis === "inferred" && parents.length
            ? "inferred"
            : "unknown";
    cache.set(id, state);
    return state;
  }
  return evaluate;
}
export function claimState(workspace, claimId, options, context) {
  assertWorkspace(workspace, context);
  return claimEvaluator(workspace, options)(claimId);
}
/** Each authority is resolved independently. No ownership -> utility/HVAC authority inference. */
export function authorityFor(
  workspace,
  { kind, subject, asOf, maxAgeDays = 0 },
  context,
) {
  assertWorkspace(workspace, context);
  if (
    !AUTHORITY_KINDS.includes(kind) ||
    !subject ||
    !Object.hasOwn(COLLECTIONS, subject.type) ||
    !workspace[COLLECTIONS[subject.type]].some((r) => r.id === subject.id)
  )
    throw new TypeError("Known authority kind and subject required");
  const evaluate = claimEvaluator(workspace, { asOf, maxAgeDays });
  const assertions = workspace.authorityAssertions.filter(
    (a) => a.kind === kind && same(a.subject, subject),
  );
  const evidence = assertions.map((a) => ({
    id: a.id,
    holder: a.holder,
    claimIds: [...a.claimIds],
    states: a.claimIds.map(evaluate),
  }));
  const supported = evidence.filter(
    (e) =>
      e.holder && e.states.some((s) => s === "verified" || s === "inferred"),
  );
  const disputed =
    evidence.some((e) => e.states.includes("disputed")) ||
    new Set(supported.map((e) => canonical(e.holder))).size > 1;
  if (disputed) return { state: "disputed", holder: null, evidence };
  if (!supported.length) return { state: "unknown", holder: null, evidence };
  return {
    state: supported.some((e) => e.states.includes("verified"))
      ? "verified"
      : "inferred",
    holder: structuredClone(supported[0].holder),
    evidence,
  };
}
/** Explicit scopes supplied by caller; membership is visible but NEVER authorization/eligibility. */
export function prospectDecision(workspace, subjects, asOf, context) {
  assertWorkspace(workspace, context);
  if (!validTimestamp(asOf) || !Array.isArray(subjects) || !subjects.length)
    throw new TypeError(
      "Explicit subject scopes and UTC asOf timestamp required",
    );
  for (const s of subjects)
    if (
      !Object.hasOwn(COLLECTIONS, s.type) ||
      !workspace[COLLECTIONS[s.type]].some((r) => r.id === s.id)
    )
      throw new TypeError("Unknown subject scope");
  const applies = (r) => subjects.some((s) => same(s, r.subject));
  const directives = workspace.prospectAuthorizations.filter(
    (r) => applies(r) && Date.parse(r.issuedAt) <= Date.parse(asOf),
  );
  const bySubject = new Map();
  for (const d of directives) {
    const key = canonical(d.subject),
      prior = bySubject.get(key);
    if (!prior || Date.parse(d.issuedAt) > Date.parse(prior.issuedAt))
      bySubject.set(key, d);
    else if (
      Date.parse(d.issuedAt) === Date.parse(prior.issuedAt) &&
      d.decision !== prior.decision
    )
      bySubject.set(key, { ...d, decision: "conflicting" });
  }
  const current = [...bySubject.values()];
  const authorization = current.some((x) => x.decision === "conflicting")
    ? "disputed"
    : current.some((x) => x.decision === "withdrawn")
      ? "withdrawn"
      : current.some((x) => x.decision === "authorized")
        ? "authorized"
        : "unknown";
  const suppressions = workspace.suppressions.filter(
    (r) => applies(r) && Date.parse(r.issuedAt) <= Date.parse(asOf),
  );
  const releases = workspace.suppressionReleases.filter(
    (r) => Date.parse(r.issuedAt) <= Date.parse(asOf),
  );
  const active = suppressions.filter(
    (s) => !releases.some((r) => r.suppressionId === s.id),
  );
  return {
    authorization,
    suppressed: active.length > 0,
    mayResearch: authorization === "authorized" && !active.length,
    eligibility: "not_established",
    scopes: structuredClone(subjects),
    authorizationIds: directives.map((d) => d.id),
    suppressionIds: suppressions.map((s) => s.id),
    activeSuppressionIds: active.map((s) => s.id),
    releaseIds: releases
      .filter((r) => suppressions.some((s) => s.id === r.suppressionId))
      .map((r) => r.id),
    memberships: structuredClone(workspace.listMemberships.filter(applies)),
  };
}
/** Retains all historical account facts, never interprets history as a present device inventory. */
export function mimoHistory(workspace, accountId, context) {
  assertWorkspace(workspace, context);
  if (!workspace.utilityAccounts.some((a) => a.id === accountId))
    throw new TypeError("Unknown utility account");
  return {
    accountId,
    claims: structuredClone(
      workspace.claims.filter(
        (c) =>
          c.subject.type === "utilityAccount" &&
          c.subject.id === accountId &&
          ["historical_participation", "historical_equipment"].includes(
            c.predicate,
          ),
      ),
    ),
    currentEquipment: "unknown",
    currentEligibility: "not_established",
    accountSequence: "not_inferred",
  };
}
