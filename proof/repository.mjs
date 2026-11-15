/** Isolated SQLite test engine. Not an app adapter, authentication provider or production database choice. */
import { DatabaseSync } from "node:sqlite";
import { createHash } from "node:crypto";
import { CONTRACTS, emptyWorkspace } from "../domain/contracts.mjs";
import { appendRecords } from "../domain/functions.mjs";
import { assertWorkspace } from "../domain/validate.mjs";
import { graphBudget } from "../domain/limits.mjs";
const stable = (v) =>
  Array.isArray(v)
    ? v.map(stable)
    : v && typeof v === "object"
      ? Object.fromEntries(
          Object.keys(v)
            .sort()
            .map((k) => [k, stable(v[k])]),
        )
      : v;
export class BoundaryError extends Error {
  constructor(code) {
    super(code);
    this.code = code;
  }
}
const allowed = (request, keys) => {
  if (
    !request ||
    typeof request !== "object" ||
    Array.isArray(request) ||
    Object.keys(request).some((k) => !keys.includes(k))
  )
    throw new BoundaryError("invalid_request");
};
const identifier = (v) =>
  typeof v === "string" && /^[A-Za-z0-9_-]{1,128}$/.test(v);
export function createRepositoryProof({
  verifyCredential,
  currentRoles,
  actorRegistry,
  now,
  fault = () => {},
}) {
  if (
    ![verifyCredential, currentRoles, actorRegistry, now].every(
      (x) => typeof x === "function",
    )
  )
    throw new TypeError("Trusted test boundary functions required");
  const db = new DatabaseSync(":memory:");
  db.exec(`PRAGMA foreign_keys=ON;
 CREATE TABLE workspaces(workspace_id TEXT PRIMARY KEY, revision INTEGER NOT NULL CHECK(revision>=0));
 CREATE TABLE entities(workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id), entity_id TEXT NOT NULL, collection TEXT NOT NULL, payload TEXT NOT NULL CHECK(json_valid(payload)), PRIMARY KEY(workspace_id,entity_id), CHECK(json_extract(payload,'$.workspaceId')=workspace_id), CHECK(json_extract(payload,'$.id')=entity_id));
 CREATE TABLE commands(workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id), command_id TEXT NOT NULL, digest TEXT NOT NULL, revision INTEGER NOT NULL, actor_id TEXT NOT NULL, PRIMARY KEY(workspace_id,command_id));
 CREATE TABLE audit(workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id), revision INTEGER NOT NULL, actor_id TEXT NOT NULL, command_id TEXT NOT NULL, PRIMARY KEY(workspace_id,revision));`);
  function authenticate(credential, workspaceId, write = false) {
    if (!identifier(workspaceId)) throw new BoundaryError("invalid_request");
    let principal;
    try {
      principal = verifyCredential(credential);
    } catch {
      throw new BoundaryError("unauthenticated");
    }
    const clock = now();
    if (
      !Number.isFinite(clock) ||
      !principal ||
      !identifier(principal.subject) ||
      !Number.isFinite(Date.parse(principal.expiresAt)) ||
      Date.parse(principal.expiresAt) <= clock
    )
      throw new BoundaryError("unauthenticated");
    const roles = currentRoles(principal.subject, workspaceId) || [];
    if (
      !(write
        ? roles.some((r) =>
            ["manager", "representative", "researcher"].includes(r),
          )
        : roles.some((r) => ["manager", "representative"].includes(r)))
    )
      throw new BoundaryError("forbidden");
    return {
      actorId: principal.subject,
      actors: actorRegistry(workspaceId),
      roles,
    };
  }
  function load(workspaceId) {
    const row = db
      .prepare("SELECT revision FROM workspaces WHERE workspace_id=?")
      .get(workspaceId);
    if (!row) throw new BoundaryError("not_found");
    const workspace = emptyWorkspace(workspaceId);
    for (const e of db
      .prepare(
        "SELECT collection,payload FROM entities WHERE workspace_id=? ORDER BY rowid",
      )
      .all(workspaceId))
      workspace[e.collection].push(JSON.parse(e.payload));
    return { workspace, revision: row.revision };
  }
  // Privileged fixture seeding is intentionally outside the proposed read/commit request surface.
  function seed(workspace) {
    graphBudget(workspace);
    assertWorkspace(workspace, {
      actors: actorRegistry(workspace.workspaceId),
    });
    db.exec("BEGIN IMMEDIATE");
    try {
      db.prepare("INSERT INTO workspaces VALUES(?,0)").run(
        workspace.workspaceId,
      );
      const insert = db.prepare("INSERT INTO entities VALUES(?,?,?,?)");
      for (const collection of Object.keys(CONTRACTS))
        for (const r of workspace[collection])
          insert.run(
            workspace.workspaceId,
            r.id,
            collection,
            JSON.stringify(r),
          );
      db.exec("COMMIT");
    } catch (e) {
      db.exec("ROLLBACK");
      throw e;
    }
  }
  function read(request) {
    allowed(request, ["credential", "workspaceId"]);
    authenticate(request.credential, request.workspaceId);
    return structuredClone(load(request.workspaceId));
  }
  function commit(request) {
    allowed(request, [
      "credential",
      "workspaceId",
      "expectedRevision",
      "commandId",
      "additions",
    ]);
    const { credential, workspaceId, expectedRevision, commandId, additions } =
        request,
      context = authenticate(credential, workspaceId, true);
    if (
      !identifier(commandId) ||
      !Number.isSafeInteger(expectedRevision) ||
      expectedRevision < 0 ||
      !additions ||
      typeof additions !== "object" ||
      Array.isArray(additions)
    )
      throw new BoundaryError("invalid_request");
    // Current session roles, not historical actorRegistry roles, authorize new writes.
    const actors = structuredClone(context.actors);
    for (const [collection, records] of Object.entries(additions)) {
      if (!Object.hasOwn(CONTRACTS, collection) || !Array.isArray(records))
        throw new BoundaryError("invalid_request");
      for (const record of records) {
        if (record?.workspaceId !== workspaceId)
          throw new BoundaryError("forbidden");
        if (
          [
            "prospectAuthorizations",
            "suppressions",
            "suppressionReleases",
          ].includes(collection) &&
          (!context.roles.includes("manager") ||
            record.issuedBy !== context.actorId)
        )
          throw new BoundaryError("forbidden");
        if (
          collection === "fieldObservations" &&
          (!context.roles.includes("representative") ||
            record.observerId !== context.actorId)
        )
          throw new BoundaryError("forbidden");
      }
      if (
        !context.roles.some((r) => ["manager", "representative"].includes(r)) &&
        (!["claims", "researchRuns"].includes(collection) ||
          (collection === "claims" &&
            records.some(
              (r) => r.origin !== "ai" || r.review !== "unreviewed",
            )))
      )
        throw new BoundaryError("forbidden");
    }
    let digest;
    try {
      const serialized = JSON.stringify(
        stable({ expectedRevision, additions }),
      );
      if (Buffer.byteLength(serialized) > 16 * 1024 * 1024) throw new Error();
      digest = createHash("sha256").update(serialized).digest("hex");
    } catch {
      throw new BoundaryError("invalid_request");
    }
    let committed = false;
    db.exec("BEGIN IMMEDIATE");
    try {
      const replay = db
        .prepare(
          "SELECT digest,revision,actor_id FROM commands WHERE workspace_id=? AND command_id=?",
        )
        .get(workspaceId, commandId);
      if (replay) {
        if (replay.digest !== digest || replay.actor_id !== context.actorId)
          throw new BoundaryError("command_conflict");
        db.exec("COMMIT");
        return { revision: replay.revision, replayed: true, commandId };
      }
      const original = load(workspaceId);
      if (original.revision !== expectedRevision)
        throw new BoundaryError("revision_conflict");
      // Validate resource bounds before the existing recursive domain validator.
      const candidate = structuredClone(original.workspace);
      for (const [k, records] of Object.entries(additions)) {
        const ids = new Set(candidate[k].map((r) => r.id));
        for (const r of records)
          if (!ids.has(r.id)) {
            candidate[k].push(r);
            ids.add(r.id);
          }
      }
      graphBudget(candidate);
      let next;
      try {
        next = appendRecords(original.workspace, additions, {
          actorId: context.actorId,
          actors,
          callerRoles: context.roles,
        });
      } catch {
        throw new BoundaryError("validation_failed");
      }
      const insert = db.prepare("INSERT INTO entities VALUES(?,?,?,?)");
      const added = new Set(next.added);
      for (const [collection, records] of Object.entries(next.workspace))
        if (Array.isArray(records))
          for (const r of records)
            if (added.has(r.id))
              insert.run(workspaceId, r.id, collection, JSON.stringify(r));
      fault("after_entities");
      const revision = expectedRevision + 1;
      if (
        db
          .prepare(
            "UPDATE workspaces SET revision=? WHERE workspace_id=? AND revision=?",
          )
          .run(revision, workspaceId, expectedRevision).changes !== 1
      )
        throw new BoundaryError("revision_conflict");
      fault("after_revision");
      db.prepare("INSERT INTO commands VALUES(?,?,?,?,?)").run(
        workspaceId,
        commandId,
        digest,
        revision,
        context.actorId,
      );
      db.prepare("INSERT INTO audit VALUES(?,?,?,?)").run(
        workspaceId,
        revision,
        context.actorId,
        commandId,
      );
      fault("before_commit");
      const refreshed = authenticate(credential, workspaceId, true);
      if (
        refreshed.actorId !== context.actorId ||
        JSON.stringify([...refreshed.roles].sort()) !==
          JSON.stringify([...context.roles].sort())
      )
        throw new BoundaryError("authorization_changed");
      db.exec("COMMIT");
      committed = true;
      fault("after_commit");
      return { revision, replayed: false, commandId };
    } catch (e) {
      if (!committed) db.exec("ROLLBACK");
      if (committed) throw new BoundaryError("outcome_unknown");
      if (e instanceof BoundaryError) throw e;
      if (e.diagnostics || e instanceof RangeError || e instanceof TypeError)
        throw new BoundaryError("validation_failed");
      throw new BoundaryError("write_failed");
    }
  }
  return {
    testOnly: {
      seed,
      inspect: (workspaceId) => ({
        commands: db
          .prepare(
            "SELECT command_id,revision,actor_id FROM commands WHERE workspace_id=?",
          )
          .all(workspaceId),
        audit: db
          .prepare(
            "SELECT revision,actor_id,command_id FROM audit WHERE workspace_id=?",
          )
          .all(workspaceId),
        foreignKeyFailures: db.prepare("PRAGMA foreign_key_check").all(),
      }),
    },
    read,
    commit,
    close: () => db.close(),
  };
}
