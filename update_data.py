#!/usr/bin/env python3
"""Refresh public La Primitiva draw history. Stdlib only; no API keys."""
import csv, io, json, re, urllib.request, datetime, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parent
DEST=ROOT/'data'/'sorteos.json'
SOURCES=[
 ('artdecos/primitiva','Histórico de sorteos de La Primitiva.csv'),
 ('Lorenhdc/Proyecto_LaPrimitiva','Dataset_primitiva.csv'),
]
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'PrimitivaResearch/1.0','Accept':'application/vnd.github+json'})
 with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode('utf-8-sig',errors='replace')
def date_parse(s):
 s=s.strip(); m=re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',s)
 if m:
  d,mn,y=map(int,m.groups());return datetime.date(y,mn,d).isoformat()
 m=re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',s)
 if m:
  y,mn,d=map(int,m.groups());return datetime.date(y,mn,d).isoformat()
 return None
def valid(nums):return len(nums)==6 and len(set(nums))==6 and all(1<=n<=49 for n in nums)
def extract(text):
 rows=[]
 for delim in (';',',','\t','|'):
  try:
   rdr=csv.reader(io.StringIO(text),delimiter=delim)
   found=[]
   for row in rdr:
    if not row:continue
    date=next((d for c in row if (d:=date_parse(c))),None)
    if not date:continue
    cells=[]
    for c in row:
     if date_parse(c):continue
     cells.append(c.strip())
    # Support columns with six distinct numbers or one combined field.
    values=[]
    for c in cells:
     if re.fullmatch(r'\d{1,2}',c):values.append(int(c))
     elif len(values)<6 and re.fullmatch(r'\s*\d{1,2}(?:[\s-]+\d{1,2}){5,7}\s*',c):values.extend(map(int,re.findall(r'\d+',c)))
    nums=values[:6]
    if valid(nums):found.append({'date':date,'nums':sorted(nums)})
   if len(found)>len(rows):rows=found
  except (csv.Error,ValueError):pass
 return rows
def main():
 existing={}
 if DEST.exists():
  try:existing={r['date']:r for r in json.loads(DEST.read_text())['draws'] if valid(r['nums'])}
  except (ValueError,KeyError,TypeError):pass
 incoming={};used=[]
 for repo,filename in SOURCES:
  from urllib.parse import quote
  for branch in ('main','master'):
   url=f'https://raw.githubusercontent.com/{repo}/{branch}/{quote(filename)}'
   try:
    rows=extract(get(url))
    if len(rows)<100:continue
    for r in rows:
     if r['date'] in incoming and incoming[r['date']]['nums']!=r['nums']:
      print('Conflicting draw:',r['date'],file=sys.stderr);continue
     incoming[r['date']]=r
    used.append(url);break
   except Exception as e:print('Source unavailable:',url,str(e)[:150],file=sys.stderr)
 if not incoming:
  print('No valid source downloaded; existing file unchanged',file=sys.stderr);return 1
 # Avoid overwriting known results with conflicting values; flag and keep previous.
 conflicts=[d for d,r in incoming.items() if d in existing and existing[d]['nums']!=r['nums']]
 if conflicts:
  print('Conflict with existing data, aborting:',conflicts[:10],file=sys.stderr);return 1
 merged={**existing,**incoming};draws=[merged[k] for k in sorted(merged)]
 if len(draws)<100:print('Insufficient valid draws',file=sys.stderr);return 1
 DEST.parent.mkdir(parents=True,exist_ok=True)
 output={'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':used,'draws':draws}
 DEST.write_text(json.dumps(output,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 print(f'Validated {len(draws)} draws, last {draws[-1]["date"]}; sources: {len(used)}')
 return 0
if __name__=='__main__':sys.exit(main())
