import { writeFileSync } from "node:fs";
import { syntheticWorkspace, syntheticLegacy, context } from "./synthetic.mjs";
import { previewLegacy } from "../domain/legacy-preview.mjs";
import { createIntelligenceProjection } from "../domain/intelligence.mjs";
const w = syntheticWorkspace(2),
  p = createIntelligenceProjection(w, { asOf: "2026-11-20" }, context);
writeFileSync(
  "examples/b2a-legacy-preview.json",
  JSON.stringify(
    previewLegacy(syntheticLegacy(3), { referenceWorkspace: w, context }),
    null,
    2,
  ) + "\n",
);
writeFileSync(
  "examples/b2a-intelligence.json",
  JSON.stringify(
    {
      syntheticOnly: true,
      note: "Independent subject briefs from a known synthetic scenario; no real identity relationship accepted or migrated.",
      premise: p.brief({ type: "premise", id: "p-0" }),
      business: p.brief({ type: "business", id: "b-0" }),
      historicalAccount: p.brief({ type: "utilityAccount", id: "a-0" }),
    },
    null,
    2,
  ) + "\n",
);
