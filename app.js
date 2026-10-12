const $=id=>document.getElementById(id);
function ball(n,gold=false){const el=document.createElement('span');el.className='ball'+(gold?' gold':'');el.textContent=n;return el}
function combination(nums,reintegro){const row=document.createElement('div');row.className='balls';for(const n of nums)row.appendChild(ball(n));if(Number.isInteger(reintegro)&&reintegro>=0&&reintegro<=9){const plus=document.createElement('span');plus.className='plus';plus.textContent='+';row.appendChild(plus);row.appendChild(ball(reintegro,true))}return row}
function p(text,cls=''){const e=document.createElement('p');e.textContent=text;if(cls)e.className=cls;return e}
function explain(r){
 const root=$('reasoning');root.replaceChildren();
 const d=document.createElement('details');d.open=true;
 const summary=document.createElement('summary');summary.textContent='Por qué se eligieron estos números';d.appendChild(summary);
 const list=document.createElement('div');list.className='selection-reasons';
 function reasonCard(n,description,gold=false){
  const item=document.createElement('div');item.className='selection-reason';
  const badge=document.createElement('span');badge.className='chosen-number'+(gold?' chosen-gold':'');badge.textContent=n;
  const copy=document.createElement('div');copy.className='reason-copy';copy.textContent=description;
  item.append(badge,copy);list.appendChild(item);
 }
 if(Array.isArray(r.numberEvidence)&&r.numberEvidence.length){
  d.appendChild(p('Análisis de frecuencia frente al azar: últimos 30, 90 y 365 días, ponderados al 45 %, 35 % y 20 %.'));
  for(const item of [...r.numberEvidence].sort((a,b)=>a.number-b.number)){
   const windows=(item.windows||[]).map(w=>w.days+' días: '+w.hits+' apariciones en '+w.draws+' sorteos (esperadas '+w.expected+')').join('. ');
   reasonCard(item.number,windows+'. Puntuación ponderada: '+Number(item.score).toFixed(2)+'.');
  }
 }else{
  d.appendChild(p('Esta predicción pertenece al método anterior. No se inventarán motivos que no quedaron registrados.'));
  for(const n of r.nums||[])reasonCard(n,'Número registrado con el método anterior; no se conserva una justificación individual verificable.');
 }
 if(Number.isInteger(r.reintegro)&&r.reintegro>=0&&r.reintegro<=9){
  if(r.reintegroEvidence&&Array.isArray(r.reintegroEvidence.windows)){
   const ev=r.reintegroEvidence;
   reasonCard(r.reintegro,'Reintegro: '+ev.windows.map(w=>w.days+' días: '+w.hits+' de '+w.draws+' sorteos (esperadas '+w.expected+')').join('. ')+'.',true);
  }else reasonCard(r.reintegro,'Reintegro registrado sin explicación estadística individual.',true);
 }
 d.appendChild(list);
 if(r.reintegroEvidence?.backtest){const b=r.reintegroEvidence.backtest;d.appendChild(p('Comprobación retrospectiva del reintegro: '+b.hits+' aciertos en '+b.tests+' pruebas; referencia aleatoria '+b.expectedRandom+'.','muted'));}
 d.appendChild(p('Las frecuencias son descriptivas; no hay una ventaja predictiva demostrada.','muted'));
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
