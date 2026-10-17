"""Latest-draw review, predeclared descriptive scans and chronological rule tests.
Never writes production predictions or accepts a model on historical evidence.
"""
from collections import Counter
from datetime import date
from functools import lru_cache
from itertools import combinations
from math import comb
from control_modelo import sign_p
from evaluar_metodos import load_current_recency

RULES=('hot20','cold20','repeat','transitions100')
LABELS={'hot20':'Frecuentes en 20 sorteos','cold20':'Menos frecuentes en 20 sorteos',
        'repeat':'Repetición del último sorteo','transitions100':'Transiciones de los últimos 100 sorteos'}
PROTOCOL={'selectionDraws':100,'validationDraws':100,'minimumTrainingDraws':120,
          'rules':list(RULES),'comparisons':16,'alpha':.05,
          'note':'Reglas predefinidas. Selección en 100 sorteos y contraste en 100 posteriores; cada predicción solo usa resultados anteriores. Análisis histórico exploratorio.'}


def binomial_upper(k,n,p):
    return min(1.,sum(comb(n,j)*p**j*(1-p)**(n-j) for j in range(k,n+1)))


@lru_cache(maxsize=4)
def main_hit_distribution(n):
    probabilities=[comb(6,k)*comb(43,6-k)/comb(49,6) for k in range(7)]
    distribution=[1.]
    for _ in range(n):
        next_dist=[0.]*(len(distribution)+6)
        for i,value in enumerate(distribution):
            for k,p in enumerate(probabilities):next_dist[i+k]+=value*p
        distribution=next_dist
    return distribution


def random_upper(hits,n,refund=False):
    return binomial_upper(hits,n,.1) if refund else min(1.,sum(main_hit_distribution(n)[hits:]))


def choose_rule(history,rule,refund=False):
    if not history:raise ValueError('No hay histórico previo.')
    if rule not in RULES:raise ValueError('Regla desconocida.')
    if refund:
        history=[r for r in history if type(r.get('reintegro')) is int]
        if not history:return None
    space=range(10) if refund else range(1,50)
    take=1 if refund else 6
    values=lambda r:[r['reintegro']] if refund else r['nums']
    if rule in ('hot20','cold20'):
        counts=Counter(n for r in history[-20:] for n in values(r))
        key=(lambda n:(-counts[n],n)) if rule=='hot20' else (lambda n:(counts[n],n))
        chosen=sorted(space,key=key)[:take]
    elif rule=='repeat':chosen=list(values(history[-1]))
    else:
        last=set(values(history[-1]));counts=Counter()
        for j in range(max(1,len(history)-100),len(history)):
            overlap=len(last.intersection(values(history[j-1])))
            for n in values(history[j]):counts[n]+=overlap
        chosen=sorted(space,key=lambda n:(-counts[n],n))[:take]
    return chosen[0] if refund else sorted(chosen)


def baseline_refund(history):
    valid=[r for r in history if type(r.get('reintegro')) is int]
    if not valid:return None
    latest=date.fromisoformat(history[-1]['date']);scores=Counter()
    for days,weight in ((30,.45),(90,.35),(365,.20)):
        sample=[r for r in valid if (latest-date.fromisoformat(r['date'])).days<=days]
        counts=Counter(r['reintegro'] for r in sample)
        for digit in range(10):
            z=(counts[digit]-.1*len(sample))/(.09*len(sample))**.5 if sample else 0
            scores[digit]+=weight*max(-3,min(3,z))
    return min(range(10),key=lambda n:(-scores[n],n))


def test_rules(rows):
    needed=PROTOCOL['minimumTrainingDraws']+200
    if len(rows)<needed:
        return {'status':'insufficient-history','requiredDraws':needed,'available':len(rows),'historicalSignal':False}
    start=len(rows)-200;rank,_=load_current_recency()
    trace=[]
    for i in range(start,len(rows)):
        history=rows[:i];actual=rows[i]
        base={e['number'] for e in rank(history)[:6]}
        refund_base=baseline_refund(history)
        record={'date':actual['date'],'historyUntil':history[-1]['date'],
                'baselineMainHits':len(base.intersection(actual['nums'])),
                'baselineRefundHit':int(refund_base==actual.get('reintegro')) if refund_base is not None and type(actual.get('reintegro')) is int else None,'rules':{}}
        for rule in RULES:
            nums=choose_rule(history,rule);refund=choose_rule(history,rule,True)
            record['rules'][rule]={'nums':nums,'reintegro':refund,
                'mainHits':len(set(nums).intersection(actual['nums'])),
                'refundHit':int(refund==actual['reintegro']) if refund is not None and type(actual.get('reintegro')) is int else None}
        trace.append(record)
    selection,validation=trace[:100],trace[100:]
    channels={}
    for channel,field,baseline in [('main','mainHits','baselineMainHits'),('refund','refundHit','baselineRefundHit')]:
        selected=max(RULES,key=lambda rule:sum(r['rules'][rule][field] or 0 for r in selection))
        evaluations=[]
        for rule in RULES:
            usable=[r for r in validation if r['rules'][rule][field] is not None and r[baseline] is not None]
            hits=sum(r['rules'][rule][field] for r in usable);base_hits=sum(r[baseline] for r in usable)
            count=len(usable);expected=count*(.1 if channel=='refund' else 36/49)
            p_random=random_upper(hits,count,channel=='refund') if count else 1.
            differences=[r['rules'][rule][field]-r[baseline] for r in usable]
            p_baseline=sign_p(differences)
            # Two baselines x four rules x two channels; no claim from a chosen lucky rule.
            adjusted_random=min(1.,p_random*PROTOCOL['comparisons'])
            adjusted_baseline=min(1.,p_baseline*PROTOCOL['comparisons'])
            consistent=all(sum(r['rules'][rule][field] for r in block)>=sum(r[baseline] for r in block)
                           for block in (usable[:50],usable[50:]) if block)
            signal=count==100 and hits>base_hits and hits>expected and consistent and adjusted_random<=.05 and adjusted_baseline<=.05
            evaluations.append({'rule':rule,'label':LABELS[rule],'draws':count,'hits':hits,
                                'baselineHits':base_hits,'expectedRandom':round(expected,4),
                                'adjustedRandomP':adjusted_random,'adjustedBaselineP':adjusted_baseline,
                                'historicalSignal':signal})
        selected_result=next(r for r in evaluations if r['rule']==selected)
        channels[channel]={'selectedUsingEarlierBlock':selected,'label':LABELS[selected],
                           'selectionFrom':selection[0]['date'],'selectionThrough':selection[-1]['date'],
                           'validationFrom':validation[0]['date'],'validationThrough':validation[-1]['date'],
                           'selectedResult':selected_result,'allRules':evaluations}
    signal=any(c['selectedResult']['historicalSignal'] for c in channels.values())
    return {'status':'evaluated','historicalSignal':signal,'channels':channels,
            'trace':trace,'note':PROTOCOL['note']}


def analyze(rows,predictions,target,checked_at):
    if not rows or rows[-1]['date']>=target:raise ValueError('Objetivo posterior al último resultado requerido.')
    if any(a['date']>=b['date'] for a,b in zip(rows,rows[1:])):raise ValueError('Fechas duplicadas o desordenadas.')
    last=rows[-1];previous=rows[-2] if len(rows)>1 else None
    prediction=next((r for r in predictions if r['target']==last['date']),None)
    review={'date':last['date'],'nums':last['nums'],'reintegro':last.get('reintegro'),
            'predictionAvailable':prediction is not None,
            'matched':sorted(set(prediction['nums']).intersection(last['nums'])) if prediction else [],
            'refundHit':prediction['reintegro']==last['reintegro'] if prediction and type(prediction.get('reintegro')) is int and type(last.get('reintegro')) is int else None,
            'predictionVersion':prediction.get('strategyVersion') if prediction else None,
            'repeatedFromPrevious':sorted(set(last['nums']).intersection(previous['nums'])) if previous else [],
            'consecutivePairs':[list(pair) for pair in combinations(sorted(last['nums']),2) if pair[1]-pair[0]==1]}
    scans=[]
    # 2 windows x (49 numbers + 1176 pairs + 10 refunds); fixed family.
    family=2*(49+comb(49,2)+10)
    for window in (20,50):
        sample=rows[-window:];n=len(sample)
        counts=Counter(x for r in sample for x in r['nums'])
        pairs=Counter(pair for r in sample for pair in combinations(sorted(r['nums']),2))
        refunds=[r['reintegro'] for r in sample if type(r.get('reintegro')) is int]
        refund_counts=Counter(refunds)
        def evidence(key,count,p,total):
            return {'value':list(key) if isinstance(key,tuple) else key,'hits':count,'draws':total,
                    'expected':round(total*p,4),'adjustedP':min(1.,binomial_upper(count,total,p)*family)}
        top_numbers=[evidence(k,counts[k],6/49,n) for k in sorted(range(1,50),key=lambda k:(-counts[k],k))[:5]]
        top_pairs=[evidence(k,v,30/(49*48),n) for k,v in sorted(pairs.items(),key=lambda kv:(-kv[1],kv[0]))[:5]]
        top_refunds=[evidence(k,refund_counts[k],.1,len(refunds)) for k in sorted(range(10),key=lambda k:(-refund_counts[k],k))[:3]] if refunds else []
        scans.append({'window':window,'draws':n,'topNumbers':top_numbers,'topPairs':top_pairs,'topRefunds':top_refunds})
    backtest=test_rules(rows)
    signal=backtest['historicalSignal']
    proposals=[]
    for rule in RULES:
        proposals.append({'rule':rule,'label':LABELS[rule],'target':target,'historyUntil':last['date'],
                          'nums':choose_rule(rows,rule),'reintegro':choose_rule(rows,rule,True),
                          'productionPrediction':False})
    existing=next((p for p in predictions if p['target']==target),None)
    return {'version':1,'status':'analyzed','checkedAt':checked_at,'historyUntil':last['date'],
            'latestResult':review,'recentScans':scans,'scanComparisons':family,
            'protocol':PROTOCOL,'ruleEvaluation':backtest,'patternProposals':proposals,
            'hasDemonstratedPredictiveAdvantage':False,
            'conclusion':'Una regla supera el contraste histórico; requiere validación prospectiva antes de cambiar el modelo activo.' if signal else 'No se ha validado una señal que permita anticipar el siguiente sorteo. Las coincidencias recientes se muestran como observaciones, no como ventaja predictiva.',
            'existingPrediction':{'target':target,'historyUntil':existing.get('historyUntil'),'preserved':True,
                                  'usesLatestResult':existing.get('historyUntil')==last['date']} if existing else None,
            'pipeline':['latest-result-review','recent-pattern-scan','chronological-rule-test','candidate-training','prospective-control','register-next-if-absent']}
