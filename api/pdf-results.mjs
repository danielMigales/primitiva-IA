export const PDF_SOURCE='https://www.loteriasyapuestas.es/f/loterias/documentos/La%20Primitiva/Notas%20de%20prensa/';
const weekdays={1:'LUNES',4:'JUEVES',6:'SABADO'};
const months=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
const fold=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
export function pdfUrls(day){
 const d=new Date(day+'T00:00:00Z'),w=d.getUTCDay();if(!weekdays[w])throw Error('Fecha fuera de calendario');
 const names=w===6?['SÁBADO','SABADO']:[weekdays[w]];
 const dates=w===4?[String(d.getUTCDate()).padStart(2,'0'),String(d.getUTCDate())]:[String(d.getUTCDate()),String(d.getUTCDate()).padStart(2,'0')];
 return [...new Set(names.flatMap(name=>dates.flatMap(n=>[String(d.getUTCMonth()+1),String(d.getUTCMonth()+1).padStart(2,'0')].map(month=>PDF_SOURCE+encodeURIComponent('NOTA_DE_PRENSA_LA_PRIMITIVA_'+name+'_'+n+'_'+month+'_'+String(d.getUTCFullYear()).slice(-2)+'.pdf')))))];
}
export function parsePdfText(text,target){
 const normalized=fold(text),marker='la combinacion ganadora ha correspondido a los siguientes numeros:';
 if(normalized.split(marker).length!==2)throw Error('Bloque oficial ambiguo');
 const [header,body]=normalized.split(marker);
 if(!header.includes('loteria primitiva'))throw Error('Juego incorrecto');
 const dates=[...header.matchAll(/(lunes|jueves|sabado)\s+dia\s+(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})/g)];
 const d=new Date(target+'T00:00:00Z');
 if(dates.length!==1||Number(dates[0][2])!==d.getUTCDate()||months.indexOf(dates[0][3])!==d.getUTCMonth()||Number(dates[0][4])!==d.getUTCFullYear()||dates[0][1]!==fold(weekdays[d.getUTCDay()]||''))throw Error('Fecha oficial incorrecta');
 if(!body.includes('la recaudacion'))throw Error('Resultados sin delimitación');
 let block=body.split('la recaudacion')[0];
 if(block.split('complementario').length!==2||block.split('reintegro').length!==2||!block.match(/joker:\s*\d{7}/))throw Error('Campos oficiales incompletos');
 block=block.replace(/joker:\s*\d{7}/,'').replace('complementario',' ').replace('reintegro',' ');
 if(!/^[\d\s-]+$/.test(block))throw Error('Formato oficial desconocido');
 const values=(block.match(/\d+/g)||[]).map(Number);
 if(values.length!==8)throw Error('Número de bolas ambiguo');
 const nums=values.slice(0,6).sort((a,b)=>a-b),complementario=values[6],reintegro=values[7];
 if(new Set(nums).size!==6||nums.some(n=>n<1||n>49)||complementario<1||complementario>49||nums.includes(complementario)||reintegro<0||reintegro>9)throw Error('Bolas oficiales inválidas');
 return {date:target,nums,complementario,reintegro};
}
export async function extractPdf(bytes){
 const {getDocumentProxy}=await import('unpdf');
 const pdf=await getDocumentProxy(bytes,{isEvalSupported:false,useSystemFonts:false,disableFontFace:true});
 try{
  if(pdf.numPages!==1)throw Error('Nota oficial con número de páginas inesperado');
  const page=await pdf.getPage(1),content=await page.getTextContent();
  const items=content.items.filter(i=>i.str?.trim()).map(i=>({text:i.str,x:i.transform[4],y:i.transform[5]})).sort((a,b)=>b.y-a.y||a.x-b.x);
  const lines=[];
  for(const item of items){let line=lines.at(-1);if(!line||Math.abs(line.y-item.y)>2){line={y:item.y,items:[]};lines.push(line)}line.items.push(item)}
  return lines.map(l=>l.items.sort((a,b)=>a.x-b.x).map(i=>i.text).join(' ')).join('\n');
 }finally{await pdf.loadingTask.destroy()}
}
export async function pdfResults(from,to,signal,extract=extractPdf){
 const lower=new Date(Date.parse(to+'T00:00:00Z')-14*86400000).toISOString().slice(0,10);
 if(from<lower)from=lower;
 const days=[];
 for(let day=from;day<=to;day=new Date(Date.parse(day+'T00:00:00Z')+86400000).toISOString().slice(0,10))if(weekdays[new Date(day).getUTCDay()])days.push(day);
 const results=await Promise.allSettled(days.map(async day=>{
  for(const url of pdfUrls(day)){
   const response=await fetch(url,{headers:{Accept:'application/pdf','User-Agent':'Mozilla/5.0 (compatible; PrimitivaIA/1.0)'},signal,redirect:'manual'});
   if(response.status===404)continue;
   if(!response.ok)throw Error('PDF SELAE HTTP '+response.status);
   if(Number(response.headers?.get('Content-Length')||0)>1500000)throw Error('PDF demasiado grande');
   const bytes=new Uint8Array(await response.arrayBuffer());
   if(bytes.length>1500000||new TextDecoder().decode(bytes.slice(0,5))!=='%PDF-')throw Error('Documento oficial no válido');
   const row=parsePdfText(await extract(bytes),day);
   return {...row,sourceUrl:url};
  }
  return null;
 }));
 const draws=results.filter(r=>r.status==='fulfilled'&&r.value).map(r=>r.value);
 const unavailableDates=days.filter((day,i)=>results[i].status==='rejected');
 if(!draws.length&&unavailableDates.length)throw results.find(r=>r.status==='rejected').reason;
 return {draws,from,unavailableDates};
}
