const $=id=>document.getElementById(id);
function validDate(value){
 if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))return false;
 const time=Date.parse(value+'T00:00:00Z');
 return Number.isFinite(time)&&new Date(time).toISOString().slice(0,10)===value;
}
function validNumbers(nums){return Array.isArray(nums)&&nums.length===6&&nums.every(n=>Number.isInteger(n)&&n>=1&&n<=49)&&new Set(nums).size===6}
function validReintegro(n){return Number.isInteger(n)&&n>=0&&n<=9}
function evidenceWindows(value){return Array.isArray(value)?value.filter(w=>w&&[30,90,365].includes(w.days)&&Number.isInteger(w.hits)&&Number.isInteger(w.draws)&&w.draws>0&&w.hits>=0&&w.hits<=w.draws):[]}
function madridToday(){
 const parts=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Madrid',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
 const values=Object.fromEntries(parts.map(p=>[p.type,p.value]));
 return values.year+'-'+values.month+'-'+values.day;
}
function ball(n,gold=false){const el=document.createElement('span');el.className='ball'+(gold?' gold':'');el.textContent=n;return el}
function hitBall(n,gold,hit){
 const el=ball(n,gold);
 if(hit){
  el.classList.add('hit');
  el.setAttribute('aria-label',(gold?'Reintegro ':'Número ')+n+' acertado');
  const mark=document.createElement('span');mark.className='hit-mark';mark.textContent='✓';mark.setAttribute('aria-hidden','true');el.appendChild(mark);
 }
 return el;
}
function combination(nums,reintegro,actual=null){
 const row=document.createElement('div');row.className='balls';
 for(const n of nums)row.appendChild(hitBall(n,false,!!actual?.nums.includes(n)));
 if(validReintegro(reintegro)){
  const plus=document.createElement('span');plus.className='plus';plus.textContent='+';row.appendChild(plus);
  row.appendChild(hitBall(reintegro,true,!!actual&&validReintegro(actual.reintegro)&&reintegro===actual.reintegro));
 }
 return row;
}
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
 if(['online-logistic-v1','guarded-online-logistic-v1'].includes(r.algorithm)){
  root.appendChild(p('Modelo entrenado hasta '+r.historyUntil+'. Los seis números tienen las mayores puntuaciones del modelo; el reintegro se estima con un modelo separado.'));
  for(const e of r.numberEvidence||[])if(r.nums.includes(e?.number)&&Number.isFinite(e.estimatedScore))root.appendChild(p('Número '+e.number+' · puntuación estimada '+(100*e.estimatedScore).toFixed(2)+' %.'));
  root.appendChild(p('Son estimaciones del modelo, sin ventaja demostrada. Identificador de entrenamiento: '+(r.modelId||'no disponible')+'.','muted'));return;
 }
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
function renderCompact(entries,draws,historyLoaded,predLoaded,proofs,analysis,discovery,learning){
 const latestRoot=$('latest-summary'),findings=$('findings-summary'),nextRoot=$('next-summary');
 if(!latestRoot||!findings||!nextRoot)return;
 latestRoot.replaceChildren();findings.replaceChildren();nextRoot.replaceChildren();
 const actual=draws[0];
 if(!historyLoaded)latestRoot.appendChild(p('No se ha podido cargar el último resultado.'));
 else if(!actual)latestRoot.appendChild(p('No hay resultados disponibles.'));
 else{
  latestRoot.appendChild(p('Sorteo del '+actual.date));latestRoot.appendChild(combination(actual.nums,actual.reintegro));
  const prediction=entries.find(r=>r.target===actual.date);
  if(!predLoaded)latestRoot.appendChild(p('No se ha podido comprobar la predicción anterior.'));
  else if(!prediction)latestRoot.appendChild(p('Sin predicción registrada para este sorteo.'));
  else{
   const hits=prediction.nums.filter(n=>actual.nums.includes(n));
   latestRoot.appendChild(p('Predicción anterior: '+hits.length+' de 6 aciertos'+(validReintegro(prediction.reintegro)&&validReintegro(actual.reintegro)?' · Reintegro '+(prediction.reintegro===actual.reintegro?'acertado':'no acertado'):'')+'.'));
   latestRoot.appendChild(p('Números acertados: '+(hits.length?hits.join(', '):'ninguno')+'.','muted'));
  }
  latestRoot.appendChild(p(verificationFor(actual,proofs)+'.','verification-note'));
 }
 if(analysis&&analysis.status!=='analyzed')findings.appendChild(p(analysis.conclusion||'Esperando el último resultado antes de continuar el análisis.'));
 else if(!historyLoaded||!actual)findings.appendChild(p('No se puede comprobar si el análisis está actualizado.'));
 else{
  const current=discovery?.status==='searched'&&discovery.historyUntil===actual.date;
  if(current&&Number.isInteger(discovery.totalDraws)&&Number.isInteger(discovery.search?.survivedFinalAudit)){
   findings.appendChild(p(discovery.totalDraws.toLocaleString('es-ES')+' sorteos analizados · '+discovery.search.survivedFinalAudit+' hipótesis superan los contrastes.'));
   findings.appendChild(p(discovery.search.survivedFinalAudit?'Las hipótesis encontradas aún necesitan comprobarse con sorteos futuros.':'No se ha encontrado una regla con ventaja predictiva demostrada.'));
  }else findings.appendChild(p('El informe de búsqueda no está disponible o está pendiente de actualización.'));
  const histogram=learning?.simulation?.hitHistogram;
  if(learning?.historyUntil===actual.date&&Number.isInteger(learning.simulation.draws)&&Array.isArray(histogram)&&histogram.length===7&&histogram.every(n=>Number.isInteger(n)&&n>=0)){
   findings.appendChild(p('Modelo de patrones: '+learning.simulation.draws.toLocaleString('es-ES')+' ensayos históricos.'));
   findings.appendChild(p([3,4,5,6].map(hits=>hits+' aciertos: '+histogram[hits]+(histogram[hits]===1?' ensayo':' ensayos')).join(' · ')+'.'));
   findings.appendChild(p('Estos aciertos aislados no han demostrado una mejora sostenida.','muted'));
  }
 }
 if(!predLoaded){nextRoot.appendChild(p('No se ha podido cargar la próxima predicción.'));return;}
 const next=entries.filter(r=>r.target>=madridToday()&&!draws.some(d=>d.date===r.target)).sort((a,b)=>a.target.localeCompare(b.target))[0];
 if(!next){nextRoot.appendChild(p('Próxima predicción pendiente de registro.'));return;}
 nextRoot.appendChild(p('Registrada para '+next.target));nextRoot.appendChild(combination(next.nums,next.reintegro));
 nextRoot.appendChild(p('Histórico utilizado hasta '+(next.historyUntil||'fecha no indicada')+'.','muted'));
 if(actual&&next.historyUntil&&next.historyUntil<actual.date)nextRoot.appendChild(p('Se conserva tal como se registró, antes del último resultado.','muted'));
}

function renderLearning(entries,draws,active,proofs=[],training=null){
 const root=$('learning-review');if(!root)return;root.replaceChildren();
 const rows=trackingResults(entries,draws).filter(r=>r.actual).sort((a,b)=>b.record.target.localeCompare(a.record.target));
 const last=rows[0];
 if(!last){root.appendChild(p('Aún no hay una predicción con resultado disponible para evaluar.'));return}
 const {record,actual,hits,reintegro}=last;
 const adjustment=Array.isArray(training?.lastUpdates)?training.lastUpdates.find(r=>r.date===actual.date):null;
 root.appendChild(p('Balance del '+record.target+': '+hits+' de 6 aciertos'+(reintegro===null?' · Reintegro no evaluable.':reintegro?' · Reintegro acertado.':' · Reintegro no acertado.')));
 root.appendChild(p('Predicción registrada: '+record.nums.join(', ')+'. Resultado: '+actual.nums.join(', ')+'.'));
 root.appendChild(p(verificationFor(actual,proofs)+'.','verification-note'));
 const sameMotor=record.algorithm===active?.strategy?.algorithm;
 const adaptive=['online-logistic-v1','guarded-online-logistic-v1'].includes(record.algorithm);
 root.appendChild(p(adaptive?'Por qué se eligieron: el modelo estimó sus puntuaciones con pesos aprendidos únicamente de sorteos anteriores.':sameMotor?'Por qué se eligieron: el método priorizó frecuencias recientes en ventanas de 30, 90 y 365 días. Esa clasificación describe el pasado y no garantiza coincidencias en el siguiente sorteo.':'La predicción usó el método registrado '+(record.algorithm||'sin identificador')+'. No se conserva una explicación causal verificable de su fallo.'));
 if(hits===0)root.appendChild(p('Ninguno de los seis números elegidos coincidió. En un sorteo uniforme de 6 entre 49, la probabilidad de obtener 0 aciertos con una combinación fija es '+(100*choose(43,6)/choose(49,6)).toFixed(2)+' %. El fallo, por sí solo, no identifica una causa especial ni demuestra que otro método prediga mejor.'));
 else root.appendChild(p('Los aciertos observados se incorporan al seguimiento. Un único sorteo no demuestra una ventaja predictiva ni permite atribuir el resultado a una causa concreta.'));
 const sample=rows.filter(r=>r.record.strategyVersion===active?.version&&r.record.algorithm===active?.strategy?.algorithm);
 const minimum=Number.isInteger(active?.minimumSettledDraws)?active.minimumSettledDraws:30;
 root.appendChild(p(!adaptive&&[3,4].includes(active?.version)?'Esta predicción pertenece a un motor anterior. Se conserva su resultado; el entrenamiento del nuevo modelo se muestra en su propio informe.':record.algorithm==='guarded-online-logistic-v1'?'El resultado sirve para evaluar candidatos y entrenar nuevas propuestas. Los pesos del modelo activo solo cambian al aprobar la evaluación prospectiva.':adaptive?'El resultado se incorpora al siguiente entrenamiento: el error entre estimación y resultado ajusta los pesos. El informe de entrenamiento muestra la última actualización disponible.':'Qué se ha aprendido: queda registrado este resultado para evaluar el método. No se ha demostrado una mejora predictiva ni se ha reentrenado el modelo a partir de este fallo. Se mantienen los pesos del método durante un mínimo de '+minimum+' sorteos evaluables de su versión.'));
 root.appendChild(p('Seguimiento de la versión activa: '+sample.length+' / '+minimum+' sorteos con predicción y resultado. Los registros anteriores sin esa versión se conservan por separado.','muted'));
 if(adjustment&&Array.isArray(adjustment.weightsBefore)&&Array.isArray(adjustment.weightsAfter)&&adjustment.weightsBefore.length===4&&adjustment.weightsAfter.length===4&&[...adjustment.weightsBefore,...adjustment.weightsAfter].every(Number.isFinite)){
  const delta=adjustment.weightsAfter.reduce((sum,w,i)=>sum+Math.abs(w-adjustment.weightsBefore[i]),0);
  root.appendChild(p('Al incorporar este resultado al entrenamiento, el cambio total de los cuatro pesos fue '+delta.toFixed(5)+'. Este cálculo procede de la reproducción cronológica del entrenamiento. Los ajustes siguen sujetos al control de mejoras.'));
 }
 const next=entries.filter(r=>r.target>actual.date&&!draws.some(d=>d.date===r.target)).sort((a,b)=>a.target.localeCompare(b.target))[0];
 if(next){
  root.appendChild(p('Siguiente predicción registrada: '+next.target+' · Histórico hasta '+next.historyUntil+'.'));
  const added=next.nums.filter(n=>!record.nums.includes(n)),removed=record.nums.filter(n=>!next.nums.includes(n));
  root.appendChild(p(added.length?'Cambio en la combinación: entran '+added.join(', ')+'; salen '+removed.join(', ')+'.':'La nueva clasificación conserva los mismos seis números.'));
  root.appendChild(p(['online-logistic-v1','guarded-online-logistic-v1'].includes(next.algorithm)?'La siguiente propuesta usa el modelo adaptativo. Sus aciertos se evaluarán por separado de las versiones anteriores.':'La nueva propuesta recalcula las frecuencias del histórico indicado con el mismo método; un cambio de números no demuestra que haya aprendido a anticipar el sorteo.','muted'));
 }else root.appendChild(p('Siguiente predicción pendiente de registro. Se generará al actualizar el histórico; no se modificará la predicción ya evaluada.','incident-warning'));
}
function trackingResults(entries,draws){
 const results=new Map(draws.map(d=>[d.date,d]));
 const seen=new Set();
 return entries.filter(r=>{if(seen.has(r.target))return false;seen.add(r.target);return true}).map(r=>{
  const actual=results.get(r.target);
  return {record:r,actual,hits:actual?r.nums.filter(n=>actual.nums.includes(n)).length:null,
   reintegro:actual&&validReintegro(r.reintegro)&&validReintegro(actual.reintegro)?Number(r.reintegro===actual.reintegro):null};
 });
}
function strategyLabel(record){
 if(record.algorithm==='guarded-online-logistic-v1')return 'Modelo con evaluación previa · Versión 4';
 if(['online-logistic-v1','guarded-online-logistic-v1'].includes(record.algorithm))return 'Modelo adaptativo · Versión '+record.strategyVersion;
 const algorithm=typeof record.algorithm==='string'?record.algorithm:'sin identificador';
 const version=Number.isInteger(record.strategyVersion)?'versión '+record.strategyVersion:'registro anterior sin versión de estrategia';
 return algorithm+' / ventana '+(record.window??'no indicada')+' / '+version;
}
function validActiveStrategy(config){return config?.status==='active'&&Number.isInteger(config.version)&&((config.version===2&&config.strategy?.type==='recency-z'&&config.strategy.window===365)||(config.version===3&&config.strategy?.type==='online-logistic'&&config.strategy.algorithm==='online-logistic-v1')||(config.version===4&&config.strategy?.type==='guarded-online-logistic'&&config.strategy.algorithm==='guarded-online-logistic-v1'))}
function verificationFor(draw,proofs){
 const proof=proofs.find(r=>r?.date===draw.date&&r.source==='SELAE'&&/^https:\/\/www\.loteriasyapuestas\.es\//.test(r.url||'')&&typeof r.checkedAt==='string'&&Number.isFinite(Date.parse(r.checkedAt))&&validNumbers(r.nums));
 if(!proof)return 'Pendiente de cotejo SELAE';
 if([...proof.nums].sort((a,b)=>a-b).join(',')!==[...draw.nums].sort((a,b)=>a-b).join(',')||(validReintegro(proof.reintegro)&&validReintegro(draw.reintegro)&&proof.reintegro!==draw.reintegro))return 'Discrepancia con el cotejo SELAE';
 return validReintegro(proof.reintegro)&&validReintegro(draw.reintegro)?'Números y reintegro cotejados con SELAE':'Números cotejados; reintegro pendiente';
}
function shiftDay(day,offset){return new Date(Date.parse(day+'T00:00:00Z')+offset*86400000).toISOString().slice(0,10)}
function drawDay(day){return [1,4,6].includes(new Date(day+'T00:00:00Z').getUTCDay())}
function madridMinutes(){
 const parts=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Madrid',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date());
 const values=Object.fromEntries(parts.map(p=>[p.type,p.value]));return Number(values.hour)*60+Number(values.minute);
}
function renderIncidents(entries,draws,historyLoaded,predLoaded,report){
 const root=$('incidents');root.replaceChildren();
 const today=madridToday(),minutes=madridMinutes();
 let next=minutes>=21*60+40?shiftDay(today,1):today;
 while(!drawDay(next))next=shiftDay(next,1);
 const before=shiftDay(next,-1);
 const warningDue=today>=next||(today===before&&minutes>=14*60);
 const hasNext=entries.some(r=>r.target===next);
 root.appendChild(p('Próximo sorteo según el calendario configurado: '+next+'.'));
 if(!predLoaded)root.appendChild(p('No se puede comprobar si la próxima predicción está registrada.','incident-warning'));
 else if(hasNext)root.appendChild(p('Predicción para '+next+' registrada.'));
 else root.appendChild(p(warningDue?'Falta la predicción para '+next+'. Revisa la generación automática.':'La predicción para '+next+' aún no está registrada. La generación está prevista el día anterior. ',warningDue?'incident-warning':'muted'));
 if(!historyLoaded||!draws.length)root.appendChild(p('Histórico no disponible: no se pueden comprobar los resultados.','incident-warning'));
 else{
  // Allow the next morning's scheduled update before declaring a missing result.
  let expected=shiftDay(today,-1);
  if(minutes<12*60&&drawDay(expected))expected=shiftDay(expected,-1);
  while(!drawDay(expected))expected=shiftDay(expected,-1);
  if(!draws.some(r=>r.date===expected))root.appendChild(p('Falta el resultado del '+expected+' en el histórico. Los aciertos están pendientes de actualización.','incident-warning'));
 }
 if(report?.status==='unavailable')root.appendChild(p('El último intento de actualización no obtuvo resultados oficiales verificables de SELAE'+(report.checkedAt?' ('+report.checkedAt+')':'')+'.','incident-warning'));
 else if(report?.status==='conflict')root.appendChild(p('El actualizador detectó una discrepancia con SELAE. Se ha detenido sin sustituir los resultados existentes.','incident-warning'));
 else if(report?.status==='invalid-history')root.appendChild(p('La actualización se ha detenido porque el histórico está incompleto o es inválido.','incident-warning'));
 else if(report?.status==='confirmed')root.appendChild(p('Último cotejo automático: '+report.checkedAt+'. Solo los resultados con evidencia individual se marcan como cotejados.','muted'));
 else root.appendChild(p('Aún no hay un informe de cotejo automático disponible.','muted'));
 root.appendChild(p('Calendario del proyecto: lunes, jueves y sábado. Aviso de predicción ausente desde las 14:00 del día anterior; resultado ausente desde las 12:00 del día siguiente, hora de Madrid. Son avisos en esta página, sin notificaciones externas.','notice'));
}
function renderTracking(entries,draws,historyLoaded,activeStrategy,proofs=[]){
 const root=$('tracking');root.replaceChildren();
 if(!entries.length){root.appendChild(p('Aún no hay predicciones válidas registradas.'));return}
 const rows=trackingResults(entries,draws);
 const settled=rows.filter(r=>r.actual);
 root.appendChild(p(rows.length+' predicciones registradas · '+settled.length+' con resultado disponible · '+(rows.length-settled.length)+' sin resultado disponible.'));
 if(!historyLoaded)root.appendChild(p('No se puede comprobar el histórico en este momento.','muted'));
 const groups=new Map();
 if(validActiveStrategy(activeStrategy))groups.set(strategyLabel({algorithm:activeStrategy.strategy.algorithm,window:activeStrategy.strategy.window,strategyVersion:activeStrategy.version}),[]);
 for(const row of rows){
  const key=strategyLabel(row.record);
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
  const milestone=label==='Modelo con evaluación previa · Versión 4'?60:30;
  card.appendChild(p('Seguimiento: '+resolved.length+' / '+milestone+' sorteos con resultado'+(resolved.length>=milestone?' · Primer hito alcanzado; no demuestra ventaja.':'.')));
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
  item.appendChild(p(row.record.target+' · Predicción registrada'));
  item.appendChild(combination(row.record.nums,row.record.reintegro,row.actual));
  const result=row.actual?row.hits+' / 6 aciertos'+(row.reintegro!==null?' · Reintegro '+(row.reintegro?'acertado':'no acertado'):' · Reintegro no evaluable'):!historyLoaded?'Resultado sin comprobar':row.record.target<madridToday()?'Resultado no disponible en el histórico':'Pendiente de resultado';
  item.appendChild(p(result,'muted'));detail.appendChild(item);
  if(row.actual){
   item.appendChild(p('Resultado publicado:','muted'));
   item.appendChild(combination(row.actual.nums,row.actual.reintegro));
   item.appendChild(p('✓ señala los aciertos de la predicción. '+verificationFor(row.actual,proofs)+'.','verification-note'));
  }
 }
 root.appendChild(detail);
 root.appendChild(p('Se incluyen también los fallos. Cada algoritmo se evalúa por separado; las revisiones conservadas no cuentan como apuestas adicionales. La referencia al azar es matemática para sorteos uniformes de 6 entre 49 y reintegro de 0 a 9; no son apuestas generadas después del resultado. Las fechas de publicación se comprueban en los commits y los resultados pueden requerir cotejo oficial.','notice'));
}




function renderDiscovery(root,discovery){
 const s=discovery.search,m=discovery.finalEvaluation;
 root.appendChild(p('Búsqueda automática en '+discovery.totalDraws+' sorteos.'));
 root.appendChild(p(s.hypothesesEvaluated.toLocaleString('es-ES')+' hipótesis evaluadas · '+s.shortlisted+' seleccionadas · '+s.confirmed+' confirmadas · '+s.survivedFinalAudit+' superan la auditoría final.'));
 root.appendChild(p('El programa elige números, ventanas, retardos, umbrales y combinaciones de hasta '+s.maxConditionsPerRule+' condiciones. Busca dentro de esas familias; no recibe reglas ganadoras.'));
 root.appendChild(p(discovery.conclusion));
 root.appendChild(p('Descubrimiento hasta '+discovery.protocol.discoveryThrough+'; confirmación del '+discovery.protocol.confirmationFrom+' al '+discovery.protocol.confirmationThrough+'; auditoría del '+discovery.protocol.auditFrom+' al '+discovery.protocol.auditThrough+'.','muted'));
 for(const r of Array.isArray(discovery.examples)?discovery.examples:[]){
  const detail=document.createElement('details'),title=document.createElement('summary');
  title.textContent=(r.channel==='refund'?'Reintegro ':'Número ')+r.number+' · '+(r.audit?.passed?'Supera ambos contrastes':r.confirmation?.passed?'No supera la auditoría':'Descartada en confirmación');detail.appendChild(title);
  detail.appendChild(p('Condición descubierta: '+r.text+'.'));
  for(const [key,label] of [['discovery','Descubrimiento'],['confirmation','Confirmación'],['audit','Auditoría final']]){
   const block=r[key];if(!block)continue;
   detail.appendChild(p(block.status==='not-tested'?label+': no se abre para rescatar una hipótesis descartada.':label+': salió en '+block.hits+' de '+block.support+' casos'+(Number.isFinite(block.rate)?' ('+(block.rate*100).toFixed(1)+' %)':'')+'.'+(block.reason?' '+block.reason:'')));
  }
  root.appendChild(detail);
 }
 if(m)root.appendChild(p('Modelo exploratorio de las hipótesis seleccionadas, antes de descartar las que fallan: '+m.mainHits+' aciertos principales en '+m.draws+' sorteos de auditoría · Solo frecuencias '+m.frequencyHits+' · Referencia al azar '+Number(m.expectedRandomHits).toFixed(2)+'. La combinación de reglas se fija antes de abrir ese tramo.'));
 const experiment=discovery.registeredExperiment;
 if(experiment&&experiment.algorithm!==discovery.algorithm)root.appendChild(p('El pronóstico experimental para '+experiment.target+' ya estaba registrado con el motor anterior y se conserva. La búsqueda podrá aportar un nuevo candidato cuando alguna hipótesis supere los contrastes.','muted'));
 if(discovery.next.patternPredictionAvailable!==false){
 const proposal=document.createElement('details'),ptitle=document.createElement('summary');ptitle.textContent='Propuesta exploratoria de la búsqueda para '+discovery.next.target;proposal.appendChild(ptitle);
 proposal.appendChild(combination(discovery.next.nums,discovery.next.reintegro));proposal.appendChild(p('Es una propuesta experimental basada en las hipótesis que superaron los dos contrastes históricos. Requiere prueba con resultados futuros.'));root.appendChild(proposal);
 }
 for(const [href,label] of [['./data/hipotesis-investigadas.jsonl','Consultar las hipótesis seleccionadas y sus descartes'],['./data/auditoria-hipotesis.jsonl','Consultar las predicciones de auditoría']]){const link=document.createElement('a');link.href=href;link.textContent=label;const row=p('');row.appendChild(link);root.appendChild(row);}
 root.appendChild(p('Se corrigen las comparaciones múltiples. Acertar una combinación aislada no demuestra el motivo del sorteo ni una ventaja futura.','notice'));
}

function renderPatterns(report,discovery=null){
 let root=$('pattern-analysis');if(!root)return;root.replaceChildren();
 if(report?.version!==1){root.appendChild(p('El análisis de patrones aún no está disponible.'));return;}
 if(report.status!=='analyzed'){root.appendChild(p(report.conclusion||'Esperando el último resultado antes de continuar.'));return;}
 if(!validDate(report.historyUntil)||!report.latestResult){root.appendChild(p('No se puede comprobar la fecha del análisis.'));return;}
 if(discovery?.status==='searched'&&discovery.historyUntil===report.historyUntil&&discovery.search&&discovery.protocol&&validNumbers(discovery.next?.nums)){
  renderDiscovery(root,discovery);
  const legacy=document.createElement('details'),title=document.createElement('summary');title.textContent='Observaciones y contraste de las reglas anteriores';legacy.appendChild(title);root.appendChild(legacy);root=legacy;
 }
 root.appendChild(p('Análisis actualizado con el resultado del '+report.historyUntil+'.'));
 const last=report.latestResult;
 root.appendChild(p('Respecto al sorteo anterior: '+(last.repeatedFromPrevious?.length?'se repiten '+last.repeatedFromPrevious.join(', '):'no se repite ningún número')+'.'));
 if(Array.isArray(last.consecutivePairs)&&last.consecutivePairs.length)root.appendChild(p('Números consecutivos en el último resultado: '+last.consecutivePairs.map(x=>x.join(' y ')).join('; ')+'. Es una observación, no una señal de repetición futura.'));
 for(const scan of Array.isArray(report.recentScans)?report.recentScans:[]){
  const detail=document.createElement('details'),title=document.createElement('summary');title.textContent='Observaciones de los últimos '+scan.draws+' sorteos';detail.appendChild(title);
  if(Array.isArray(scan.topNumbers))detail.appendChild(p('Más frecuentes: '+scan.topNumbers.map(x=>x.value+' ('+x.hits+' veces)').join(', ')+'.'));
  if(Array.isArray(scan.topPairs))detail.appendChild(p('Parejas más repetidas: '+scan.topPairs.map(x=>x.value.join('–')+' ('+x.hits+' veces)').join(', ')+'.'));
  if(Array.isArray(scan.topRefunds)&&scan.topRefunds.length)detail.appendChild(p('Reintegros más frecuentes: '+scan.topRefunds.map(x=>x.value+' ('+x.hits+' veces)').join(', ')+'.'));
  detail.appendChild(p('Se comprueban múltiples números y parejas. Una frecuencia llamativa puede aparecer por azar.','muted'));root.appendChild(detail);
 }
 root.appendChild(p('¿Permite anticipar? '+report.conclusion));
 const validation=report.ruleEvaluation;
 if(validation?.status==='evaluated'){
  root.appendChild(p('Contraste: se elige una regla en 100 sorteos y se comprueba en los 100 siguientes. Se predice siempre con datos anteriores al resultado.'));
  for(const [key,label] of [['main','Números principales'],['refund','Reintegro']]){
   const result=validation.channels?.[key],r=result?.selectedResult;
   if(r&&Number.isFinite(r.expectedRandom))root.appendChild(p(label+' · Regla elegida: '+result.label+'. En '+r.draws+' sorteos: '+r.hits+' aciertos · Recencia fija '+r.baselineHits+' · Referencia al azar '+r.expectedRandom.toFixed(2)+'.'));
  }
 }else root.appendChild(p('Aún no hay suficiente histórico para el contraste separado.'));
 if(report.existingPrediction?.usesLatestResult===false)root.appendChild(p('La predicción del '+report.existingPrediction.target+' ya estaba registrada con histórico hasta '+report.existingPrediction.historyUntil+'. Se conserva para mantener el registro. Este análisis no la sustituye.','muted'));
 root.appendChild(p('El estudio histórico no autoriza cambios automáticos: cualquier nuevo método debe superar la evaluación de sorteos futuros antes de sustituir al modelo activo.','notice'));
}

function renderPatternLearning(report,analysis){
 const root=$('pattern-learning');if(!root)return;root.replaceChildren();
 if(analysis&&analysis.status!=='analyzed'){
  root.appendChild(p(analysis.conclusion||'Esperando el último resultado antes de simular.'));return;
 }
 if(report?.version!==1||report.algorithm!=='rolling-pattern-logistic-v1'||!validDate(report.historyUntil)||!report.protocol||!report.simulation||!report.validation||!report.frozenValidation){
  root.appendChild(p('Las simulaciones de aprendizaje aún no están disponibles.'));return;
 }
 if(validDate(analysis?.historyUntil)&&analysis.historyUntil!==report.historyUntil){root.appendChild(p('El informe de aprendizaje del '+report.historyUntil+' está pendiente de actualizar al resultado del '+analysis.historyUntil+'.'));return;}
 root.appendChild(p('Aprendizaje con ventanas de '+report.protocol.window+' sorteos · Histórico hasta '+report.historyUntil+'.'));
 root.appendChild(p('Una combinación por ensayo, antes de descubrir el resultado. Después se puntúan los aciertos y se ajustan los pesos de intervalos, repeticiones, parejas y transiciones entre tipos de combinación.'));
 const all=report.simulation,online=report.validation,frozen=report.frozenValidation;
 root.appendChild(p(all.draws+' ensayos históricos · '+all.mainHits+' aciertos acumulados · Mejor ensayo: '+report.bestHits+' de 6.'));
 if(Array.isArray(all.hitHistogram)&&all.hitHistogram.length===7)root.appendChild(p('Distribución completa: '+all.hitHistogram.map((count,hits)=>hits+' aciertos: '+count+' sorteos').join(' · ')+'.'));
 root.appendChild(p('Validación del '+report.protocol.validationFrom+' al '+report.protocol.validationThrough+' ('+online.draws+' sorteos), posterior al aprendizaje inicial.'));
 if(Number.isFinite(online.expectedRandomHits))root.appendChild(p('Aprendiendo después de cada resultado: '+online.mainHits+' aciertos · Solo frecuencias de 30 sorteos: '+online.frequencyHits+' · Referencia al azar: '+online.expectedRandomHits.toFixed(2)+'.'));
 root.appendChild(p('Con pesos congelados antes de la validación: '+frozen.mainHits+' aciertos. Este modelo no se ajusta con los resultados del tramo reservado.'));
 if(Number.isFinite(online.mainBrier)&&Number.isFinite(frozen.mainBrier))root.appendChild(p('Error de estimación (menor es mejor): aprendizaje continuo '+online.mainBrier.toFixed(5)+' · Pesos congelados '+frozen.mainBrier.toFixed(5)+' · Uniforme '+Number(online.uniformMainBrier).toFixed(5)+'.','muted'));
 if(online.refundDraws)root.appendChild(p('Reintegro en validación: '+online.refundHits+' / '+online.refundDraws+' aprendiendo · '+frozen.refundHits+' con pesos congelados.'));
 if(Number.isInteger(report.prospective?.registered))root.appendChild(p('Seguimiento fuera de la simulación: '+report.prospective.registered+' pronósticos experimentales registrados antes del sorteo · '+report.prospective.settled+' con resultado · '+report.prospective.mainHits+' aciertos principales.'));
 const updates=document.createElement('details'),title=document.createElement('summary');title.textContent='Últimos cinco ensayos: predicción, resultado y ajuste';updates.appendChild(title);
 for(const r of Array.isArray(report.lastUpdates)?report.lastUpdates:[]){
  if(!validNumbers(r.nums)||!validNumbers(r.actualNums))continue;
  const item=document.createElement('div');item.className='tracking-entry';
  item.appendChild(p(r.date+' · '+r.hits+' de 6 aciertos · Datos previos: '+r.historyFrom+' a '+r.historyUntil+'.'));
  item.appendChild(p('Predicción simulada:'));item.appendChild(combination(r.nums,r.reintegro,{nums:r.actualNums,reintegro:r.actualReintegro}));
  item.appendChild(p('Resultado real:'));item.appendChild(combination(r.actualNums,r.actualReintegro));
  item.appendChild(p('Acertados: '+(r.matched?.join(', ')||'ninguno')+' · Faltaron: '+(r.missed?.join(', ')||'ninguno')+'.'));
  const adjustments=(Array.isArray(r.adjustments)?r.adjustments:[]).filter(a=>Number.isFinite(a.delta));
  item.appendChild(p('Ajustes de mayor magnitud después del resultado: '+adjustments.map(a=>a.label+' '+(a.delta>=0?'+':'')+a.delta.toFixed(5)).join('; ')+'.','muted'));
  updates.appendChild(item);
 }
 root.appendChild(updates);
 const intervals=document.createElement('details'),ititle=document.createElement('summary');ititle.textContent='Intervalos, parejas y tipos de combinación en los últimos '+report.protocol.window+' sorteos';intervals.appendChild(ititle);
 for(const r of Array.isArray(report.recentPatterns?.intervals)?report.recentPatterns.intervals:[])if(r.appearances>=2&&Array.isArray(r.observedGaps))intervals.appendChild(p(r.number+': '+r.appearances+' apariciones · Intervalos observados: '+r.observedGaps.join(', ')+' sorteos · Ausente desde hace '+r.drawsSinceLast+' sorteos.'));
 intervals.appendChild(p('Parejas: '+(Array.isArray(report.recentPatterns?.pairs)?report.recentPatterns.pairs:[]).filter(r=>Array.isArray(r.nums)).map(r=>r.nums.join('–')+' ('+r.appearances+')').join(', ')+'.'));
 for(const s of Array.isArray(report.recentPatterns?.shapes)?report.recentPatterns.shapes:[])intervals.appendChild(p('Tipo observado '+s.appearances+' veces: '+s.odd+' impares, '+(6-s.odd)+' pares; '+s.low+' números del 1 al 24; suma entre '+s.sumBandFrom+' y '+(s.sumBandFrom+39)+'; '+s.consecutivePairsCappedAt3+(s.consecutivePairsCappedAt3===3?' o más':'')+' parejas consecutivas.'));
 root.appendChild(intervals);
 const experimental=report.registeredExperiment||report.next;
 if(validNumbers(experimental?.nums)){
  const proposal=document.createElement('details'),ptitle=document.createElement('summary');ptitle.textContent=(report.registeredExperiment?'Pronóstico experimental registrado para ':'Propuesta simulada para ')+experimental.target;proposal.appendChild(ptitle);
  proposal.appendChild(combination(experimental.nums,experimental.reintegro));
  proposal.appendChild(p('No sustituye la combinación designada ni sus registros anteriores. '+(report.candidateStatus==='in-trial'?'Este candidato está en evaluación prospectiva.':'El entrenamiento alimenta el próximo candidato; la evaluación ya iniciada se conserva.')));
  if(!report.registeredExperiment||report.registeredExperiment.modelId===report.modelId)for(const n of Array.isArray(report.numberEvidence)?report.numberEvidence:[])proposal.appendChild(p(n.number+': '+(Array.isArray(n.signals)?n.signals:[]).filter(s=>Number.isFinite(s.contribution)).map(s=>s.label+' ('+(s.contribution>=0?'+':'')+s.contribution.toFixed(4)+')').join('; ')+'.','muted'));
  proposal.appendChild(p('Las contribuciones explican cómo el modelo eligió esos números; no explican por qué saldrían en el sorteo.','muted'));root.appendChild(proposal);
 }
 root.appendChild(p('Se incluyen todos los ensayos y fallos. Acertar seis en una simulación aislada no prueba una regla general. No se vuelve a intentar el mismo resultado hasta acertarlo.','notice'));
 const audit=document.createElement('a');audit.href='./data/simulaciones-patrones.jsonl';audit.textContent='Consultar todos los ensayos históricos';root.appendChild(audit);
 if(!analysis)root.appendChild(p('No se pudo comprobar si hay un resultado más reciente pendiente. Fecha del informe: '+report.historyUntil+'.','muted'));
}

function renderQuality(report){
 const root=$('data-quality');if(!root)return;root.replaceChildren();
 if(report?.version!==1||typeof report.valid!=='boolean'||!Number.isInteger(report.total)){
  root.appendChild(p('No se ha podido cargar el informe de calidad del histórico.'));return;
 }
 root.appendChild(p(report.valid?'Histórico válido en los controles estructurales.':'Entrenamiento detenido: el histórico requiere revisión.',report.valid?'':'incident-warning'));
 root.appendChild(p(report.total+' sorteos revisados · Último resultado guardado: '+report.latestDate+'.'));
 if(Array.isArray(report.missingRecentDates)&&report.missingRecentDates.length)root.appendChild(p('Faltan sorteos dentro del histórico reciente: '+report.missingRecentDates.join(', ')+'.','incident-warning'));
 if(Array.isArray(report.errors)&&report.errors.length)root.appendChild(p('Registros con errores: '+report.errors.length+'. Se conservan los pesos y predicciones anteriores.','incident-warning'));
 if(Array.isArray(report.pendingDates)&&report.pendingDates.length)root.appendChild(p('Pendientes de incorporar al archivo central: '+report.pendingDates.join(', ')+'. Este informe no determina si SELAE ya los ha publicado.'));
 root.appendChild(p('Cotejo completo con SELAE: '+report.fullyVerifiedDraws+' / '+report.total+' sorteos. La comprobación de huecos cubre los últimos 90 días del histórico.','muted'));
 if(report.refundMissing)root.appendChild(p(report.refundMissing+' sorteos carecen de reintegro: se excluyen del aprendizaje de ese dato.'));
 root.appendChild(p('Informe del archivo central: '+report.checkedAt+'. Al abrir o actualizar se cargan los últimos archivos publicados.','muted'));
}
function renderDecisionHistory(control){
 const root=$('decision-history');if(!root)return;root.replaceChildren();
 if(control?.version!==1||!Array.isArray(control.decisions)){root.appendChild(p('No se pudo cargar el historial de decisiones.'));return;}
 if(!control.decisions.length){root.appendChild(p('Aún no hay cambios aceptados ni rechazados: los ensayos necesitan resultados de sorteos futuros.'));return;}
 root.appendChild(p(control.decisions.length+' decisiones registradas. Se muestran las diez más recientes.'));
 for(const d of [...control.decisions].reverse().slice(0,10)){
  const item=document.createElement('details');
  const title=document.createElement('summary');title.textContent=d.decidedAfter+' · Candidato '+d.epoch+' · '+(d.status==='accepted'?'Aceptado':'Rechazado');item.appendChild(title);
  item.appendChild(p(d.reason||'Sin motivo registrado.'));
  item.appendChild(p(d.draws+' sorteos evaluados después del entrenamiento.'));
  for(const [key,label] of [['main','Números principales'],['refund','Reintegro']]){
   const h=d.comparisons?.[key+'-hits'];if(h&&Number.isFinite(h.expectedUniform))item.appendChild(p(label+': candidato '+h.challenger+' aciertos · Activo '+h.champion+' · Referencia al azar '+h.expectedUniform.toFixed(2)+'.'));
  }
  item.appendChild(p('Modelo anterior: '+d.previousChampionId+' · Candidato: '+d.challengerId,'muted'));root.appendChild(item);
 }
}

function renderControl(control,active){
 const root=$('model-control');if(!root)return;root.replaceChildren();
 if(active?.version!==4)return;
 if(control?.version!==1||!validDate(control.champion?.historyUntil)||!control.assessment||!Number.isInteger(control.assessment.draws)||!Number.isInteger(control.policy?.minimumDraws)){
  root.appendChild(p('No se puede comprobar el control de mejoras. Se conserva el modelo activo.'));return;
 }
 root.appendChild(p('Pesos activos entrenados hasta '+control.champion.historyUntil+'. Se conservan hasta que otro modelo apruebe las pruebas.'));
 const a=control.assessment;
 root.appendChild(p(a.status==='waiting'?'Esperando un nuevo resultado para preparar un candidato distinto del modelo activo.':'Candidato en evaluación: '+a.draws+' / '+control.policy.minimumDraws+' sorteos posteriores al entrenamiento.'));
 root.appendChild(p('Para aceptar un cambio: menor error de estimación de forma consistente frente al modelo activo y al azar, tanto en números como en reintegro, y sin reducir los aciertos. Se realiza una sola decisión por candidato.'));
 const last=Array.isArray(control.decisions)?control.decisions.at(-1):null;
 root.appendChild(p(last?'Última decisión: '+(last.status==='accepted'?'cambio aceptado. ':'cambio rechazado. ')+(last.reason||''):'Todavía no hay cambios aceptados: faltan comparaciones prospectivas.'));
 if(last?.comparisons)for(const [key,label] of [['main','Números principales'],['refund','Reintegro']]){
  const h=last.comparisons[key+'-hits'];
  if(h&&Number.isFinite(h.expectedUniform))root.appendChild(p(label+': candidato '+h.challenger+' aciertos · Activo '+h.champion+' · Referencia al azar '+h.expectedUniform.toFixed(2)+'.'));
 }
 root.appendChild(p('Las simulaciones históricas no autorizan cambios. Las comparaciones se registran antes del sorteo y se guardan para poder revisarlas.'));
 if(control.nextTrainingCandidate?.algorithm==='rolling-pattern-logistic-v1')root.appendChild(p('Siguiente entrenamiento: patrones e intervalos con ventanas de '+control.nextTrainingCandidate.window+' sorteos. El ensayo ya iniciado conserva su candidato y sus resultados.'));
 if(control.nextTrainingCandidate?.algorithm==='automatic-rule-search-v1')root.appendChild(p('El siguiente candidato se prepara con hipótesis descubiertas automáticamente. El ensayo ya iniciado conserva su candidato y sus resultados.'));
}

function renderModel(model,active){
 const root=$('model-learning');if(!root)return;root.replaceChildren();
 if(![3,4].includes(active?.version))return;
 const metric=model?.evaluation;
 if(model?.version!==3||model.algorithm!=='online-logistic-v1'||!validDate(model.historyUntil)||!Number.isInteger(model.trainedDraws)||!metric||!Number.isFinite(metric.mainBrier)||!Number.isFinite(metric.uniformBrier)){
  root.appendChild(p('El informe de entrenamiento no está disponible. No se puede comprobar el último ajuste.'));return;
 }
 root.appendChild(p('Modelo entrenado con '+model.trainedDraws+' sorteos, hasta '+model.historyUntil+'. Ajusta pesos de frecuencias de 30/90/365 días, aparición en el sorteo anterior y sesgo de cada número.'));
 const last=Array.isArray(model.lastUpdates)?model.lastUpdates.at(-1):null;
 if(last&&validDate(last.date)&&Array.isArray(last.weightsBefore)&&Array.isArray(last.weightsAfter)&&last.weightsBefore.length===4&&last.weightsAfter.length===4&&[...last.weightsBefore,...last.weightsAfter].every(Number.isFinite)){
  const labels=['30 días','90 días','365 días','Sorteo anterior'];
  root.appendChild(p('Último ajuste, después del '+last.date+':'));
  labels.forEach((label,i)=>root.appendChild(p(label+': '+last.weightsBefore[i].toFixed(5)+' → '+last.weightsAfter[i].toFixed(5))));
 }
 root.appendChild(p('Evaluación histórica exploratoria: '+metric.draws+' sorteos. En cada paso se predice antes de incorporar su resultado; después se aprende del error.'));
 root.appendChild(p('Aciertos principales: modelo '+metric.mainHits+' · Recencia fija '+metric.recencyHits+' · Referencia al azar '+Number(metric.expectedRandomHits).toFixed(2)+'.'));
 root.appendChild(p('Error de estimación (Brier; menor es mejor): modelo '+metric.mainBrier.toFixed(5)+' · Probabilidad uniforme '+metric.uniformBrier.toFixed(5)+'.'));
 if(metric.refundDraws)root.appendChild(p('Reintegro: '+metric.refundHits+' aciertos en '+metric.refundDraws+' sorteos · Referencia al azar '+Number(metric.expectedRandomRefundHits).toFixed(2)+'.'));
 if(active?.version===4)root.appendChild(p('Estos pesos son del candidato entrenado. La combinación designada usa los pesos del modelo activo, que solo cambian al aprobar la evaluación prospectiva.'));
 if(active?.version===3&&model.next?.registered===false)root.appendChild(p('La predicción ya registrada para '+model.next.target+' se conserva. El nuevo motor se aplicará a las siguientes predicciones.'));
 root.appendChild(p('El modelo aprende parámetros; esta simulación histórica no demuestra que prediga mejor. Las mejoras se comprueban con predicciones registradas antes de cada sorteo.','notice'));
}


function renderCentralStatus(report,latest){
 const status=$('sync-status');if(!status)return;
 let message='Mostrando los últimos resultados publicados'+(latest?' · Último sorteo: '+latest:'')+'.';
 if(typeof report?.checkedAt==='string'&&Number.isFinite(Date.parse(report.checkedAt))){
  const checked=new Intl.DateTimeFormat('es-ES',{timeZone:'Europe/Madrid',dateStyle:'short',timeStyle:'short'}).format(new Date(report.checkedAt));
  message+=' Última comprobación central: '+checked+' (hora de Madrid).';
 }else message+=' No se ha podido comprobar la fecha de la última revisión central.';
 if(report?.status==='unavailable')message+=' La última comprobación no pudo obtener resultados oficiales.';
 if(['conflict','invalid-history'].includes(report?.status))message+=' La actualización central está detenida para revisar los datos.';
 if(latest){
  let expected=madridToday();if(madridMinutes()<21*60+40)expected=shiftDay(expected,-1);
  while(!drawDay(expected))expected=shiftDay(expected,-1);
  if(latest<expected)message+=' El resultado del '+expected+' todavía no está incorporado. Se volverá a comprobar en las ejecuciones centrales previstas.';
 }
 status.textContent=message;
}

async function fetchJson(path){const r=await fetch(path+'?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);return r.json()}
let loading=false;
async function load(){
 if(loading)return;loading=true;
 try{await loadContent()}finally{loading=false}
}
async function loadContent(){
 if($('sync-status'))$('sync-status').textContent='Cargando los últimos resultados publicados…';
 const [pred,history,active,verification,update,model,control,quality,patterns,patternLearning,discovery]=await Promise.allSettled([fetchJson('./data/reto-predictor.json'),fetchJson('./data/sorteos.json'),fetchJson('./data/reto-estrategia-activa.json'),fetchJson('./data/verificacion-sorteos.json'),fetchJson('./data/estado-actualizacion.json'),fetchJson('./data/modelo-adaptativo.json'),fetchJson('./data/control-modelo.json'),fetchJson('./data/calidad-datos.json'),fetchJson('./data/analisis-patrones.json'),fetchJson('./data/aprendizaje-patrones.json'),fetchJson('./data/descubrimiento-hipotesis.json')]);
 let proofs=verification.status==='fulfilled'&&Array.isArray(verification.value?.draws)?verification.value.draws:[];
 const report=update.status==='fulfilled'?update.value:null;
 const activeStrategy=active.status==='fulfilled'?active.value:null;
 renderModel(model.status==='fulfilled'?model.value:null,activeStrategy);
 renderControl(control.status==='fulfilled'?control.value:null,activeStrategy);
 renderDecisionHistory(control.status==='fulfilled'?control.value:null);
 renderQuality(quality.status==='fulfilled'?quality.value:null);
 renderPatterns(patterns.status==='fulfilled'?patterns.value:null,discovery.status==='fulfilled'?discovery.value:null);
 renderPatternLearning(patternLearning.status==='fulfilled'?patternLearning.value:null,patterns.status==='fulfilled'?patterns.value:null);
 $('active-strategy').textContent=validActiveStrategy(activeStrategy)?(activeStrategy.version===4?'Motor con evaluación previa · Versión 4. Los pesos activos se mantienen hasta que un candidato supere las pruebas.':activeStrategy.version===3?'Motor activo: modelo que ajusta sus pesos tras cada sorteo · Versión 3. Las predicciones anteriores conservan su motor original.':'Motor activo: recencia 30/90/365 días · Versión '+activeStrategy.version+'. Su evaluación empieza con las nuevas predicciones de esta versión.'):'No se ha podido comprobar la estrategia activa.';
 let draws=[];
 const historyLoaded=history.status==='fulfilled'&&Array.isArray(history.value?.draws);
 if(historyLoaded){
  draws=history.value.draws.filter(r=>r&&validDate(r.date)&&validNumbers(r.nums)).sort((a,b)=>b.date.localeCompare(a.date));
  renderCentralStatus(report,draws[0]?.date);
  $('draws-status').textContent='Último resultado registrado: '+(draws[0]?.date||'ninguno')+'. Actualización del archivo: '+(history.value.updated_at||'no indicada')+'.';
  const root=$('recent-draws');root.replaceChildren();
  const recent=draws.slice(0,5);
  const counts=new Map();
  for(const draw of recent)for(const n of new Set(draw.nums))counts.set(n,(counts.get(n)||0)+1);
  const reintegroCounts=new Map();
  for(const draw of recent)if(validReintegro(draw.reintegro))reintegroCounts.set(draw.reintegro,(reintegroCounts.get(draw.reintegro)||0)+1);
  const repeated=[...counts].filter(([,times])=>times>=2).map(([n])=>n).sort((a,b)=>a-b);
  const colorByNumber=new Map(repeated.map((n,i)=>[n,i]));
  for(const r of recent){
   const item=document.createElement('div');item.className='draw';
   const date=document.createElement('time');date.textContent=r.date;item.appendChild(date);
   const balls=combination(r.nums,r.reintegro);
   for(const b of balls.querySelectorAll('.ball:not(.gold)')){const times=counts.get(Number(b.textContent))||0;if(times>=2){b.classList.add('repeated');b.style.setProperty('--repeat-hue',String((colorByNumber.get(Number(b.textContent))*137.508+25)%360));b.title='Aparece '+times+' veces en los últimos 5 sorteos';const tag=document.createElement('span');tag.className='repeat-count';tag.textContent='×'+times;b.appendChild(tag)}}
   for(const b of balls.children){
    if(!b.className.split(' ').includes('gold'))continue;
    const times=reintegroCounts.get(r.reintegro)||0;
    if(times>=2){
     b.classList.add('repeated-reintegro');
     b.title='Reintegro '+r.reintegro+': aparece '+times+' veces en los últimos 5 sorteos';
     b.setAttribute('aria-label',b.title);
     const tag=document.createElement('span');tag.className='repeat-count';tag.textContent='×'+times;b.appendChild(tag);
    }
   }
   item.appendChild(balls);root.appendChild(item);
   item.appendChild(p(verificationFor(r,proofs),'verification-note'));
  }
  if(!draws.length)root.appendChild(p('No hay sorteos válidos disponibles.'));
 }else {
  $('draws-status').textContent='No se ha podido cargar el histórico actualizado.';
  if($('sync-status'))$('sync-status').textContent='No se ha podido cargar el histórico publicado. Vuelve a intentarlo.';
 }
 const predLoaded=pred.status==='fulfilled'&&Array.isArray(pred.value?.predictions);
 const entries=predLoaded?pred.value.predictions.filter(r=>r&&validDate(r.target)&&validNumbers(r.nums)).sort((a,b)=>b.target.localeCompare(a.target)):[];
 renderCompact(entries,draws,historyLoaded,predLoaded,proofs,patterns.status==='fulfilled'?patterns.value:null,discovery.status==='fulfilled'?discovery.value:null,patternLearning.status==='fulfilled'?patternLearning.value:null);
 if(!predLoaded){renderIncidents([],draws,historyLoaded,false,report); $('prediction-status').textContent='No se pudo cargar el registro de predicciones.';$('tracking').replaceChildren(p('No se pudo cargar el registro de predicciones.'));return}
 renderLearning(entries,draws,activeStrategy,proofs,model.status==='fulfilled'?model.value:null);
 renderIncidents(entries,draws,historyLoaded,true,report);
 renderTracking(entries,draws,historyLoaded,activeStrategy,proofs);
 const latest=entries[0];if(!latest){$('prediction-status').textContent='Aún no hay predicciones registradas.';return}
 const actual=draws.find(d=>d.date===latest.target);
 const status=actual?'Sorteo ya celebrado':!historyLoaded||!draws.length?'Resultado sin comprobar: histórico no disponible':latest.target<madridToday()?'Resultado no disponible en el histórico':'Pendiente de resultado';
 $('prediction-status').textContent='Predicción registrada para '+latest.target+' · Histórico utilizado hasta '+(latest.historyUntil||'fecha no indicada')+' · '+status;
 const root=$('prediction');root.replaceChildren();root.appendChild(combination(latest.nums,latest.reintegro,actual));
 if(!validReintegro(latest.reintegro))root.appendChild(p('No hay un reintegro válido registrado para esta predicción. No se añadirá retrospectivamente.','muted'));
 if(actual){
  const hits=latest.nums.filter(n=>actual.nums.includes(n)).length;
  root.appendChild(p('Resultado: '+hits+' de 6 números acertados'+(validReintegro(latest.reintegro)&&validReintegro(actual.reintegro)?' · Reintegro '+(latest.reintegro===actual.reintegro?'acertado':'no acertado'):'')+'.'));
  root.appendChild(p('Resultado publicado:','muted'));root.appendChild(combination(actual.nums,actual.reintegro));
  root.appendChild(p('✓ señala los aciertos de la predicción. '+verificationFor(actual,proofs)+'.','verification-note'));
 }
 explain(latest,draws,entries);
}
load().catch(()=>{
 $('prediction-status').textContent='No se ha podido cargar la aplicación. Vuelve a intentarlo.';
 for(const id of ['latest-summary','findings-summary','next-summary'])if($(id))$(id).textContent='No se ha podido cargar la aplicación. Vuelve a intentarlo.';
});


if(typeof window!=='undefined'){
 window.addEventListener('pageshow',event=>{if(event.persisted)load().catch(()=>{})});
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')load().catch(()=>{})});
}
