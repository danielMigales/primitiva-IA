const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');

// Minimal DOM for testing the actual app load/render path without dependencies.
class Element {
 constructor(tag) { this.tagName=tag; this.children=[]; this.value=''; this.className=''; this.style={setProperty(){}}; this.classList={add:n=>{this.className+=' '+n}}; }
 set textContent(value) { this.value=String(value); this.children=[]; }
 get textContent() { return this.value+this.children.map(c=>c.textContent).join(' '); }
 appendChild(child) { this.children.push(child); return child; }
 append(...children) { children.forEach(c=>this.appendChild(c)); }
 replaceChildren(...children) { this.value=''; this.children=children; }
 querySelectorAll(selector) { return this.children.filter(c=>c.className.split(' ').includes('ball')&&!c.className.split(' ').includes('gold')); }
}
const entry = {target:'2026-10-15',nums:[4,10,20,22,40,45],historyUntil:'2026-10-12',reintegro:8};
const draw = {date:'2026-10-12',nums:[2,5,26,40,42,45],reintegro:9};
const activeConfig=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/reto-estrategia-activa.json'),'utf8'));
async function render(pred={predictions:[entry]}, history={draws:[draw]}, today='2026-10-13T20:00:00Z') {
 const elements=Object.fromEntries(['prediction','prediction-status','reasoning','recent-draws','draws-status','tracking','active-strategy'].map(id=>[id,new Element('div')]));
 class Clock extends Date { constructor(...args){super(...(args.length?args:[today]));} static now(){return Date.parse(today);} }
 const context=vm.createContext({document:{getElementById:id=>elements[id],createElement:tag=>new Element(tag)},Date:Clock,Intl,
  fetch:async url=>{const data=url.includes('estrategia-activa')?activeConfig:url.includes('sorteos')?history:pred; if(data instanceof Error)throw data; return {ok:true,json:async()=>data};}});
 vm.runInContext(source.replace('load().catch(', 'globalThis.loaded=load().catch('),context);
 await context.loaded;
 return {elements,context};
}
test('published data renders six numbers, reintegro and five draws',async()=>{
 const base=path.join(__dirname,'../data');
 const {elements}=await render(JSON.parse(fs.readFileSync(path.join(base,'reto-predictor.json'))),JSON.parse(fs.readFileSync(path.join(base,'sorteos.json'))));
 const latest=JSON.parse(fs.readFileSync(path.join(base,'reto-predictor.json'))).predictions.slice().sort((a,b)=>b.target.localeCompare(a.target))[0];
 assert.ok(elements['prediction-status'].textContent.includes(latest.target));
 assert.doesNotMatch(elements['prediction-status'].textContent,/Error/);
 assert.equal(elements['recent-draws'].children.length,5);
 assert.equal(elements.prediction.children[0].children.length,Number.isInteger(latest.reintegro)&&latest.reintegro>=0&&latest.reintegro<=9?8:6);
});
test('null root JSON does not crash the independent prediction panel',async()=>{
 const {elements}=await render(undefined,null);
 assert.match(elements['draws-status'].textContent,/No se ha podido cargar/);
 assert.doesNotMatch(elements['prediction-status'].textContent,/Error de carga/);
 const other=await render(null);
 assert.match(other.elements['prediction-status'].textContent,/No se pudo cargar/);
});
test('invalid numbers and impossible dates are excluded',async()=>{
 const invalid=[{...entry,target:'2026-10-99'},{...entry,target:'2026-10-20',nums:[1,1,1,1,1,1]},{...entry,target:'2026-10-21',nums:[1,2,3,4,5,'6']}];
 const {elements}=await render({predictions:[entry,...invalid]},{draws:[draw,{...draw,date:'2026-02-30'},{...draw,date:'2026-10-13',nums:[1,1,1,1,1,1]}]});
 assert.match(elements['prediction-status'].textContent,/2026-10-15/);
 assert.equal(elements['recent-draws'].children.length,1);
});
test('missing history is not reported as a pending draw',async()=>{
 const {elements}=await render(undefined,new Error('offline'));
 assert.match(elements['prediction-status'].textContent,/sin comprobar/);
 assert.doesNotMatch(elements.reasoning.textContent,/0 apariciones en 0 sorteos/);
});
test('past target missing from history is reported as unavailable',async()=>{
 const {elements}=await render(undefined,undefined,'2026-10-17T12:00:00Z');
 assert.match(elements['prediction-status'].textContent,/Resultado no disponible/);
});
test('Madrid date is used when UTC is still the previous day',async()=>{
 const {elements}=await render({predictions:[{...entry,target:'2026-10-13'}]},undefined,'2026-10-13T22:30:00Z');
 assert.match(elements['prediction-status'].textContent,/Resultado no disponible/);
});
test('malformed evidence does not crash or explain unrelated numbers',async()=>{
 const bad={...entry,numberEvidence:[null,{number:49,windows:[{days:30,hits:2,draws:4}]},{number:4,windows:[null,{days:30,hits:2,draws:4}]}],reintegroEvidence:{windows:{days:30}}};
 const {elements}=await render({predictions:[bad]});
 assert.doesNotMatch(elements['prediction-status'].textContent,/Error/);
 const cards=elements.reasoning.children[0].children.find(c=>c.className==='selection-reasons').children;
 assert.deepEqual(cards.map(c=>c.children[0].textContent),['4','10','20','22','40','45','8']);
});
test('weekly reintegro frequency excludes draws lacking reintegro',async()=>{
 const {context}=await render();
 context.input={entry,draws:[draw,{date:'2026-10-10',nums:draw.nums}]};
 const result=vm.runInContext('weeklyEvidence(input.entry,input.draws,8,true)',context);
 assert.equal(result.draws,1);
 assert.equal(result.hits,0);
});
test('settled prediction has correct main and reintegro hits',async()=>{
 const {elements}=await render({predictions:[{...entry,target:draw.date,reintegro:9}]});
 assert.match(elements.prediction.textContent,/2 de 6 números acertados · Reintegro acertado/);
});

test('tracking separates algorithms and counts failures and pending records',async()=>{
 const predictions=[
  {...entry,target:draw.date,algorithm:'pairs',window:50,nums:[1,3,4,6,7,8],reintegro:8},
  {...entry,algorithm:'recency',window:365}
 ];
 const {elements}=await render({predictions},undefined);
 const text=elements.tracking.textContent;
 assert.match(text,/2 predicciones registradas · 1 con resultado disponible · 1 sin resultado disponible/);
 assert.match(text,/pairs \/ ventana 50/);
 assert.match(text,/recency \/ ventana 365/);
 assert.match(text,/Aciertos principales: 0 · Sorteos con 3 o más: 0/);
 assert.match(text,/0 \/ 6 aciertos · Reintegro no acertado/);
 assert.match(text,/0.73 aciertos principales y 0.02 sorteos/);
});
test('tracking does not count duplicate targets or unavailable reintegros',async()=>{
 const prediction={...entry,target:draw.date,reintegro:null};
 const {context}=await render();
 context.input={entries:[prediction,prediction],draws:[draw]};
 const rows=vm.runInContext('trackingResults(input.entries,input.draws)',context);
 assert.equal(rows.length,1);
 assert.equal(rows[0].hits,2);
 assert.equal(rows[0].reintegro,null);
});
test('random reference is exact for six numbers out of 49',async()=>{
 const {context}=await render();
 assert.equal(vm.runInContext('choose(49,6)',context),13983816);
 const p=vm.runInContext('[3,4,5,6].reduce((s,k)=>s+choose(6,k)*choose(43,6-k)/choose(49,6),0)',context);
 assert.ok(Math.abs(p-260624/13983816)<1e-12);
});
test('tracking reports loading failures without inventing results',async()=>{
 const {elements}=await render(undefined,new Error('offline'));
 assert.match(elements.tracking.textContent,/0 con resultado disponible/);
 assert.match(elements.tracking.textContent,/No se puede comprobar el histórico/);
 const empty=await render({predictions:[]});
 assert.match(empty.elements.tracking.textContent,/Aún no hay predicciones válidas/);
});
test('active strategy version starts a separate sample from old recency records',async()=>{
 const {elements}=await render({predictions:[{...entry,target:draw.date,algorithm:activeConfig.strategy.algorithm,window:365}]});
 assert.match(elements['active-strategy'].textContent,/Versión 2/);
 const groups=elements.tracking.children.filter(c=>c.className==='tracking-group');
 const active=groups.find(c=>c.textContent.includes('/ versión 2'));
 const old=groups.find(c=>c.textContent.includes('registro anterior sin versión'));
 assert.match(active.textContent,/Seguimiento: 0 \/ 30/);
 assert.match(old.textContent,/Seguimiento: 1 \/ 30/);
});
