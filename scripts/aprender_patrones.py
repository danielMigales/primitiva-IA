"""Rolling-draw pattern learner: predict once, reveal, score, then update.

Fixed protocol and features; never retry a known target until it matches. Historical
replay is not prospective evidence and cannot establish the cause of a draw.
"""
from collections import Counter
from copy import deepcopy
from datetime import date, datetime, time
from hashlib import sha256
from itertools import combinations
import json
from math import exp, log, sqrt
from zoneinfo import ZoneInfo

from modelo_adaptativo import ranking, validate_rows

FEATURES = ['frequency', 'previous', 'gapShort', 'gapMedium', 'gapLong',
            'returnHazard', 'intervalProximity', 'partners', 'transition',
            'oddShape', 'lowShape', 'sumShape', 'consecutiveShape']
LABELS = ['Frecuencia reciente', 'Presencia anterior', 'Ausencia de 1–3 sorteos',
          'Ausencia de 4–8 sorteos', 'Ausencia de 9 o más sorteos',
          'Retorno tras una ausencia similar', 'Proximidad a intervalos anteriores',
          'Parejas con números del último resultado', 'Transiciones entre números',
          'Transición de pares e impares', 'Transición de bajos y altos',
          'Transición de sumas', 'Transición de consecutivos']
PARAMETERS = {'algorithm': 'rolling-pattern-logistic-v1', 'window': 30,
              'learningRate': .12, 'l2': .002, 'features': FEATURES,
              'validationFraction': .2, 'minimumValidation': 30}


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def shape(row):
    nums = sorted(row['nums'])
    return (sum(n % 2 for n in nums), sum(n <= 24 for n in nums),
            sum(nums) // 40, min(3, sum(b-a == 1 for a, b in zip(nums, nums[1:]))))


def features(history, refund=False, parameters=None):
    """All intervals/windows count DRAWS, not days. No target result argument."""
    parameters = parameters or PARAMETERS
    sample = history[-parameters['window']:]
    # Missing refunds are not negative labels or invented intervals.
    if refund:
        sample = [r for r in sample if type(r.get('reintegro')) is int]
    size, base = (10, .1) if refund else (49, 6/49)
    values = [set([r['reintegro']]) if refund else {n-1 for n in r['nums']} for r in sample]
    total = len(sample)
    if not total:
        return [[0.] * len(FEATURES) for _ in range(size)]
    counts = Counter(n for row in values for n in row)
    pairs = Counter(pair for row in values for pair in combinations(sorted(row), 2))
    last = values[-1]
    # Conditional next-number frequencies, built entirely inside this window.
    transitions = Counter()
    transition_weight = 0
    shape_counts = [Counter() for _ in range(4)]
    shape_totals = [0] * 4
    shapes = [shape(r) for r in sample]
    for i in range(1, total):
        overlap = len(last & values[i-1])
        transition_weight += overlap
        for n in values[i]:
            transitions[n] += overlap
        for j in range(4):
            if shapes[i-1][j] == shapes[-1][j]:
                shape_totals[j] += 1
                shape_counts[j].update(values[i])
    result = []
    for n in range(size):
        positions = [i for i, row in enumerate(values) if n in row]
        age = total-positions[-1] if positions else total+1
        gaps = [b-a for a, b in zip(positions, positions[1:])]
        # Laplace smoothing with the marginal reference; absent intervals give zero evidence.
        at_risk = sum(g >= age for g in gaps)
        returns = gaps.count(age)
        hazard = ((returns + 4*base)/(at_risk+4)-base) if gaps else 0.
        proximity = sum(exp(-abs(g-age)/2) for g in gaps)/len(gaps) if gaps else 0.
        partner = sum(pairs[tuple(sorted((n, other)))] for other in last if other != n)
        frequency = (counts[n]-total*base)/sqrt(total*base*(1-base))
        row = [max(-3., min(3., frequency)), float(n in last),
               float(bool(positions) and 1 <= age <= 3),
               float(bool(positions) and 4 <= age <= 8), float(age >= 9),
               hazard, proximity, partner/max(1, total*len(last)),
               (transitions[n]+4*base)/(transition_weight+4)-base]
        row.extend((c[n]+4*base)/(t+4)-base for c, t in zip(shape_counts, shape_totals))
        result.append(row)
    return result


class PatternLearner:
    def __init__(self, size, base, parameters=None, state=None):
        self.size, self.base = size, base
        self.parameters = deepcopy(parameters or PARAMETERS)
        if self.parameters.get('algorithm') != PARAMETERS['algorithm'] or self.parameters.get('features') != FEATURES:
            raise ValueError('Especificación de características desconocida.')
        self.weights = [0.] * len(FEATURES)
        self.biases = [0.] * size
        self.updates = 0
        if state is not None:
            if len(state['featureWeights']) != len(FEATURES) or len(state['numberBiases']) != size:
                raise ValueError('Dimensiones de pesos incorrectas.')
            self.weights = state['featureWeights'][:]
            self.biases = state['numberBiases'][:]
            self.updates = state['updates']

    def predict(self, matrix):
        offset = log(self.base/(1-self.base))
        return [1/(1+exp(-max(-20, min(20, offset+self.biases[n]+sum(w*x for w, x in zip(self.weights, row))))))
                for n, row in enumerate(matrix)]

    def learn(self, matrix, probabilities, values):
        errors = [float(n in values)-probabilities[n] for n in range(self.size)]
        rate, penalty = self.parameters['learningRate'], self.parameters['l2']
        for j in range(len(FEATURES)):
            gradient = sum(e*row[j] for e, row in zip(errors, matrix))/self.size
            self.weights[j] += rate*(gradient-penalty*self.weights[j])
        for n, error in enumerate(errors):
            self.biases[n] += rate*(error-penalty*self.biases[n])
        self.updates += 1

    def state(self):
        return {'featureWeights': self.weights[:], 'numberBiases': self.biases[:], 'updates': self.updates}


def score_snapshot(model, rows, target):
    if not rows or model['historyUntil'] >= target or any(r['date'] >= target for r in rows):
        raise ValueError('Los pesos y datos deben preceder al objetivo.')
    if model['historyUntil'] > rows[-1]['date']:
        raise ValueError('Pesos posteriores al histórico permitido.')
    result = []
    for key, size, base in (('main', 49, 6/49), ('refund', 10, .1)):
        learner = PatternLearner(size, base, model['parameters'], model[key])
        result.append(learner.predict(features(rows, key == 'refund', model['parameters'])))
    return result


def new_metrics():
    return {'draws': 0, 'mainHits': 0, 'hitHistogram': [0]*7, 'mainBrier': 0.,
            'frequencyHits': 0, 'refundDraws': 0, 'refundHits': 0, 'refundBrier': 0.}


def add_metrics(metrics, probabilities, actual, chosen, frequency, refund_probabilities):
    hits = len(set(chosen) & {n-1 for n in actual['nums']})
    metrics['draws'] += 1
    metrics['mainHits'] += hits
    metrics['hitHistogram'][hits] += 1
    metrics['frequencyHits'] += len(set(frequency) & {n-1 for n in actual['nums']})
    metrics['mainBrier'] += sum((p-float(n+1 in actual['nums']))**2 for n, p in enumerate(probabilities))/49
    if type(actual.get('reintegro')) is int and refund_probabilities is not None:
        metrics['refundDraws'] += 1
        metrics['refundHits'] += int(ranking(refund_probabilities, 1)[0] == actual['reintegro'])
        metrics['refundBrier'] += sum((p-float(n == actual['reintegro']))**2 for n, p in enumerate(refund_probabilities))/10


def finish_metrics(metrics):
    for loss, denominator in (('mainBrier', 'draws'), ('refundBrier', 'refundDraws')):
        metrics[loss] = metrics[loss]/metrics[denominator] if metrics[denominator] else None
    metrics['expectedRandomHits'] = metrics['draws']*36/49
    metrics['expectedRandomRefundHits'] = metrics['refundDraws']/10
    metrics['uniformMainBrier'] = (6/49)*(1-6/49)
    metrics['uniformRefundBrier'] = .09
    return metrics


def train_patterns(rows, target, parameters=None):
    parameters = deepcopy(parameters or PARAMETERS)
    validate_rows(rows)
    if target <= rows[-1]['date']:
        raise ValueError('Objetivo posterior al histórico requerido.')
    window = parameters['window']
    if type(window) is not int or window < 2 or window >= len(rows):
        raise ValueError('Ventana de sorteos inválida.')
    start = len(rows)-max(parameters['minimumValidation'], int(len(rows)*parameters['validationFraction']))
    if start <= window:
        raise ValueError('Histórico insuficiente para separar entrenamiento y validación.')
    main, refund = PatternLearner(49, 6/49, parameters), PatternLearner(10, .1, parameters)
    all_metrics, validation, frozen_metrics = new_metrics(), new_metrics(), new_metrics()
    frozen_main = frozen_refund = None
    frozen_state = None
    trace, best, recent = [], [], []
    best_hits = -1
    for i in range(window, len(rows)):
        history = rows[i-window:i]
        actual = rows[i]
        if i == start:
            frozen_main, frozen_refund = deepcopy(main), deepcopy(refund)
            frozen_state = {'historyUntil': rows[i-1]['date'], 'main': main.state(), 'refund': refund.state()}
        x, rx = features(history, parameters=parameters), features(history, True, parameters)
        before, refund_before = main.state(), refund.state()
        # A single proposal, produced before consulting this outcome.
        probabilities, rp = main.predict(x), refund.predict(rx)
        refund_ready = bool(refund_before['updates'] or any(type(r.get('reintegro')) is int for r in history))
        chosen, refund_chosen = ranking(probabilities, 6), ranking(rp, 1)[0]
        frequency = ranking([row[0] for row in x], 6)
        nums = sorted(n+1 for n in chosen)
        values = {n-1 for n in actual['nums']}
        matched = sorted(set(nums) & set(actual['nums']))
        add_metrics(all_metrics, probabilities, actual, chosen, frequency, rp if refund_ready else None)
        if i >= start:
            add_metrics(validation, probabilities, actual, chosen, frequency, rp if refund_ready else None)
            fp, frp = frozen_main.predict(x), frozen_refund.predict(rx)
            add_metrics(frozen_metrics, fp, actual, ranking(fp, 6), frequency, frp if refund_ready else None)
        # Outcome is now revealed. Misses AND false positives influence the gradient.
        main.learn(x, probabilities, values)
        refund_known = type(actual.get('reintegro')) is int
        if refund_known:
            refund.learn(rx, rp, {actual['reintegro']})
        deltas = [b-a for a, b in zip(before['featureWeights'], main.weights)]
        changed = sorted(range(len(FEATURES)), key=lambda j: -abs(deltas[j]))[:3]
        record = {'date': actual['date'], 'phase': 'validation' if i >= start else 'training',
                  'historyFrom': history[0]['date'], 'historyUntil': history[-1]['date'],
                  'historyDraws': window, 'nums': nums, 'reintegro': refund_chosen if refund_ready else None,
                  'actualNums': actual['nums'], 'actualReintegro': actual.get('reintegro'),
                  'matched': matched, 'hits': len(matched),
                  'missed': sorted(set(actual['nums'])-set(nums)),
                  'refundHit': refund_chosen == actual['reintegro'] if refund_known and refund_ready else None,
                  'stateBefore': fingerprint([before, refund_before]),
                  'stateAfter': fingerprint([main.state(), refund.state()]),
                  'adjustments': [{'feature': FEATURES[j], 'label': LABELS[j], 'delta': deltas[j]} for j in changed],
                  'biasChangeL1': sum(abs(a-b) for a, b in zip(before['numberBiases'], main.biases))}
        if i >= start:
            record['frozenNums'] = sorted(n+1 for n in ranking(fp, 6))
            record['frozenReintegro'] = ranking(frp, 1)[0] if refund_ready else None
        trace.append(record)
        recent.append({**record, 'weightsBefore': before['featureWeights'], 'weightsAfter': main.weights[:],
                       'missedScoresBefore': [{'number': n, 'score': probabilities[n-1]} for n in record['missed']],
                       'falsePositiveScoresBefore': [{'number': n, 'score': probabilities[n-1]} for n in sorted(set(nums)-set(actual['nums']))]})
        recent = recent[-5:]
        if len(matched) > best_hits:
            best_hits, best = len(matched), []
        if len(matched) == best_hits and len(best) < 5:
            best.append({k: record[k] for k in ('date', 'nums', 'actualNums', 'matched', 'hits', 'phase')})
    x, rx = features(rows, parameters=parameters), features(rows, True, parameters)
    probabilities, rp = main.predict(x), refund.predict(rx)
    selected = ranking(probabilities, 6)
    evidence = []
    for n in sorted(selected):
        contributions = [w*v for w, v in zip(main.weights, x[n])]
        top = sorted(range(len(FEATURES)), key=lambda j: -abs(contributions[j]))[:3]
        evidence.append({'number': n+1, 'score': probabilities[n], 'numberBias': main.biases[n],
                         'signals': [{'feature': FEATURES[j], 'label': LABELS[j], 'value': x[n][j],
                                      'weight': main.weights[j], 'contribution': contributions[j]} for j in top]})
    latest = rows[-window:]
    intervals = []
    for n in range(1, 50):
        positions = [i for i, r in enumerate(latest) if n in r['nums']]
        gaps = [b-a for a, b in zip(positions, positions[1:])]
        intervals.append({'number': n, 'appearances': len(positions),
                          'drawsSinceLast': window-1-positions[-1] if positions else None,
                          'observedGaps': gaps, 'meanGap': sum(gaps)/len(gaps) if gaps else None})
    pair_counts = Counter(pair for r in latest for pair in combinations(sorted(r['nums']), 2))
    shape_counts = Counter(shape(r) for r in latest)
    return {'version': 1, 'algorithm': PARAMETERS['algorithm'], 'parameters': parameters,
            'modelId': fingerprint({'rows': rows, 'parameters': parameters}),
            'historyUntil': rows[-1]['date'], 'trainedDraws': len(rows),
            'main': main.state(), 'refund': refund.state(),
            'protocol': {'window': window, 'onePredictionPerDraw': True, 'retriesPerTarget': 0,
                         'trainingThrough': rows[start-1]['date'], 'validationFrom': rows[start]['date'],
                         'validationThrough': rows[-1]['date'], 'parametersSelectedUsingValidation': False,
                         'onlineValidation': 'Predict first, then update after revealing each result.',
                         'frozenValidation': 'Weights frozen before validation; features use only previous draws.',
                         'refundIntervals': 'Only draws with known refund in the rolling window.'},
            'simulation': finish_metrics(all_metrics), 'validation': finish_metrics(validation),
            'frozenValidation': finish_metrics(frozen_metrics), 'frozenValidationState': frozen_state,
            'bestHits': best_hits, 'bestExamples': best, 'lastUpdates': recent,
            'featureWeights': [{'feature': feature, 'label': label, 'weight': weight}
                               for feature, label, weight in zip(FEATURES, LABELS, main.weights)],
            'recentPatterns': {'intervals': intervals,
                               'pairs': [{'nums': list(pair), 'appearances': count} for pair, count in pair_counts.most_common(10)],
                               'shapes': [{'odd': s[0], 'low': s[1], 'sumBandFrom': s[2]*40,
                                           'consecutivePairsCappedAt3': s[3], 'appearances': count}
                                          for s, count in shape_counts.most_common(5)]},
            'next': {'target': target, 'nums': sorted(n+1 for n in selected),
                     'reintegro': ranking(rp, 1)[0] if refund.updates else None, 'registered': False},
            'numberEvidence': evidence, 'hasDemonstratedAdvantage': False,
            'note': 'Simulación histórica reproducible, no apuestas publicadas antes del sorteo. Las contribuciones explican la elección del modelo, no la causa del resultado. No se reintenta un sorteo conocido hasta acertarlo.',
            'trace': trace}


def register_experiment(report, rows, now, previous):
    """Separate immutable experimental forecasts; never writes the designated bet."""
    if previous.get('version') != 1 or not isinstance(previous.get('predictions'), list):
        raise ValueError('Registro experimental inválido; no se reinicia.')
    state = deepcopy(previous)
    actuals = {r['date']: r for r in rows}
    seen = set()
    for record in state['predictions']:
        if record['target'] in seen:
            raise ValueError('Predicciones experimentales duplicadas.')
        seen.add(record['target'])
        deadline = datetime.combine(date.fromisoformat(record['target']), time(21, 40), ZoneInfo('Europe/Madrid'))
        if datetime.fromisoformat(record['created']) >= deadline or record['historyUntil'] >= record['target']:
            raise ValueError('El pronóstico experimental debe preceder al sorteo.')
        actual = actuals.get(record['target'])
        if actual is None:
            continue
        actual_value = {'nums': actual['nums'], 'reintegro': actual.get('reintegro')}
        if record.get('result'):
            if record['result']['actual'] != actual_value:
                raise ValueError('Un resultado experimental ya evaluado ha cambiado.')
            continue
        matched = sorted(set(record['nums']) & set(actual['nums']))
        record['result'] = {'actual': actual_value, 'matched': matched, 'hits': len(matched),
                            'refundHit': record['reintegro'] == actual.get('reintegro')
                            if type(record.get('reintegro')) is int and type(actual.get('reintegro')) is int else None}
    target = report['next']['target']
    current = next((r for r in state['predictions'] if r['target'] == target), None)
    if current is None:
        deadline = datetime.combine(date.fromisoformat(target), time(21, 40), ZoneInfo('Europe/Madrid'))
        if now >= deadline or rows[-1]['date'] >= target or report['historyUntil'] != rows[-1]['date']:
            raise ValueError('No se puede registrar un experimento después de su resultado.')
        current = {'target': target, 'created': now.isoformat(), 'historyUntil': report['historyUntil'],
                   'modelId': report['modelId'], 'algorithm': report['algorithm'],
                   'parameters': deepcopy(report['parameters']), 'nums': report['next']['nums'][:],
                   'reintegro': report['next']['reintegro'], 'productionPrediction': False}
        state['predictions'].append(current)
        state['predictions'].sort(key=lambda r: r['target'])
    settled = [r for r in state['predictions'] if r.get('result')]
    return state, deepcopy(current), {'registered': len(state['predictions']), 'settled': len(settled),
        'mainHits': sum(r['result']['hits'] for r in settled),
        'hitHistogram': [sum(r['result']['hits'] == k for r in settled) for k in range(7)],
        'refundDraws': sum(r['result']['refundHit'] is not None for r in settled),
        'refundHits': sum(r['result']['refundHit'] is True for r in settled)}
