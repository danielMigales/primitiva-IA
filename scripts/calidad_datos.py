"""Validate all records and detect internal gaps in the last 90 calendar days.
A missing result after the latest known draw is pending, not a fabricated error.
"""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import json
from pathlib import Path


def inspect_history(rows, now=None, proofs=None):
    now=(now or datetime.now(ZoneInfo('Europe/Madrid'))).astimezone(ZoneInfo('Europe/Madrid'))
    errors=[];dates={};refund_missing=0;verified=0
    evidence={r.get('date'):r for r in (proofs or []) if isinstance(r,dict)}
    for i,r in enumerate(rows):
        try:
            day=date.fromisoformat(r['date'])
            if day.isoformat()!=r['date'] or day>now.date():raise ValueError('fecha inválida o futura')
            nums=r['nums']
            if not isinstance(nums,list) or len(nums)!=6 or any(type(n)is not int or not 1<=n<=49 for n in nums) or len(set(nums))!=6:
                raise ValueError('seis números no válidos')
            if r['date'] in dates:raise ValueError('fecha duplicada')
            if r.get('reintegro') is None:refund_missing+=1
            elif type(r['reintegro'])is not int or not 0<=r['reintegro']<=9:raise ValueError('reintegro inválido')
            dates[r['date']]=r
            proof=evidence.get(r['date'],{})
            if proof.get('source')=='SELAE' and str(proof.get('url','')).startswith('https://www.loteriasyapuestas.es/') and sorted(proof.get('nums',[]))==sorted(nums) and type(r.get('reintegro'))is int and proof.get('reintegro')==r['reintegro']:
                verified+=1
        except (TypeError,ValueError,KeyError) as exc:
            errors.append({'row':i,'date':r.get('date') if isinstance(r,dict) else None,'reason':str(exc)})
    latest=max(dates) if dates else None
    missing=[];pending=[]
    if latest:
        end=date.fromisoformat(latest);start=max(date.fromisoformat(min(dates)),end-timedelta(days=90))
        for saved_day in dates:
            day=date.fromisoformat(saved_day)
            if day>=start and day.weekday() not in (0,3,5):
                errors.append({'date':saved_day,'reason':'Sorteo fuera del calendario configurado.'})
        for i in range((end-start).days+1):
            day=start+timedelta(days=i)
            if day.weekday() in (0,3,5) and day.isoformat() not in dates:missing.append(day.isoformat())
        due=now.date()
        if (now.hour,now.minute)<(21,40):due-=timedelta(days=1)
        for i in range(1,(due-end).days+1):
            day=end+timedelta(days=i)
            if day.weekday() in (0,3,5):pending.append(day.isoformat())
    else:errors.append({'reason':'histórico vacío'})
    return {'version':1,'checkedAt':now.isoformat(),'valid':not errors and not missing,
            'total':len(rows),'latestDate':latest,'errors':errors,'missingRecentDates':missing,
            'pendingDates':pending,'refundMissing':refund_missing,'fullyVerifiedDraws':verified,
            'calendarScope':'Huecos internos: últimos 90 días del histórico, calendario lunes/jueves/sábado.',
            'note':'Validez estructural no demuestra veracidad ni auditoría oficial completa. Los resultados pendientes se distinguen de huecos internos.'}


if __name__=='__main__':
    data=Path('data')
    history=json.loads((data/'sorteos.json').read_text())['draws']
    proof=json.loads((data/'verificacion-sorteos.json').read_text()) if (data/'verificacion-sorteos.json').exists() else {}
    report=inspect_history(history,proofs=proof.get('draws',[]))
    (data/'calidad-datos.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('valid','total','latestDate','missingRecentDates','pendingDates')}))
    raise SystemExit(0 if report['valid'] else 1)
