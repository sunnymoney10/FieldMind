import { emptyWorkspace } from "../domain/contracts.mjs";
export const AT = "2026-11-15T12:00:00.000Z";
export const context = {
  actorId: "rep",
  actors: {
    rep: { workspaceId: "synthetic-workspace", roles: ["representative"] },
    manager: { workspaceId: "synthetic-workspace", roles: ["manager"] },
    ai: { workspaceId: "synthetic-workspace", roles: ["researcher"] },
  },
};
const base = (id) => ({
  id,
  workspaceId: "synthetic-workspace",
  createdAt: AT,
});
const ref = (type, id) => ({ type, id });
export function syntheticWorkspace(prospects) {
  const w = emptyWorkspace("synthetic-workspace");
  w.importBatches = [
    {
      ...base("batch"),
      fileName: "synthetic-only.csv",
      rawText:
        "Name,Account,Device\n" +
        Array.from(
          { length: prospects },
          (_, i) => `Synthetic ${i},000-${i},Synthetic thermostat\n`,
        ).join(""),
      declaredSource: "Synthetic manager list",
      importedBy: "manager",
      listType: "mimo",
      parserVersion: "benchmark-1",
      mappingVersion: "benchmark-1",
    },
  ];
  w.researchRuns = [
    {
      ...base("run"),
      requestedPremiseIds: [],
      protocolVersion: "synthetic-1",
      rawRequest: "Synthetic benchmark request",
      rawResponse: "Synthetic response",
      completedAt: AT,
      coverage: [],
    },
  ];
  for (let i = 0; i < prospects; i++) {
    w.premises.push({
      ...base("p-" + i),
      buildingId: null,
      suiteId: null,
      addressRaw: `${100 + i} Fictional Way`,
      externalRefs: [],
    });
    w.businesses.push({
      ...base("b-" + i),
      name: "Synthetic Business " + i,
      aliases: [],
      externalRefs: [],
    });
    w.utilityAccounts.push({
      ...base("a-" + i),
      provider: "Synthetic Utility",
      reference: "000-" + i,
      serviceLocationIds: [],
      period: { from: null, to: null },
      supportClaimIds: [],
    });
    w.sourceRows.push({
      ...base("r-" + i),
      batchId: "batch",
      rowIndex: i,
      headers: ["Name", "Account", "Device"],
      cells: ["Synthetic " + i, "000-" + i, "Synthetic thermostat"],
    });
    w.researchRuns[0].requestedPremiseIds.push("p-" + i);
    const ids = Array.from({ length: 8 }, (_, j) => "c-" + i + "-" + j);
    for (let j = 0; j < 8; j++) {
      const subject =
          j === 1 || j === 5
            ? ref("business", "b-" + i)
            : j === 3
              ? ref("utilityAccount", "a-" + i)
              : ref("premise", "p-" + i),
        predicate = [
          "operating_status",
          "occupant_identity",
          "hvac_context",
          "historical_equipment",
          "energy_experience",
          "authority.business_ownership",
          "hvac_context",
          "energy_experience",
        ][j],
        inferred = j >= 5;
      w.claims.push({
        ...base(ids[j]),
        subject,
        predicate,
        value: [
          "Operating",
          "Synthetic operator " + i,
          "Permit records cooling work",
          "Synthetic thermostat",
          "Comfort mentioned",
          "Owner hypothesis",
          "Zoned cooling hypothesis",
          "Comfort may affect decisions",
        ][j],
        origin: inferred ? "ai" : j === 3 ? "manager_list" : "public_source",
        basis: inferred ? "inferred" : "reported",
        review: "unreviewed",
        temporal: j === 3 ? "historical" : "as_of",
        period: { from: j === 3 ? null : "2026-11-15", to: null },
        observedAt: AT,
        sourcePublishedOn: null,
        sourceRowIds: j === 3 ? ["r-" + i] : [],
        citations:
          inferred || j === 3
            ? []
            : [
                {
                  url: "https://example.com/synthetic/" + i + "/" + j,
                  title: "Synthetic source",
                  excerpt: "Entirely synthetic benchmark evidence",
                  retrievedAt: AT,
                  publishedOn: null,
                  scope: subject,
                },
              ],
        fieldObservationIds: [],
        derivedFrom:
          j === 5
            ? [ids[1]]
            : j === 6
              ? [ids[2]]
              : j === 7
                ? [ids[4], ids[6]]
                : [],
        conflictsWith: [],
        researchRunId: inferred ? "run" : null,
        verificationObservationId: null,
      });
    }
  }
  return w;
}
export function syntheticLegacy(count) {
  return JSON.stringify({
    fieldmind: 1,
    accounts: Object.fromEntries(
      Array.from({ length: count }, (_, i) => [
        "legacy-" + i,
        {
          name: "Synthetic Business " + (i % 1000),
          addr: `${100 + (i % 1000)} Fictional Way`,
          acct: "000-" + i,
          list: i % 3 ? "approved" : "mimo",
          device: i % 3 ? "" : "Synthetic historical device",
          sourceRows: [
            {
              Name: "Synthetic " + i,
              Account: "000-" + i,
              Custom: "Kept exactly",
            },
          ],
          unknown: { nested: ["unchanged", i] },
        },
      ]),
    ),
    notes: { orphan: { preserved: true } },
    meta: { synthetic: true },
  });
}
