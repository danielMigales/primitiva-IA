"""Data-driven symbolic rule search with chronological confirmation and audit.

The grammar bounds the search, but the program chooses the variables, thresholds,
lags and interactions. No rule is supplied as a winning rule; no six-hit stopping.
"""
from collections import Counter, deque
from hashlib import sha256
from heapq import nlargest
from itertools import combinations
import json
from math import exp, log, sqrt

from modelo_adaptativo import validate_rows

PARAMETERS = {'algorithm': 'automatic-rule-search-v1', 'warmup': 100,
              'windows': [5, 10, 20, 30, 50, 100], 'maxLag': 20,
              'beamWidth': 8, 'maxDepth': 3, 'rulesPerTarget': 2,
              'minimumDiscoverySupport': 30, 'minimumTestSupport': 20,
              'minimumHistory': 600, 'splitFractions': [.6, .8], 'alpha': .05,
              'thresholdQuantiles': [.25, .5, .75, .9]}


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def interval_mask(start, end):
    return ((1 << end)-1) ^ ((1 << start)-1)


def quantiles(values):
    values = sorted(values)
    return sorted({values[min(len(values)-1, int(q*len(values)))] for q in PARAMETERS['thresholdQuantiles']}) if values else []


def bits_where(values, predicate):
    # Building a bit vector this way avoids repeated large-int concatenations.
    return int(''.join('1' if predicate(v) else '0' for v in reversed(values)), 2)


def build_atoms(rows, discovery_end):
    """Bit i describes only rows[:i], including a prospective bit at len(rows)."""
    count = len(rows)
    full = (1 << (count+1))-1
    outcomes, atoms = {}, []
    valid_refund = 0
    for i, r in enumerate(rows):
        if type(r.get('reintegro')) is int: valid_refund |= 1 << i
    for refund, space in ((False, range(1, 50)), (True, range(10))):
        for number in space:
            key = ('refund' if refund else 'main', number)
            present = [int(r.get('reintegro') == number) if refund and type(r.get('reintegro')) is int
                       else int(number in r['nums']) if not refund else 0 for r in rows]
            outcomes[key] = bits_where(present, bool)
    def add(mask, kind, **fields):
        mask &= full
        support = (mask & interval_mask(PARAMETERS['warmup'], discovery_end)).bit_count()
        if support >= PARAMETERS['minimumDiscoverySupport']:
            atoms.append({'kind': kind, **fields, '_mask': mask})
    for (channel, number), outcome in outcomes.items():
        refund = channel == 'refund'
        # Refund intervals are censored at missing values, never filled as misses.
        present = [(outcome >> i) & 1 for i in range(count)]
        for lag in range(1, PARAMETERS['maxLag']+1):
            add(outcome << lag, 'lag', channel=channel, number=number, lag=lag)
        for window in PARAMETERS['windows']:
            queue = deque(); total = 0; values = []
            for i in range(count+1):
                values.append(total)
                if i == count: break
                queue.append(present[i]); total += present[i]
                if len(queue) > window: total -= queue.popleft()
            for threshold in quantiles(values[PARAMETERS['warmup']:discovery_end]):
                if threshold > 0:
                    add(bits_where(values, lambda v: v >= threshold), 'count', channel=channel,
                        number=number, window=window, threshold=threshold)
        ages = []; last = None
        for i in range(count+1):
            ages.append(i-last if last is not None else -1)
            if i < count:
                if refund and not ((valid_refund >> i) & 1): last = None
                elif present[i]: last = i
        discovery_ages = [v for v in ages[PARAMETERS['warmup']:discovery_end] if v > 0]
        modes = [v for v, _ in Counter(discovery_ages).most_common(5)]
        for age in sorted(set(modes)):
            add(bits_where(ages, lambda v: v == age), 'gap-equal', channel=channel, number=number, gap=age)
        for age in quantiles(discovery_ages):
            add(bits_where(ages, lambda v: v >= age), 'gap-at-least', channel=channel, number=number, gap=age)
    # Every main-number pair is considered, not a hand-picked example.
    for a, b in combinations(range(1, 50), 2):
        pair = outcomes['main', a] & outcomes['main', b]
        for window in (1, 5, 30):
            mask = 0
            for lag in range(1, window+1): mask |= pair << lag
            add(mask, 'pair', numbers=[a, b], window=window)
    # Learn thresholds/types from discovery features, never from later labels.
    shapes = {key: [None] for key in ('odd', 'low', 'sum', 'consecutive', 'repeat')}
    for i, r in enumerate(rows):
        nums = sorted(r['nums'])
        shape = {'odd': sum(n % 2 for n in nums), 'low': sum(n <= 24 for n in nums),
                 'sum': sum(nums), 'consecutive': sum(b-a == 1 for a, b in zip(nums, nums[1:])),
                 'repeat': len(set(nums) & set(rows[i-1]['nums'])) if i else 0}
        for key, value in shape.items(): shapes[key].append(value)
    for key, values in shapes.items():
        sample = [v for v in values[PARAMETERS['warmup']:discovery_end] if v is not None]
        for value in quantiles(sample):
            add(bits_where(values, lambda v: v is not None and v >= value), 'shape', feature=key, threshold=value)
    # Different descriptions with the same discovery mask may differ later;
    # retain them, and count all evaluations in the search budget.
    return atoms, outcomes, valid_refund


def description(atom):
    channel = 'reintegro' if atom.get('channel') == 'refund' else 'número'
    if atom['kind'] == 'lag': return f"el {channel} {atom['number']} salió hace {atom['lag']} sorteos"
    if atom['kind'] == 'count': return f"el {channel} {atom['number']} apareció al menos {atom['threshold']} veces en {atom['window']} sorteos"
    if atom['kind'] == 'gap-equal': return f"la última aparición conocida del {channel} {atom['number']} está a {atom['gap']} sorteos del objetivo"
    if atom['kind'] == 'gap-at-least': return f"la última aparición conocida del {channel} {atom['number']} está a {atom['gap']} o más sorteos del objetivo"
    if atom['kind'] == 'pair': return f"la pareja {atom['numbers'][0]}–{atom['numbers'][1]} apareció en los {atom['window']} sorteos anteriores"
    labels = {'odd': 'impares', 'low': 'números del 1 al 24', 'sum': 'suma', 'consecutive': 'parejas consecutivas', 'repeat': 'números repetidos del sorteo previo'}
    return f"el último resultado tuvo {labels[atom['feature']]} ≥ {atom['threshold']}"


def screen(mask, outcomes, universe, minimum):
    total = universe.bit_count(); support = (mask & universe).bit_count()
    if support < minimum or total-support < minimum: return None
    hits = (mask & universe & outcomes).bit_count()
    all_hits = (universe & outcomes).bit_count()
    base = all_hits/total
    if base in (0, 1): return None
    rate, outside = hits/support, (all_hits-hits)/(total-support)
    score = abs(rate-outside)/sqrt(base*(1-base)*(1/support+1/(total-support)))
    return {'support': support, 'hits': hits, 'rate': rate, 'outsideRate': outside,
            'score': score, 'effect': rate-outside}


def shortlist(atoms, outcomes, valid_refund, discovery_end):
    selected = []; tested = 0
    discovery = interval_mask(PARAMETERS['warmup'], discovery_end)
    minimum = PARAMETERS['minimumDiscoverySupport']
    for (channel, number), outcome in outcomes.items():
        universe = discovery & valid_refund if channel == 'refund' else discovery
        candidates = []
        for j, atom in enumerate(atoms):
            tested += 1
            stats = screen(atom['_mask'], outcome, universe, minimum)
            if stats and stats['score'] > 0:
                candidates.append((stats['score'], (j,), atom['_mask'], stats))
        seeds = nlargest(PARAMETERS['beamWidth'], candidates, key=lambda r: (r[0], tuple(-j for j in r[1])))
        pool = list(seeds); beam = list(seeds); seen = {r[1] for r in seeds}
        for depth in range(2, PARAMETERS['maxDepth']+1):
            next_beam = []
            for _, ids, mask, _ in beam:
                for _, seed_ids, seed_mask, _ in seeds:
                    joined = tuple(sorted(set(ids+seed_ids)))
                    if len(joined) != depth or joined in seen: continue
                    seen.add(joined); tested += 1
                    combined = mask & seed_mask
                    stats = screen(combined, outcome, universe, minimum)
                    if stats and stats['score'] > 0:
                        next_beam.append((stats['score'], joined, combined, stats))
            beam = nlargest(PARAMETERS['beamWidth'], next_beam, key=lambda r: (r[0], tuple(-j for j in r[1])))
            pool.extend(beam)
        masks_seen = set(); chosen = 0
        for _, ids, mask, stats in sorted(pool, key=lambda r: (-r[0], r[1])):
            # Avoid giving a number several copies of an identical condition.
            if mask in masks_seen: continue
            masks_seen.add(mask)
            base = .1 if channel == 'refund' else 6/49
            probability = (stats['hits']+3*base)/(stats['support']+3)
            rule = {'channel': channel, 'number': number,
                    'conditions': [{k: v for k, v in atoms[j].items() if k != '_mask'} for j in ids],
                    'text': ' Y '.join(description(atoms[j]) for j in ids),
                    'discovery': stats, 'estimatedProbability': probability, '_mask': mask}
            rule['id'] = digest({k: rule[k] for k in ('channel', 'number', 'conditions')})[:16]
            selected.append(rule); chosen += 1
            if chosen == PARAMETERS['rulesPerTarget']: break
    return selected, tested


def test_rule(rule, outcomes, universe, comparisons):
    # A fixed likelihood ratio is a nonnegative test martingale under the
    # uniform-draw null. Unlike a fixed-n binomial tail it tolerates a condition
    # whose support depends on previous outcomes. q was fixed on discovery.
    mask = rule['_mask'] & universe
    support, hits = mask.bit_count(), (mask & outcomes).bit_count()
    total, all_hits = universe.bit_count(), (outcomes & universe).bit_count()
    base = .1 if rule['channel'] == 'refund' else 6/49
    q = max(.001, min(.999, rule['estimatedProbability']))
    log_e = hits*log(q/base)+(support-hits)*log((1-q)/(1-base))
    adjusted_p_bound = min(1., exp(min(0., log(max(1, comparisons))-log_e)))
    rate = hits/support if support else None
    outside = (all_hits-hits)/(total-support) if total > support else None
    consistent = rate is not None and outside is not None and (rate-outside)*rule['discovery']['effect'] > 0
    passed = support >= PARAMETERS['minimumTestSupport'] and consistent and adjusted_p_bound <= PARAMETERS['alpha']
    return {'support': support, 'hits': hits, 'rate': rate, 'outsideRate': outside,
            'logEvidence': log_e, 'adjustedPBound': adjusted_p_bound, 'passed': passed,
            'reason': 'Supera evidencia corregida y conserva la dirección.' if passed else
                      'Muestra insuficiente.' if support < PARAMETERS['minimumTestSupport'] else
                      'No conserva la dirección observada.' if not consistent else
                      'No supera la evidencia exigida tras corregir las comparaciones.'}


def predict(rules, index, rows):
    output = {}; evidence = {}
    for channel, space, take, base in (('main', range(1, 50), 6, 6/49), ('refund', range(10), 1, .1)):
        counts = Counter(n for r in rows[max(0, index-30):index] for n in r['nums']) if channel == 'main' else Counter(r['reintegro'] for r in rows[max(0, index-30):index] if type(r.get('reintegro')) is int)
        if channel == 'refund' and not counts:
            output[channel] = None; output[channel+'Baseline'] = []; evidence[channel] = []; continue
        scores = {}; evidence[channel] = []
        for n in space:
            active = [r for r in rules if r['channel'] == channel and r['number'] == n and ((r['_mask'] >> index) & 1)]
            contributions = [log(r['estimatedProbability']/(1-r['estimatedProbability']))-log(base/(1-base)) for r in active]
            scores[n] = (sum(contributions)/len(contributions) if contributions else 0.)+counts[n]*1e-9
            if active: evidence[channel].append({'number': n, 'score': scores[n], 'ruleIds': [r['id'] for r in active]})
        chosen = sorted(space, key=lambda n: (-scores[n], -counts[n], n))[:take]
        output[channel] = sorted(chosen) if channel == 'main' else chosen[0]
        output[channel+'Baseline'] = sorted(space, key=lambda n: (-counts[n], n))[:take]
    return output, evidence


def condition_applies(atom, rows):
    if not rows: return False
    kind = atom['kind']
    def present(row):
        return row.get('reintegro') == atom['number'] if atom.get('channel') == 'refund' else atom['number'] in row['nums']
    if kind == 'lag': return len(rows) >= atom['lag'] and present(rows[-atom['lag']])
    if kind == 'count': return sum(present(r) for r in rows[-atom['window']:]) >= atom['threshold']
    if kind in ('gap-equal', 'gap-at-least'):
        age = None
        for i, row in enumerate(reversed(rows), 1):
            if atom.get('channel') == 'refund' and type(row.get('reintegro')) is not int: break
            if present(row): age = i; break
        return age is not None and (age == atom['gap'] if kind == 'gap-equal' else age >= atom['gap'])
    if kind == 'pair': return any(set(atom['numbers']).issubset(r['nums']) for r in rows[-atom['window']:])
    if kind != 'shape': raise ValueError('Condición de hipótesis desconocida.')
    nums = sorted(rows[-1]['nums'])
    values = {'odd': sum(n % 2 for n in nums), 'low': sum(n <= 24 for n in nums),
              'sum': sum(nums), 'consecutive': sum(b-a == 1 for a, b in zip(nums, nums[1:])),
              'repeat': len(set(nums) & set(rows[-2]['nums'])) if len(rows) > 1 else 0}
    return values[atom['feature']] >= atom['threshold']


def score_model(model, rows, target):
    """Use EXACTLY the frozen discovered rules; never run another search here."""
    if not rows or model['historyUntil'] >= target or model['historyUntil'] > rows[-1]['date'] or any(r['date'] >= target for r in rows):
        raise ValueError('No se puede puntuar con datos o reglas posteriores al objetivo.')
    result = []
    for channel, space, base in (('main', range(1, 50), 6/49), ('refund', range(10), .1)):
        counts = Counter(n for r in rows[-30:] for n in r['nums']) if channel == 'main' else Counter(r['reintegro'] for r in rows[-30:] if type(r.get('reintegro')) is int)
        probabilities = []
        rules = model[channel]['rules']
        for n in space:
            active = [r for r in rules if r['number'] == n and all(condition_applies(a, rows) for a in r['conditions'])]
            changes = [log(r['estimatedProbability']/(1-r['estimatedProbability']))-log(base/(1-base)) for r in active]
            # Infinitesimal, documented frequency tie-break; same ranking as predict().
            offset = sum(changes)/len(changes) if changes else 0.
            value = log(base/(1-base))+offset+counts[n]*1e-9
            probabilities.append(1/(1+exp(-max(-20., min(20., value)))))
        result.append(probabilities)
    return result


def discover(rows, target):
    validate_rows(rows)
    if target <= rows[-1]['date']: raise ValueError('El objetivo debe ser posterior al histórico.')
    if len(rows) < PARAMETERS['minimumHistory']:
        return {'version': 1, 'status': 'insufficient-history', 'required': PARAMETERS['minimumHistory'], 'available': len(rows), 'historyUntil': rows[-1]['date']}
    first, second = [int(len(rows)*f) for f in PARAMETERS['splitFractions']]
    atoms, outcomes, valid_refund = build_atoms(rows, first)
    rules, tested = shortlist(atoms, outcomes, valid_refund, first)
    for rule in rules:
        universe = interval_mask(first, second)
        if rule['channel'] == 'refund': universe &= valid_refund
        rule['confirmation'] = test_rule(rule, outcomes[rule['channel'], rule['number']], universe, len(rules))
    confirmed = [r for r in rules if r['confirmation']['passed']]
    for rule in rules:
        if not rule['confirmation']['passed']:
            rule['audit'] = {'passed': False, 'status': 'not-tested', 'reason': 'Descartada antes de abrir el tramo final.'}
            continue
        universe = interval_mask(second, len(rows))
        if rule['channel'] == 'refund': universe &= valid_refund
        rule['audit'] = test_rule(rule, outcomes[rule['channel'], rule['number']], universe, len(confirmed))
    validated = [r for r in confirmed if r['audit']['passed']]
    # Diagnostic combination of shortlisted rules: fixed before opening audit.
    # Rejected rules are measured, but must never become a deployment candidate.
    forecast_rules = rules
    final_trace = []; histogram = [0]*7; total_hits = baseline_hits = refund_hits = refund_draws = 0
    for i in range(second, len(rows)):
        prediction, _ = predict(forecast_rules, i, rows)
        actual = rows[i]; matched = sorted(set(prediction['main']) & set(actual['nums']))
        hits = len(matched); histogram[hits] += 1; total_hits += hits
        baseline_hits += len(set(prediction['mainBaseline']) & set(actual['nums']))
        if type(actual.get('reintegro')) is int:
            refund_draws += 1; refund_hits += prediction['refund'] == actual['reintegro']
        final_trace.append({'date': actual['date'], 'historyUntil': rows[i-1]['date'],
                            'nums': prediction['main'], 'reintegro': prediction['refund'],
                            'actualNums': actual['nums'], 'actualReintegro': actual.get('reintegro'),
                            'hits': hits, 'matched': matched})
    next_prediction, evidence = predict(validated, len(rows), rows)
    public_rules = [{k: v for k, v in r.items() if k != '_mask'} for r in rules]
    frozen = {channel: {'rules': [{k: r[k] for k in ('id', 'number', 'conditions', 'estimatedProbability')}
                                 for r in validated if r['channel'] == channel]} for channel in ('main', 'refund')}
    fingerprint = digest({'rows': rows, 'parameters': PARAMETERS})
    return {'version': 1, 'status': 'searched', 'algorithm': PARAMETERS['algorithm'], 'parameters': PARAMETERS,
            'modelId': fingerprint, 'historyUntil': rows[-1]['date'], 'totalDraws': len(rows),
            **frozen,
            'search': {'atomicConditions': len(atoms), 'hypothesesEvaluated': tested, 'shortlisted': len(rules),
                       'confirmed': len(confirmed), 'survivedFinalAudit': len(validated),
                       'maxConditionsPerRule': PARAMETERS['maxDepth']},
            'protocol': {'discoveryFrom': rows[PARAMETERS['warmup']]['date'], 'discoveryThrough': rows[first-1]['date'],
                         'confirmationFrom': rows[first]['date'], 'confirmationThrough': rows[second-1]['date'],
                         'auditFrom': rows[second]['date'], 'auditThrough': rows[-1]['date'],
                         'selectionUsesFinalOutcomes': False, 'nextModelSelectionUsesAudit': True,
                         'correction': 'Bonferroni over fixed shortlisted rules; likelihood-ratio test martingales against uniform draws.',
                         'searchGrammar': 'Numeric lag/count/gap conditions, all main-number pairs, combination shapes; automatic thresholds and beam search for conjunctions.',
                         'scope': 'Búsqueda automática dentro de estas familias, no exploración de todas las reglas matemáticas posibles.'},
            'finalEvaluation': {'draws': len(final_trace), 'mainHits': total_hits, 'frequencyHits': baseline_hits,
                                'expectedRandomHits': len(final_trace)*36/49, 'hitHistogram': histogram,
                                'refundHits': refund_hits, 'refundDraws': refund_draws,
                                'forecastRuleSource': 'unvalidated-discovery-before-confirmation-and-audit'},
            'rules': public_rules,
            'next': {'target': target, 'nums': next_prediction['main'], 'reintegro': next_prediction['refund'],
                     'registered': False, 'experimental': True, 'validatedRuleCount': len(validated),
                     'patternPredictionAvailable': bool(validated),
                     'method': 'surviving-rules' if validated else 'frequency-reference-only-no-surviving-rules'},
            'nextEvidence': evidence,
            'hasDemonstratedAdvantage': False,
            'conclusion': f'{len(validated)} hipótesis superan ambos contrastes históricos; falta comprobarlas con sorteos futuros.' if validated else 'Ninguna hipótesis ha superado ambos contrastes. No se propone una nueva combinación basada en reglas descartadas.',
            'note': 'El programa elige condiciones y combinaciones de condiciones; no se le entregan reglas ganadoras. Buscar muchas relaciones produce coincidencias: se separan descubrimiento, confirmación y auditoría. Revisar este histórico otra vez no convierte sus resultados en evidencia futura.',
            'trace': final_trace}
