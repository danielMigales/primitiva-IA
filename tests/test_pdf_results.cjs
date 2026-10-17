const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const live=require('../live-results.js');
const text='En el sorteo de la Lotería Primitiva celebrado hoy jueves día 15 de octubre de 2026\nla combinación ganadora ha correspondido a los siguientes números:\n24 - 17 - 35 - 47 - 06 - 39 Complementario 18 Reintegro 3 JOKER: 2666233\nLa recaudación del sorteo ascendió a 11.613.570,00';
test('official PDF parser requires exact date, game and unambiguous eight balls',async()=>{
 const {parsePdfText,pdfUrls}=await import('../api/pdf-results.mjs');
 assert.deepEqual(parsePdfText(text,'2026-10-15'),{date:'2026-10-15',nums:[6,17,24,35,39,47],complementario:18,reintegro:3});
 for(const bad of [text.replace('2026','2025'),text.replace('Lotería Primitiva','Bonoloto'),text.replace('24 - 17','24 - 24'),text.replace('Reintegro 3','Reintegro 12'),text+'\nla combinación ganadora ha correspondido a los siguientes números:'])assert.throws(()=>parsePdfText(bad,'2026-10-15'));
 assert.ok(pdfUrls('2026-10-17').some(x=>x.includes('S%C3%81BADO')));
});
test('PDF fallback skips only missing documents and rejects blocked or invalid sources',async()=>{
 const {pdfResults}=await import('../api/pdf-results.mjs');
 global.fetch=async()=>({ok:true,status:200,headers:new Headers(),arrayBuffer:async()=>new TextEncoder().encode('%PDF-test').buffer});
 const result=await pdfResults('2026-10-15','2026-10-15',new AbortController().signal,async()=>text);
 assert.equal(result.draws.length,1);
 assert.match(result.draws[0].sourceUrl,/NOTA_DE_PRENSA/);
 global.fetch=async()=>({ok:false,status:404});
 assert.equal((await pdfResults('2026-10-15','2026-10-15',undefined,async()=>text)).draws.length,0);
 global.fetch=async()=>({ok:false,status:403});
 await assert.rejects(pdfResults('2026-10-15','2026-10-15',undefined,async()=>text),/403/);
 global.fetch=async()=>({ok:true,status:200,headers:new Headers(),arrayBuffer:async()=>new TextEncoder().encode('<html>bad</html>').buffer});
 await assert.rejects(pdfResults('2026-10-15','2026-10-15',undefined,async()=>text),/no válido/);
});
test('live PDF evidence keeps individual official URL and does not claim unpublished results',async()=>{
 const {PDF_SOURCE}=await import('../api/pdf-results.mjs');
 const now=new Date('2026-10-15T20:15:00Z');
 const row={date:'2026-10-15',nums:[6,17,24,35,39,47],reintegro:3,complementario:18,sourceUrl:PDF_SOURCE+'NOTA_DE_PRENSA_LA_PRIMITIVA_JUEVES_15_10_26.pdf'};
 const payload={source:'SELAE',sourceUrl:PDF_SOURCE,publicationStatus:'official-press-pdfs',checkedAt:now.toISOString(),to:'2026-10-15',from:'2026-10-15',draws:[row]};
 global.fetch=async()=>({ok:true,json:async()=>payload});
 const good=await live.sync('https://results.example/api/resultados',[row],[],now);
 assert.equal(good.proofs[0].url,row.sourceUrl);
 assert.match(good.message,/Resultados actualizados/);
 payload.draws=[];
 const missing=await live.sync('https://results.example/api/resultados',[row],[],now);
 assert.match(missing.message,/No se ha localizado la nota oficial/);
 assert.doesNotMatch(missing.message,/no ha publicado/);
 payload.draws=[{...row,sourceUrl:'https://example.com/fake.pdf'}];
 await assert.rejects(live.sync('https://results.example/api/resultados',[row],[],now),/no es válida/);
});

test('partial official PDF availability never discards verified rows or claims unpublished',async()=>{
 const {pdfResults,PDF_SOURCE}=await import('../api/pdf-results.mjs');
 global.fetch=async url=>url.includes('JUEVES_15_')?{ok:true,status:200,headers:new Headers(),arrayBuffer:async()=>new TextEncoder().encode('%PDF-test').buffer}:{ok:false,status:403};
 const official=await pdfResults('2026-10-15','2026-10-17',undefined,async()=>text);
 assert.equal(official.draws.length,1);
 assert.deepEqual(official.unavailableDates,['2026-10-17']);
 const now=new Date('2026-10-17T20:15:00Z');
 global.fetch=async()=>({ok:true,json:async()=>({source:'SELAE',sourceUrl:PDF_SOURCE,publicationStatus:'official-press-pdfs',checkedAt:now.toISOString(),from:official.from,to:'2026-10-17',draws:official.draws,unavailableDates:official.unavailableDates})});
 const result=await live.sync('https://results.example/api/resultados',official.draws,[],now);
 assert.match(result.message,/No se ha podido comprobar SELAE/);
 assert.doesNotMatch(result.message,/no ha publicado/);
});
