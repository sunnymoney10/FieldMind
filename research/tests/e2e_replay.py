"""End-to-end: app UI -> local server (real) -> worker replaced by a replay of the recorded live job -> engine
-> draft review -> save -> reload. Use where live search is unavailable. Run: python3 research/tests/e2e_replay.py [chrome]"""
import json, os, shutil, subprocess, sys, tempfile, threading
from pathlib import Path
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R)); sys.path.insert(0, str(R / "proof"))
import server  # noqa: E402

RECORDED = R / "runs" / "8ffec3dea0de4c7bbf5bf209aaf6fecd"
replay = Path(tempfile.mkdtemp()) / "replay_worker.py"
replay.write_text(f"""import os,shutil
src={str(RECORDED)!r};dst=os.environ['FIELDMIND_RUN_DIR']
for n in os.listdir(src):
    s=os.path.join(src,n)
    if n=='target.json': continue
    (shutil.copytree(s,os.path.join(dst,n),dirs_exist_ok=True) if os.path.isdir(s) else shutil.copy(s,dst))
""")
_Popen = subprocess.Popen
seen_targets = []


def fake_popen(args, **kw):  # only the worker launch is replaced; everything else in run_job is real
    if "FIELDMIND_TARGET_FILE" not in (kw.get("env") or {}):
        return _Popen(args, **kw)
    seen_targets.append(json.loads(Path(kw["env"]["FIELDMIND_TARGET_FILE"]).read_text()))
    return _Popen([sys.executable, str(replay)], **kw)


server.subprocess.Popen = fake_popen
runs_before = set(os.listdir(R / "runs"))
httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
port = httpd.server_port

CSV = ("Company Name,Service Address,City,State,ZIP,ZIP+4,Premise ID,Itron Account,Device Type,Energy Supplier,Prospect Status,Prospect Created,Street Number,Street Name,Other Names at Premise\n"
       "Videri Chocolate Factory,327 W Davie St,Raleigh,NC,27601,,9000000099,SYN0000099,SYNTH-DEV,DEP,New,2026-11-14 10:00,327,W Davie St,\n")

from playwright.sync_api import sync_playwright  # noqa: E402
out = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=sys.argv[1] if len(sys.argv) > 1 else "/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 390, "height": 844}); errors = []; bodies = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("request", lambda r: bodies.append(r.post_data) if r.method == "POST" and "/api/research" in r.url else None)
    pg.goto(f"http://127.0.0.1:{port}/"); pg.wait_for_timeout(800)
    rid = pg.evaluate("""csv=>{ startReal(); const rows=parseCSV(csv),map=guessMap(rows[0]); const m=mergeImport(S.accounts,rowsToAccounts(rows,map,'mimo','e2e'));
        S.accounts=m.accounts; Store.saveAll&&Store.saveAll(); const id=Object.keys(S.accounts).find(k=>S.accounts[k].name.startsWith('Videri')); openLiveResearch(id); return id; }""", CSV)
    pg.click("[data-act=beginresearch]")
    pg.wait_for_function("UI.liveResearch && ['complete','failed'].includes(UI.liveResearch.state)", timeout=60000)
    out["state"] = pg.evaluate("UI.liveResearch.state"); out["error"] = pg.evaluate("UI.liveResearch.error||''")
    sheet = pg.inner_text("body")
    out["sheet_shows_candidate"] = "Likely Videri Chocolate Factory" in sheet
    out["sheet_shows_suite_question"] = "Suite 100" in sheet
    pg.screenshot(path=str(R / "runs" / "e2e-replay-draft.png"), full_page=False)
    pg.click("[data-act=attachresearch]"); pg.wait_for_timeout(800)
    out["save_error"] = pg.evaluate("UI.liveResearch.error||''")
    out["saved_questions"] = pg.evaluate(f"(S.notes[{json.dumps(rid)}]?.brief?.questions||[]).length")
    out["saved_evidence"] = pg.evaluate(f"(S.notes[{json.dumps(rid)}]?.evidence||[]).length")
    out["occupant_after_save"] = pg.evaluate(f"S.notes[{json.dumps(rid)}]?.brief?.occupant")
    pg.reload(); pg.wait_for_timeout(1200)
    out["after_reload_questions"] = pg.evaluate(f"(()=>{{ const n=(S.notes||{{}})[{json.dumps(rid)}]; return n&&n.brief?(n.brief.questions||[]).length:null; }})()")
    out["page_errors"] = errors
    out["sent_fields"] = sorted(json.loads(bodies[0]).keys()) if bodies else None
    out["sent_has_ids"] = any(x in (bodies[0] or "") for x in ("9000000099", "SYN0000099", "SYNTH-DEV")) if bodies else None
    b.close()
httpd.shutdown()
out["worker_target"] = seen_targets[0] if seen_targets else None
for d in set(os.listdir(R / "runs")) - runs_before:  # remove this test's job folder
    if len(d) == 32:
        shutil.rmtree(R / "runs" / d, ignore_errors=True)
ok = (out["state"] == "complete" and out["sheet_shows_candidate"] and out["sheet_shows_suite_question"] and not out["save_error"]
      and out["saved_questions"] == 6 and out["saved_evidence"] >= 4 and (out["occupant_after_save"] or {}).get("status") == "unknown"
      and out["after_reload_questions"] == 6 and not out["page_errors"] and out["sent_fields"] == ["addr", "city", "name", "ref"] and out["sent_has_ids"] is False)
print(json.dumps(out, indent=1)); print("PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
