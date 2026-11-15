const { test } = require("node:test");
const assert = require("node:assert/strict");
const { setup } = require("./fixtures/repository-b2a.cjs");
const f = require("./fixtures/domain-b1.cjs");
const code = (name) => (e) => e.code === name;
test("B2A repository rejects forged/expired credentials and request-provided roles or actor context", async () => {
  const { repo, request } = await setup();
  try {
    for (const credential of [
      "bad",
      "expired-token",
      { subject: "manager", roles: ["manager"] },
    ])
      assert.throws(
        () => repo.read({ credential, workspaceId: "synthetic-workspace" }),
        code("unauthenticated"),
      );
    assert.throws(
      () => repo.commit({ ...request(), roles: ["manager"] }),
      code("invalid_request"),
    );
    assert.throws(
      () => repo.commit({ ...request(), actorContext: f.context }),
      code("invalid_request"),
    );
  } finally {
    repo.close();
  }
});
test("B2A repository enforces workspace isolation for read, write, record payloads and guessed IDs", async () => {
  const { repo, request, observation } = await setup();
  try {
    assert.throws(
      () =>
        repo.read({ credential: "rep-token", workspaceId: "other-workspace" }),
      code("forbidden"),
    );
    assert.throws(
      () => repo.commit(request({}, { workspaceId: "other-workspace" })),
      code("forbidden"),
    );
    assert.throws(
      () =>
        repo.commit(
          request({
            fieldObservations: [
              { ...observation(), workspaceId: "other-workspace" },
            ],
          }),
        ),
      code("forbidden"),
    );
    assert.equal(
      repo.read({ credential: "other-token", workspaceId: "other-workspace" })
        .revision,
      0,
    );
  } finally {
    repo.close();
  }
});
test("B2A researcher has no full-workspace read and cannot issue manager or representative records", async () => {
  const { repo, request, observation } = await setup();
  try {
    assert.throws(
      () =>
        repo.read({
          credential: "ai-token",
          workspaceId: "synthetic-workspace",
        }),
      code("forbidden"),
    );
    assert.throws(
      () =>
        repo.commit(
          request(
            { fieldObservations: [observation()] },
            { credential: "ai-token" },
          ),
        ),
      code("forbidden"),
    );
    assert.throws(
      () =>
        repo.commit(
          request(
            {
              suppressions: [
                {
                  ...f.base("s"),
                  subject: f.ref("premise", "premise-101"),
                  issuedBy: "manager",
                  sourceRowId: "row-old",
                  reason: "Spoof",
                  issuedAt: f.AT,
                },
              ],
            },
            { credential: "ai-token" },
          ),
        ),
      code("forbidden"),
    );
    const c = f.claim("ai-claim", { origin: "ai", researchRunId: "run" });
    assert.equal(
      repo.commit(request({ claims: [c] }, { credential: "ai-token" }))
        .revision,
      1,
    );
  } finally {
    repo.close();
  }
});
test("B2A read returns a detached snapshot and failed validation cannot partially change storage", async () => {
  const { repo, request, observation } = await setup();
  try {
    const read = repo.read({
      credential: "rep-token",
      workspaceId: "synthetic-workspace",
    });
    read.workspace.businesses[0].name = "Mutated client copy";
    assert.notEqual(
      repo.read({ credential: "rep-token", workspaceId: "synthetic-workspace" })
        .workspace.businesses[0].name,
      read.workspace.businesses[0].name,
    );
    assert.throws(
      () =>
        repo.commit(
          request({
            fieldObservations: [
              observation(),
              {
                ...observation(),
                id: "invalid",
                subject: f.ref("premise", "missing"),
              },
            ],
          }),
        ),
      code("validation_failed"),
    );
    assert.equal(
      repo.read({ credential: "rep-token", workspaceId: "synthetic-workspace" })
        .revision,
      0,
    );
    assert.equal(
      repo.testOnly.inspect("synthetic-workspace").commands.length,
      0,
    );
  } finally {
    repo.close();
  }
});
test("B2A two stale clients cannot silently overwrite; conflict preserves the rejected draft", async () => {
  const { repo, request, observation } = await setup();
  try {
    const a = repo.read({
        credential: "rep-token",
        workspaceId: "synthetic-workspace",
      }),
      b = repo.read({
        credential: "rep-token",
        workspaceId: "synthetic-workspace",
      });
    assert.equal(a.revision, b.revision);
    repo.commit(request({ fieldObservations: [observation()] }));
    const draft = request(
      { fieldObservations: [{ ...observation(), id: "second" }] },
      { commandId: "second-command", expectedRevision: b.revision },
    );
    const copy = JSON.stringify(draft);
    assert.throws(() => repo.commit(draft), code("revision_conflict"));
    assert.equal(JSON.stringify(draft), copy);
    assert.equal(
      repo.read({ credential: "rep-token", workspaceId: "synthetic-workspace" })
        .workspace.fieldObservations.length,
      1,
    );
  } finally {
    repo.close();
  }
});
for (const phase of ["after_entities", "after_revision", "before_commit"])
  test("B2A rollback/recovery at " + phase, async () => {
    const { repo, request, observation } = await setup(phase);
    try {
      const command = request({ fieldObservations: [observation()] });
      assert.throws(() => repo.commit(command), code("write_failed"));
      const state = repo.read({
        credential: "rep-token",
        workspaceId: "synthetic-workspace",
      });
      assert.equal(state.revision, 0);
      assert.equal(state.workspace.fieldObservations.length, 0);
      assert.equal(
        repo.testOnly.inspect("synthetic-workspace").commands.length,
        0,
      );
      assert.equal(
        repo.testOnly.inspect("synthetic-workspace").audit.length,
        0,
      );
      assert.equal(repo.commit(command).revision, 1);
      assert.equal(
        repo.testOnly.inspect("synthetic-workspace").foreignKeyFailures.length,
        0,
      );
    } finally {
      repo.close();
    }
  });
test("B2A lost commit acknowledgement returns unknown outcome; exact retry recovers without duplicating", async () => {
  const { repo, request, observation } = await setup("after_commit");
  try {
    const command = request({ fieldObservations: [observation()] });
    assert.throws(() => repo.commit(command), code("outcome_unknown"));
    assert.equal(
      repo.read({ credential: "rep-token", workspaceId: "synthetic-workspace" })
        .revision,
      1,
    );
    const retry = repo.commit(command);
    assert.equal(retry.replayed, true);
    assert.equal(retry.revision, 1);
    assert.equal(repo.testOnly.inspect("synthetic-workspace").audit.length, 1);
    assert.equal(
      repo.read({ credential: "rep-token", workspaceId: "synthetic-workspace" })
        .workspace.fieldObservations.length,
      1,
    );
  } finally {
    repo.close();
  }
});
test("B2A command identity rejects changed payload or replay by another actor", async () => {
  const { repo, request, observation } = await setup();
  try {
    repo.commit(request({ fieldObservations: [observation()] }));
    assert.throws(
      () =>
        repo.commit(
          request({
            fieldObservations: [{ ...observation(), value: "Different" }],
          }),
        ),
      code("command_conflict"),
    );
    assert.throws(
      () =>
        repo.commit(
          request(
            { fieldObservations: [observation()] },
            { credential: "manager-token" },
          ),
        ),
      code("forbidden"),
    );
  } finally {
    repo.close();
  }
});
test("B2A revoked/downgraded roles apply to new requests without erasing historical audit provenance", async () => {
  const { repo, roles, request } = await setup();
  try {
    const restriction = {
      ...f.base("manager-restriction"),
      subject: f.ref("building", "building"),
      sourceRowId: "row-old",
      issuedBy: "manager",
      reason: "Synthetic DNC",
      issuedAt: f.AT,
    };
    repo.commit(
      request({ suppressions: [restriction] }, { credential: "manager-token" }),
    );
    roles.set("manager|synthetic-workspace", ["representative"]);
    assert.throws(
      () =>
        repo.commit(
          request(
            { suppressions: [{ ...restriction, id: "new-s" }] },
            {
              credential: "manager-token",
              commandId: "new-command",
              expectedRevision: 1,
            },
          ),
        ),
      code("forbidden"),
    );
    const note = {
      ...f.verified(
        "manager-note",
        f.ref("building", "building"),
        "hours",
        "9–5",
      ).observation,
      observerId: "manager",
    }; // Historical registry has manager-only; this observer is not attested there.
    assert.throws(
      () =>
        repo.commit(
          request(
            { fieldObservations: [note] },
            {
              credential: "manager-token",
              commandId: "note",
              expectedRevision: 1,
            },
          ),
        ),
      code("validation_failed"),
    );
    roles.set("rep|synthetic-workspace", []);
    assert.throws(
      () =>
        repo.read({
          credential: "rep-token",
          workspaceId: "synthetic-workspace",
        }),
      code("forbidden"),
    );
    assert.equal(
      repo.read({
        credential: "manager-token",
        workspaceId: "synthetic-workspace",
      }).workspace.suppressions.length,
      1,
    );
  } finally {
    repo.close();
  }
});
test("B2A identity and current roles are rechecked before transaction commit", async () => {
  const { createRepositoryProof } = await import("../proof/repository.mjs");
  const { emptyWorkspace } = await import("../domain/contracts.mjs");
  let roles = ["representative"];
  const repo = createRepositoryProof({
    verifyCredential: () => ({
      subject: "rep",
      expiresAt: "2026-11-16T00:00:00.000Z",
    }),
    currentRoles: () => roles,
    actorRegistry: () => f.context.actors,
    now: () => Date.parse(f.AT),
    fault: (phase) => {
      if (phase === "before_commit") roles = [];
    },
  });
  try {
    repo.testOnly.seed(f.fixture(emptyWorkspace));
    const observation = f.verified(
      "recheck",
      f.ref("business", "business-a"),
      "hours",
      "9–5",
    ).observation;
    assert.throws(
      () =>
        repo.commit({
          credential: "synthetic",
          workspaceId: "synthetic-workspace",
          expectedRevision: 0,
          commandId: "recheck",
          additions: { fieldObservations: [observation] },
        }),
      code("forbidden"),
    );
    roles = ["representative"];
    assert.equal(
      repo.read({ credential: "synthetic", workspaceId: "synthetic-workspace" })
        .revision,
      0,
    );
    assert.equal(repo.testOnly.inspect("synthetic-workspace").audit.length, 0);
  } finally {
    repo.close();
  }
});
