const {test}=require('node:test');const assert=require('node:assert/strict');const {app}=require('./harness.cjs');
const payload='<img src=x onerror=alert(1)>';
test('source metadata, claims, excerpts and identifiers are HTML escaped',()=>{
 const a=app();a.set('payload',payload);a.run(`S.accounts.x={id:'x',name:'Synthetic',addr:'100 Fictional Way'}; note('x').evidence=[{id:'" onclick="alert(1)',source:payload,claim:payload,detail:payload,dim:'business',basis:'observed'}]`);
 const out=a.run(`sourcesBody('x')`);assert.ok(!out.includes(payload));assert.ok(out.includes('&lt;img'));assert.ok(!out.includes('data-ev="" onclick='));
});
test('unsafe URL protocols, credentials, controls and relative URLs are rejected',()=>{
 const a=app();for(const url of ['javascript:alert(1)','JaVaScRiPt:alert(1)','data:text/html,x','//example.com','/relative','https://user:pass@example.com','https://example.com/\nfoo']){a.set('url',url);assert.equal(a.run('safeHttpUrl(url)'),'',url);}
 for(const url of ['https://example.com/a?x=1&y=2','http://example.com/']){a.set('url',url);assert.equal(a.run('safeHttpUrl(url)'),url);}
});
test('all source/profile render paths suppress unsafe links, preserve safe links',()=>{
 const a=app();a.run(`S.accounts.x={id:'x',name:'Synthetic'}; note('x').evidence=[];`);
 for(const link of ['javascript:alert(1)','data:text/html,evil','https://example.com/evidence']){
  a.set('link',link);a.run(`E={id:'e',source:'Synthetic',claim:'Finding',link,rel:'neutral',basis:'observed'};note('x').evidence=[E]`);
  for(const code of ["sourcesBody('x')","evidenceCard('x',E)","evidenceCard('x',{...E,disputed:{note:'Correction',at:'2026-11-15'}})","fieldHtml({status:'found',value:'Fact',source:'Synthetic',link})"]){const out=a.run(code);assert.equal(out.includes('href="'+link+'"'),link.startsWith('https:'),code);}
 }
});
test('legacy rendering escapes class attributes and visit numeric fields from backups',()=>{const a=app();a.set('payload',payload);assert.ok(!a.run(`visitCard('x',{result:'other',at:'2026-11-15',minutes:payload,gates:[]})`).includes(payload));assert.ok(!a.run(`evidenceCard('x',{id:'e',rel:'" onclick="evil',claim:'Synthetic'})`).includes('class="ev " onclick='));});
test('CSV blocks formulas including whitespace/control prefixes and preserves ordinary values',()=>{
 const a=app();for(const value of ['=1+1','+cmd','-1+2','@SUM(1)','  =1','\t=1','\r=1','\n=1']){a.set('value',value);const out=a.run('csvCell(value)');assert.ok(out.startsWith("'")||out.startsWith('"\''),JSON.stringify(value));}
 a.set('value','Synthetic, "Bakery"');assert.equal(a.run('csvCell(value)'),'"Synthetic, ""Bakery"""');assert.equal(a.run('csvCell(12.5)'),'12.5');
});
test('visit CSV uses protected encoding on imported business and notes',()=>{const a=app();a.run(`S.accounts.x={name:'=1+1',addr:'Synthetic'};note('x').visits=[{at:'2026-11-15',result:'other',notes:'@SUM(1)',gates:[]}];`);const out=a.run('visitsCSV()');assert.ok(out.includes("'=1+1"));assert.ok(out.includes("'@SUM(1)"));});

test('import counts restored from backups render as text',()=>{const a=app();a.set('payload',payload);a.run(`S.meta.lastImport={rows:payload,premises:1,shared:0};S.demo=false`);assert.ok(!a.run('viewAccounts()').includes(payload));});
