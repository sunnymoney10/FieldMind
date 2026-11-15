import { performance } from "node:perf_hooks";
import { writeFileSync } from "node:fs";
import os from "node:os";
import {
  syntheticWorkspace,
  syntheticLegacy,
  context,
  AT,
} from "./synthetic.mjs";
import { validateWorkspace } from "../domain/validate.mjs";
import { createIntelligenceProjection } from "../domain/intelligence.mjs";
import { previewLegacy } from "../domain/legacy-preview.mjs";
import { createRepositoryProof } from "../proof/repository.mjs";
const SAMPLES = 5;
function measure(name, budgetMs, run, samples = SAMPLES) {
  run();
  const durations = [];
  for (let i = 0; i < samples; i++) {
    const start = performance.now();
    run();
    durations.push(performance.now() - start);
  }
  const sorted = [...durations].sort((a, b) => a - b),
    p95 = sorted[Math.ceil(sorted.length * 0.95) - 1];
  return {
    name,
    budgetMs,
    samples,
    durationsMs: durations.map((x) => +x.toFixed(2)),
    p95Ms: +p95.toFixed(2),
    pass: p95 <= budgetMs,
  };
}
const results = [];
let small;
for (const n of [1000, 5000]) {
  const w = syntheticWorkspace(n);
  if (n === 1000) small = w;
  results.push(
    measure(
      `validate_${n}_prospects_${8 * n}_claims`,
      n === 1000 ? 1000 : 5000,
      () => {
        const v = validateWorkspace(w, context);
        if (!v.ok) throw new Error(JSON.stringify(v.errors.slice(0, 2)));
      },
    ),
  );
  results.push(
    measure(
      `projection_${n}_prospects_${8 * n}_claims`,
      n === 1000 ? 1500 : 7000,
      () => {
        const p = createIntelligenceProjection(
          w,
          { asOf: "2026-11-20" },
          context,
        );
        if (p.stats().claims !== 8 * n)
          throw new Error("Projection count mismatch");
      },
    ),
  );
  const p = createIntelligenceProjection(w, { asOf: "2026-11-20" }, context);
  let index = 0;
  results.push(
    measure(
      `indexed_finding_${n}_prospects`,
      10,
      () => {
        if (!p.finding("c-" + (index++ % n) + "-5"))
          throw new Error("Missing finding");
      },
      100,
    ),
  );
}
const skew = syntheticWorkspace(1),
  template = skew.claims[0];
skew.claims = Array.from({ length: 2000 }, (_, i) => ({
  ...structuredClone(template),
  id: "alternative-" + i,
  value: "Synthetic competing value " + i,
}));
results.push(
  measure("projection_2000_competing_values_one_subject", 1500, () => {
    const p = createIntelligenceProjection(
        skew,
        { asOf: "2026-11-20" },
        context,
      ),
      f = p.finding("alternative-0");
    if (
      f.status !== "disputed" ||
      f.conflictIds.length > 20 ||
      f.conflictAlternativeCount !== 1999
    )
      throw new Error("Alternative cap or dispute failure");
  }),
);
const legacy = syntheticLegacy(10000);
results.push(
  measure("legacy_preview_10000_records", 2000, () => {
    const preview = previewLegacy(legacy, {
      referenceWorkspace: small,
      context,
    });
    if (
      preview.items.length !== 10000 ||
      preview.rawText !== legacy ||
      preview.items.some((i) => i.acceptedIdentity !== null)
    )
      throw new Error("Preview integrity failure");
  }),
);
const repo = createRepositoryProof({
  verifyCredential: (t) =>
    t === "synthetic-token"
      ? { subject: "rep", expiresAt: "2026-11-16T00:00:00.000Z" }
      : null,
  currentRoles: () => ["representative"],
  actorRegistry: () => context.actors,
  now: () => Date.parse(AT),
});
try {
  repo.testOnly.seed(small);
  let revision = 0;
  results.push(
    measure("repository_commit_on_1000_prospect_snapshot", 3000, () => {
      const id = "observation-" + revision;
      const out = repo.commit({
        credential: "synthetic-token",
        workspaceId: "synthetic-workspace",
        expectedRevision: revision,
        commandId: "command-" + revision,
        additions: {
          fieldObservations: [
            {
              id,
              workspaceId: "synthetic-workspace",
              createdAt: AT,
              observerId: "rep",
              subject: { type: "premise", id: "p-0" },
              predicate: "hours",
              value: "Synthetic hours",
              kind: "direct_observation",
              note: "Synthetic only",
              observedAt: AT,
            },
          ],
        },
      });
      revision = out.revision;
    }),
  );
} finally {
  repo.close();
}
const resourceBudget = {
  maxRssMiB: 1024,
  observedMaxRssMiB: +(process.resourceUsage().maxRSS / 1024).toFixed(1),
  pass: process.resourceUsage().maxRSS / 1024 <= 1024,
};
const report = {
  protocol: "b2a-performance-1",
  syntheticOnly: true,
  generatedAt: new Date().toISOString(),
  environment: {
    node: process.version,
    platform: process.platform,
    arch: process.arch,
    cpu: os.cpus()[0]?.model,
    maxRssMiB: +(process.resourceUsage().maxRSS / 1024).toFixed(1),
  },
  method:
    "One warmup then 5 measured sequential runs; p95 nearest-rank (5 samples => max). Indexed lookup uses 100 samples. Construction excluded, validation included in projection/commit. No network, disk durability, live identity or device-performance claim.",
  results,
  resourceBudget,
  pass: results.every((x) => x.pass) && resourceBudget.pass,
};
const output = process.argv.indexOf("--output");
if (output !== -1)
  writeFileSync(
    process.argv[output + 1],
    JSON.stringify(report, null, 2) + "\n",
  );
console.log(JSON.stringify(report, null, 2));
if (!report.pass) process.exitCode = 1;
