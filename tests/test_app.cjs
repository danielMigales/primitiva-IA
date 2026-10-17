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
 setAttribute(name,value) { (this.attributes??={})[name]=value; }
 querySelectorAll(selector) { return this.children.filter(c=>c.className.split(' ').includes('ball')&&!c.className.split(' ').includes('gold')); }
}
const entry = {target:'2026-10-15',nums:[4,10,20,22,40,45],historyUntil:'2026-10-12',reintegro:8};
const draw = {date:'2026-10-12',nums:[2,5,26,40,42,45],reintegro:9};
const activeConfig=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/reto-estrategia-v2.json'),'utf8'));
async function render(pred={predictions:[entry]}, history={draws:[draw]}, today='2026-10-13T20:00:00Z',proofs={draws:[]},report={status:'not-run'},live=null,config=activeConfig,model=null,control=null,quality=null) {
 const elements=Object.fromEntries(['decision-history','data-quality','model-control','model-learning','learning-review','sync-status','prediction','prediction-status','reasoning','recent-draws','draws-status','tracking','active-strategy','incidents'].map(id=>[id,new Element('div')]));
 class Clock extends Date { constructor(...args){super(...(args.length?args:[today]));} static now(){return Date.parse(today);} }
 const context=vm.createContext({document:{getElementById:id=>elements[id],createElement:tag=>new Element(tag)},Date:Clock,Intl,PrimitivaLive:live,PRIMITIVA_RESULTS_ENDPOINT:'https://results.example/api/resultados',
  fetch:async url=>{const data=url.includes('calidad-datos')?quality:url.includes('control-modelo')?control:url.includes('modelo-adaptativo')?model:url.includes('estrategia-activa')?config:url.includes('verificacion-sorteos')?proofs:url.includes('estado-actualizacion')?report:url.includes('sorteos')?history:pred; if(data instanceof Error)throw data; return {ok:true,json:async()=>data};}});
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

test('missing prediction warns only after the configured generation grace period',async()=>{
 const morning=await render({predictions:[]},undefined,'2026-10-14T10:00:00Z');
 assert.doesNotMatch(morning.elements.incidents.textContent,/Falta la predicción/);
 const afternoon=await render({predictions:[]},undefined,'2026-10-14T12:00:00Z');
 assert.match(afternoon.elements.incidents.textContent,/Falta la predicción para 2026-10-15/);
});
test('missing results allow the next morning update and use Madrid time',async()=>{
 const history={draws:[{...draw,date:'2026-10-10'}]};
 const early=await render(undefined,history,'2026-10-13T09:00:00Z');
 assert.doesNotMatch(early.elements.incidents.textContent,/Falta el resultado/);
 const late=await render(undefined,history,'2026-10-13T10:00:00Z');
 assert.match(late.elements.incidents.textContent,/Falta el resultado del 2026-10-12/);
});
test('official verification requires matching snapshots and has partial coverage',async()=>{
 const proof={...draw,source:'SELAE',checkedAt:'2026-10-13T10:00:00Z',url:'https://www.loteriasyapuestas.es/resultados'};
 const full=await render(undefined,undefined,undefined,{draws:[proof]});
 assert.match(full.elements['recent-draws'].textContent,/Números y reintegro cotejados con SELAE/);
 const partial=await render(undefined,undefined,undefined,{draws:[{...proof,reintegro:null}]});
 assert.match(partial.elements['recent-draws'].textContent,/Números cotejados; reintegro pendiente/);
 const conflict=await render(undefined,undefined,undefined,{draws:[{...proof,reintegro:8}]});
 assert.match(conflict.elements['recent-draws'].textContent,/Discrepancia con el cotejo SELAE/);
 const absent=await render();
 assert.match(absent.elements['recent-draws'].textContent,/Pendiente de cotejo SELAE/);
});
test('update report surfaces inaccessible sources and conflicts',async()=>{
 const unavailable=await render(undefined,undefined,undefined,undefined,{status:'unavailable',checkedAt:'2026-10-13T10:00:00Z'});
 assert.match(unavailable.elements.incidents.textContent,/no obtuvo resultados oficiales verificables/);
 const conflict=await render(undefined,undefined,undefined,undefined,{status:'conflict'});
 assert.match(conflict.elements.incidents.textContent,/discrepancia con SELAE/);
});
test('matched main numbers and reintegro are highlighted with accessible labels',async()=>{
 const {elements}=await render({predictions:[{...entry,target:draw.date,reintegro:9}]});
 const balls=elements.prediction.children[0].children;
 const hits=balls.filter(b=>b.className.split(' ').includes('hit'));
 assert.equal(hits.length,3);
 assert.deepEqual(hits.map(b=>b.attributes['aria-label']),['Número 40 acertado','Número 45 acertado','Reintegro 9 acertado']);
 assert.match(elements.prediction.textContent,/Resultado publicado/);
 assert.match(elements.prediction.textContent,/Pendiente de cotejo SELAE/);
});
test('pending prediction has no hit marks',async()=>{
 const {elements}=await render();
 assert.equal(elements.prediction.children[0].children.filter(b=>b.className.split(' ').includes('hit')).length,0);
});
test('historical predictions highlight only actual matches',async()=>{
 const prediction={...entry,target:draw.date,reintegro:8};
 const {elements}=await render({predictions:[entry,prediction]});
 const detail=elements.tracking.children.find(c=>c.tagName==='details');
 const past=detail.children.find(c=>c.className==='tracking-entry'&&c.textContent.includes(draw.date));
 const predicted=past.children.find(c=>c.className==='balls');
 assert.equal(predicted.children.filter(c=>c.className.split(' ').includes('hit')).length,2);
});

test('opening reads published history without calling the direct service',async()=>{
 const actual={date:entry.target,nums:[6,17,24,35,39,47],reintegro:3};
 let calls=0;
 const live={sync:async()=>{calls++;throw Error('Direct consultation must not run')}};
 const report={status:'confirmed',checkedAt:'2026-10-15T20:16:00Z'};
 const {elements}=await render(undefined,{draws:[actual,draw]},'2026-10-15T20:17:00Z',undefined,report,live);
 assert.equal(calls,0);
 assert.match(elements['sync-status'].textContent,/Última comprobación central/);
 assert.match(elements['sync-status'].textContent,/22:16/);
 assert.match(elements.prediction.textContent,/0 de 6 números acertados/);
 assert.equal(elements['recent-draws'].children.length,2);
});
test('a failed central check keeps published results and does not claim unpublished',async()=>{
 const report={status:'unavailable',checkedAt:'2026-10-13T12:00:00Z'};
 const {elements}=await render(undefined,undefined,undefined,undefined,report);
 assert.match(elements['sync-status'].textContent,/Mostrando los últimos resultados publicados/);
 assert.match(elements['sync-status'].textContent,/no pudo obtener resultados oficiales/);
 assert.equal(elements['recent-draws'].children.length,1);
 assert.doesNotMatch(elements['sync-status'].textContent,/aún no ha publicado/);
});
test('missing report timestamp does not invent a check date',async()=>{
 const {elements}=await render();
 assert.match(elements['sync-status'].textContent,/No se ha podido comprobar la fecha/);
});
test('a due draw missing from central data is shown as not incorporated',async()=>{
 const {elements}=await render(undefined,undefined,'2026-10-17T20:30:00Z');
 assert.match(elements['sync-status'].textContent,/2026-10-17 todavía no está incorporado/);
 assert.doesNotMatch(elements['sync-status'].textContent,/SELAE.*no ha publicado/);
});
test('HTML no longer loads the retired direct-query client',()=>{
 const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
 assert.doesNotMatch(html,/<script[^>]+(?:live-results|results-config)/);
 assert.match(html,/Actualizar resultados publicados/);
});

test('zero-hit review remains visible when the next prediction is displayed',async()=>{
 const old={...entry,algorithm:activeConfig.strategy.algorithm,strategyVersion:2};
 const actual={date:entry.target,nums:[6,17,24,35,39,47],reintegro:3};
 const next={...old,target:'2026-10-17',historyUntil:actual.date,nums:[6,10,20,22,40,45]};
 const {elements}=await render({predictions:[old,next]},{draws:[actual,draw]},'2026-10-15T20:30:00Z');
 assert.match(elements['prediction-status'].textContent,/2026-10-17/);
 const review=elements['learning-review'].textContent;
 assert.match(review,/2026-10-15: 0 de 6/);
 assert.match(review,/43.60 %/);
 assert.match(review,/No se ha demostrado una mejora/);
 assert.match(review,/1 \/ 30/);
 assert.match(review,/entran 6; salen 4/);
});
test('unversioned results are reviewed without being added to the active sample',async()=>{
 const {elements}=await render({predictions:[{...entry,target:draw.date}]});
 assert.match(elements['learning-review'].textContent,/0 \/ 30/);
 assert.doesNotMatch(elements['learning-review'].textContent,/43.60/);
 assert.match(elements['learning-review'].textContent,/Siguiente predicción pendiente/);
});

test('adaptive training report distinguishes learned weights and historical evaluation',async()=>{
 const config=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/reto-estrategia-activa.json')));
 const model=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/modelo-adaptativo.json')));
 const {elements}=await render(undefined,undefined,undefined,undefined,undefined,null,config,model);
 assert.match(elements['active-strategy'].textContent,/evaluación previa/);
 assert.match(elements['model-learning'].textContent,/→/);
 assert.match(elements['model-learning'].textContent,/exploratoria/);
 assert.match(elements['model-learning'].textContent,/no demuestra/);
 assert.doesNotMatch(elements['prediction-status'].textContent,/No se ha podido cargar/);
});
test('adaptive prediction explains model scores and safely handles missing report',async()=>{
 const config=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/reto-estrategia-activa.json')));
 const adaptive={...entry,algorithm:'online-logistic-v1',strategyVersion:3,numberEvidence:[{number:4,estimatedScore:.13}]};
 const {elements}=await render({predictions:[adaptive]},undefined,undefined,undefined,undefined,null,config,{});
 assert.match(elements.reasoning.textContent,/13.00 %/);
 assert.match(elements['model-learning'].textContent,/no está disponible/);
});

test('promotion control shows prospective progress and preserves active weights',async()=>{
 const config=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/reto-estrategia-activa.json')));
 const control=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/control-modelo.json')));
 const {elements}=await render(undefined,undefined,undefined,undefined,undefined,null,config,null,control);
 assert.match(elements['model-control'].textContent,/Esperando un nuevo resultado/);
 assert.match(elements['model-control'].textContent,/no autorizan cambios/);
 const collecting={...control,assessment:{status:'collecting',draws:12},decisions:[{status:'rejected',reason:'No supera los controles.'}]};
 const other=await render(undefined,undefined,undefined,undefined,undefined,null,config,null,collecting);
 assert.match(other.elements['model-control'].textContent,/12 \/ 60/);
 assert.match(other.elements['model-control'].textContent,/rechazado/);
});

test('data quality distinguishes missing internal draws from pending publications',async()=>{
 const quality={version:1,valid:false,total:3001,latestDate:'2026-10-15',fullyVerifiedDraws:320,errors:[],missingRecentDates:['2026-10-12'],pendingDates:['2026-10-17'],checkedAt:'2026-10-17'};
 const {elements}=await render(undefined,undefined,undefined,undefined,undefined,null,activeConfig,null,null,quality);
 assert.match(elements['data-quality'].textContent,/Entrenamiento detenido/);
 assert.match(elements['data-quality'].textContent,/2026-10-12/);
 assert.match(elements['data-quality'].textContent,/no determina si SELAE/);
 assert.match(elements['data-quality'].textContent,/320 \/ 3001/);
});
test('decision history retains accepted and rejected outcomes',async()=>{
 const control={version:1,decisions:[{epoch:1,decidedAfter:'2026-10-15',status:'rejected',reason:'Sin mejora',draws:60},{epoch:2,decidedAfter:'2026-10-17',status:'accepted',reason:'Mejora consistente',draws:60}]};
 const {elements}=await render(undefined,undefined,undefined,undefined,undefined,null,activeConfig,null,control);
 assert.match(elements['decision-history'].textContent,/Aceptado/);
 assert.match(elements['decision-history'].textContent,/Rechazado/);
 assert.match(elements['decision-history'].textContent,/Sin mejora/);
});

test('latest draw balance shows only the matching training adjustment',async()=>{
 const config=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/reto-estrategia-activa.json')));
 const training={lastUpdates:[{date:'2026-10-15',weightsBefore:[0,0,0,0],weightsAfter:[.1,0,0,0]}]};
 const {elements}=await render({predictions:[entry]},{draws:[{...draw,date:'2026-10-15'}]},undefined,undefined,undefined,null,config,training);
 assert.match(elements['learning-review'].textContent,/0.10000/);
 assert.match(elements['learning-review'].textContent,/reproducción cronológica/);
 assert.match(elements['learning-review'].textContent,/sujetos al control/);
});
