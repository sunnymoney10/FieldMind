import { assertWorkspace, validTimestamp } from "./validate.mjs";
import { SUBJECT_TYPES, COLLECTIONS } from "./contracts.mjs";
const scopeTypes = new Set(SUBJECT_TYPES.filter((t) => t !== "party"));
const key = (s) => JSON.stringify([s.type, s.id]);
/** Proposed scope annotations are separate, manager-attested preview inputs, not B1 data migrations. */
export function evaluateScope(
  workspace,
  { target, relatedCandidates = [], statements = [], asOf },
  context,
) {
  assertWorkspace(workspace, context);
  if (!validTimestamp(asOf)) throw new TypeError("Explicit UTC asOf required");
  const exists = (s) =>
    s &&
    scopeTypes.has(s.type) &&
    workspace[COLLECTIONS[s.type]].some((r) => r.id === s.id);
  if (!exists(target) || !relatedCandidates.every(exists))
    throw new TypeError("Unknown/unsupported target scope");
  const directives = [
      ...workspace.prospectAuthorizations.map((d) => ({
        ...d,
        kind: "authorization",
      })),
      ...workspace.suppressions.map((d) => ({ ...d, kind: "suppression" })),
    ],
    byId = new Map(directives.map((d) => [d.id, d])),
    annotations = new Map();
  for (const s of statements) {
    const d = byId.get(s.directiveId),
      actor = Object.hasOwn(context?.actors || {}, s.issuedBy)
        ? context.actors[s.issuedBy]
        : null;
    if (
      typeof s.id !== "string" ||
      !s.id.trim() ||
      !d ||
      !actor ||
      actor.workspaceId !== workspace.workspaceId ||
      !actor.roles.includes("manager") ||
      s.workspaceId !== workspace.workspaceId ||
      !["exact", "explicit_targets", "ambiguous"].includes(s.mode) ||
      !Array.isArray(s.targets) ||
      !s.targets.every(exists) ||
      !s.sourceRowId ||
      !workspace.sourceRows.some((r) => r.id === s.sourceRowId) ||
      !s.reason?.trim() ||
      !validTimestamp(s.issuedAt) ||
      Date.parse(s.issuedAt) < Date.parse(d.issuedAt) ||
      (s.mode === "exact" && s.targets.length)
    )
      throw new TypeError(
        "Scope statement needs manager, source, valid targets, reason and chronology",
      );
    if (Date.parse(s.issuedAt) > Date.parse(asOf)) continue;
    const prior = annotations.get(s.directiveId);
    if (prior)
      throw new TypeError(
        "Conflicting scope statements require review, not implicit last-writer wins",
      );
    annotations.set(s.directiveId, s);
  }
  const applied = [],
    held = [],
    irrelevant = [];
  for (const d of directives) {
    if (Date.parse(d.issuedAt) > Date.parse(asOf)) continue;
    if (
      d.kind === "suppression" &&
      workspace.suppressionReleases.some(
        (r) =>
          r.suppressionId === d.id &&
          Date.parse(r.issuedAt) <= Date.parse(asOf),
      )
    )
      continue;
    const annotation = annotations.get(d.id),
      direct = key(d.subject) === key(target),
      explicit = annotation?.targets.some((s) => key(s) === key(target)),
      related = relatedCandidates.some((s) => key(s) === key(d.subject));
    if (annotation?.mode === "ambiguous" && (direct || explicit || related))
      held.push({
        id: d.id,
        kind: d.kind,
        reason: "Manager/source scope unresolved",
      });
    else if (direct || (annotation?.mode === "explicit_targets" && explicit))
      applied.push(d);
    else if (related && !annotation)
      held.push({
        id: d.id,
        kind: d.kind,
        reason:
          "Related location/entity is a review candidate, not inherited scope",
      });
    else irrelevant.push(d.id);
  }
  const authorizations = applied
    .filter((d) => d.kind === "authorization")
    .sort((a, b) => Date.parse(b.issuedAt) - Date.parse(a.issuedAt));
  // Latest per scoped root; withdrawal or equal-time disagreement never becomes approval.
  const groups = new Map();
  for (const d of authorizations) {
    const k = key(d.subject),
      g = groups.get(k);
    if (!g) groups.set(k, [d]);
    else if (Date.parse(g[0].issuedAt) === Date.parse(d.issuedAt)) g.push(d);
  }
  const decisions = [...groups.values()].map((g) =>
    new Set(g.map((d) => d.decision)).size > 1 ? "disputed" : g[0].decision,
  );
  const authorization = decisions.includes("disputed")
      ? "disputed"
      : decisions.includes("withdrawn")
        ? "withdrawn"
        : decisions.includes("authorized")
          ? "authorized"
          : "unknown",
    suppressed = applied.some((d) => d.kind === "suppression");
  return {
    target: structuredClone(target),
    authorization,
    suppressed,
    reviewRequired: held.length > 0,
    hold: suppressed || held.length > 0 || authorization !== "authorized",
    eligibility: "not_established",
    appliedIds: applied.map((d) => d.id),
    held,
    irrelevantIds: irrelevant,
    scopeStatementIds: [...annotations.values()].map((s) => s.id),
    policyVersion: "b2a-scope-proposed-1",
  };
}
