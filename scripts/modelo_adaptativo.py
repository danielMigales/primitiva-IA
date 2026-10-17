"""Deterministic online logistic learners. Predict first, then learn each draw.
No external dependencies; historical replay is exploratory, never prospective evidence.
"""
from collections import deque
from datetime import date
from hashlib import sha256
import json
from math import exp, log, sqrt

ALGORITHM = 'online-logistic-v1'
PARAMETERS = {'learningRate': 0.08, 'l2': 0.002, 'warmup': 120,
              'windows': [30, 90, 365], 'features': ['z30', 'z90', 'z365', 'previous']}


class Learner:
    def __init__(self, size, base, parameters):
        self.size, self.base, self.parameters = size, base, parameters
        self.weights = [0.0] * 4
        self.biases = [0.0] * size
        self.queues = [deque() for _ in parameters['windows']]
        self.counts = [[0] * size for _ in self.queues]
        self.previous = set()
        self.updates = 0

    def features(self, day):
        # Windows are anchored on the target day and contain ONLY prior draws.
        for days, queue, counts in zip(self.parameters['windows'], self.queues, self.counts):
            while queue and (day - queue[0][0]).days > days:
                _, values = queue.popleft()
                for n in values:
                    counts[n] -= 1
        result = []
        for n in range(self.size):
            row = []
            for queue, counts in zip(self.queues, self.counts):
                total = len(queue)
                z = (counts[n] - total*self.base) / sqrt(total*self.base*(1-self.base)) if total else 0
                row.append(max(-3.0, min(3.0, z)))
            result.append(row + [float(n in self.previous)])
        return result

    def predict(self, features):
        offset = log(self.base/(1-self.base))
        return [1/(1+exp(-max(-20, min(20, offset+self.biases[n]+sum(w*x for w,x in zip(self.weights,row))))))
                for n,row in enumerate(features)]

    def learn(self, day, values, features, probabilities):
        errors = [float(n in values)-probabilities[n] for n in range(self.size)]
        rate, penalty = self.parameters['learningRate'], self.parameters['l2']
        for j in range(4):
            gradient = sum(e*row[j] for e,row in zip(errors,features))/self.size
            self.weights[j] += rate*(gradient-penalty*self.weights[j])
        for n,e in enumerate(errors):
            self.biases[n] += rate*(e-penalty*self.biases[n])
        for queue,counts in zip(self.queues,self.counts):
            queue.append((day,values))
            for n in values:
                counts[n] += 1
        self.previous = values
        self.updates += 1

    def state(self):
        return {'featureWeights': self.weights[:], 'numberBiases': self.biases[:], 'updates': self.updates}


def ranking(scores, count):
    return sorted(range(len(scores)),key=lambda n:(-scores[n],n))[:count]


def validate_rows(rows):
    if len(rows) < 120:
        raise ValueError('Se requieren al menos 120 sorteos.')
    previous = None
    for r in rows:
        day = date.fromisoformat(r['date'])
        if previous is not None and day <= previous:
            raise ValueError('Histórico desordenado o fechas duplicadas.')
        previous = day
        nums = r.get('nums')
        if not isinstance(nums,list) or len(nums)!=6 or len(set(nums))!=6 or any(type(n)is not int or not 1<=n<=49 for n in nums):
            raise ValueError('Números históricos inválidos.')
        if r.get('reintegro') is not None and (type(r['reintegro'])is not int or not 0<=r['reintegro']<=9):
            raise ValueError('Reintegro histórico inválido.')


def train(rows, target, parameters=None):
    parameters = PARAMETERS if parameters is None else parameters
    validate_rows(rows)
    if target <= rows[-1]['date']:
        raise ValueError('El objetivo debe ser posterior al histórico.')
    main, refund = Learner(49,6/49,parameters), Learner(10,.1,parameters)
    totals = {'draws':0,'mainHits':0,'recencyHits':0,'mainBrier':0.,'uniformBrier':0.,
              'refundDraws':0,'refundHits':0,'refundBrier':0.,'refundUniformBrier':0.}
    # Fixed last 20% evaluation; updates continue AFTER each evaluated prediction.
    start = max(parameters['warmup'], int(len(rows)*.8))
    recent = []
    for i,r in enumerate(rows):
        day = date.fromisoformat(r['date'])
        baseline_features = main.features(date.fromisoformat(rows[i-1]['date'])) if i else main.features(day)
        baseline = ranking([round(sum(w*v for w,v in zip((.45,.35,.20),row[:3])),5) for row in baseline_features],6)
        x = main.features(day)
        probabilities = main.predict(x)
        values = {n-1 for n in r['nums']}
        chosen = ranking(probabilities,6)
        before = main.state()
        if i>=start:
            totals['draws'] += 1
            totals['mainHits'] += len(set(chosen)&values)
            totals['recencyHits'] += len(set(baseline)&values)
            totals['mainBrier'] += sum((p-float(n in values))**2 for n,p in enumerate(probabilities))/49
            totals['uniformBrier'] += sum((6/49-float(n in values))**2 for n in range(49))/49
        main.learn(day,values,x,probabilities)
        last = {'date':r['date'],'predictedNumbers':[n+1 for n in sorted(chosen)],
                'hits':len(set(chosen)&values),'weightsBefore':before['featureWeights'],
                'weightsAfter':main.weights[:], 'biasChangeL1':sum(abs(a-b) for a,b in zip(before['numberBiases'],main.biases))}
        if type(r.get('reintegro')) is int:
            rx=refund.features(day)
            rp=refund.predict(rx)
            rv={r['reintegro']}
            if i>=start:
                totals['refundDraws']+=1
                totals['refundHits']+=int(ranking(rp,1)[0] in rv)
                totals['refundBrier']+=sum((p-float(n in rv))**2 for n,p in enumerate(rp))/10
                totals['refundUniformBrier']+=.09
            last['refundPredicted']=ranking(rp,1)[0]
            last['refundHit']=last['refundPredicted']==r['reintegro']
            refund.learn(day,rv,rx,rp)
        recent.append(last)
        recent=recent[-5:]
    day=date.fromisoformat(target)
    mp=main.predict(main.features(day))
    rp=refund.predict(refund.features(day))
    fingerprint=sha256(json.dumps({'rows':rows,'parameters':parameters},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    for key,denom in [('mainBrier','draws'),('uniformBrier','draws'),('refundBrier','refundDraws'),('refundUniformBrier','refundDraws')]:
        totals[key]=totals[key]/totals[denom] if totals[denom] else None
    totals['expectedRandomHits']=totals['draws']*36/49
    totals['expectedRandomRefundHits']=totals['refundDraws']/10
    totals['from']=rows[start]['date'] if start<len(rows) else None
    totals['to']=rows[-1]['date']
    return {'version':3,'algorithm':ALGORITHM,'modelId':fingerprint,'historyUntil':rows[-1]['date'],
            'trainedDraws':len(rows),'parameters':parameters,'main':main.state(),'refund':refund.state(),
            'evaluation':totals,'lastUpdates':recent,'hasDemonstratedAdvantage':False,
            'evaluationType':'exploratory-chronological-replay-predict-before-update',
            'note':'Simulación histórica, no apuestas registradas antes de los sorteos. Aprende pesos; no demuestra ventaja predictiva. Histórico pendiente de auditoría completa.',
            'next':{'target':target,'nums':sorted(n+1 for n in ranking(mp,6)), 'reintegro':ranking(rp,1)[0]},
            'numberEvidence':[{'number':n+1,'estimatedScore':mp[n]} for n in ranking(mp,6)],
            'refundScore':rp[ranking(rp,1)[0]]}
