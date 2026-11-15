#!/usr/bin/env python3
"""FieldMind pilot helper. Runs on YOUR computer; the list never leaves it.

  python3 pilot/pilot.py prepare <brian_list.csv> <out_dir> [--only REF,REF] [--limit N]
      One run folder per premise with prospect.json holding only: ref, listed name, address and suite.
      Premise IDs, account numbers and device fields are not written. Suppressed or ineligible rows are skipped.
      A history note from older listed names is passed as list_context (names only).
  python3 pilot/pilot.py merge <out_dir> <research_file.json>
      Combines every run's research.v2.json into one file to import in FieldMind.
  python3 pilot/pilot.py summary <out_dir>
      Time, failures and claim counts across runs (for Experiment 001).
"""
import csv, json, os, re, sys, argparse, datetime as dt

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "worker"))
import fmworker as W  # noqa: E402

SUPPRESS_RE = re.compile(r"suppress|do\s*not|dnc|reject|inelig|remove|hold|exclude", re.I)  # same rule as the app


def fnv(s):
    h = 2166136261
    for ch in s:
        h ^= ord(ch); h = (h * 16777619) & 0xFFFFFFFF
    d = "0123456789abcdefghijklmnopqrstuvwxyz"; out = ""
    if h == 0:
        return "0"
    while h:
        out = d[h % 36] + out; h //= 36
    return out


def ref_of(premise_id):
    """Same code the app puts in research requests: r + fnv("fm:a-<premise>")[:6]."""
    return "r" + fnv("fm:a-" + str(premise_id).strip())[:6]


def col(row, *names):
    low = {k.strip().lower(): v for k, v in row.items() if k}
    for n in names:
        v = low.get(n.lower())
        if v not in (None, ""):
            return v.strip()
    return ""


SUITE_RE = re.compile(r"\b(?:STE|SUITE|UNIT|APT|#)\s*\.?\s*([0-9A-Z-]+)\b", re.I)


def split_address(service_address, number, street):
    s = service_address or f"{number} {street}"
    m = SUITE_RE.search(s)
    suite = f"Ste {m.group(1)}" if m else None
    base = s[:m.start()].strip(" ,") if m else s.strip()
    num = number or (base.split()[0] if base.split() and base.split()[0][0].isdigit() else "")
    st = street or base[len(num):].strip()
    return num, st.title(), suite


def prepare(csv_path, out_dir, only=None, limit=None):
    rows = list(csv.DictReader(open(csv_path, newline="", encoding="utf-8-sig")))
    by_premise = {}
    for r in rows:
        pid = col(r, "Premise ID", "Premise", "PremiseID")
        if pid:
            by_premise.setdefault(pid, []).append(r)
    made, skipped = [], []
    for pid, rs in by_premise.items():
        ref = ref_of(pid)
        if only and ref not in only:
            continue
        if any(SUPPRESS_RE.search(col(r, "Prospect Status", "Status")) for r in rs):
            skipped.append({"ref": ref, "reason": "suppressed or ineligible on the list"}); continue
        rs.sort(key=lambda r: col(r, "Prospect Created", "Created"), reverse=True)
        newest = rs[0]
        num, street, suite = split_address(col(newest, "Service Address", "Address"), col(newest, "Street Number"), col(newest, "Street Name"))
        names = []
        for r in rs:
            n = col(r, "Company Name", "Name")
            if n and n not in names:
                names.append(n)
        p = {"ref": ref, "listed_name": names[0] if names else "", "synthetic": False,
             "address": {"number": num, "street": street, "suite": suite, "city": col(newest, "City").title(),
                         "state": col(newest, "State"), "zip": col(newest, "ZIP", "Zip")[:5]}}
        if len(names) > 1:
            p["list_context"] = {"listed_names_historical": names[1:]}
        try:
            W.check_prospect(p)  # same guard the worker uses; refuses anything ID-like
        except W.IntakeError as e:
            skipped.append({"ref": ref, "reason": f"intake guard: {e}"}); continue
        d = os.path.join(out_dir, ref)
        os.makedirs(d, exist_ok=True)
        json.dump(p, open(os.path.join(d, "prospect.json"), "w"), indent=1)
        json.dump(W.plan(p), open(os.path.join(d, "plan.json"), "w"), indent=1)
        made.append(ref)
        if limit and len(made) >= limit:
            break
    json.dump({"prepared": made, "skipped": skipped, "at": W.now_iso()}, open(os.path.join(out_dir, "prepare-log.json"), "w"), indent=1)
    return made, skipped


def merge(out_dir, dest):
    premises, runs = [], {"minutes": 0, "searches": 0, "pages_read": 0}
    for ref in sorted(os.listdir(out_dir)):
        f = os.path.join(out_dir, ref, "research.v2.json")
        if os.path.isfile(f):
            r = json.load(open(f))
            premises += r["premises"]
            for k in runs:
                runs[k] += r.get("run", {}).get(k, 0) or 0
    out = {"schema": "fieldmind.research", "version": 2, "generated": W.now_iso(), "researcher": "fmworker-prototype", "run": runs, "premises": premises}
    json.dump(out, open(dest, "w"), indent=1)
    return len(premises)


def summary(out_dir):
    rows = []
    for ref in sorted(os.listdir(out_dir)):
        f = os.path.join(out_dir, ref, "run-report.json")
        if os.path.isfile(f):
            r = json.load(open(f))
            rows.append({"ref": ref, "seconds": r["timing"]["elapsed_seconds"], "within_cap": r["timing"]["within_cap"],
                         "failures": len(r["retrieval"]["failures"]), "accepted": r["claims"]["accepted"],
                         "rejected": len(r["claims"]["rejected"]), "unresolved": len(r["unresolved_questions"])})
    secs = sorted(x["seconds"] for x in rows if x["seconds"])
    med = secs[len(secs) // 2] if secs else None
    return {"runs": rows, "count": len(rows), "median_seconds": med, "over_cap": sum(not x["within_cap"] for x in rows)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("prepare"); s.add_argument("csv"); s.add_argument("out_dir"); s.add_argument("--only"); s.add_argument("--limit", type=int)
    s = sub.add_parser("merge"); s.add_argument("out_dir"); s.add_argument("dest")
    s = sub.add_parser("summary"); s.add_argument("out_dir")
    a = ap.parse_args()
    if a.cmd == "prepare":
        made, skipped = prepare(a.csv, a.out_dir, set(a.only.split(",")) if a.only else None, a.limit)
        print(json.dumps({"prepared": len(made), "skipped": skipped}, indent=1))
    elif a.cmd == "merge":
        print(f"{merge(a.out_dir, a.dest)} premises written to {a.dest}")
    else:
        print(json.dumps(summary(a.out_dir), indent=1))


if __name__ == "__main__":
    main()
