"""Import the worker's research.v2.json into an isolated copy of the app (not the live artifact)."""
import asyncio, json, os, sys
import jsonschema
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
RUN = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "runs", "live-001")
research = json.load(open(os.path.join(RUN, "research.v2.json")))
schema = json.load(open(os.path.join(ROOT, "reference", "research.v2.schema.json")))
errs = [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(research)]
# Synthetic one-row list: a public test business with a made-up premise ID. Not Brian's data.
CSV = ("Company Name,Service Address,City,State,ZIP,ZIP+4,Premise ID,Itron Account,Device Type,Energy Supplier,Prospect Status,Prospect Created,Street Number,Street Name,Other Names at Premise\n"
       "Videri Chocolate Factory,327 W DAVIE ST,Raleigh,NC,27601,,9000000099,SYN0000099,,DEP,New,2026-11-14 10:00,327,W DAVIE ST,\n")
JS = r"""([csv, res]) => { startReal();
  const rows=parseCSV(csv), map=guessMap(rows[0]); const inc=rowsToAccounts(rows,map,'mimo','btx');
  const m=mergeImport(S.accounts,inc); S.accounts=m.accounts;
  const v=validateResearch(res); if(!v.ok) return {ok:false, errors:v.errors};
  const r=applyResearch(v,S.accounts,S.notes); const id='a-9000000099';
  UI.briefTab='overview'; const hero=accountBody(id); openSources && (UI.srcFilter='all'); const src=sourcesBody(id);
  return {ok:true, warnings:v.warnings, matched:r.matched, unmatched:r.unmatched, label:readiness(id),
          heroHasOccupant: hero.includes('Videri'), heroHasFindOut: hero.includes('Suite 100'), sourceLinks:(src.match(/href="https?:/g)||[]).length,
          premiseIdShown: (hero+src).replace(/data-id="[^"]*"/g,'').includes('9000000099')}; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = await b.new_page(); pe = []; pg.on("pageerror", lambda e: pe.append(str(e)))
        await pg.goto("file://" + os.path.abspath(os.path.join(ROOT, "reference", "app-copy.html"))); await pg.wait_for_timeout(600)
        r = await pg.evaluate(JS, [CSV, research]); await b.close()
    print(json.dumps({"schema_errors": errs, "app": r, "page_errors": pe}, indent=1, default=str))
    ok = not errs and r.get("ok") and r["label"].get("t") != "Not researched" and r.get("matched") == 1 and r.get("heroHasOccupant") and r.get("sourceLinks", 0) > 0 and not r.get("premiseIdShown") and not pe
    print("PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
asyncio.run(main())
