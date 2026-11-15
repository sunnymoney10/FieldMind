"""Pilot helper tests on the synthetic fixture list only."""
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "pilot"))
import pilot as P  # noqa: E402

FX = os.path.join(HERE, "fixtures", "fx_list.csv")


class Prepare(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.made, self.skipped = P.prepare(FX, self.d)

    def test_one_folder_per_premise_and_suppressed_skipped(self):
        self.assertEqual(len(self.made), 3)
        self.assertEqual([s["ref"] for s in self.skipped], [P.ref_of("9000000003")])

    def test_ref_matches_app(self):
        self.assertEqual(P.ref_of("9000000004"), "r1mvlv0")  # value the app computes (see worker tests)

    def test_no_identifiers_written(self):
        blob = ""
        for root, _, files in os.walk(self.d):
            for f in files:
                blob += open(os.path.join(root, f)).read()
        for bad in ("9000000001", "9000000002", "9000000004", "DUK900000", "IntelliTemp", "Sensi"):
            self.assertNotIn(bad, blob)

    def test_suite_and_history(self):
        p = json.load(open(os.path.join(self.d, P.ref_of("9000000002"), "prospect.json")))
        self.assertEqual(p["address"]["suite"], "Ste 2")
        self.assertEqual(p["address"]["number"], "200")
        self.assertEqual(p["listed_name"], "FIXTURE New Tenant Bakery LLC")
        self.assertEqual(p["list_context"]["listed_names_historical"], ["FIXTURE Old Tenant Cafe LLC"])

    def test_limit_and_only(self):
        d = tempfile.mkdtemp()
        made, _ = P.prepare(FX, d, only={P.ref_of("9000000004")})
        self.assertEqual(made, [P.ref_of("9000000004")])
        d = tempfile.mkdtemp()
        made, _ = P.prepare(FX, d, limit=1)
        self.assertEqual(len(made), 1)


class Merge(unittest.TestCase):
    def test_merge_live_run(self):
        d = tempfile.mkdtemp()
        os.symlink(os.path.join(HERE, "..", "runs", "live-001"), os.path.join(d, "r1kedpv"))
        out = os.path.join(d, "merged.json")
        self.assertEqual(P.merge(d, out), 1)
        s = P.summary(d)
        self.assertEqual(s["count"], 1)
        self.assertTrue(s["runs"][0]["within_cap"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
