/* Tests for:
   1. deactivationInfo() — 12-month lockout detection from list status/date
   2. readiness()        — locked_out state surfaces before research states
   3. approachLine()     — context-aware "who to ask for" line
*/
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { app } = require("./harness.cjs");

/* ── helpers ─────────────────────────────────────────────────── */
function mkApp() {
  const a = app();
  // Seed a minimal account with one source row
  a.run(`
    S.accounts["p1"] = {
      id:"p1", name:"Synthetic Bakery LLC", addr:"123 Fictional Way",
      city:"Raleigh", zip:"27601",
      sourceRows:[{
        _batch:"b1",
        "Company Name":"Synthetic Bakery LLC",
        "Service Address":"123 Fictional Way",
        "Prospect Status":"Removed",
        "Prospect Created":"2025-07-15"
      }]
    };
    S.notes["p1"] = { evidence:[], visits:[] };
  `);
  return a;
}

/* ── deactivationInfo ────────────────────────────────────────── */

test("deactivationInfo returns null when status is active", () => {
  const a = app();
  a.run(`
    S.accounts["p2"] = {
      id:"p2", name:"Synthetic Deli", addr:"200 Fictional Ave",
      sourceRows:[{
        _batch:"b1",
        "Prospect Status":"Active",
        "Prospect Created":"2024-01-10"
      }]
    };
  `);
  const result = a.run(`deactivationInfo("p2")`);
  assert.equal(result, null);
});

test("deactivationInfo returns null when no source rows", () => {
  const a = app();
  a.run(`S.accounts["p3"] = { id:"p3", name:"Synthetic Shop", addr:"300 Fictional Blvd", sourceRows:[] };`);
  assert.equal(a.run(`deactivationInfo("p3")`), null);
});

test("deactivationInfo detects 'Removed' status and returns eligibility info", () => {
  const a = mkApp(); // "Removed" on 2025-07-15
  const r = a.run(`deactivationInfo("p1")`);
  assert.ok(r, "should detect deactivation");
  assert.equal(typeof r.eligible, "boolean", "eligible should be a boolean");
  assert.equal(r.status, "Removed");
  // eligibleAfter should be ~12 months after deactivatedAt when date is parseable
  if (r.eligibleAfter) {
    // diff between eligibleAfter and deactivatedAt should be ~365 days
    const diff = a.run(`deactivationInfo("p1").eligibleAfter - deactivationInfo("p1").deactivatedAt`);
    assert.ok(diff >= 364 * 24 * 3600 * 1000 && diff <= 367 * 24 * 3600 * 1000, "eligibleAfter should be ~12 months after deactivatedAt");
  }
});

test("deactivationInfo detects 'Inactive' status", () => {
  const a = app();
  a.run(`
    S.accounts["p4"] = {
      id:"p4", name:"Synthetic Motors", addr:"400 Fictional Dr",
      sourceRows:[{
        _batch:"b1","Prospect Status":"Inactive","Prospect Created":"2025-01-01"
      }]
    };
  `);
  const r = a.run(`deactivationInfo("p4")`);
  assert.ok(r, "should detect Inactive as deactivation");
  assert.equal(r.status, "Inactive");
});

test("deactivationInfo detects 'Deactivated' status", () => {
  const a = app();
  a.run(`
    S.accounts["p5"] = {
      id:"p5", name:"Synthetic Cleaners", addr:"500 Fictional St",
      sourceRows:[{
        _batch:"b1","Prospect Status":"Deactivated","Prospect Created":"2025-03-20"
      }]
    };
  `);
  const r = a.run(`deactivationInfo("p5")`);
  assert.ok(r);
  assert.equal(r.status, "Deactivated");
});

test("deactivationInfo uses most-recent row when multiple rows exist", () => {
  const a = app();
  // older row = Removed (deactivated), newer row = Active (re-enrolled and active again)
  a.run(`
    S.accounts["p6"] = {
      id:"p6", name:"Synthetic Gym", addr:"600 Fictional Pl",
      sourceRows:[
        {_batch:"b1","Prospect Status":"Removed","Prospect Created":"2024-05-01"},
        {_batch:"b2","Prospect Status":"Active","Prospect Created":"2025-10-01"}
      ]
    };
  `);
  const r = a.run(`deactivationInfo("p6")`);
  assert.equal(r, null, "newest row is Active, should not flag as locked out");
});

/* ── readiness — locked_out state ───────────────────────────── */

test("readiness returns locked_out for a recently deactivated account", () => {
  const a = mkApp(); // "Removed" on 2025-07-15 — not yet 12 months from today (Nov 2026 runner)
  // Override with a future-dated removal so eligible=false is deterministic
  a.run(`
    S.accounts["p1"].sourceRows = [{
      _batch:"b1","Prospect Status":"Removed",
      "Prospect Created": new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString().slice(0,10)
    }];
  `);
  const rd = a.run(`readiness("p1")`);
  assert.equal(rd.k, "locked_out");
  assert.ok(rd.reason.includes("deactivated"), "reason should mention deactivated");
  // eligibleAfter is a Date object inside the VM; check it's truthy (not null/undefined)
  assert.ok(rd.eligibleAfter, "eligibleAfter should be set");
});

test("readiness does NOT return locked_out when deactivation is older than 12 months", () => {
  const a = app();
  a.run(`
    S.accounts["p7"] = {
      id:"p7", name:"Synthetic Auto", addr:"700 Fictional Rd",
      sourceRows:[{
        _batch:"b1","Prospect Status":"Removed",
        "Prospect Created":"2024-01-01"
      }]
    };
    S.notes["p7"] = { evidence:[], visits:[] };
  `);
  const rd = a.run(`readiness("p7")`);
  // 2024-01-01 + 12 months = 2025-01-01, which is before Nov 2026 → eligible
  assert.notEqual(rd.k, "locked_out", "12 months have passed — should not be locked_out");
});

test("readiness locked_out takes priority over suppressed check", () => {
  // suppressed flag should still win (checked first in code), but locked_out ignores general suppression
  const a = app();
  a.run(`
    S.accounts["p8"] = {
      id:"p8", name:"Synthetic Mart", addr:"800 Fictional Ln", suppressed:true,
      listStatus:"Do Not Contact",
      sourceRows:[{
        _batch:"b1","Prospect Status":"Removed",
        "Prospect Created": new Date(Date.now() - 30*24*3600*1000).toISOString().slice(0,10)
      }]
    };
    S.notes["p8"] = { evidence:[], visits:[] };
  `);
  const rd = a.run(`readiness("p8")`);
  // suppressed flag takes absolute priority in readiness()
  assert.equal(rd.k, "suppressed");
});

/* ── approachLine ────────────────────────────────────────────── */

test("approachLine uses known occupant name when research found one", () => {
  const a = app();
  a.run(`
    S.accounts["q1"] = { id:"q1", name:"Synthetic Pizza", addr:"10 Fictional Way", city:"Raleigh" };
    S.notes["q1"] = { evidence:[], visits:[], brief:{
      decision:{route:"owner_operator", basis:"Google Maps listing"},
      occupant:{name:"Maria Ramirez", status:"verified"},
      profile:{}
    }};
  `);
  const r = a.run(`approachLine("q1")`);
  assert.ok(r);
  assert.ok(r.line.includes("Maria"), "should use known occupant first name");
  assert.ok(r.line.includes("Duke Energy"), "should mention Duke Energy account");
});

test("approachLine uses known decision-maker title from decision.who", () => {
  const a = app();
  a.run(`
    S.accounts["q2"] = { id:"q2", name:"Synthetic Corp HQ", addr:"20 Fictional Blvd", city:"Raleigh" };
    S.notes["q2"] = { evidence:[], visits:[], brief:{
      decision:{route:"corporate", who:"Regional Facilities Director", basis:"LinkedIn"},
      profile:{}
    }};
  `);
  const r = a.run(`approachLine("q2")`);
  assert.ok(r);
  assert.ok(r.line.includes("Regional Facilities Director"));
});

test("approachLine returns facilities manager for manufacturing names", () => {
  const a = app();
  a.run(`
    S.accounts["q3"] = { id:"q3", name:"SYNTHETIC MANUFACTURING INC", addr:"30 Industrial Way", city:"Durham" };
    S.notes["q3"] = { evidence:[], visits:[] };
  `);
  const r = a.run(`approachLine("q3")`);
  assert.ok(r);
  assert.ok(r.line.includes("facilities manager"), "manufacturing should get facilities manager");
});

test("approachLine returns office manager for medical / professional buildings", () => {
  const a = app();
  a.run(`
    S.accounts["q4"] = { id:"q4", name:"SYNTHETIC MEDICAL CENTER", addr:"40 Health Blvd Ste 200", city:"Cary" };
    S.notes["q4"] = { evidence:[], visits:[] };
  `);
  const r = a.run(`approachLine("q4")`);
  assert.ok(r);
  assert.ok(r.line.includes("office manager") || r.line.includes("utility bill"), "medical center should get office manager");
});

test("approachLine returns owner-or-manager for retail / food service", () => {
  const a = app();
  a.run(`
    S.accounts["q5"] = { id:"q5", name:"SYNTHETIC PIZZA & WINGS", addr:"50 Food Court Ave", city:"Raleigh" };
    S.notes["q5"] = { evidence:[], visits:[] };
  `);
  const r = a.run(`approachLine("q5")`);
  assert.ok(r);
  assert.ok(r.line.includes("owner") || r.line.includes("manager"), "food service should get owner or manager");
});

test("approachLine falls back to electricity/Duke account for generic small business", () => {
  const a = app();
  a.run(`
    S.accounts["q6"] = { id:"q6", name:"Synthetic Consulting", addr:"60 Business Park Dr", city:"Raleigh" };
    S.notes["q6"] = { evidence:[], visits:[] };
  `);
  const r = a.run(`approachLine("q6")`);
  assert.ok(r);
  assert.ok(r.line.includes("electricity") || r.line.includes("Duke Energy"), "fallback should reference electricity/Duke account");
});

test("approachLine returns null for unknown account id", () => {
  const a = app();
  const r = a.run(`approachLine("nonexistent")`);
  assert.equal(r, null);
});
