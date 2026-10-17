"""Train candidates and apply only prospectively accepted weights; preserve every registered prediction."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from modelo_adaptativo import PARAMETERS, train
from validar_reto import validate_prediction
from control_modelo import POLICY, update_control
from calidad_datos import inspect_history
from analizar_patrones import analyze
from aprender_patrones import train_patterns, register_experiment, PARAMETERS as PATTERN_PARAMETERS

config=json.loads(Path('data/reto-estrategia-activa.json').read_text())
if config.get('version')!=4 or config.get('status')!='active' or config.get('strategy')!={'type':'guarded-online-logistic','window':99999,'algorithm':'guarded-online-logistic-v1','reintegroAlgorithm':'guarded-online-logistic-v1','parameters':PARAMETERS}:
    raise ValueError('La estrategia activa no coincide con la versión 4 aprobada.')
if config.get('promotionPolicy')!=POLICY:
    raise ValueError('La política de evaluación no coincide con la aprobada.')
if config.get('candidateTraining')!={'algorithm':PATTERN_PARAMETERS['algorithm'], 'parameters':PATTERN_PARAMETERS, 'status':'historical-training-and-prospective-gate'}:
    raise ValueError('La configuración del aprendizaje de patrones no coincide con la aprobada.')
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
analysis_path=Path('data/analisis-patrones.json')
path=Path('data/reto-predictor.json')
registry=json.loads(path.read_text())
if quality['pendingDates']:
    analysis_path.write_text(json.dumps({'version':1,'status':'waiting-result','checkedAt':now.isoformat(),
        'historyUntil':rows[-1]['date'],'pendingDates':quality['pendingDates'],
        'conclusion':'Se espera el último resultado antes de analizar patrones, entrenar o registrar otra predicción.'},ensure_ascii=False,indent=2)+'\n')
    print('Waiting for latest draw:',quality['pendingDates'])
    raise SystemExit(0)
latest_proof=next((p for p in proofs if p.get('date')==rows[-1]['date'] and p.get('source')=='SELAE'
    and str(p.get('url','')).startswith('https://www.loteriasyapuestas.es/')
    and type(rows[-1].get('reintegro')) is int and type(p.get('reintegro')) is int
    and sorted(p.get('nums',[]))==sorted(rows[-1]['nums']) and p.get('reintegro')==rows[-1].get('reintegro')),None)
if latest_proof is None:
    analysis_path.write_text(json.dumps({'version':1,'status':'waiting-verification','checkedAt':now.isoformat(),
        'historyUntil':rows[-1]['date'],'conclusion':'El último resultado requiere cotejo oficial antes de continuar.'},ensure_ascii=False,indent=2)+'\n')
    print('Waiting for verification:',rows[-1]['date'])
    raise SystemExit(0)
analysis=analyze(rows,registry['predictions'],target,now.isoformat())
trace=analysis['ruleEvaluation'].pop('trace',[])
Path('data/validacion-patrones.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n' for row in trace))
analysis['ruleEvaluation']['traceFile']='data/validacion-patrones.jsonl'
analysis_path.write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n')
report=train(rows,target)
pattern_report=train_patterns(rows,target)
pattern_trace=pattern_report.pop('trace')
Path('data/simulaciones-patrones.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in pattern_trace))
pattern_report['traceFile']='data/simulaciones-patrones.jsonl'
research_path=Path('data/pronosticos-patrones.json')
research,current_experiment,prospective=register_experiment(pattern_report,rows,now,json.loads(research_path.read_text()))
pattern_report['registeredExperiment']=current_experiment
pattern_report['prospective']=prospective
control_path=Path('data/control-modelo.json')
# Missing control state must stop generation, never silently approve new weights.
previous=json.loads(control_path.read_text())
control,selected=update_control(pattern_report,rows,target,now,previous)
pattern_report['candidateStatus']='in-trial' if (control.get('challenger') or {}).get('modelId')==pattern_report['modelId'] else 'queued'
if control['champion']['modelId']==pattern_report['modelId']:
    pattern_report['candidateStatus']='active'
control['nextTrainingCandidate']={'modelId':pattern_report['modelId'],'historyUntil':pattern_report['historyUntil'],
    'algorithm':pattern_report['algorithm'],'window':pattern_report['parameters']['window'],
    'status':pattern_report['candidateStatus']}
Path('data/aprendizaje-patrones.json').write_text(json.dumps(pattern_report,ensure_ascii=False,indent=2)+'\n')
existing=any(r['target']==target for r in registry['predictions'])
entry={'target':target,'nums':selected['nums'],'reintegro':selected['reintegro'],
       'window':99999,'historyUntil':rows[-1]['date'],'created':now.isoformat(),
       'algorithm':'guarded-online-logistic-v1','reintegroAlgorithm':'guarded-online-logistic-v1','strategyVersion':4,
       'strategyFile':'data/reto-estrategia-activa.json','modelId':control['champion']['modelId'],'weightsTrainedUntil':control['champion']['historyUntil'],
       'numberEvidence':selected['numberEvidence'],'reintegroEvidence':{'estimatedScore':selected['refundScore']},
       'analysisFile':'data/analisis-patrones.json','analysisUntil':analysis['historyUntil'],'goal':config['objective'],'recordedBy':'Modelo activo con pesos protegidos por evaluación prospectiva; commit de GitHub acredita publicación'}
if not existing:
    validate_prediction(entry,rows[-1]['date'])
report['next']['registered']=False
report['activeNext']={**selected,'modelId':control['champion']['modelId'],'target':target,'registered':not existing}
report['next']['note']='Propuesta del entrenamiento, sin autorización para sustituir al modelo activo.'
control_path.write_text(json.dumps(control,ensure_ascii=False,indent=2)+'\n')
Path('data/modelo-adaptativo.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
research_path.write_text(json.dumps(research,ensure_ascii=False,indent=2)+'\n')
if existing:
    print('Already recorded',target,'; modelo entrenado sin sustituir la predicción.')
    raise SystemExit(0)
registry['predictions'].append(entry)
registry['predictions'].sort(key=lambda r:r['target'])
path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
print('Prospective prediction:',target,entry['nums'])
