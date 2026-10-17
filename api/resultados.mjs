import {RSS_SOURCE,rssResults} from './rss-results.mjs';
import {PDF_SOURCE,pdfResults} from './pdf-results.mjs';
// Fixed upstream: this service cannot proxy arbitrary URLs or write to GitHub.
export const SOURCE = 'https://www.loteriasyapuestas.es/servicios/buscadorSorteos';
export function madridDate(now = new Date()) {
  return new Intl.DateTimeFormat('sv-SE', {timeZone:'Europe/Madrid'}).format(now);
}
export function parseResults(data, from, to) {
  if (!Array.isArray(data)) throw new Error('Formato SELAE desconocido');
  const rows = new Map();
  for (const value of data) {
    const date = value?.fecha_sorteo?.slice(0,10);
    const match = /^\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s+C\((\d{1,2})\)\s+R\((\d)\)\s*$/.exec(value?.combinacion || '');
    if (value?.game_id !== 'LAPR' || !date || !/^\d{4}-\d{2}-\d{2}$/.test(date) || !Number.isFinite(Date.parse(date)) || new Date(date).toISOString().slice(0,10)!==date || date < from || date > to || !match || ![1,4,6].includes(new Date(date+'T00:00:00Z').getUTCDay())) throw new Error('Resultado SELAE inválido');
    const nums = match.slice(1,7).map(Number).sort((a,b)=>a-b), complementario = Number(match[7]);
    if (new Set(nums).size !== 6 || nums.some(n=>n<1||n>49) || complementario<1 || complementario>49 || nums.includes(complementario)) throw new Error('Bolas SELAE inválidas');
    const row = {date, nums, reintegro:Number(match[8]), complementario};
    if (rows.has(date) && JSON.stringify(rows.get(date)) !== JSON.stringify(row)) throw new Error('Resultados SELAE contradictorios');
    rows.set(date,row);
  }
  return [...rows.values()].sort((a,b)=>a.date.localeCompare(b.date));
}
export default {
  async fetch(request, env, ctx) {
    const headers = {'Content-Type':'application/json; charset=utf-8', 'Access-Control-Allow-Origin':'https://danielmigales.github.io', 'Cache-Control':'no-store', 'Vary':'Origin'};
    const respond = (data,status=200)=>new Response(JSON.stringify(data),{status,headers});
    if (request.method !== 'GET') return respond({error:'Método no permitido'},405);
    const url = new URL(request.url);
    if (url.pathname === '/') return respond({service:'Primitiva IA · resultados SELAE',status:'online'});
    if (url.pathname !== '/api/resultados') return respond({error:'No encontrado'},404);
    const to = madridDate(), lower = new Date(Date.parse(to+'T00:00:00Z')-365*86400000).toISOString().slice(0,10);
    let from = url.searchParams.get('from') || new Date(Date.parse(to+'T00:00:00Z')-35*86400000).toISOString().slice(0,10);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(from) || !Number.isFinite(Date.parse(from)) || new Date(from).toISOString().slice(0,10)!==from || from>to) return respond({error:'Fecha inválida'},400);
    if (from<lower) from=lower;
    const upstream = new URL(SOURCE);
    for (const [key,value] of Object.entries({game_id:'LAPR',celebrados:'true',fechaInicioInclusiva:from.replaceAll('-',''),fechaFinInclusiva:to.replaceAll('-','')})) upstream.searchParams.set(key,value);
    upstream.searchParams.set('_',String(Math.floor(Date.now()/60000)));
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),12000);
    try {
      try {
        const result=await fetch(upstream,{headers:{Accept:'application/json','User-Agent':'Mozilla/5.0 (compatible; PrimitivaIA/1.0)'},signal:controller.signal,redirect:'manual'});
        if(!result.ok)throw Error('SELAE HTTP '+result.status);
        const text=await result.text();if(text.length>2000000)throw Error('Respuesta demasiado grande');
        const draws=parseResults(JSON.parse(text),from,to);
        return respond({version:1,source:'SELAE',sourceUrl:upstream.href,checkedAt:new Date().toISOString(),from,to,draws});
      } catch(error) {
        console.warn('Servicio JSON SELAE no disponible:',error?.message);
        try{
          const rss=await rssResults(from,to,controller.signal);
          return respond({version:1,source:'SELAE',sourceUrl:RSS_SOURCE,publicationStatus:'official-rss',checkedAt:new Date().toISOString(),from:rss.from,to,draws:rss.draws});
        }catch(rssError){console.warn('Canal RSS SELAE no disponible:',rssError?.message)}
        const official=await pdfResults(from,to,controller.signal);
        return respond({version:1,source:'SELAE',sourceUrl:PDF_SOURCE,publicationStatus:'official-press-pdfs',checkedAt:new Date().toISOString(),from:official.from,to,draws:official.draws,unavailableDates:official.unavailableDates});
      }
    } catch(error) {
      console.error('Consulta SELAE:',error?.name,error?.message);
      return respond({error:'No se ha podido consultar SELAE. No se puede determinar si los resultados están publicados.'},502);
    } finally {clearTimeout(timer)}
  }
};
