"""Train version 3 on prior draws; preserve every registered prediction."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from modelo_adaptativo import ALGORITHM, PARAMETERS, train
from validar_reto import validate_prediction

config=json.loads(Path('data/reto-estrategia-activa.json').read_text())
if config.get('version')!=3 or config.get('status')!='active' or config.get('strategy')!={'type':'online-logistic','window':99999,'algorithm':ALGORITHM,'reintegroAlgorithm':ALGORITHM,'parameters':PARAMETERS}:
    raise ValueError('La estrategia activa no coincide con la versión 3 aprobada.')
now=datetime.now(ZoneInfo('Europe/Madrid'))
day=now.date()
if (now.hour,now.minute)>=(21,40):
    day+=timedelta(days=1)
while day.weekday() not in (0,3,5):
    day+=timedelta(days=1)
target=day.isoformat()
rows=sorted(json.loads(Path('data/sorteos.json').read_text())['draws'],key=lambda r:r['date'])
report=train(rows,target)
path=Path('data/reto-predictor.json')
registry=json.loads(path.read_text())
existing=any(r['target']==target for r in registry['predictions'])
entry={'target':target,'nums':report['next']['nums'],'reintegro':report['next']['reintegro'],
       'window':99999,'historyUntil':rows[-1]['date'],'created':now.isoformat(),
       'algorithm':ALGORITHM,'reintegroAlgorithm':ALGORITHM,'strategyVersion':3,
       'strategyFile':'data/reto-estrategia-activa.json','modelId':report['modelId'],
       'numberEvidence':report['numberEvidence'],'reintegroEvidence':{'estimatedScore':report['refundScore']},
       'goal':config['objective'],'recordedBy':'Modelo logístico entrenado cronológicamente; commit de GitHub acredita publicación'}
if not existing:
    validate_prediction(entry,rows[-1]['date'])
report['next']['registered']=not existing
report['next']['note']='Propuesta del modelo; se conserva la predicción existente para este sorteo.' if existing else 'Predicción nueva registrada.'
Path('data/modelo-adaptativo.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if existing:
    print('Already recorded',target,'; modelo entrenado sin sustituir la predicción.')
    raise SystemExit(0)
registry['predictions'].append(entry)
registry['predictions'].sort(key=lambda r:r['target'])
path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
print('Prospective prediction:',target,entry['nums'])
