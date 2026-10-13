const $=id=>document.getElementById(id);
function validDate(value){
 if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))return false;
 const time=Date.parse(value+'T00:00:00Z');
 return Number.isFinite(time)&&new Date(time).toISOString().slice(0,10)===value;
}
function validNumbers(nums){return Array.isArray(nums)&&nums.length===6&&nums.every(n=>Number.isInteger(n)&&n>=1&&n<=49)&&new Set(nums).size===6}
function validReintegro(n){return Number.isInteger(n)&&n>=0&&n<=9}
function evidenceWindows(value){return Array.isArray(value)?value.filter(w=>w&&[30,90].includes(w.days)&&Number.isInteger(w.hits)&&Number.isInteger(w.draws)&&w.draws>0&&w.hits>=0&&w.hits<=w.draws):[]}
function madridToday(){
 const parts=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Madrid',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
 const values=Object.fromEntries(parts.map(p=>[p.type,p.value]));
 return values.year+'-'+values.month+'-'+values.day;
}
function ball(n,gold=false){const el=document.createElement('span');el.className='ball'+(gold?' gold':'');el.textContent=n;return el}
function combination(nums,reintegro){const row=document.createElement('div');row.className='balls';for(const n of nums)row.appendChild(ball(n));if(Number.isInteger(reintegro)&&reintegro>=0&&reintegro<=9){const plus=document.createElement('span');plus.className='plus';plus.textContent='+';row.appendChild(plus);row.appendChild(ball(reintegro,true))}return row}
function p(text,cls=''){const e=document.createElement('p');e.textContent=text;if(cls)e.className=cls;return e}
function weeklyEvidence(r,draws,n,gold=false){
 if(!validDate(r.historyUntil))return null;
 const end=Date.parse(r.historyUntil+'T00:00:00Z');
 const start=end-6*86400000;
 const recent=draws.filter(d=>{const t=Date.parse(d.date+'T00:00:00Z');return t>=start&&t<=end&&(!gold||validReintegro(d.reintegro))});
 if(!recent.length)return null;
 return {days:7,hits:recent.filter(d=>gold?d.reintegro===n:d.nums.includes(n)).length,draws:recent.length};
}
function explain(r,draws,entries){
 const root=$('reasoning');root.replaceChildren();
 const d=document.createElement('details');d.open=true;
 const summary=document.createElement('summary');summary.textContent='Por qué se eligieron estos números';d.appendChild(summary);
 const list=document.createElement('div');list.className='selection-reasons';
 function reasonCard(n,windows,gold=false,fallback=''){
  const item=document.createElement('div');item.className='selection-reason';
  const badge=document.createElement('span');badge.className='chosen-number'+(gold?' chosen-gold':'');badge.textContent=n;
  const copy=document.createElement('div');copy.className='reason-copy';
  if(Array.isArray(windows)&&windows.length){
   for(const w of windows){
    const line=document.createElement('div');line.className='frequency-line';
    const period=document.createElement('span');period.className='frequency-period';
    period.textContent=w.days===7?'Última semana':w.days===30?'Último mes':w.days===90?'Últimos 3 meses':w.days===365?'Último año':'Últimos '+w.days+' días';
    const count=document.createElement('span');count.className='frequency-count';
    count.textContent=w.hits+' '+(w.hits===1?'aparición':'apariciones')+' en '+w.draws+' sorteos';
    line.append(period,count);copy.appendChild(line);
   }
  }else copy.textContent=fallback;
  if(!gold){
   const last=draws.find(x=>x.date===r.historyUntil);
   const prior=entries.find(x=>x.target===last?.date);
   if(last?.nums.includes(n)&&prior?.nums?.includes(n)){
    copy.appendChild(p('Acertado también en la predicción del '+last.date+'. Sigue entre los seis números mejor clasificados por su frecuencia reciente; esto no aumenta su probabilidad real de salir.','repeat-note'));
   }
  }
  item.append(badge,copy);list.appendChild(item);
 }
 if(Array.isArray(r.numberEvidence)&&r.numberEvidence.length){
  for(const n of [...r.nums].sort((a,b)=>a-b)){
   const item=r.numberEvidence.find(e=>e&&e.number===n);
   const week=weeklyEvidence(r,draws,n);
   const windows=[...(week?[week]:[]),...evidenceWindows(item?.windows)];
   reasonCard(n,windows,false,'Sin desglose estadístico registrado.');
  }
 }else{
  d.appendChild(p('Predicción anterior: no se conservaron explicaciones individuales verificables.','muted'));
  for(const n of r.nums||[])reasonCard(n,null,false,'Sin desglose estadístico registrado.');
 }
 if(validReintegro(r.reintegro)){
  const week=weeklyEvidence(r,draws,r.reintegro,true);
  const windows=[...(week?[week]:[]),...evidenceWindows(r.reintegroEvidence?.windows)];
  reasonCard(r.reintegro,windows,true,'Reintegro registrado sin desglose estadístico.');
 }
 d.appendChild(list);
 d.appendChild(p('Estos datos describen el histórico; no demuestran una ventaja predictiva.','muted'));
 root.appendChild(d);
}
function choose(n,k){let result=1;for(let i=1;i<=k;i++)result=result*(n-i+1)/i;return result}
function trackingResults(entries,draws){
 const results=new Map(draws.map(d=>[d.date,d]));
 const seen=new Set();
 return entries.filter(r=>{if(seen.has(r.target))return false;seen.add(r.target);return true}).map(r=>{
  const actual=results.get(r.target);
  return {record:r,actual,hits:actual?r.nums.filter(n=>actual.nums.includes(n)).length:null,
   reintegro:actual&&validReintegro(r.reintegro)&&validReintegro(actual.reintegro)?Number(r.reintegro===actual.reintegro):null};
 });
}
function renderTracking(entries,draws,historyLoaded){
 const root=$('tracking');root.replaceChildren();
 if(!entries.length){root.appendChild(p('Aún no hay predicciones válidas registradas.'));return}
 const rows=trackingResults(entries,draws);
 const settled=rows.filter(r=>r.actual);
 root.appendChild(p(rows.length+' predicciones registradas · '+settled.length+' con resultado disponible · '+(rows.length-settled.length)+' sin resultado disponible.'));
 if(!historyLoaded)root.appendChild(p('No se puede comprobar el histórico en este momento.','muted'));
 const groups=new Map();
 for(const row of rows){
  const algorithm=typeof row.record.algorithm==='string'?row.record.algorithm:'sin identificador';
  const key=algorithm+' / ventana '+(row.record.window??'no indicada');
  if(!groups.has(key))groups.set(key,[]);
  groups.get(key).push(row);
 }
 const chanceThree=[3,4,5,6].reduce((sum,k)=>sum+choose(6,k)*choose(43,6-k)/choose(49,6),0);
 for(const [label,group] of groups){
  const resolved=group.filter(r=>r.actual);
  const hits=resolved.reduce((sum,r)=>sum+r.hits,0);
  const three=resolved.filter(r=>r.hits>=3).length;
  const reintegros=resolved.filter(r=>r.reintegro!==null);
  const card=document.createElement('div');card.className='tracking-group';
  card.appendChild(p(label,'tracking-label'));
  card.appendChild(p('Seguimiento: '+resolved.length+' / 30 sorteos con resultado'+(resolved.length>=30?' · Primer hito alcanzado; no demuestra ventaja.':'.')));
  if(resolved.length){
   card.appendChild(p('Aciertos principales: '+hits+' · Sorteos con 3 o más: '+three+'.'));
   card.appendChild(p('Referencia al azar para '+resolved.length+' sorteos: '+(resolved.length*36/49).toFixed(2)+' aciertos principales y '+(resolved.length*chanceThree).toFixed(2)+' sorteos con 3 o más, en promedio.','muted'));
   card.appendChild(p(reintegros.length?'Reintegro: '+reintegros.reduce((sum,r)=>sum+r.reintegro,0)+' aciertos en '+reintegros.length+' predicciones evaluables · Referencia al azar: '+(reintegros.length/10).toFixed(2)+'.':'Reintegro: sin predicciones evaluables.','muted'));
  }
  root.appendChild(card);
 }
 const detail=document.createElement('details');detail.open=true;
 const summary=document.createElement('summary');summary.textContent='Resultados de todas las predicciones';detail.appendChild(summary);
 for(const row of rows){
  const item=document.createElement('div');item.className='tracking-entry';
  item.appendChild(p(row.record.target+' · '+row.record.nums.join(', ')+(validReintegro(row.record.reintegro)?' + R '+row.record.reintegro:'')));
  const result=row.actual?row.hits+' / 6 aciertos'+(row.reintegro!==null?' · Reintegro '+(row.reintegro?'acertado':'no acertado'):' · Reintegro no evaluable'):!historyLoaded?'Resultado sin comprobar':row.record.target<madridToday()?'Resultado no disponible en el histórico':'Pendiente de resultado';
  item.appendChild(p(result,'muted'));detail.appendChild(item);
 }
 root.appendChild(detail);
 root.appendChild(p('Se incluyen también los fallos. Cada algoritmo se evalúa por separado; las revisiones conservadas no cuentan como apuestas adicionales. La referencia al azar es matemática para sorteos uniformes de 6 entre 49 y reintegro de 0 a 9; no son apuestas generadas después del resultado. Las fechas de publicación se comprueban en los commits y los resultados pueden requerir cotejo oficial.','notice'));
}
async function fetchJson(path){const r=await fetch(path+'?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);return r.json()}
async function load(){
 const [pred,history]=await Promise.allSettled([fetchJson('./data/reto-predictor.json'),fetchJson('./data/sorteos.json')]);
 let draws=[];
 const historyLoaded=history.status==='fulfilled'&&Array.isArray(history.value?.draws);
 if(historyLoaded){
  draws=history.value.draws.filter(r=>r&&validDate(r.date)&&validNumbers(r.nums)).sort((a,b)=>b.date.localeCompare(a.date));
  $('draws-status').textContent='Último resultado registrado: '+(draws[0]?.date||'ninguno')+'. Actualización del archivo: '+(history.value.updated_at||'no indicada')+'.';
  const root=$('recent-draws');root.replaceChildren();
  const recent=draws.slice(0,5);
  const counts=new Map();
  for(const draw of recent)for(const n of new Set(draw.nums))counts.set(n,(counts.get(n)||0)+1);
  const repeated=[...counts].filter(([,times])=>times>=2).map(([n])=>n).sort((a,b)=>a-b);
  const colorByNumber=new Map(repeated.map((n,i)=>[n,i]));
  for(const r of recent){
   const item=document.createElement('div');item.className='draw';
   const date=document.createElement('time');date.textContent=r.date;item.appendChild(date);
   const balls=combination(r.nums,r.reintegro);
   for(const b of balls.querySelectorAll('.ball:not(.gold)')){const times=counts.get(Number(b.textContent))||0;if(times>=2){b.classList.add('repeated');b.style.setProperty('--repeat-hue',String((colorByNumber.get(Number(b.textContent))*137.508+25)%360));b.title='Aparece '+times+' veces en los últimos 5 sorteos';const tag=document.createElement('span');tag.className='repeat-count';tag.textContent='×'+times;b.appendChild(tag)}}
   item.appendChild(balls);root.appendChild(item);
  }
  if(!draws.length)root.appendChild(p('No hay sorteos válidos disponibles.'));
 }else $('draws-status').textContent='No se ha podido cargar el histórico actualizado.';
 if(pred.status!=='fulfilled'||!Array.isArray(pred.value?.predictions)){ $('prediction-status').textContent='No se pudo cargar el registro de predicciones.';$('tracking').replaceChildren(p('No se pudo cargar el registro de predicciones.'));return}
 const entries=pred.value.predictions.filter(r=>r&&validDate(r.target)&&validNumbers(r.nums)).sort((a,b)=>b.target.localeCompare(a.target));
 renderTracking(entries,draws,historyLoaded);
 const latest=entries[0];if(!latest){$('prediction-status').textContent='Aún no hay predicciones registradas.';return}
 const actual=draws.find(d=>d.date===latest.target);
 const status=actual?'Sorteo ya celebrado':!historyLoaded||!draws.length?'Resultado sin comprobar: histórico no disponible':latest.target<madridToday()?'Resultado no disponible en el histórico':'Pendiente de resultado';
 $('prediction-status').textContent='Predicción registrada para '+latest.target+' · Histórico utilizado hasta '+(latest.historyUntil||'fecha no indicada')+' · '+status;
 const root=$('prediction');root.replaceChildren();root.appendChild(combination(latest.nums,latest.reintegro));
 if(!validReintegro(latest.reintegro))root.appendChild(p('No hay un reintegro válido registrado para esta predicción. No se añadirá retrospectivamente.','muted'));
 if(actual){const hits=latest.nums.filter(n=>actual.nums.includes(n)).length;root.appendChild(p('Resultado: '+hits+' de 6 números acertados'+(validReintegro(latest.reintegro)&&validReintegro(actual.reintegro)?' · Reintegro '+(latest.reintegro===actual.reintegro?'acertado':'no acertado'):'')+'.'))}
 explain(latest,draws,entries);
}
load().catch(e=>{$('prediction-status').textContent='Error de carga: '+e.message});
