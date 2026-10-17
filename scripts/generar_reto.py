"""Train candidates and apply only prospectively accepted weights; preserve every registered prediction."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from modelo_adaptativo import PARAMETERS, train
from validar_reto import validate_prediction
from control_modelo import POLICY, update_control
from calidad_datos import inspect_history

config=json.loads(Path('data/reto-estrategia-activa.json').read_text())
if config.get('version')!=4 or config.get('status')!='active' or config.get('strategy')!={'type':'guarded-online-logistic','window':99999,'algorithm':'guarded-online-logistic-v1','reintegroAlgorithm':'guarded-online-logistic-v1','parameters':PARAMETERS}:
    raise ValueError('La estrategia activa no coincide con la versión 4 aprobada.')
if config.get('promotionPolicy')!=POLICY:
    raise ValueError('La política de evaluación no coincide con la aprobada.')
now=datetime.now(ZoneInfo('Europe/Madrid'))
day=now.date()
if (now.hour,now.minute)>=(21,40):
    day+=timedelta(days=1)
while day.weekday() not in (0,3,5):
    day+=timedelta(days=1)
target=day.isoformat()
rows=sorted(json.loads(Path('data/sorteos.json').read_text())['draws'],key=lambda r:r['date'])
proof_path=Path('data/verificacion-sorteos.json')
proofs=json.loads(proof_path.read_text()).get('draws',[]) if proof_path.exists() else []
quality=inspect_history(rows,now,proofs)
Path('data/calidad-datos.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2)+'\n')
if not quality['valid']:
    raise ValueError('Histórico inválido o con huecos recientes: entrenamiento detenido; revisar calidad-datos.json.')
report=train(rows,target)
control_path=Path('data/control-modelo.json')
# Missing control state must stop generation, never silently approve new weights.
previous=json.loads(control_path.read_text())
control,selected=update_control(report,rows,target,now,previous)
path=Path('data/reto-predictor.json')
registry=json.loads(path.read_text())
existing=any(r['target']==target for r in registry['predictions'])
entry={'target':target,'nums':selected['nums'],'reintegro':selected['reintegro'],
       'window':99999,'historyUntil':rows[-1]['date'],'created':now.isoformat(),
       'algorithm':'guarded-online-logistic-v1','reintegroAlgorithm':'guarded-online-logistic-v1','strategyVersion':4,
       'strategyFile':'data/reto-estrategia-activa.json','modelId':control['champion']['modelId'],'weightsTrainedUntil':control['champion']['historyUntil'],
       'numberEvidence':selected['numberEvidence'],'reintegroEvidence':{'estimatedScore':selected['refundScore']},
       'goal':config['objective'],'recordedBy':'Modelo activo con pesos protegidos por evaluación prospectiva; commit de GitHub acredita publicación'}
if not existing:
    validate_prediction(entry,rows[-1]['date'])
report['next']['registered']=False
report['activeNext']={**selected,'modelId':control['champion']['modelId'],'target':target,'registered':not existing}
report['next']['note']='Propuesta del entrenamiento, sin autorización para sustituir al modelo activo.'
control_path.write_text(json.dumps(control,ensure_ascii=False,indent=2)+'\n')
Path('data/modelo-adaptativo.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if existing:
    print('Already recorded',target,'; modelo entrenado sin sustituir la predicción.')
    raise SystemExit(0)
registry['predictions'].append(entry)
registry['predictions'].sort(key=lambda r:r['target'])
path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
print('Prospective prediction:',target,entry['nums'])
