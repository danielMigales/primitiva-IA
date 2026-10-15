const test=require('node:test');
const assert=require('node:assert/strict');
const live=require('../live-results.js');
const now=new Date('2026-10-15T20:15:00Z');
const row={date:'2026-10-15',nums:[6,17,24,35,39,47],reintegro:3,complementario:18};
const url='https://www.loteriasyapuestas.es/servicios/buscadorSorteos?game_id=LAPR';
function mock(draws){global.fetch=async()=>({ok:true,json:async()=>({source:'SELAE',sourceUrl:url,checkedAt:now.toISOString(),to:'2026-10-15',draws})})}
const history=[{...row,date:'2026-10-12'}];
test('Madrid calendar includes the draw only from 21:40 and handles winter',()=>{
 assert.equal(live.expected(new Date('2026-10-15T19:39:00Z')),'2026-10-12');
 assert.equal(live.expected(now),'2026-10-15');
 assert.equal(live.expected(new Date('2026-12-03T20:39:00Z')),'2026-11-30');
 assert.equal(live.expected(new Date('2026-12-03T20:40:00Z')),'2026-12-03');
});
test('fresh official results replace a provisional result and supply matching evidence',async()=>{
 mock([row]);
 const result=await live.sync('https://results.example/api/resultados',[{...row,reintegro:8}],[],now);
 assert.equal(result.draws[0].reintegro,3);
 assert.equal(result.proofs[0].source,'SELAE');
 assert.equal(result.proofs[0].url,url);
});
test('successful empty results say unpublished rather than a connection failure',async()=>{
 mock([]);const result=await live.sync('https://results.example/api/resultados',history,[],now);
 assert.match(result.message,/SELAE aún no ha publicado/);
 assert.equal(result.draws.length,1);
});
test('network failure cannot be reported as unpublished',async()=>{
 global.fetch=async()=>{throw Error('offline')};
 await assert.rejects(live.sync('https://results.example/api/resultados',history,[],now),/offline/);
});
test('invalid or future results and verified conflicts do not overwrite history',async()=>{
 mock([{...row,nums:[1,1,1,1,1,1]}]);
 await assert.rejects(live.sync('https://results.example/api/resultados',history,[],now),/no es válida/);
 mock([{...row,date:'2026-10-17'}]);
 await assert.rejects(live.sync('https://results.example/api/resultados',history,[],now),/no es válida/);
 mock([row]);
 await assert.rejects(live.sync('https://results.example/api/resultados',history,[{...row,source:'SELAE',reintegro:4}],now),/Discrepancia/);
});
test('server parses published SELAE response, rejects other games and never invents empty results on failure',async()=>{
 const {parseResults,default:worker}=await import('../api/resultados.mjs');
 assert.deepEqual(parseResults([{game_id:'LAPR',fecha_sorteo:'2026-10-15 21:42:00',combinacion:'06 - 17 - 24 - 35 - 39 - 47 C(18) R(3)'}],'2026-10-12','2026-10-15'),[row]);
 assert.throws(()=>parseResults([{game_id:'BONO',fecha_sorteo:'2026-10-15',combinacion:'06 - 17 - 24 - 35 - 39 - 47 C(18) R(3)'}],'2026-10-12','2026-10-15'));
 global.fetch=async()=>{throw Error('offline')};
 const response=await worker.fetch(new Request('https://results.example/api/resultados'));
 assert.equal(response.status,502);
 assert.match((await response.json()).error,/No se puede determinar/);
});
