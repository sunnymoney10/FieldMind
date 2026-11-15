"""Import test list 001 and its merged research into an isolated app copy; report what the app shows."""
import asyncio, json, os, sys
import jsonschema
from playwright.async_api import async_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
csv = open(os.path.join(ROOT, "testlist", "test_list_001.csv")).read()
research = json.load(open(os.path.join(ROOT, "testlist", "test-research-001.json")))
schema = json.load(open(os.path.join(ROOT, "reference", "research.v2.schema.json")))
errs = [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(research)]
JS = r"""([csv, res]) => { startReal();
  const rows=parseCSV(csv), map=guessMap(rows[0]); const inc=rowsToAccounts(rows,map,'mimo','bt1');
  const m=mergeImport(S.accounts,inc); S.accounts=m.accounts;
  const before=JSON.stringify(Object.values(S.accounts).map(a=>[a.id,!!a.suppressed,a.list]));
  const v=validateResearch(res); if(!v.ok) return {ok:false, errors:v.errors};
  const r=applyResearch(v,S.accounts,S.notes);
  const after=JSON.stringify(Object.values(S.accounts).map(a=>[a.id,!!a.suppressed,a.list]));
  const out={}; for(const id of Object.keys(S.accounts)){ const a=S.accounts[id]; UI.briefTab='overview';
    const h=accountBody(id).replace(/<[^>]+>/g,' ').replace(/\s+/g,' ');
    out[a.name||id]={label:readiness(id).t, suppressed:!!a.suppressed, occupant:(S.notes[id]&&S.notes[id].occupant)||null, text:h.slice(0,400)}; }
  return {ok:true, matched:r.matched, unmatched:r.unmatched, listUnchanged: before===after, premises:out}; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = await b.new_page(); pe = []; pg.on("pageerror", lambda e: pe.append(str(e)))
        await pg.goto("file://" + os.path.abspath(os.path.join(ROOT, "reference", "app-copy.html"))); await pg.wait_for_timeout(600)
        r = await pg.evaluate(JS, [csv, research]); await b.close()
    json.dump({"schema_errors": errs, "app": r, "page_errors": pe}, open(os.path.join(ROOT, "testlist", "app-import-result.json"), "w"), indent=1)
    print(json.dumps({"schema_errors": errs, "matched": r.get("matched"), "listUnchanged": r.get("listUnchanged"), "page_errors": pe,
                      "labels": {k: (v["label"], v["suppressed"], v["occupant"]) for k, v in r.get("premises", {}).items()}}, indent=1))
asyncio.run(main())
