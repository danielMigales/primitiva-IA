(function(root){
 const SOURCE='https://www.loteriasyapuestas.es/servicios/buscadorSorteos';
 function valid(row){return row&&/^\d{4}-\d{2}-\d{2}$/.test(row.date)&&Number.isFinite(Date.parse(row.date))&&new Date(row.date).toISOString().slice(0,10)===row.date&&[1,4,6].includes(new Date(row.date).getUTCDay())&&Array.isArray(row.nums)&&row.nums.length===6&&new Set(row.nums).size===6&&row.nums.every(n=>Number.isInteger(n)&&n>=1&&n<=49)&&Number.isInteger(row.reintegro)&&row.reintegro>=0&&row.reintegro<=9&&Number.isInteger(row.complementario)&&row.complementario>=1&&row.complementario<=49&&!row.nums.includes(row.complementario)}
 function expected(now=new Date()){
  const parts=Object.fromEntries(new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Madrid',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(now).map(p=>[p.type,p.value]));
  let day=parts.year+'-'+parts.month+'-'+parts.day;
  const back=()=>{day=new Date(Date.parse(day+'T00:00:00Z')-86400000).toISOString().slice(0,10)};
  if(Number(parts.hour)*60+Number(parts.minute)<21*60+40)back();
  while(![1,4,6].includes(new Date(day+'T00:00:00Z').getUTCDay()))back();
  return day;
 }
 async function sync(endpoint,draws,proofs,now=new Date()){
  if(!endpoint)throw new Error('Servicio de actualización pendiente de activar.');
  const latest=draws.map(r=>r.date).sort().at(-1)||expected(now);
  const from=new Date(Date.parse(latest+'T00:00:00Z')-14*86400000).toISOString().slice(0,10);
  const response=await fetch(endpoint+'?from='+from,{cache:'no-store',signal:AbortSignal.timeout(15000)});
  if(!response.ok)throw new Error('No se ha podido conectar con SELAE. Se mantienen los últimos datos guardados.');
  const data=await response.json();
  const source=new URL(data.sourceUrl);
  if(data.source!=='SELAE'||source.origin+source.pathname!==SOURCE||!Number.isFinite(Date.parse(data.checkedAt))||Math.abs(now-Date.parse(data.checkedAt))>5*60000||!Array.isArray(data.draws)||data.draws.some(r=>!valid(r)||r.date<from||r.date>data.to)||new Set(data.draws.map(r=>r.date)).size!==data.draws.length)throw new Error('La respuesta de SELAE no es válida. Se mantienen los datos guardados.');
  const merged=new Map(draws.map(r=>[r.date,r])),verified=new Map(proofs.map(r=>[r.date,r]));
  for(const row of data.draws){
   const proof=verified.get(row.date);
   if(proof?.source==='SELAE'&&Array.isArray(proof.nums)&&([...proof.nums].sort((a,b)=>a-b).join(',')!==row.nums.join(',')||(Number.isInteger(proof.reintegro)&&proof.reintegro!==row.reintegro)))throw new Error('Discrepancia con un resultado previamente cotejado. Revisión necesaria.');
   merged.set(row.date,{...row,sourceType:'official-results-service',sourceUrl:data.sourceUrl});
   verified.set(row.date,{...row,source:'SELAE',url:data.sourceUrl,checkedAt:data.checkedAt});
  }
  const due=expected(now),missing=[];
  for(let day=from;day<=due;day=new Date(Date.parse(day+'T00:00:00Z')+86400000).toISOString().slice(0,10))if([1,4,6].includes(new Date(day).getUTCDay())&&!data.draws.some(r=>r.date===day))missing.push(day);
  return {draws:[...merged.values()].sort((a,b)=>b.date.localeCompare(a.date)),proofs:[...verified.values()],checkedAt:data.checkedAt,message:missing.length?'SELAE aún no ha publicado los resultados de los sorteos: '+missing.join(', ')+'.':'Resultados actualizados con SELAE. Último sorteo: '+due+'.'};
 }
 const api={sync,expected,valid};if(typeof module!=='undefined')module.exports=api;else root.PrimitivaLive=api;
})(globalThis);
