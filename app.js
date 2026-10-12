const $=id=>document.getElementById(id);let draws=[];const choose=(n,k)=>{let x=1;for(let i=1;i<=k;i++)x=x*(n-i+1)/i;return x};const expPair=15/choose(49,2),expTriple=20/choose(49,3);function parse(text){let out=[],seen=new Set();for(const line of text.split(/\r?\n/)){let d=line.match(/(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})/);if(!d)continue;let iso=`${d[3]}-${d[2].padStart(2,'0')}-${d[1].padStart(2,'0')}`;if(!Number.isFinite(Date.parse(iso)))continue;let rest=line.slice(d.index+d[0].length);let nums=(rest.match(/\d+/g)||[]).map(Number);if(nums.length<6)continue;let a=nums.slice(0,6);if(a.some(x=>x<1||x>49)||new Set(a).size!==6)continue;if(seen.has(iso))continue;seen.add(iso);out.push({date:iso,nums:a.sort((a,b)=>a-b)})}return out.sort((a,b)=>a.date.localeCompare(b.date))}function setDraws(rows,source){draws=rows;$('status').textContent=`${rows.length} sorteos válidos cargados de ${source}. Rango: ${rows[0]?.date||'—'} a ${rows.at(-1)?.date||'—'}. Comprueba la integridad con SELAE.`;$('analyze').disabled=rows.length<30}function stats(rows){let counts=Array(50).fill(0),last=Array(50).fill(rows.length),pairs=new Map(),triples=new Map();rows.forEach((r,i)=>{for(let a of r.nums){counts[a]++;last[a]=rows.length-1-i}for(let x=0;x<6;x++)for(let y=x+1;y<6;y++){let k=`${r.nums[x]}-${r.nums[y]}`;pairs.set(k,(pairs.get(k)||0)+1);for(let z=y+1;z<6;z++){let t=`${k}-${r.nums[z]}`;triples.set(t,(triples.get(t)||0)+1)}}});return{counts,last,pairs,triples}}function select(rows,recent=[]){let s=stats(rows),short=stats(rows.slice(-Math.min(50,rows.length))),recentStats=recent.length?stats(recent):null,scores=Array(50).fill(0);for(let n=1;n<=49;n++){let p=6/49;let z=(s.counts[n]-rows.length*p)/Math.sqrt(rows.length*p*(1-p));let z2=(short.counts[n]-Math.min(50,rows.length)*p)/Math.sqrt(Math.min(50,rows.length)*p*(1-p));scores[n]=.6*Math.max(-3,Math.min(3,z))+.4*Math.max(-3,Math.min(3,z2));if(recentStats){const zr=(recentStats.counts[n]-recent.length*p)/Math.sqrt(recent.length*p*(1-p));scores[n]=.85*scores[n]+.15*Math.max(-3,Math.min(3,zr))}}let chosen=[];while(chosen.length<6){let best=-Infinity,pick=0;for(let n=1;n<=49;n++){if(chosen.includes(n))continue;let val=scores[n]+(Math.random()-.5)*.12;for(let m of chosen){let k=[n,m].sort((a,b)=>a-b).join('-');let observed=s.pairs.get(k)||0;let expected=rows.length*expPair;val+=.12*Math.max(-2,Math.min(2,(observed-expected)/Math.sqrt(expected||1)))}for(let i=0;i<chosen.length;i++)for(let j=i+1;j<chosen.length;j++){let k=[n,chosen[i],chosen[j]].sort((a,b)=>a-b).join('-');let expected=rows.length*expTriple;val+=.03*Math.max(-2,Math.min(2,((s.triples.get(k)||0)-expected)/Math.sqrt(expected||1)))}if(val>best){best=val;pick=n}}chosen.push(pick)}return{nums:chosen.sort((a,b)=>a-b),s,scores}}function backtest(rows){let start=Math.max(100,Math.floor(rows.length*.6)),hits=0,random=0,counts=[0,0,0,0,0,0,0];let tests=Math.min(160,rows.length-start);for(let t=0;t<tests;t++){let idx=start+Math.floor(t*(rows.length-start)/tests),past=rows.slice(Math.max(0,idx-500),idx),actual=new Set(rows[idx].nums);let a=select(past).nums.filter(x=>actual.has(x)).length;hits+=a;counts[a]++;let shuffled=Array.from({length:49},(_,i)=>i+1);for(let i=48;i>0;i--){let j=Math.floor(Math.random()*(i+1));[shuffled[i],shuffled[j]]=[shuffled[j],shuffled[i]]}random+=shuffled.slice(0,6).filter(x=>actual.has(x)).length}return{tests,hits,random,counts}}function periodRows(rows){if(!rows.length)return [];const mode=$('window').value;if(mode==='all')return rows.slice();const last=rows.at(-1).date;const end=new Date(last+'T12:00:00Z');const cutoff=new Date(end);if(mode==='week')cutoff.setUTCDate(cutoff.getUTCDate()-7);else cutoff.setUTCMonth(cutoff.getUTCMonth()-Number(mode));const iso=cutoff.toISOString().slice(0,10);return rows.filter(r=>r.date>=iso)}
/* Motor exploratorio: ventanas temporales, asociaciones y contraste fuera de muestra.
   Las puntuaciones no son probabilidades predictivas. */
function recentDays(rows,days){if(!rows.length)return [];const d=new Date(rows.at(-1).date+'T12:00:00Z');d.setUTCDate(d.getUTCDate()-days);const cut=d.toISOString().slice(0,10);return rows.filter(r=>r.date>=cut)}
function normTail(z){const x=Math.abs(z),t=1/(1+.2316419*x),density=Math.exp(-x*x/2)/Math.sqrt(2*Math.PI);return Math.min(1,2*density*(.319381530*t-.356563782*t*t+1.781477937*t**3-1.821255978*t**4+1.330274429*t**5))}
function frequencyModel(rows,field='nums'){
 const digits=field==='reintegro',size=digits?10:50,first=digits?0:1,last=digits?9:49,p=digits?.1:6/49;
 const horizons=[30,90,365],windows=horizons.map(days=>({days,rows:recentDays(rows,days)}));
 const year=rows.length?rows.at(-1).date.slice(0,4):'';
 const ytd=rows.filter(r=>r.date.startsWith(year));
 const scores=Array(size).fill(0),evidence=[];
 for(let n=first;n<=last;n++){
  const occurrences=rows.filter(r=>digits?r.reintegro===n:r.nums.includes(n));
  const gaps=occurrences.slice(1).map((r,i)=>(new Date(r.date)-new Date(occurrences[i].date))/86400000);
  const blocks=windows.map(w=>{const k=w.rows.filter(r=>digits?r.reintegro===n:r.nums.includes(n)).length;const expected=w.rows.length*p;const z=w.rows.length?(k-expected)/Math.sqrt(w.rows.length*p*(1-p)):0;return {days:w.days,k,total:w.rows.length,expected,z}});
  const ycount=ytd.filter(r=>digits?r.reintegro===n:r.nums.includes(n)).length;
  const zy=ytd.length?(ycount-ytd.length*p)/Math.sqrt(ytd.length*p*(1-p)):0;
  const score=blocks.reduce((a,b,i)=>a+[.45,.35,.20][i]*Math.max(-3,Math.min(3,b.z)),0);
  scores[n]=score;
  const lastDate=occurrences.at(-1)?.date||'sin apariciones';
  evidence.push({n,blocks,ycount,yTotal:ytd.length,zy,lastDate,gaps,score,nominalP:normTail(zy)});
 }
 return {scores,evidence,windows,ytd,field};
}
function rankModel(rows,field='nums'){
 const m=frequencyModel(rows,field),sorted=m.evidence.slice().sort((a,b)=>b.score-a.score||a.n-b.n);
 return {model:m,sorted};
}
function validateModel(rows,field='nums'){
 const digits=field==='reintegro',start=Math.max(120,Math.floor(rows.length*.55)),step=Math.max(1,Math.floor((rows.length-start)/140));
 let tests=0,hits=0,baseline=0;
 for(let i=start;i<rows.length;i+=step){
  const past=rows.slice(0,i),rank=rankModel(past,field).sorted;
  if(digits){if(!Number.isInteger(rows[i].reintegro))continue;hits+=Number(rank[0].n===rows[i].reintegro);baseline+=.1}
  else{const chosen=new Set(rank.slice(0,6).map(x=>x.n));hits+=rows[i].nums.filter(n=>chosen.has(n)).length;baseline+=36/49}
  tests++;
 }
 const variance=digits?tests*.1*.9:tests*(6*(6/49)*(43/49)*(43/48));
 const z=variance?(hits-baseline)/Math.sqrt(variance):0;
 return {tests,hits,baseline,z,significant:tests>=60&&z>2.58};
}
function analyze(){
 const observed=periodRows(draws),rank=rankModel(draws),model=rank.model;
 const nums=rank.sorted.slice(0,6).map(x=>x.n).sort((a,b)=>a-b);
 const bt=validateModel(draws);
 const data=rank.sorted.slice(0,6);
 const associations=stats(recentDays(draws,365));
 const topPairs=[...associations.pairs.entries()].sort((a,b)=>b[1]-a[1]).slice(0,5);
 const explanations=data.map(e=>{
  const period=e.blocks.map(b=>b.days+' días: '+b.k+'/'+b.total+' (esperado '+b.expected.toFixed(1)+')').join(' · ');
  return '<li class="selection-reason"><span class="chosen-number">'+e.n+'</span><span class="reason-copy">Última aparición: '+e.lastDate+'. '+period+'. En '+model.ytd[0]?.date?.slice(0,4)+': '+e.ycount+'/'+e.yTotal+'. Puntuación descriptiva: '+e.score.toFixed(2)+'.</span></li>'
 }).join('');
 const status=bt.significant?'Hay una señal exploratoria que requiere confirmación independiente.':'No hay evidencia suficiente de ventaja sobre el azar.';
 $('output').innerHTML='<h3>Combinación experimental</h3><div class="balls">'+nums.map(n=>'<span class="ball">'+n+'</span>').join('')+'</div>'+
 '<p><strong>'+status+'</strong> Probabilidad teórica de seis aciertos: 1 entre 13.983.816. El análisis utiliza todos los sorteos disponibles desde 2000, dando prioridad a 30, 90 y 365 días; el selector solo cambia el periodo observado ('+observed.length+' sorteos).</p>'+
 '<details open><summary>Por qué estos números</summary><ul class="selection-reasons">'+explanations+'</ul><p>Se estudian fechas, frecuencias recientes y desviaciones frente a 6/49 por sorteo. Las puntuaciones no indican probabilidades futuras.</p></details>'+
 '<details><summary>Coincidencias, parejas y rachas</summary><p>Parejas más frecuentes en 365 días: '+topPairs.map(([k,v])=>k+' ('+v+')').join(' · ')+'. Una pareja cualquiera tiene '+(100*expPair).toFixed(2)+' % de aparecer en un sorteo justo. Estas coincidencias no se usan como prueba de causalidad.</p><p>Los intervalos entre apariciones se calculan para cada número; una racha no demuestra que vaya a repetirse.</p></details>'+
 '<details open><summary>Validación cronológica</summary><p>'+bt.tests+' sorteos futuros simulados sin utilizar sus resultados para escoger los números: '+bt.hits+' aciertos individuales, frente a '+bt.baseline.toFixed(1)+' esperados por azar. Contraste exploratorio z='+bt.z.toFixed(2)+'. '+status+'</p><p>El método se ha diseñado observando este histórico; hacen falta pruebas prospectivas independientes. Se examinan 49 números y varios periodos, por lo que una frecuencia llamativa puede surgir por comparaciones múltiples.</p></details>';
}
 $('analyze').onclick=()=>{analyze();renderReintegroLaboratorio()};$('file').onchange=async e=>{let f=e.target.files[0];if(f)setDraws(parse(await f.text()),f.name)};async function refreshHistory(){
 $('status').textContent='Cargando histórico validado…';
 try{
  const response=await fetch('./data/sorteos.json?nocache='+Date.now(),{cache:'no-store'});
  if(!response.ok)throw Error('El archivo histórico todavía no está publicado (HTTP '+response.status+')');
  const payload=await response.json();
  if(!Array.isArray(payload.draws))throw Error('Formato histórico incorrecto');
  const unique=new Map();
  for(const row of payload.draws){
   if(!/^\d{4}-\d{2}-\d{2}$/.test(row.date)||!Array.isArray(row.nums)||row.nums.length!==6||new Set(row.nums).size!==6||row.nums.some(n=>!Number.isInteger(n)||n<1||n>49))continue;
   if(unique.has(row.date)&&JSON.stringify(unique.get(row.date).nums)!==JSON.stringify(row.nums))throw Error('Resultados contradictorios para '+row.date);
   unique.set(row.date,{date:row.date,nums:[...row.nums].sort((a,b)=>a-b)});
  }
  const rows=[...unique.values()].sort((a,b)=>a.date.localeCompare(b.date));
  if(rows.length<30)throw Error('No hay suficientes sorteos válidos');
  setDraws(rows,'archivo histórico automático');
  $('status').textContent+='\nActualización del archivo: '+(payload.updated_at||'no indicada')+'. Último sorteo registrado: '+rows.at(-1).date+'.';
  try{localStorage.setItem('primitiva_public_history',JSON.stringify({updated_at:payload.updated_at,draws:rows}))}catch(_){}
 }catch(e){
  try{let cached=JSON.parse(localStorage.getItem('primitiva_public_history'));if(cached.draws?.length>=30){setDraws(cached.draws,'copia local anterior');$('status').textContent+='\nSin conexión o sin actualización: '+e.message+'; fecha de la copia: '+(cached.updated_at||'desconocida');return}}catch(_){}
  $('status').textContent='No se pudo actualizar: '+e.message+'. Publica el proyecto con la tarea de GitHub Actions o importa un CSV manualmente.';
 }
}
$('load').onclick=refreshHistory;
window.addEventListener('DOMContentLoaded',refreshHistory);

/* Importación local segura: CSV/TXT o JSON; nunca modifica GitHub automáticamente. */
(function(){
 const fileInput=$('file');
 fileInput.accept='.csv,.txt,.json,text/csv,application/json';
 const section=fileInput.closest('section');
 const heading=section.querySelector('h2');
 if(heading)heading.textContent='Importar resultados oficiales (archivo)';
 const intro=section.querySelector('p');
 if(intro)intro.textContent='Selecciona un CSV, TXT o JSON descargado de una fuente fiable. Se validarán fechas y números y se detectarán conflictos con el histórico cargado. Los archivos no se envían a ningún servidor.';
 const report=document.createElement('p');report.id='import-report';report.style.whiteSpace='pre-wrap';
 const exportBtn=document.createElement('button');exportBtn.textContent='Descargar histórico combinado (JSON)';exportBtn.disabled=true;
 section.appendChild(report);section.appendChild(exportBtn);
 let mergedForExport=null;
 function isValidDate(s){if(!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;const d=new Date(s+'T00:00:00Z');return !isNaN(d)&&d.toISOString().slice(0,10)===s;}
 function normalize(rows){
  if(!Array.isArray(rows))throw Error('No se encontró una lista de sorteos.');
  const out=new Map();
  for(const r of rows){
   if(!r||!isValidDate(r.date)||!Array.isArray(r.nums)||r.nums.length!==6)throw Error('Hay filas con fecha o combinación no válida.');
   const nums=r.nums.map(Number).sort((a,b)=>a-b);
   if(nums.some(n=>!Number.isInteger(n)||n<1||n>49)||new Set(nums).size!==6)throw Error('Hay números inválidos o repetidos.');
   if(out.has(r.date)&&JSON.stringify(out.get(r.date).nums)!==JSON.stringify(nums))throw Error('El archivo contiene resultados distintos para '+r.date);
   out.set(r.date,{date:r.date,nums});
  }
  return out;
 }
 fileInput.onchange=async function(){
  exportBtn.disabled=true;mergedForExport=null;
  const f=fileInput.files&&fileInput.files[0];if(!f)return;
  try{
   if(f.size>15*1024*1024)throw Error('Archivo demasiado grande (máximo 15 MB).');
   const text=await f.text();
   let imported;
   if(f.name.toLowerCase().endsWith('.json')){
    const obj=JSON.parse(text);imported=Array.isArray(obj)?obj:obj.draws;
   }else imported=parse(text);
   const fresh=normalize(imported);
   if(!fresh.size)throw Error('No se han encontrado sorteos válidos. Revisa el formato del archivo.');
   const current=normalize(draws);
   const conflicts=[];
   for(const [date,row] of fresh){
    if(current.has(date)&&JSON.stringify(current.get(date).nums)!==JSON.stringify(row.nums))conflicts.push(date);
   }
   if(conflicts.length){
    report.textContent='IMPORTACIÓN DETENIDA. Hay '+conflicts.length+' fechas con números diferentes: '+conflicts.slice(0,8).join(', ')+'. Verifica estas fechas en SELAE. No se ha cambiado el histórico.';
    return;
   }
   let added=0;
   for(const [date,row] of fresh){if(!current.has(date)){current.set(date,row);added++;}}
   const combined=[...current.values()].sort((a,b)=>a.date.localeCompare(b.date));
   mergedForExport={updated_at:new Date().toISOString(),sources:['Importación local; verificar procedencia del archivo: '+f.name],draws:combined};
   exportBtn.disabled=false;
   report.textContent='Archivo revisado: '+fresh.size+' sorteos válidos. Nuevos: '+added+'. Total combinado: '+combined.length+'. No se ha subido nada a GitHub. Pulsa «Descargar histórico combinado (JSON)» para guardar el resultado.';
   if(combined.length>=30)setDraws(combined,'histórico combinado local (pendiente de verificación)');
  }catch(err){report.textContent='No se ha importado el archivo: '+err.message;}
 };
 exportBtn.onclick=()=>{
  if(!mergedForExport)return;
  const blob=new Blob([JSON.stringify(mergedForExport,null,2)+'\n'],{type:'application/json'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');a.href=url;a.download='sorteos-combinados.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);
 };
})();

/* Panel de los 5 últimos sorteos disponibles en el histórico cargado. */
(function(){
 const historySection=document.getElementById('load').closest('section');
 const panel=document.createElement('section');
 panel.innerHTML='<h2>Últimos 5 sorteos</h2><p id="last20-info" class="muted">Cargando histórico…</p><div id="last20-list"></div>';
 historySection.insertAdjacentElement('beforebegin',panel);
 const render=()=>{
  const info=document.getElementById('last20-info'),list=document.getElementById('last20-list');
  if(!draws.length){info.textContent='Todavía no hay resultados cargados.';list.replaceChildren();return;}
  const latest=[...draws].sort((a,b)=>b.date.localeCompare(a.date)).slice(0,5);
  const counts=new Map();
  for(const item of latest)for(const n of item.nums)counts.set(n,(counts.get(n)||0)+1);
  info.textContent='Último sorteo disponible: '+latest[0].date+'. Son los últimos resultados guardados, no necesariamente los últimos celebrados. Verifica los datos con SELAE.';
  list.replaceChildren();
  const legend=document.createElement('p');legend.style.cssText='font-size:14px;color:#fce7bf;margin:12px 0';legend.textContent='🟠 Naranja = número repetido entre estos 5 sorteos · ×2, ×3… = veces que aparece';list.appendChild(legend);
  for(const item of latest){
   const row=document.createElement('div');row.style.cssText='padding:10px 0;border-bottom:1px solid #365066';
   const date=document.createElement('strong');date.textContent=item.date;
   const balls=document.createElement('div');balls.className='balls';balls.style.marginTop='7px';
   for(const n of item.nums){const ball=document.createElement('span');ball.className='ball';const count=counts.get(n)||1;if(count>1){ball.style.cssText='background:#ffb347;color:#291600;border:3px solid #fff0c9;box-sizing:border-box;position:relative;font-weight:900;box-shadow:0 0 0 2px #a24b00';ball.title=n+' aparece '+count+' veces en los últimos 5 sorteos';const marker=document.createElement('span');marker.textContent='×'+count;marker.style.cssText='position:absolute;top:-9px;right:-10px;background:#6c2600;color:white;border-radius:10px;font-size:11px;line-height:17px;min-width:20px;padding:0 2px';ball.appendChild(document.createTextNode(n));ball.appendChild(marker);}else{ball.textContent=n;}balls.appendChild(ball);}
   row.append(date,balls);list.appendChild(row);
  }
 };
 const previous=setDraws;
 setDraws=function(rows,source){previous(rows,source);render();};
 render();
})();


/* Reto Predictor: lectura exclusivamente desde el repositorio GitHub. */
(function(){
 const history=document.getElementById('reto-history');
 const message=document.getElementById('reto-message');
 if(!history||!message)return;
 let predictions=[];
 function render(){
  history.replaceChildren();
  if(!predictions.length){const p=document.createElement('p');p.className='muted';p.textContent='Aún no hay predicciones publicadas en GitHub.';history.appendChild(p);return}
  for(const r of [...predictions].sort((a,b)=>b.target.localeCompare(a.target))){
   const card=document.createElement('div');card.className='reto-card';
   const title=document.createElement('strong');title.textContent='Sorteo: '+r.target;card.appendChild(title);
   const meta=document.createElement('p');meta.className='reto-meta';meta.textContent='Registrada: '+r.created+' · Ventana: '+r.window+' sorteos · Datos hasta: '+r.historyUntil;card.appendChild(meta);
   const actual=draws.find(d=>d.date===r.target);
   const balls=document.createElement('div');balls.className='balls';
   for(const n of r.nums){const ball=document.createElement('span');ball.className='ball';ball.textContent=n;if(actual?.nums.includes(n))ball.classList.add('reto-hit');balls.appendChild(ball)}
   card.appendChild(balls);
   const status=document.createElement('p');
   if(actual){const hits=r.nums.filter(n=>actual.nums.includes(n)).length;status.textContent='Resultado en histórico: '+hits+' acierto'+(hits===1?'':'s')+' de 6. Coincidencias en naranja. Números oficiales pendientes de contrastar con SELAE.'}
   else{status.className='muted';status.textContent='Pendiente de resultado en el histórico.'}
   card.appendChild(status);history.appendChild(card);
  }
 }
 async function load(){
  try{
   const response=await fetch('./data/reto-predictor.json?nocache='+Date.now(),{cache:'no-store'});
   if(!response.ok)throw Error('HTTP '+response.status);
   const data=await response.json();
   if(!Array.isArray(data.predictions))throw Error('Formato no válido');
   predictions=data.predictions.filter(r=>r&&typeof r.target==='string'&&Array.isArray(r.nums)&&r.nums.length===6);
   message.textContent='Historial permanente consultado en GitHub. Nuevas predicciones programadas antes de los sorteos de lunes, jueves y sábado.';
   render();
  }catch(e){message.textContent='No se ha podido consultar el historial de GitHub: '+e.message}
 }
 const previous=setDraws;
 setDraws=function(rows,source){previous(rows,source);render()};
 load();
})();


/* Mostrar únicamente propuesta y estado del aprendizaje, no cada prueba. */
(async function(){
 const node=document.getElementById('reto-learning');if(!node)return;
 try{
  const response=await fetch('./data/reto-aprendizaje.json?nocache='+Date.now(),{cache:'no-store'});
  if(!response.ok)throw Error('aún no publicado');
  const model=await response.json();
  node.replaceChildren();
  const title=document.createElement('p');title.textContent='Objetivo: 3 o más aciertos. Estrategia seleccionada con pruebas cronológicas: '+model.strategy.mode+' · ventana '+model.strategy.window+' sorteos.';node.appendChild(title);
  if(model.goal==='at-least-three-hits'){const stat=document.createElement('p');stat.className='muted';stat.textContent='Prueba reservada: '+model.holdoutThreePlus+' sorteos con 3 o más aciertos de '+model.holdoutDraws+' · referencia aleatoria: '+model.holdoutExpectedThreePlus.toFixed(1)+'.';node.appendChild(stat)}
  const row=document.createElement('div');row.className='balls';
  for(const n of model.nextCombination){const ball=document.createElement('span');ball.className='ball';ball.textContent=n;row.appendChild(ball)}node.appendChild(row);
  const note=document.createElement('p');note.className='muted';note.textContent='Combinación experimental calculada con datos hasta '+model.lastHistoricalDate+'. No se ha demostrado una ventaja predictiva frente al azar. La predicción oficial del reto es la que queda registrada antes del sorteo en GitHub.';node.appendChild(note);
 }catch(e){node.textContent='El aprendizaje automático todavía no se ha ejecutado o publicado en GitHub.'}
})();


/* Reintegro integrado en Laboratorio: histórico aportado por el usuario.
   La elección retrospectiva no tiene ventaja predictiva demostrada. */
let reintegrosHistoricos=[];

function renderReintegroLaboratorio(){
 const output=$('output'),balls=output?.querySelector('.balls');if(!balls)return;
 output.querySelector('#reintegro-details')?.remove();
 balls.querySelector('#reintegro-result')?.remove();
 const rows=reintegrosHistoricos,rank=rankModel(rows,'reintegro'),choice=rank.sorted[0],bt=validateModel(rows,'reintegro');
 if(!choice)return;
 const wrapper=document.createElement('span');wrapper.id='reintegro-result';wrapper.style.cssText='display:inline-flex;align-items:center;gap:6px';
 const plus=document.createElement('strong');plus.textContent='+';wrapper.appendChild(plus);
 const ball=document.createElement('span');ball.className='ball';ball.style.cssText='background:#ffd965;color:#3b2600;border:2px solid #fff7d6;box-sizing:border-box';ball.textContent=choice.n;wrapper.appendChild(ball);balls.appendChild(wrapper);
 const y=rank.model.ytd.length,expected=y/10;
 const all=rank.sorted.slice().sort((a,b)=>a.n-b.n);
 const details=document.createElement('details');details.id='reintegro-details';details.open=true;
 const summary=document.createElement('summary');summary.textContent='Investigación del reintegro';details.appendChild(summary);
 const p=document.createElement('p');p.textContent='Candidato exploratorio: '+choice.n+'. Última aparición: '+choice.lastDate+'. Frecuencia del año en curso: '+choice.ycount+' de '+y+' sorteos (esperado '+expected.toFixed(1)+'). Frecuencias recientes: '+choice.blocks.map(b=>b.days+' días '+b.k+'/'+b.total).join(' · ')+'.';details.appendChild(p);
 const compare=document.createElement('p');compare.textContent='Comparación anual de los 10 dígitos: '+all.map(e=>e.n+': '+e.ycount).join(' · ')+'. Valor p nominal del candidato frente al 10 %: '+choice.nominalP.toFixed(3)+'; no corregido por buscar entre diez dígitos y varios periodos.';details.appendChild(compare);
 const val=document.createElement('p');val.textContent='Prueba cronológica independiente del sorteo evaluado: '+bt.hits+' aciertos en '+bt.tests+' predicciones, frente a '+bt.baseline.toFixed(1)+' esperados al azar. '+(bt.significant?'Señal exploratoria pendiente de confirmación.':'Sin ventaja estadística demostrada.')+' La probabilidad teórica de cada dígito continúa siendo del 10 % en un sorteo justo.';details.appendChild(val);
 const disclaimer=document.createElement('p');disclaimer.textContent='Datos de reintegros procedentes del CSV del usuario, no contrastados individualmente con SELAE. El reintegro del resguardo lo asigna aleatoriamente SELAE: no puede elegirse al apostar.';details.appendChild(disclaimer);
 const link=document.createElement('a');link.href='./data/sorteos.json';link.target='_blank';link.rel='noopener noreferrer';link.textContent='Consultar histórico y procedencia';details.appendChild(link);output.appendChild(details);
}

(async function(){try{
 const response=await fetch('./data/sorteos.json?nocache='+Date.now(),{cache:'no-store'});
 if(!response.ok)throw Error('HTTP '+response.status);
 const data=await response.json();if(!Array.isArray(data.draws))throw Error('Formato inválido');
 const seen=new Set();reintegrosHistoricos=data.draws.filter(r=>r&&/^\d{4}-\d{2}-\d{2}$/.test(r.date)&&r.date>='1991-06-20'&&Number.isInteger(r.reintegro)&&r.reintegro>=0&&r.reintegro<=9&&!seen.has(r.date)&&seen.add(r.date)).sort((a,b)=>a.date.localeCompare(b.date));
 }catch(e){console.warn('Reintegros no disponibles:',e.message)}
 if(document.getElementById('output')?.querySelector('.balls'))renderReintegroLaboratorio();
})();
