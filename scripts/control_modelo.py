"""Frozen champion/challenger trials on predictions recorded BEFORE each draw.
Promotion is evaluated once per non-overlapping trial; never on historical replay.
"""
from copy import deepcopy
from datetime import date, datetime, time
from math import comb
from zoneinfo import ZoneInfo
from modelo_adaptativo import Learner, PARAMETERS, ranking

POLICY = {'minimumDraws':60, 'familyAlpha':0.05,
          'metric':'mean-brier-and-paired-one-sided-sign-test',
          'multipleTesting':'alpha/(4*epoch*(epoch+1)); one decision per epoch',
          'requireHitsNotWorse':True}


def snapshot(report):
    return {k:deepcopy(report[k]) for k in ('modelId','historyUntil','main','refund','parameters')}


def scores(model, rows, target):
    """Recompute prior-draw features while keeping all learned weights frozen."""
    if model['parameters'].get('algorithm') == 'rolling-pattern-logistic-v1':
        from aprender_patrones import score_snapshot
        return score_snapshot(model, rows, target)
    if model['historyUntil']>=target or model['historyUntil']>rows[-1]['date']:
        raise ValueError('Los pesos contienen entrenamiento posterior al histórico permitido.')
    output=[]
    for key,size,base in (('main',49,6/49),('refund',10,.1)):
        learner=Learner(size,base,model['parameters'])
        learner.weights=model[key]['featureWeights'][:]
        learner.biases=model[key]['numberBiases'][:]
        for r in rows:
            if r['date']>=target:
                raise ValueError('No se puede predecir con resultados del objetivo o posteriores.')
            if key=='refund' and type(r.get('reintegro')) is not int:
                continue
            values={n-1 for n in r['nums']} if key=='main' else {r['reintegro']}
            day=date.fromisoformat(r['date'])
            for queue,counts in zip(learner.queues,learner.counts):
                queue.append((day,values))
                for n in values:counts[n]+=1
            learner.previous=values
        output.append(learner.predict(learner.features(date.fromisoformat(target))))
    return output


def sign_p(differences):
    # Positive = challenger has lower loss. Exact binomial upper tail, omit ties.
    values=[d for d in differences if abs(d)>1e-12]
    n=len(values);wins=sum(d>0 for d in values)
    return sum(comb(n,k) for k in range(wins,n+1))/(2**n) if n else 1.0


def decision(records, epoch, policy=POLICY):
    """Four comparisons: each output against champion and uniform reference."""
    evaluated=[r['result'] for r in records if r.get('result')]
    if len(evaluated)<policy['minimumDraws']:
        return {'status':'collecting','draws':len(evaluated),'required':policy['minimumDraws']}
    evaluated=evaluated[:policy['minimumDraws']]
    alpha=policy['familyAlpha']/(4*epoch*(epoch+1))
    comparisons={}
    accepted=True
    for channel in ('main','refund'):
        for baseline in ('champion','uniform'):
            differences=[r[channel][baseline+'Loss']-r[channel]['challengerLoss'] for r in evaluated]
            difference=sum(differences)/len(differences)
            p=sign_p(differences)
            passed=difference>0 and p<=alpha
            comparisons[channel+'-'+baseline]={'meanLossImprovement':difference,'pValue':p,'passed':passed}
            accepted=accepted and passed
        challenger_hits=sum(r[channel]['challengerHits'] for r in evaluated)
        champion_hits=sum(r[channel]['championHits'] for r in evaluated)
        uniform_hits=len(evaluated)*(36/49 if channel=='main' else .1)
        accepted=accepted and challenger_hits>=champion_hits and challenger_hits>=uniform_hits
        comparisons[channel+'-hits']={'challenger':challenger_hits,'champion':champion_hits,'expectedUniform':uniform_hits}
    return {'status':'accepted' if accepted else 'rejected','draws':len(evaluated),
            'required':policy['minimumDraws'],'perComparisonAlpha':alpha,'comparisons':comparisons,
            'reason':'Mejora de error consistente en principales y reintegro, sin empeorar aciertos.' if accepted else 'No supera todos los controles de error, consistencia y aciertos. Se conserva el modelo activo.'}


def outcome(record, actual):
    values={n-1 for n in actual['nums']};refund={actual['reintegro']}
    result={}
    for channel,size,base,labels,count in (('main',49,6/49,values,6),('refund',10,.1,refund,1)):
        result[channel]={}
        for name in ('champion','challenger'):
            probabilities=record[name][channel]
            result[channel][name+'Loss']=sum((p-float(n in labels))**2 for n,p in enumerate(probabilities))/size
            result[channel][name+'Hits']=len(set(ranking(probabilities,count))&labels)
        result[channel]['uniformLoss']=sum((base-float(n in labels))**2 for n in range(size))/size
    return result


def update_control(report, rows, target, now, previous=None):
    state=deepcopy(previous) if previous else {
        'version':1,'policy':POLICY,'champion':snapshot(report),'challenger':None,
        'epoch':0,'records':[],'decisions':[],
        'note':'Solo cuentan comparaciones registradas antes del sorteo. La publicación en GitHub acredita la fecha. Los ensayos históricos no autorizan ascensos.'}
    if state['policy']!=POLICY or state['version']!=1:
        raise ValueError('Política de promoción inesperada; requiere migración explícita.')
    # Only new official history can settle a previously saved shadow record.
    actuals={r['date']:r for r in rows}
    for record in state['records']:
        actual=actuals.get(record['target'])
        if not actual or type(actual.get('reintegro')) is not int:
            continue
        current_actual={'nums':actual['nums'],'reintegro':actual['reintegro']}
        if record.get('result'):
            if record.get('actual')!=current_actual:
                raise ValueError('Un resultado ya evaluado ha cambiado; se requiere revisión.')
            continue
        deadline=datetime.combine(date.fromisoformat(record['target']),time(21,40),ZoneInfo('Europe/Madrid'))
        if datetime.fromisoformat(record['recordedAt'])>=deadline or record['historyUntil']>=record['target']:
            raise ValueError('Registro de evaluación retrospectivo.')
        record['result']=outcome(record,actual)
        record['actual']=current_actual
    if state['challenger']:
        current=[r for r in state['records'] if r['epoch']==state['epoch']]
        assessment=decision(current,state['epoch'])
        if assessment['status']!='collecting':
            assessment.update({'epoch':state['epoch'],'decidedAfter':rows[-1]['date'],
                               'challengerId':state['challenger']['modelId'],'previousChampionId':state['champion']['modelId']})
            if assessment['status']=='accepted':
                state['champion']=deepcopy(state['challenger'])
            state['decisions'].append(assessment)
            state['challenger']=None
    if state['challenger'] is None:
        last_cutoff=state['decisions'][-1]['decidedAfter'] if state['decisions'] else state['champion']['historyUntil']
        if report['historyUntil']>state['champion']['historyUntil'] and report['historyUntil']>=last_cutoff:
            state['epoch']+=1
            state['challenger']=snapshot(report)
    cp=scores(state['champion'],rows,target)
    if state['challenger'] and not any(r['target']==target for r in state['records']):
        deadline=datetime.combine(date.fromisoformat(target),time(21,40),ZoneInfo('Europe/Madrid'))
        if now>=deadline or report['historyUntil']>=target:
            raise ValueError('La comparación debe registrarse antes del sorteo.')
        candidate=scores(state['challenger'],rows,target)
        state['records'].append({'target':target,'recordedAt':now.isoformat(),
            'historyUntil':rows[-1]['date'],'epoch':state['epoch'],
            'championId':state['champion']['modelId'],'challengerId':state['challenger']['modelId'],
            'champion':{'main':cp[0],'refund':cp[1]},'challenger':{'main':candidate[0],'refund':candidate[1]}})
    state['assessment']=decision([r for r in state['records'] if r['epoch']==state['epoch']],state['epoch']) if state['challenger'] else {'status':'waiting','draws':0,'required':POLICY['minimumDraws']}
    state['updatedThrough']=rows[-1]['date']
    return state, {'nums':sorted(n+1 for n in ranking(cp[0],6)),'reintegro':ranking(cp[1],1)[0],
                   'numberEvidence':[{'number':n+1,'estimatedScore':cp[0][n]} for n in ranking(cp[0],6)],
                   'refundScore':cp[1][ranking(cp[1],1)[0]]}
