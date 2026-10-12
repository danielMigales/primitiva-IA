const $=id=>document.getElementById(id);let draws=[];const choose=(n,k)=>{let x=1;for(let i=1;i<=k;i++)x=x*(n-i+1)/i;return x};const expPair=15/choose(49,2),expTriple=20/choose(49,3);function parse(text){let out=[],seen=new Set();for(const line of text.split(/\r?\n/)){let d=line.match(/(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})/);if(!d)continue;let iso=`${d[3]}-${d[2].padStart(2,'0')}-${d[1].padStart(2,'0')}`;if(!Number.isFinite(Date.parse(iso)))continue;let rest=line.slice(d.index+d[0].length);let nums=(rest.match(/\d+/g)||[]).map(Number);if(nums.length<6)continue;let a=nums.slice(0,6);if(a.some(x=>x<1||x>49)||new Set(a).size!==6)continue;if(seen.has(iso))continue;seen.add(iso);out.push({date:iso,nums:a.sort((a,b)=>a-b)})}return out.sort((a,b)=>a.date.localeCompare(b.date))}function setDraws(rows,source){draws=rows;$('status').textContent=`${rows.length} sorteos válidos cargados de ${source}. Rango: ${rows[0]?.date||'—'} a ${rows.at(-1)?.date||'—'}. Comprueba la integridad con SELAE.`;$('analyze').disabled=rows.length<30}function stats(rows){let counts=Array(50).fill(0),last=Array(50).fill(rows.length),pairs=new Map(),triples=new Map();rows.forEach((r,i)=>{for(let a of r.nums){counts[a]++;last[a]=rows.length-1-i}for(let x=0;x<6;x++)for(let y=x+1;y<6;y++){let k=`${r.nums[x]}-${r.nums[y]}`;pairs.set(k,(pairs.get(k)||0)+1);for(let z=y+1;z<6;z++){let t=`${k}-${r.nums[z]}`;triples.set(t,(triples.get(t)||0)+1)}}});return{counts,last,pairs,triples}}function select(rows){let s=stats(rows),short=stats(rows.slice(-Math.min(50,rows.length))),scores=Array(50).fill(0);for(let n=1;n<=49;n++){let p=6/49;let z=(s.counts[n]-rows.length*p)/Math.sqrt(rows.length*p*(1-p));let z2=(short.counts[n]-Math.min(50,rows.length)*p)/Math.sqrt(Math.min(50,rows.length)*p*(1-p));scores[n]=.6*Math.max(-3,Math.min(3,z))+.4*Math.max(-3,Math.min(3,z2))}let chosen=[];while(chosen.length<6){let best=-Infinity,pick=0;for(let n=1;n<=49;n++){if(chosen.includes(n))continue;let val=scores[n]+(Math.random()-.5)*.12;for(let m of chosen){let k=[n,m].sort((a,b)=>a-b).join('-');let observed=s.pairs.get(k)||0;let expected=rows.length*expPair;val+=.12*Math.max(-2,Math.min(2,(observed-expected)/Math.sqrt(expected||1)))}for(let i=0;i<chosen.length;i++)for(let j=i+1;j<chosen.length;j++){let k=[n,chosen[i],chosen[j]].sort((a,b)=>a-b).join('-');let expected=rows.length*expTriple;val+=.03*Math.max(-2,Math.min(2,((s.triples.get(k)||0)-expected)/Math.sqrt(expected||1)))}if(val>best){best=val;pick=n}}chosen.push(pick)}return{nums:chosen.sort((a,b)=>a-b),s,scores}}function backtest(rows){let start=Math.max(100,Math.floor(rows.length*.6)),hits=0,random=0,counts=[0,0,0,0,0,0,0];let tests=Math.min(160,rows.length-start);for(let t=0;t<tests;t++){let idx=start+Math.floor(t*(rows.length-start)/tests),past=rows.slice(Math.max(0,idx-500),idx),actual=new Set(rows[idx].nums);let a=select(past).nums.filter(x=>actual.has(x)).length;hits+=a;counts[a]++;let shuffled=Array.from({length:49},(_,i)=>i+1);for(let i=48;i>0;i--){let j=Math.floor(Math.random()*(i+1));[shuffled[i],shuffled[j]]=[shuffled[j],shuffled[i]]}random+=shuffled.slice(0,6).filter(x=>actual.has(x)).length}return{tests,hits,random,counts}}function analyze(){let rows=draws.slice(-Number($('window').value)),{nums,s,scores}=select(rows),bt=backtest(draws),windows=[20,50,100,500].map(w=>{let r=draws.slice(-w);return{w:r.length,s:stats(r)}});let top=(map,n)=>[...map.entries()].sort((a,b)=>b[1]-a[1]).slice(0,n).map(([k,v])=>`${k} (${v})`).join(', ');let sum=nums.reduce((a,b)=>a+b,0),ev=bt.tests*36/49;let explanations=nums.map(n=>`<li class="selection-reason"><span class="chosen-number" aria-label="Número seleccionado ${n}">${n}</span><span class="reason-copy">${s.counts[n]} apariciones en ${rows.length} sorteos; retraso ${s.last[n]} sorteos; puntuación histórica ${scores[n].toFixed(2)}. Ventanas: ${windows.map(x=>`${x.w}: ${x.s.counts[n]}`).join(' · ')}.</span></li>`).join('');$('output').innerHTML=`<h3>Combinación experimental</h3><div class="balls">${nums.map(n=>`<span class="ball">${n}</span>`).join('')}</div><p><strong>Sin ventaja predictiva demostrada.</strong> Cada combinación tiene 1 entre 13.983.816 de acertar los seis números en un sorteo justo.</p><details open><summary>Por qué se escogieron</summary><ul class="selection-reasons">${explanations}</ul><p>Pares: ${nums.filter(n=>n%2===0).length}; suma: ${sum}. La selección pondera frecuencias y coapariciones, pero estas pueden ser puro azar.</p></details><details><summary>Parejas y tríos frecuentes</summary><p>Parejas: ${top(s.pairs,8)}</p><p>Tríos: ${top(s.triples,8)}</p><p>Frecuencia esperada por pareja en ${rows.length} sorteos: ${(rows.length*expPair).toFixed(2)}; por trío: ${(rows.length*expTriple).toFixed(2)}. Muchos patrones aparentes surgen al comparar miles de grupos.</p></details><details open><summary>Prueba histórica sin mirar el futuro</summary><p>${bt.tests} predicciones retrospectivas; aciertos totales del modelo: ${bt.hits}; referencia matemática de azar: ${ev.toFixed(1)} aciertos esperados; una muestra aleatoria de control: ${random=bt.random}. Distribución de aciertos: ${bt.counts.map((x,i)=>`${i}: ${x}`).join(' · ')}.</p><p>Esto es una prueba exploratoria, no una validación estadística suficiente para afirmar que supera al azar. La estrategia fue diseñada tras estudiar patrones históricos y requiere pruebas prospectivas independientes.</p></details>`} $('analyze').onclick=()=>{analyze();renderReintegroLaboratorio()};$('file').onchange=async e=>{let f=e.target.files[0];if(f)setDraws(parse(await f.text()),f.name)};async function refreshHistory(){
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
function reintegroMasFrecuente(rows){
 const counts=Array(10).fill(0);
 for(const r of rows)counts[r.reintegro]++;
 let best=0;for(let i=1;i<10;i++)if(counts[i]>counts[best])best=i;
 return {digit:best,counts};
}
function renderReintegroLaboratorio(){
 const output=document.getElementById('output');if(!output)return;
 const previous=document.getElementById('reintegro-result');if(previous)previous.remove();
 const balls=output.querySelector('.balls');if(!balls)return; // Solo tras solicitar una combinación.
 const rows=reintegrosHistoricos.slice(-Number(document.getElementById('window').value));
 const wrapper=document.createElement('div');wrapper.id='reintegro-result';wrapper.style.cssText='display:contents';balls.style.cssText='display:flex;flex-wrap:nowrap;gap:clamp(3px,1.3vw,7px);align-items:center;width:100%;max-width:100%;overflow-x:auto;padding:5px 0';for(const ball of balls.querySelectorAll('.ball'))ball.style.cssText='flex:0 0 auto;width:clamp(29px,8vw,43px);height:clamp(29px,8vw,43px);font-size:clamp(13px,3.5vw,17px)';
 const label=document.createElement('span');label.textContent='+';label.title='Reintegro sugerido';label.style.cssText='font-weight:900;flex:0 0 auto';wrapper.appendChild(label);
 if(rows.length){
  const result=reintegroMasFrecuente(rows);
  const digit=document.createElement('span');digit.className='ball';digit.style.cssText='flex:0 0 auto;width:clamp(29px,8vw,43px);height:clamp(29px,8vw,43px);font-size:clamp(13px,3.5vw,17px);border:2px solid #fff7d6;box-sizing:border-box;background:radial-gradient(circle at 33% 25%,#fff9dd 0%,#ffd965 38%,#d18a19 82%,#a76b10 100%);color:#3b2600;box-shadow:inset -3px -4px 7px #6d420055,0 2px 5px #0006';digit.title='Reintegro sugerido';digit.textContent=result.digit;wrapper.appendChild(digit);
  const details=document.createElement('details');details.style.margin='10px 0';
  const summary=document.createElement('summary');summary.textContent='Cómo se eligió el reintegro';details.appendChild(summary);
  const freq=document.createElement('p');freq.textContent='Frecuencias observadas en '+rows.length+' sorteos históricos: '+result.counts.map((n,i)=>i+': '+n).join(' · ')+'. Selección: dígito más frecuente (empates: menor dígito).';details.appendChild(freq);
  let hits=0,tests=0;for(let i=5;i<rows.length;i++){if(reintegroMasFrecuente(rows.slice(0,i)).digit===rows[i].reintegro)hits++;tests++;}
  const note=document.createElement('p');note.textContent='Prueba cronológica: '+hits+' aciertos en '+tests+' sorteos evaluados; referencia de azar: '+(tests/10).toFixed(1)+'. Datos del CSV aportado, no verificados individualmente con SELAE. El dígito sugerido sigue teniendo una probabilidad teórica del 10 % en un sorteo justo; no existe ventaja demostrada.';details.appendChild(note);
  const link=document.createElement('a');link.href='./data/sorteos.json';link.textContent='Ver histórico y procedencia de los datos';link.target='_blank';link.rel='noopener noreferrer';details.appendChild(link);
  output.appendChild(details);
 }else{const unavailable=document.createElement('span');unavailable.textContent='sin datos de reintegro disponibles';wrapper.appendChild(unavailable);}
 balls.appendChild(wrapper);
}

(async function(){try{
 const response=await fetch('./data/sorteos.json?nocache='+Date.now(),{cache:'no-store'});
 if(!response.ok)throw Error('HTTP '+response.status);
 const data=await response.json();if(!Array.isArray(data.draws))throw Error('Formato inválido');
 const seen=new Set();reintegrosHistoricos=data.draws.filter(r=>r&&/^\d{4}-\d{2}-\d{2}$/.test(r.date)&&r.date>='1991-06-20'&&Number.isInteger(r.reintegro)&&r.reintegro>=0&&r.reintegro<=9&&!seen.has(r.date)&&seen.add(r.date)).sort((a,b)=>a.date.localeCompare(b.date));
 }catch(e){console.warn('Reintegros no disponibles:',e.message)}
 if(document.getElementById('output')?.querySelector('.balls'))renderReintegroLaboratorio();
})();
