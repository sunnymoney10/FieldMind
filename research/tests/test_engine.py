"""Engine adapter tests: recorded live job replay plus synthetic suite/identity cases. No MIMO data."""
import json, re, shutil, sys, tempfile, unittest
from pathlib import Path
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R)); sys.path.insert(0, str(R / "proof"))
import engine_adapter as E  # noqa: E402

RECORDED = R / "runs" / "8ffec3dea0de4c7bbf5bf209aaf6fecd"
TARGET = {"name": "Videri Chocolate Factory", "addr": "327 W Davie St", "city": "Raleigh", "ref": "bb6cd0bbd6db4031bf4ba85e60f89ba1"}


def attach_ok(draft, ref):
    """Python mirror of the app's attachLiveResearch safety check (index.html)."""
    p = draft["premises"][0]
    return (len(draft["premises"]) == 1 and p["match"]["ref"] == ref and p["occupant"]["status"] == "unknown"
            and p["decision_route"]["route"] == "unknown" and all(f["status"] == "not_checked" for f in p["profile"].values())
            and all(c["status"] in ("found", "historical") and c["current_verified"] is False and c["source"]["url"].startswith("http") for c in p["claims"]))


def synthetic_run(pages, queries=("q",)):
    d = Path(tempfile.mkdtemp()); (d / "raw-local-only").mkdir()
    (d / "discovery.json").write_text(json.dumps({"queries": [{"query": q, "result_count": 1, "retrieved_at": "2026-11-15T00:00:00Z", "response": {"results": []}} for q in queries]}))
    srcs = []
    for i, (url, body) in enumerate(pages, 1):
        html = "<html><body><main>" + "".join(f"<p>{b}</p>" for b in body) + "</main>" + "<!--" + "x" * 600 + "--></body></html>"
        (d / "raw-local-only" / f"S{i}.html").write_text(html)
        srcs.append({"source_id": f"S{i}", "requested_url": url, "final_url": url, "success": True, "http_status": 200, "retrieved_at": "2026-11-15T00:00:01Z"})
    (d / "retrieval-initial.json").write_text(json.dumps({"sources": srcs}))
    return d


class Engine(unittest.TestCase):
    def test_recorded_live_job(self):
        run = Path(tempfile.mkdtemp()) / "job"; shutil.copytree(RECORDED, run)
        summary = json.loads((run / "summary.json").read_text())
        draft = E.project_run(run, TARGET, summary)
        p = draft["premises"][0]
        self.assertTrue(attach_ok(draft, TARGET["ref"]))
        self.assertGreaterEqual(len(p["claims"]), 4)
        q = {x["question"]: x["answer"] for x in p["research_questions"]}
        self.assertIn("Likely Videri Chocolate Factory", q["Who appears to operate here?"])
        self.assertIn("Suite 100", q["What should I check first?"])
        self.assertIn("Ask who signs for the utility account", q["Who makes the decisions?"])
        self.assertTrue(any(c["status"] == "historical" for c in p["claims"]))  # 2023 owner mention
        self.assertEqual(len(p["research_questions"]), 6)
        rep_text = " ".join(x["answer"] for x in p["research_questions"]) + " ".join(c["claim"] for c in p["claims"]) + p["summary"] + p["find_out_first"]
        for bad in (r"\b[RCVFSQIN]\d{2}\b", r"source_supported|not_established|business_ownership|permitted public", r"[Cc]andidate|reviewer|schema|Brian"):
            self.assertIsNone(re.search(bad, rep_text), bad)

    def test_wrong_suite_not_merged(self):
        run = synthetic_run([("https://synthbakery.example/contact", ["Synth Bakery LLC, 100 Test Ave Suite 1250, Raleigh NC"])])
        t = {"name": "Synth Bakery LLC", "addr": "100 Test Ave STE 900", "city": "Raleigh", "ref": "syntheticref0001"}
        draft = E.project_run(run, t, {"elapsed_seconds": 5})
        p = draft["premises"][0]
        self.assertTrue(attach_ok(draft, t["ref"]))
        self.assertEqual(p["claims"], [])
        self.assertIn("Suite 1250", p["research_questions"][0]["answer"])
        self.assertIn("Ste 900", p["find_out_first"])

    def test_other_street_same_number_ignored(self):
        run = synthetic_run([("https://synthbakery.example/", ["Synth Bakery LLC, 100 Other Rd, Durham NC", "We roast our own coffee in the bakery."])])
        t = {"name": "Synth Bakery LLC", "addr": "100 Test Ave", "city": "Raleigh", "ref": "syntheticref0002"}
        p = E.project_run(run, t, {"elapsed_seconds": 5})["premises"][0]
        self.assertFalse(any(c["claim_type"] == "occupant_identity" for c in p["claims"]))

    def test_prospect_mapping_and_guard(self):
        pr = E.prospect_from({"name": "X Shop", "addr": "305 Church at North Hills St STE 900", "city": "Raleigh", "ref": "abcdef0123456789"})
        self.assertEqual((pr["address"]["number"], pr["address"]["suite"]), ("305", "Ste 900"))
        with self.assertRaises(Exception):
            E.prospect_from({"name": "Cafe 9000000123", "addr": "1 Test Ave", "city": "Raleigh", "ref": "abcdef0123456789"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
