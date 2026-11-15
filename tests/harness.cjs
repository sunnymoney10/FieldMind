const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const html=fs.readFileSync(process.env.FIELDMIND_TEST_HTML || path.join(__dirname,'../index.html'),'utf8');
function app(){
  const listeners={};
  const context=vm.createContext({URL,console,document:{querySelectorAll(){return [];},querySelector(){return {addEventListener(){}};},addEventListener(type,fn){listeners[type]=fn;}},setTimeout,clearTimeout});
  // Evaluate the actual production script, stopping only its side-effectful boot.
  const script=html.match(/<script>([\s\S]*?)<\/script>/)[1].split('/* ============ Boot ============ */')[0];
  vm.runInContext(script,context);
  return {run:code=>vm.runInContext(code,context),set:(name,value)=>{context[name]=value;},listeners};
}
module.exports={app,html};
