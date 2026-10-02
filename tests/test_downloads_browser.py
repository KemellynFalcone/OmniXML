"""Exercise batch behavior without contacting SEFAZ or loading certificates."""
import shutil
import subprocess
from pathlib import Path

import pytest


def test_batch_keeps_only_complete_xml_and_stops_on_cooldown():
    if not shutil.which('node'):
        pytest.skip('Node unavailable')
    source = r'''
const fs = require('fs'); const vm = require('vm'); const assert = require('assert');
class Element {
  constructor(){ this.children=[]; this.events={}; this.value=''; this.files=[]; this.disabled=false; this.textContent=''; }
  addEventListener(name,fn){this.events[name]=fn;}
  append(...items){this.children.push(...items);}
  replaceChildren(...items){this.children=items;}
  reportValidity(){return true;}
  click(){}
}
const ids=['certificate','password','token','uf','keys','results','progress','availability','download','status','complete','original','clear','stop','zip','recovery-form'];
const els=Object.fromEntries(ids.map(id=>[id,new Element()]));
els.certificate.files=[new Blob(['SYNTHETIC'])]; els.uf.value='SP';
els.keys.value='1'.repeat(44)+'\n'+'2'.repeat(44)+'\n'+'3'.repeat(44)+'\n'+'4'.repeat(44);
let calls=0,zipNames=[];
class Zip { file(name,blob){zipNames.push(name);} async generateAsync(){return new Blob(['ZIP']);} }
const responseHeaders={get(name){return name==='X-SEFAZ-cStat' ? '100' : encodeURIComponent('<untrusted>');}};
const context={console,Blob,Map,Set,FormData,URL:{createObjectURL:()=> 'blob:test',revokeObjectURL:()=>{}},JSZip:Zip,
 document:{getElementById:id=>els[id],createElement:()=>new Element()},window:{addEventListener:()=>{}},
 fetch:async path=>{
  if(path.endsWith('capabilities')) return {json:async()=>({enabled:true})};
  calls++;
  if(calls===1) return {ok:true,headers:responseHeaders,blob:async()=>new Blob(['<nfeProc/>'])};
  if(calls===2) return {ok:false,status:422,json:async()=>({error:'Resumo sem XML',code:'summary'})};
  return {ok:false,status:422,json:async()=>({error:'Pausa',code:'656',stop_batch:true})};
 }};
vm.runInNewContext(fs.readFileSync('static/downloads.js','utf8'),context);
(async()=>{
 els['recovery-form'].events.submit({preventDefault(){}});
 for(let i=0;i<30;i++) await Promise.resolve();
 assert.strictEqual(calls,3,'cooldown must stop before fourth key');
 assert.strictEqual(els.results.children.length,3);
 assert.strictEqual(els.results.children[0].children[1].textContent,'100 · <untrusted>');
 assert.strictEqual(els.results.children[1].children[2].children.length,0);
 assert.strictEqual(els.zip.disabled,false);
 await els.zip.events.click();
 assert.deepStrictEqual(zipNames,['1'.repeat(44)+'-procNFe.xml']);
 assert.strictEqual(els.download.disabled,false);
})().catch(error=>{console.error(error);process.exitCode=1;});
'''
    subprocess.run(['node','-e',source],cwd=Path(__file__).resolve().parents[1],check=True,capture_output=True,text=True)


def test_portal_recovery_needs_no_certificate_and_does_not_send_key_to_backend():
    if not shutil.which('node'):
        pytest.skip('Node unavailable')
    source = r'''
const fs = require('fs'), vm = require('vm'), assert = require('assert');
class Element {
 constructor(){this.children=[];this.events={};this.value='';this.files=[];this.disabled=false;this.textContent='';}
 addEventListener(name,fn){this.events[name]=fn;}
 append(...items){this.children.push(...items);}
 replaceChildren(...items){this.children=items;}
 reportValidity(){throw Error('Portal route must not require a certificate');}
 click(){}
}
const ids=['certificate','password','token','uf','keys','results','progress','availability','download','status','complete','original','clear','stop','zip','recovery-form'];
const els=Object.fromEntries(ids.map(id=>[id,new Element()]));
const key='52'+'2609'+'12345678000195'+'65'+'002'+'000029794'+'1'+'00114687'+'0';
els.keys.value=key;
let copied='', fiscalCalls=0;
const guidance={uf:'GO',mode:'portal',title:'Portal Goiás',description:'Use certificado no portal.',url:'https://nfeweb.sefaz.go.gov.br/nfeweb/sites/nfe/consulta-publica/principal',link_label:'Abrir recuperação'};
const context={console,Blob,Map,Set,FormData,URL:{createObjectURL:()=> 'blob:test',revokeObjectURL:()=>{}},
 navigator:{clipboard:{writeText:async text=>{copied=text;}}},
 document:{getElementById:id=>els[id],createElement:()=>new Element()},window:{addEventListener:()=>{}},
 fetch:async path=>{if(path.endsWith('capabilities'))return {json:async()=>({enabled:true,recovery_paths:{'52':guidance}})};fiscalCalls++;throw Error('Unexpected fiscal upload');}};
vm.runInNewContext(fs.readFileSync('static/downloads.js','utf8'),context);
(async()=>{
 els['recovery-form'].events.submit({preventDefault(){}});
 for(let i=0;i<30;i++)await Promise.resolve();
 assert.strictEqual(fiscalCalls,0);
 const cells=els.results.children[0].children;
 assert.ok(cells[1].textContent.includes('Portal Goiás'));
 assert.strictEqual(cells[2].children[0].href,guidance.url);
 assert.strictEqual(cells[2].children[0].rel,'noopener noreferrer');
 await cells[2].children[1].events.click();assert.strictEqual(copied,key);
 assert.strictEqual(els.zip.disabled,true,'Portal guidance is not an XML file');
 assert.strictEqual(els.download.disabled,false);
})().catch(error=>{console.error(error);process.exitCode=1;});
'''
    subprocess.run(['node','-e',source],cwd=Path(__file__).resolve().parents[1],check=True,capture_output=True,text=True)
