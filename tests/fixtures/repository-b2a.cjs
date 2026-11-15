const f = require("./domain-b1.cjs");
async function setup(faultPhase = null) {
  const { createRepositoryProof } = await import("../../proof/repository.mjs");
  const { emptyWorkspace } = await import("../../domain/contracts.mjs");
  const roles = new Map([
    ["rep|synthetic-workspace", ["representative"]],
    ["manager|synthetic-workspace", ["manager"]],
    ["ai|synthetic-workspace", ["researcher"]],
    ["other|other-workspace", ["representative"]],
  ]);
  const tokens = new Map(
    ["rep", "manager", "ai", "other"].map((subject) => [
      subject + "-token",
      { subject, expiresAt: "2026-11-16T00:00:00.000Z" },
    ]),
  );
  tokens.set("expired-token", {
    subject: "rep",
    expiresAt: "2026-11-14T00:00:00.000Z",
  });
  const faults = { phase: faultPhase };
  const repo = createRepositoryProof({
    verifyCredential: (t) => tokens.get(t),
    currentRoles: (id, w) => roles.get(id + "|" + w),
    actorRegistry: (w) =>
      Object.fromEntries(
        Object.entries(f.context.actors).map(([id, a]) => [
          id,
          { ...a, workspaceId: w },
        ]),
      ),
    now: () => Date.parse(f.AT),
    fault: (phase) => {
      if (faults.phase === phase) {
        faults.phase = null;
        throw new Error("Synthetic fault; must not leak internal details");
      }
    },
  });
  const workspace = f.fixture(emptyWorkspace);
  repo.testOnly.seed(workspace);
  const other = structuredClone(workspace);
  other.workspaceId = "other-workspace";
  for (const records of Object.values(other))
    if (Array.isArray(records))
      for (const r of records) r.workspaceId = other.workspaceId;
  repo.testOnly.seed(other);
  const request = (additions = {}, overrides = {}) => ({
    credential: "rep-token",
    workspaceId: "synthetic-workspace",
    expectedRevision: 0,
    commandId: "synthetic-command",
    additions,
    ...overrides,
  });
  const observation = () => ({
    ...f.base("new-observation"),
    observerId: "rep",
    subject: f.ref("business", "business-a"),
    predicate: "hours",
    value: "9–5",
    kind: "direct_observation",
    note: "Synthetic observed hours",
    observedAt: f.AT,
  });
  return { repo, roles, tokens, faults, request, observation, workspace };
}
module.exports = { setup };
