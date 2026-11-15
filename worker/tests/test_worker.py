"""Synthetic tests for the FieldMind research worker. No real prospect data."""
import copy, json, os, sys, unittest, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "worker"))
import fmworker as W  # noqa: E402

AS_OF = dt.date(2026, 11, 14)
PROSPECT = {"ref": "r1mvlv0", "listed_name": "FIXTURE Old Cafe", "synthetic": True,
            "address": {"number": "100", "street": "Test Ave", "suite": "Ste 2", "city": "Raleigh", "state": "NC", "zip": "27604"},
            "list_context": {"historical_participation": "FIXTURE: prior participation recorded under a previous occupant"}}

SITE = "FIXTURE Bakery LLC. Visit us at 100 Test Ave, Suite 2, Raleigh NC 27604. Open Tue-Sat 7am-3pm. Founded in 2021 by Jordan Example, owner and head baker."
REG = "Business Registration: FIXTURE BAKERY LLC. Status: Current-Active. Registered Agent: Jordan Example. Principal Office: 100 Test Ave Ste 2, Raleigh, NC 27604. Formed 2021-03-02."
OTHER = "FIXTURE Bakery LLC, 900 Elsewhere Rd, Durham NC. Catering and wholesale."
SUITE3 = "FIXTURE Nail Studio, 100 Test Ave Ste 3, Raleigh NC 27604."
LISTING = "FIXTURE Bakery, 100 Test Ave Ste 2, Raleigh. Owner Jordan Example also manages the building's HVAC contract with the landlord."
OLD = "2019: FIXTURE Old Cafe opens at 100 Test Ave Ste 2, Raleigh."
DISPUTE = "Now open at 100 Test Ave Ste 2, Raleigh: FIXTURE Smoothie Bar."


def R(id, text, stype="business_site", outcome="ok", url=None, published=None, kind="fetch"):
    return {"id": id, "kind": kind, "url": url or f"https://fixture.invalid/{id}", "title": f"Fixture {id}", "outcome": outcome,
            "source_type": stype, "captured_text": text if outcome == "ok" else "", "completed_at": "2026-11-14T12:00:00+00:00",
            "published": published, "error": None if outcome == "ok" else "HTTP 403"}


RETR = [R("R1", SITE), R("R2", REG, "registry"), R("R3", OTHER, "listing"), R("R4", SUITE3, "listing"), R("R5", LISTING, "listing"),
        R("R6", OLD, "news", published="2019-05-01"), R("R7", "", outcome="failed"), R("R8", DISPUTE, "listing")]


def C(id, **kw):
    base = {"id": id, "text": kw.pop("text", id), "claim_type": "other", "about": "occupant", "basis": "observed", "proposed_status": "found", "dimension": "business"}
    base.update(kw)
    return base


GOOD = [
    C("C1", text="FIXTURE Bakery operates at 100 Test Ave Suite 2", claim_type="occupant_identity", subject="FIXTURE Bakery LLC", value="FIXTURE Bakery LLC",
      value_key="occupant_name", retrieval="R1", excerpt="Visit us at 100 Test Ave, Suite 2, Raleigh NC 27604", address_in_source="100 Test Ave, Suite 2, Raleigh NC 27604"),
    C("C2", text="Hours Tue-Sat 7am-3pm", claim_type="hours", subject="FIXTURE Bakery LLC", value="Tue-Sat 7am-3pm", retrieval="R1", excerpt="Open Tue-Sat 7am-3pm"),
    C("C3", text="Jordan Example is registered agent of FIXTURE BAKERY LLC", claim_type="ownership", subject="FIXTURE Bakery LLC", person="Jordan Example",
      authority_role="business_ownership", proposed_status="verified", retrieval="R2", excerpt="Registered Agent: Jordan Example", dimension="people",
      address_in_source="100 Test Ave Ste 2, Raleigh, NC 27604"),
]


def run(claims, retr=RETR, prospect=PROSPECT, timing=None):
    return W.build(copy.deepcopy(prospect), W.plan(prospect), copy.deepcopy(retr), copy.deepcopy(claims), timing or {}, AS_OF)


def reasons(report):
    return {r["id"]: r["reason"] for r in report["claims"]["rejected"]}


class Intake(unittest.TestCase):
    def test_accepts_minimum(self):
        W.check_prospect(copy.deepcopy(PROSPECT))

    def test_rejects_identifiers(self):
        for bad in ({"itron_account": "x"}, {"premise_id": "1"}, {"notes": "x"}):
            p = copy.deepcopy(PROSPECT); p.update(bad)
            with self.assertRaises(W.IntakeError):
                W.check_prospect(p)
        p = copy.deepcopy(PROSPECT); p["listed_name"] = "Cafe 9000000123"
        with self.assertRaises(W.IntakeError):
            W.check_prospect(p)
        p = copy.deepcopy(PROSPECT); p["ref"] = "9000000004"
        with self.assertRaises(W.IntakeError):
            W.check_prospect(p)
        p = copy.deepcopy(PROSPECT); p["address"]["device"] = "T1"
        with self.assertRaises(W.IntakeError):
            W.check_prospect(p)

    def test_plan_uses_only_name_and_address(self):
        text = json.dumps(W.plan(PROSPECT))
        self.assertIn("100 Test Ave", text)
        self.assertNotIn("prior participation", text)


class Checks(unittest.TestCase):
    def test_good_claims_accepted(self):
        brief, research, report = run(GOOD)
        self.assertEqual(report["claims"]["accepted"], 3, report["claims"]["rejected"])
        self.assertEqual(brief["q2_decision_authority"]["business_ownership"]["state"], "verified")
        self.assertEqual(brief["q1_current_operator"]["state"], "source_supported")
        self.assertIsNone(brief["q1_current_operator"]["accepted_identity_reference"])

    def test_fabricated_excerpt_rejected(self):
        c = C("X1", claim_type="hours", subject="FIXTURE Bakery LLC", retrieval="R1", excerpt="Open every day 24 hours")
        _, _, rep = run(GOOD + [c])
        self.assertEqual(reasons(rep)["X1"], "excerpt_not_in_source")

    def test_failed_source_rejected_and_reported(self):
        c = C("X2", claim_type="hours", subject="FIXTURE Bakery LLC", retrieval="R7", excerpt="anything at all here")
        brief, _, rep = run(GOOD + [c])
        self.assertEqual(reasons(rep)["X2"], "source_failed")
        self.assertTrue(any(f["id"] == "R7" for f in rep["retrieval"]["failures"]))
        self.assertTrue(any(l.startswith("R7") for l in brief["research_limitations"]))

    def test_unknown_source_rejected(self):
        c = C("X3", claim_type="hours", subject="FIXTURE Bakery LLC", retrieval="R99", excerpt="Open Tue-Sat 7am-3pm")
        _, _, rep = run(GOOD + [c])
        self.assertEqual(reasons(rep)["X3"], "source_missing")

    def test_same_name_other_address_merge_rejected(self):
        c = C("X4", text="Bakery does catering", subject="FIXTURE Bakery LLC", retrieval="R3", excerpt="Catering and wholesale",
              address_in_source="900 Elsewhere Rd, Durham NC")
        _, _, rep = run(GOOD + [c])
        self.assertEqual(reasons(rep)["X4"], "identity_merge_rejected")

    def test_other_suite_rejected(self):
        c = C("X5", claim_type="occupant_identity", subject="FIXTURE Nail Studio", value="FIXTURE Nail Studio", value_key="occupant_name",
              retrieval="R4", excerpt="FIXTURE Nail Studio, 100 Test Ave Ste 3", address_in_source="100 Test Ave Ste 3, Raleigh NC 27604")
        brief, _, rep = run(GOOD + [c])
        self.assertEqual(reasons(rep)["X5"], "identity_merge_rejected")
        self.assertNotEqual(brief["q1_current_operator"]["state"], "disputed")

    def test_untied_name_rejected(self):
        c = C("X6", text="Some other cafe has great coffee", subject="Unrelated Cafe", retrieval="R5", excerpt="Owner Jordan Example also manages")
        _, _, rep = run(GOOD + [c])
        self.assertEqual(reasons(rep)["X6"], "identity_merge_rejected")

    def test_property_fact_without_address_rejected(self):
        c = C("X7", claim_type="hvac", about="equipment", subject="FIXTURE Bakery LLC", retrieval="R5", excerpt="manages the building's HVAC contract")
        _, _, rep = run(GOOD + [c])
        self.assertEqual(reasons(rep)["X7"], "identity_merge_rejected")

    def test_verified_from_listing_downgraded(self):
        c = C("X8", text="Jordan Example handles HVAC decisions", claim_type="hvac", subject="FIXTURE Bakery LLC", person="Jordan Example",
              authority_role="hvac_facilities", proposed_status="verified", retrieval="R5", excerpt="Owner Jordan Example also manages the building's HVAC contract",
              address_in_source="100 Test Ave Ste 2, Raleigh")
        brief, _, rep = run(GOOD + [c])
        self.assertEqual(reasons(rep)["X8"], "verified_label_rejected")
        self.assertEqual(brief["q2_decision_authority"]["hvac_facilities"]["state"], "source_supported")

    def test_verified_needs_person_in_record(self):
        c = C("X9", claim_type="ownership", subject="FIXTURE Bakery LLC", person="Pat Nobody", authority_role="business_operations",
              proposed_status="verified", retrieval="R2", excerpt="Status: Current-Active", address_in_source="100 Test Ave Ste 2, Raleigh, NC 27604")
        _, _, rep = run(GOOD + [c])
        self.assertEqual(reasons(rep)["X9"], "verified_label_rejected")

    def test_utility_authority_rejected(self):
        c = C("X10", text="Jordan Example controls the Duke account", subject="FIXTURE Bakery LLC", person="Jordan Example",
              authority_role="utility_account", proposed_status="verified", retrieval="R2", excerpt="Registered Agent: Jordan Example")
        brief, _, rep = run(GOOD + [c])
        self.assertEqual(reasons(rep)["X10"], "authority_rejected")
        self.assertEqual(brief["q2_decision_authority"]["utility_account"]["state"], "unknown")
        inf = C("X11", text="Owner likely holds the account", basis="inferred", authority_role="utility_account", derived_from=["C3"])
        _, _, rep = run(GOOD + [inf])
        self.assertEqual(reasons(rep)["X11"], "authority_rejected")

    def test_inference_rules(self):
        bad = C("X12", text="Likely small HVAC load", basis="inferred", derived_from=["X1"])
        ver = C("X13", text="Owner-operated", basis="inferred", proposed_status="verified", derived_from=["C1", "C3"])
        _, research, rep = run(GOOD + [bad, ver])
        r = reasons(rep)
        self.assertEqual(r["X12"], "inference_unsupported")
        self.assertEqual(r["X13"], "verified_label_rejected")
        st = {c["id"]: c["status"] for c in research["premises"][0]["claims"]}
        self.assertEqual(st["X13"], "inferred")

    def test_inference_cannot_assign_authority_or_move_subject(self):
        auth = C("X16", text="Jordan decides on HVAC", basis="inferred", subject="FIXTURE Bakery LLC", authority_role="hvac_facilities", derived_from=["C3"])
        move = C("X17", text="New tenant has the same owner", basis="inferred", subject="FIXTURE Smoothie Bar", derived_from=["C3"])
        _, _, rep = run(GOOD + [auth, move])
        r = reasons(rep)
        self.assertEqual(r["X16"], "authority_rejected")
        self.assertEqual(r["X17"], "identity_merge_rejected")

    def test_no_list_suite_other_tenant_rejected(self):
        p = copy.deepcopy(PROSPECT); p["address"]["suite"] = None; p["listed_name"] = "FIXTURE Bakery LLC"
        c = C("X18", claim_type="occupant_identity", subject="FIXTURE Nail Studio", value="FIXTURE Nail Studio", value_key="occupant_name",
              retrieval="R4", excerpt="FIXTURE Nail Studio, 100 Test Ave Ste 3", address_in_source="100 Test Ave Ste 3, Raleigh NC 27604")
        _, _, rep = run(GOOD + [c], prospect=p)
        self.assertEqual(reasons(rep)["X18"], "identity_merge_rejected")
        self.assertNotIn("C1", reasons(rep))  # the listed business in its suite is still accepted

    def test_contradiction_linked(self):
        c = C("X14", claim_type="occupant_identity", subject="FIXTURE Smoothie Bar", value="FIXTURE Smoothie Bar", value_key="occupant_name",
              retrieval="R8", excerpt="Now open at 100 Test Ave Ste 2", address_in_source="100 Test Ave Ste 2, Raleigh")
        brief, research, rep = run(GOOD + [c])
        self.assertEqual(brief["q1_current_operator"]["state"], "disputed")
        cl = {x["id"]: x for x in research["premises"][0]["claims"]}
        self.assertEqual(cl["X14"]["status"], "conflicting")
        self.assertIn("C1", cl["X14"]["conflicts_with"])
        self.assertEqual(research["premises"][0]["occupant"]["status"], "conflicting")
        self.assertTrue(brief["q4_uncertainty"]["contradicted"])
        self.assertIn("Who operates", brief["q5_verify_first"]["question"])

    def test_old_source_is_historical_not_contradiction(self):
        c = C("X15", claim_type="occupant_identity", subject="FIXTURE Old Cafe", value="FIXTURE Old Cafe", value_key="occupant_name",
              retrieval="R6", excerpt="FIXTURE Old Cafe opens at 100 Test Ave Ste 2", address_in_source="100 Test Ave Ste 2, Raleigh")
        brief, research, _ = run(GOOD + [c])
        cl = {x["id"]: x for x in research["premises"][0]["claims"]}
        self.assertEqual(cl["X15"]["status"], "historical")
        self.assertEqual(brief["q1_current_operator"]["state"], "source_supported")
        self.assertIn("FIXTURE Old Cafe", brief["q1_current_operator"]["summary"])  # listed name kept as list info

    def test_suite_unconfirmed_drives_verify_first(self):
        retr = RETR + [R("R9", "FIXTURE Bakery LLC, 100 Test Ave, Raleigh NC 27604", "listing")]
        c = [C("C1", claim_type="occupant_identity", subject="FIXTURE Bakery LLC", value="FIXTURE Bakery LLC", value_key="occupant_name",
               retrieval="R9", excerpt="FIXTURE Bakery LLC, 100 Test Ave", address_in_source="100 Test Ave, Raleigh NC 27604")]
        brief, _, _ = run(c, retr)
        self.assertIn("exact suite", brief["q5_verify_first"]["question"])


class Outputs(unittest.TestCase):
    def test_brief_shape(self):
        brief, _, _ = run(GOOD)
        tmpl = json.load(open(os.path.join(HERE, "..", "reference", "intelligence-brief.blank.json")))
        for k in tmpl:
            self.assertIn(k, brief, k)
        for k in tmpl["q2_decision_authority"]:
            self.assertIn(k, brief["q2_decision_authority"])
        self.assertEqual(brief["q3_energy_hvac_context"]["current_eligibility"]["state"], "not_established")
        self.assertIsNone(brief["q6_priority_judgment"]["after"])
        self.assertTrue(brief["q5_verify_first"]["requires_separate_contact_permission"])
        for f in brief["findings"]:
            self.assertTrue(f["url"] and f["excerpt"] and f["retrieved_at"], f)

    def test_research_v2_validates(self):
        import jsonschema
        schema = json.load(open(os.path.join(HERE, "..", "reference", "research.v2.schema.json")))
        c = C("X14", claim_type="occupant_identity", subject="FIXTURE Smoothie Bar", value="FIXTURE Smoothie Bar", value_key="occupant_name",
              retrieval="R8", excerpt="Now open at 100 Test Ave Ste 2", address_in_source="100 Test Ave Ste 2, Raleigh")
        for claims in (GOOD, GOOD + [c], []):
            _, research, _ = run(claims)
            errs = list(jsonschema.Draft202012Validator(schema).iter_errors(research))
            self.assertEqual(errs, [], [e.message for e in errs])

    def test_no_identifiers_in_outputs(self):
        outs = json.dumps(run(GOOD))
        self.assertNotIn("9000000004", outs)

    def test_timing_and_cap(self):
        t = {"elapsed_seconds": 1300, "phases": {"retrieve": 1000}}
        _, _, rep = run(GOOD, timing=t)
        self.assertFalse(rep["timing"]["within_cap"])
        self.assertEqual(rep["timing"]["cap_seconds"], 1200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
