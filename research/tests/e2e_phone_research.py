"""Phone research flow, end to end in the real app with an in-memory stand-in for the artifact database.
queue (app) -> result written the way Claude writes it -> banner -> review -> add -> cleanup. No MIMO data."""
import json, re, shutil, sys, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
R = Path(__file__).resolve().parents[1]; APP = R.parent / "index.html"
sys.path.insert(0, str(R)); import engine_adapter as E  # noqa: E402

FAKE_DB = r"""
(()=>{ const store=new Map(), subs=[];
  const snapOf=(col)=>({docs:[...store.entries()].filter(([k])=>k.startsWith(col+"/")&&!k.slice(col.length+1).includes("/")).map(([k,v])=>({id:k.split("/").pop(),exists:true,data:()=>JSON.parse(JSON.stringify(v))})), get empty(){return this.docs.length===0}});
  const notify=()=>subs.forEach(([col,cb])=>cb(snapOf(col)));
  const doc=(path)=>({ async get(){ const v=store.get(path); return {exists:v!==undefined, data:()=>JSON.parse(JSON.stringify(v||{}))}; },
    async set(v){ store.set(path,JSON.parse(JSON.stringify(v))); notify(); }, async delete(){ store.delete(path); notify(); },
    collection:(c)=>col(path+"/"+c) });
  const col=(path)=>({ doc:(id)=>doc(path+"/"+id), async get(){ return snapOf(path); }, onSnapshot(cb){ subs.push([path,cb]); cb(snapOf(path)); return ()=>{}; } });
  const db={doc, collection:col};
  window.__fakeStore=store; window.__notify=notify;
  window.claude={ use: async (n)=> n==="db"?db : n==="user"?{id:async()=>"u_test"} : null };
})();"""

CSV = ("Company Name,Service Address,City,State,ZIP,ZIP+4,Premise ID,Itron Account,Device Type,Energy Supplier,Prospect Status,Prospect Created,Street Number,Street Name,Other Names at Premise\n"
       "Videri Chocolate Factory,327 W DAVIE ST,Raleigh,NC,27601,,9000000099,SYN0000099,SYNTH-DEV,DEP,New,2026-11-14 10:00,327,W DAVIE ST,\n"
       "Example DNC Shop,1 FICTIONAL PL,Raleigh,NC,27601,,9000000098,SYN0000098,SYNTH-DEV,DEP,Do Not Contact,2026-11-14 10:00,1,FICTIONAL PL,\n")

run = Path(tempfile.mkdtemp()) / "j"; shutil.copytree(R / "runs" / "8ffec3dea0de4c7bbf5bf209aaf6fecd", run)
out = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=sys.argv[1] if len(sys.argv) > 1 else "/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 390, "height": 844}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(FAKE_DB)
    pg.goto("file://" + str(APP)); pg.wait_for_function("Store.mode==='cloud'", timeout=15000)
    vid = pg.evaluate("""async csv=>{ startReal(); const rows=parseCSV(csv),map=guessMap(rows[0]); const m=mergeImport(S.accounts,rowsToAccounts(rows,map,'mimo','b1')); S.accounts=m.accounts; await Store.saveAccounts(); render();
        return Object.keys(S.accounts).find(k=>S.accounts[k].name.startsWith('Videri')); }""", CSV)
    ref = pg.evaluate(f"()=>refOf('{vid}')")
    # 1. queue from the center button: two taps
    pg.click("[data-act=briefme]"); pg.wait_for_timeout(200); pg.click("[data-act=queuenext]"); pg.wait_for_timeout(300)
    q = pg.evaluate("()=>window.__fakeStore.get('research/queue')")
    out["queued"] = len(q["items"]); out["queue_fields"] = sorted(q["items"][0].keys())
    out["queue_has_ids"] = bool(re.search(r"9000000099|SYN0000099|SYNTH-DEV|9000000098", json.dumps(q)))
    out["suppressed_queued"] = any("Fictional" in x["addr"].title() for x in q["items"])
    out["open_claude_link"] = pg.locator("a[href^='https://claude.ai/new']").count() == 1
    pg.click("#sheet [aria-label='Close'], #sheetClose", timeout=2000) if pg.locator("#sheetClose").count() else pg.evaluate("()=>{UI.sheet=null;document.querySelector('#sheet').hidden=true;render();}")
    # 2. Claude writes results (one valid, one for a business not on the list)
    good = E.project_run(run, {"name": "Videri Chocolate Factory", "addr": "327 W Davie St", "city": "Raleigh", "ref": ref}, json.load(open(run / "summary.json")))
    stranger = {"fieldmind_research": 1, "generated": "2026-11-15T00:00:00Z", "accounts": [{"match": {"ref": "rzzzzzz", "name": "Somewhere Else"}, "researchedAt": "2026-11-15T00:00:00Z",
                "story": {"summary": "Older-format result for a business not on the list."}, "askFirst": "Not on the list.", "evidence": []}]}
    pg.evaluate("""([ref,good,stranger])=>{ window.__fakeStore.set('research/result_'+ref,{ref,at:'2026-11-15',research:good});
        window.__fakeStore.set('research/result_rzzzzzz',{ref:'rzzzzzz',at:'2026-11-15',research:stranger}); window.__notify(); }""", [ref, good, stranger])
    pg.click("nav.tabs button[data-tab=route]"); pg.wait_for_timeout(200)
    out["banner"] = pg.locator(".inbox-banner").inner_text().replace("\n", " ") if pg.locator(".inbox-banner").count() else None
    pg.screenshot(path=str(R / "runs" / "phone-banner.png"))
    # 3. review and add: two taps
    pg.click(".inbox-banner"); pg.wait_for_timeout(200)
    out["review_text"] = pg.inner_text("#sheetBody")[:300]
    pg.screenshot(path=str(R / "runs" / "phone-review.png"))
    pg.click("[data-act=acceptinbox]"); pg.wait_for_timeout(800)
    out["report"] = pg.inner_text("#sheetBody")[:200].replace("\n", " ")
    out["brief_questions"] = pg.evaluate(f"()=>(S.notes['{vid}']?.brief?.questions||[]).length")
    out["accounts_after"] = pg.evaluate("()=>Object.keys(S.accounts).length")
    out["results_left"] = pg.evaluate("()=>[...window.__fakeStore.keys()].filter(k=>k.startsWith('research/result_')).length")
    out["queue_left"] = len(pg.evaluate("()=>window.__fakeStore.get('research/queue').items"))
    out["note_saved_to_cloud"] = pg.evaluate(f"()=>!!window.__fakeStore.get('data/users/u_test/workspace/notes/{vid}')")
    out["banner_after"] = pg.locator(".inbox-banner").count()
    out["errors"] = errs
    b.close()
ok = (out["queued"] == 1 and out["queue_fields"] == ["addr", "city", "name", "ref", "zip"] and not out["queue_has_ids"] and not out["suppressed_queued"]
      and out["open_claude_link"] and out["banner"] and "2 new briefs" in out["banner"] and out["brief_questions"] == 6 and out["accounts_after"] == 2
      and out["results_left"] == 0 and out["queue_left"] == 0 and out["note_saved_to_cloud"] and out["banner_after"] == 0 and not out["errors"])
print(json.dumps(out, indent=1)); print("PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
