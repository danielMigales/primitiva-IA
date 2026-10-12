const $=id=>document.getElementById(id);
function ball(n,gold=false){const el=document.createElement('span');el.className='ball'+(gold?' gold':'');el.textContent=n;return el}
function combination(nums,reintegro){const row=document.createElement('div');row.className='balls';for(const n of nums)row.appendChild(ball(n));if(Number.isInteger(reintegro)&&reintegro>=0&&reintegro<=9){const plus=document.createElement('span');plus.className='plus';plus.textContent='+';row.appendChild(plus);row.appendChild(ball(reintegro,true))}return row}
function p(text,cls=''){const e=document.createElement('p');e.textContent=text;if(cls)e.className=cls;return e}
function explain(r){
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
    period.textContent=w.days===30?'Último mes':w.days===90?'Últimos 3 meses':w.days===365?'Último año':'Últimos '+w.days+' días';
    const count=document.createElement('span');count.className='frequency-count';
    count.textContent=w.hits+' '+(w.hits===1?'aparición':'apariciones')+' en '+w.draws+' sorteos';
    line.append(period,count);copy.appendChild(line);
   }
  }else copy.textContent=fallback;
  item.append(badge,copy);list.appendChild(item);
 }
 if(Array.isArray(r.numberEvidence)&&r.numberEvidence.length){
  for(const item of [...r.numberEvidence].sort((a,b)=>a.number-b.number))reasonCard(item.number,item.windows);
 }else{
  d.appendChild(p('Predicción anterior: no se conservaron explicaciones individuales verificables.','muted'));
  for(const n of r.nums||[])reasonCard(n,null,false,'Sin desglose estadístico registrado.');
 }
 if(Number.isInteger(r.reintegro)&&r.reintegro>=0&&r.reintegro<=9){
  reasonCard(r.reintegro,r.reintegroEvidence?.windows,true,'Reintegro registrado sin desglose estadístico.');
 }
 d.appendChild(list);
 d.appendChild(p('Estos datos describen el histórico; no demuestran una ventaja predictiva.','muted'));
 root.appendChild(d);
}
async function fetchJson(path){const r=await fetch(path+'?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);return r.json()}
async function load(){
 const [pred,history]=await Promise.allSettled([fetchJson('./data/reto-predictor.json'),fetchJson('./data/sorteos.json')]);
 let draws=[];
 if(history.status==='fulfilled'&&Array.isArray(history.value.draws)){
  draws=history.value.draws.filter(r=>r&&/^\d{4}-\d{2}-\d{2}$/.test(r.date)&&Array.isArray(r.nums)&&r.nums.length===6&&r.nums.every(n=>Number.isInteger(n)&&n>=1&&n<=49)).sort((a,b)=>b.date.localeCompare(a.date));
  $('draws-status').textContent='Último resultado registrado: '+(draws[0]?.date||'ninguno')+'. Actualización del archivo: '+(history.value.updated_at||'no indicada')+'.';
  const root=$('recent-draws');root.replaceChildren();
  for(const r of draws.slice(0,5)){const item=document.createElement('div');item.className='draw';const date=document.createElement('time');date.textContent=r.date;item.appendChild(date);item.appendChild(combination(r.nums,r.reintegro));root.appendChild(item)}
  if(!draws.length)root.appendChild(p('No hay sorteos válidos disponibles.'));
 }else $('draws-status').textContent='No se ha podido cargar el histórico actualizado.';
 if(pred.status!=='fulfilled'||!Array.isArray(pred.value.predictions)){ $('prediction-status').textContent='No se pudo cargar el registro de predicciones.';return}
 const entries=pred.value.predictions.filter(r=>r&&/^\d{4}-\d{2}-\d{2}$/.test(r.target)&&Array.isArray(r.nums)&&r.nums.length===6).sort((a,b)=>b.target.localeCompare(a.target));
 const latest=entries[0];if(!latest){$('prediction-status').textContent='Aún no hay predicciones registradas.';return}
 const actual=draws.find(d=>d.date===latest.target);
 $('prediction-status').textContent='Predicción registrada para '+latest.target+' · Histórico utilizado hasta '+(latest.historyUntil||'fecha no indicada')+(actual?' · Sorteo ya celebrado':' · Pendiente de resultado');
 const root=$('prediction');root.replaceChildren();root.appendChild(combination(latest.nums,latest.reintegro));
 if(!Number.isInteger(latest.reintegro))root.appendChild(p('Predicción antigua: no se registró reintegro antes del sorteo. No se añadirá retrospectivamente.','muted'));
 if(actual){const hits=latest.nums.filter(n=>actual.nums.includes(n)).length;root.appendChild(p('Resultado: '+hits+' de 6 números acertados'+(Number.isInteger(latest.reintegro)&&Number.isInteger(actual.reintegro)?' · Reintegro '+(latest.reintegro===actual.reintegro?'acertado':'no acertado'):'')+'.'))}
 explain(latest);
}
load().catch(e=>{$('prediction-status').textContent='Error de carga: '+e.message});
