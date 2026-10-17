const test=require('node:test');const assert=require('node:assert/strict');
const live=require('../live-results.js');
const item=`<item><title>La Primitiva: premios y ganadores del 15 de octubre de 2026</title><pubDate>Thu, 15 Oct 2026 22:03:00 +0200</pubDate><link>https://www.loteriasyapuestas.es/es/la-primitiva/escrutinios/la-primitiva-premios-y-ganadores-del-15-de-octubre-de-2026.formatoRSS</link><description><![CDATA[<p>En el sorteo de La Primitiva del 15 de octubre de 2026, la combinaci&oacute;n ganadora ha correspondido a los siguientes n&uacute;meros:</p><p><b>06 - 17 - 24 - 35 - 39 - 47</b> Complementario: <b>C(18)</b> Reintegro: <b>R(3)</b> Joker: <b>J(2666233)</b></p><p>El reparto de premios</p>]]></description></item>`;
const xml=`<rss><channel><description>Resultados y escrutinio de La Primitiva</description>${item}</channel></rss>`;
test('official RSS validates date, game, publication, permalink and winning block',async()=>{
 const {parseRss}=await import('../api/rss-results.mjs');
 const result=parseRss(xml,'2026-10-01','2026-10-17');assert.equal(result.draws.length,1);assert.equal(result.from,'2026-10-15');
 assert.deepEqual(result.draws[0].nums,[6,17,24,35,39,47]);
 for(const bad of [xml.replace('22:03:00','00:03:00').replace('+0200','+1400'),xml.replace('06 - 17','06 - 06'),xml.replace('C(18)','C(17)'),xml.replace('es/la-primitiva/escrutinios','evil/path'),xml.replace('En el sorteo de La Primitiva','En el sorteo de Bonoloto'),'<rss></rss>'])assert.throws(()=>parseRss(bad,'2026-10-01','2026-10-17'));
});
test('RSS results synchronize with individual evidence and an accurate pending notice',async()=>{
 const {parseRss,RSS_SOURCE}=await import('../api/rss-results.mjs');
 const now=new Date('2026-10-17T20:00:00Z'),result=parseRss(xml,'2026-10-01','2026-10-17');
 global.fetch=async()=>({ok:true,json:async()=>({source:'SELAE',sourceUrl:RSS_SOURCE,publicationStatus:'official-rss',checkedAt:now.toISOString(),to:'2026-10-17',...result})});
 const merged=await live.sync('https://results.example/api/resultados',result.draws,[],now);
 assert.match(merged.message,/canal oficial de SELAE aún no muestra/);assert.match(merged.proofs[0].url,/escrutinios/);
});
test('worker falls back to official RSS when JSON is blocked',async()=>{
 const {default:worker}=await import('../api/resultados.mjs');
 global.fetch=async url=>String(url).includes('buscadorSorteos')?{ok:false,status:403}:{ok:true,text:async()=>xml};
 const response=await worker.fetch(new Request('https://results.example/api/resultados?from=2026-10-01'));
 assert.equal(response.status,200);const data=await response.json();assert.equal(data.publicationStatus,'official-rss');assert.equal(data.draws[0].reintegro,3);
});
