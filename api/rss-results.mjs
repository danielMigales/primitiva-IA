export const RSS_SOURCE='https://www.loteriasyapuestas.es/es/la-primitiva/resultados/.formatoRSS';
const months=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
const decode=s=>s.replace(/&(?:aacute|eacute|iacute|oacute|uacute|ntilde|nbsp|amp);/g,x=>({'&aacute;':'á','&eacute;':'é','&iacute;':'í','&oacute;':'ó','&uacute;':'ú','&ntilde;':'ñ','&nbsp;':' ','&amp;':'&'}[x]));
export function parseRss(xml,from,to){
 if(!xml.includes('<rss')||!xml.includes('Resultados y escrutinio de La Primitiva'))throw Error('Canal oficial no identificado');
 const items=[...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)];
 if(!items.length)throw Error('RSS sin resultados identificables');
 const rows=new Map();
 for(const [,item] of items){
  const title=decode(item.match(/<title>([\s\S]*?)<\/title>/)?.[1]||'').trim();
  const dateMatch=/^La Primitiva: premios y ganadores del (\d{1,2}) de ([a-z]+) de (\d{4})$/.exec(title);
  if(!dateMatch)throw Error('Título RSS inesperado');
  const month=months.indexOf(dateMatch[2])+1;
  const day=dateMatch[3]+'-'+String(month).padStart(2,'0')+'-'+dateMatch[1].padStart(2,'0');
  if(!month||!Number.isFinite(Date.parse(day))||new Date(day).toISOString().slice(0,10)!==day||![1,4,6].includes(new Date(day).getUTCDay()))throw Error('Fecha RSS inválida');
  const pubDate=Date.parse(item.match(/<pubDate>([^<]+)<\/pubDate>/)?.[1]||'');
  if(!Number.isFinite(pubDate)||new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Madrid'}).format(new Date(pubDate))!==day)throw Error('Fecha de publicación RSS incoherente');
  const sourceUrl=(item.match(/<link>([\s\S]*?)<\/link>/)?.[1]||'').replace('<![CDATA[','').replace(']]>','').trim();
  if(!sourceUrl.startsWith('https://www.loteriasyapuestas.es/es/la-primitiva/escrutinios/')||!sourceUrl.endsWith('.formatoRSS'))throw Error('Enlace RSS inválido');
  const description=item.match(/<description>([\s\S]*?)<\/description>/)?.[1]||'';
  const plain=decode(description.replace(/<!\[CDATA\[|\]\]>/g,'').replace(/<[^>]*>/g,' ')).replace(/\s+/g,' ').trim();
  const block=plain.split('El reparto de premios')[0];
  if(!block.includes('En el sorteo de La Primitiva')||!block.includes('la combinación ganadora ha correspondido a los siguientes números:'))throw Error('Cabecera RSS inválida');
  const matches=[...block.matchAll(/(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s+Complementario:\s*C\((\d{1,2})\)\s+Reintegro:\s*R\((\d)\)\s+Joker:\s*J\(\d{7}\)/g)];
  if(matches.length!==1)throw Error('Combinación RSS ambigua');
  const nums=matches[0].slice(1,7).map(Number).sort((a,b)=>a-b),complementario=Number(matches[0][7]),reintegro=Number(matches[0][8]);
  if(new Set(nums).size!==6||nums.some(n=>n<1||n>49)||complementario<1||complementario>49||nums.includes(complementario))throw Error('Bolas RSS inválidas');
  const row={date:day,nums,complementario,reintegro,sourceUrl};
  if(rows.has(day)&&JSON.stringify(rows.get(day))!==JSON.stringify(row))throw Error('Resultados RSS contradictorios');
  rows.set(day,row);
 }
 const oldest=[...rows.keys()].sort()[0];
 return {from:oldest>from?oldest:from,draws:[...rows.values()].filter(r=>r.date>=from&&r.date<=to).sort((a,b)=>a.date.localeCompare(b.date))};
}
export async function rssResults(from,to,signal){
 const response=await fetch(RSS_SOURCE,{headers:{Accept:'application/rss+xml,application/xml','User-Agent':'Mozilla/5.0 (compatible; PrimitivaIA/1.0)'},signal,redirect:'manual'});
 if(!response.ok)throw Error('RSS SELAE HTTP '+response.status);
 const xml=await response.text();if(xml.length>2000000)throw Error('RSS demasiado grande');
 return parseRss(xml,from,to);
}
