from copy import deepcopy
from datetime import date, timedelta, datetime
import math
from pathlib import Path
import sys
import unittest
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from aprender_patrones import FEATURES, PARAMETERS, features, train_patterns, score_snapshot, PatternLearner, register_experiment
from control_modelo import scores, snapshot, update_control
from modelo_adaptativo import train


def history(count=160):
    return [{'date': (date(2024, 1, 1)+timedelta(days=3*i)).isoformat(),
             'nums': sorted((i+j*7) % 49+1 for j in range(6)), 'reintegro': i % 10} for i in range(count)]


class PatternLearningTests(unittest.TestCase):
    def test_one_prediction_then_update_without_seeing_target(self):
        rows = history()
        a = train_patterns(rows[:-1], rows[-1]['date'])
        changed = deepcopy(rows)
        changed[-1].update(nums=[40, 41, 42, 43, 44, 45], reintegro=8)
        b = train_patterns(changed, '2027-01-01')
        last = b['lastUpdates'][-1]
        self.assertEqual(a['next']['nums'], last['nums'])
        self.assertEqual(a['next']['reintegro'], last['reintegro'])
        self.assertEqual(a['main']['featureWeights'], last['weightsBefore'])
        self.assertNotEqual(last['weightsBefore'], last['weightsAfter'])
        self.assertGreater(last['biasChangeL1'], 0)
        self.assertEqual(len(b['trace']), len(rows)-30)
        self.assertEqual(len({r['date'] for r in b['trace']}), len(b['trace']))
        self.assertTrue(all(r['historyDraws'] == 30 and r['historyUntil'] < r['date'] for r in b['trace']))
        self.assertEqual(last['hits'], len(set(last['nums']) & set(changed[-1]['nums'])))

    def test_future_outcomes_do_not_change_earlier_forecasts(self):
        rows = history()
        a = train_patterns(rows, '2027-01-01')
        changed = deepcopy(rows)
        for r in changed[-10:]: r.update(nums=[2, 3, 4, 5, 6, 7], reintegro=9)
        b = train_patterns(changed, '2027-01-01')
        for x, y in zip(a['trace'][:-9], b['trace'][:-9]):
            self.assertEqual(x['nums'], y['nums'])
            self.assertEqual(x['reintegro'], y['reintegro'])
        self.assertEqual(a['frozenValidationState'], b['frozenValidationState'])

    def test_frozen_validation_reproduces_metrics_and_never_updates_weights(self):
        rows = history()
        report = train_patterns(rows, '2027-01-01')
        model = {**report['frozenValidationState'], 'parameters': report['parameters']}
        saved = deepcopy(model)
        hits = 0
        for step in report['trace']:
            if step['phase'] != 'validation': continue
            prefix = [r for r in rows if r['date'] < step['date']]
            probabilities = score_snapshot(model, prefix, step['date'])[0]
            chosen = sorted(n+1 for n in sorted(range(49), key=lambda n: (-probabilities[n], n))[:6])
            self.assertEqual(chosen, step['frozenNums'])
            hits += len(set(chosen) & set(step['actualNums']))
        self.assertEqual(hits, report['frozenValidation']['mainHits'])
        self.assertEqual(model, saved)
        self.assertLess(report['protocol']['trainingThrough'], report['protocol']['validationFrom'])

    def test_intervals_measure_draws_and_window_excludes_older_results(self):
        rows = history()
        for i, r in enumerate(rows): r['nums'] = [1, 2, 3, 4, 5, 6] if i % 3 == 0 else [7, 8, 9, 10, 11, 12]
        report = train_patterns(rows, '2027-01-01')
        one = report['recentPatterns']['intervals'][0]
        self.assertTrue(one['observedGaps'])
        self.assertTrue(all(g == 3 for g in one['observedGaps']))
        altered = deepcopy(rows)
        altered[0]['nums'] = [40, 41, 42, 43, 44, 45]
        self.assertEqual(features(rows), features(altered))
        self.assertEqual(len(features(rows)[0]), len(FEATURES))

    def test_learns_a_synthetic_signal_and_keeps_all_failures(self):
        rows = history()
        for r in rows: r.update(nums=[40, 41, 42, 43, 44, 45], reintegro=8)
        report = train_patterns(rows, '2027-01-01')
        self.assertEqual(report['next']['nums'], [40, 41, 42, 43, 44, 45])
        self.assertEqual(report['next']['reintegro'], 8)
        self.assertEqual(report['bestHits'], 6)
        self.assertEqual(sum(report['simulation']['hitHistogram']), len(report['trace']))
        self.assertEqual(report['trace'][0]['hits'], 0)
        self.assertGreater(report['simulation']['hitHistogram'][0], 0)
        self.assertGreater(report['simulation']['hitHistogram'][6], 0)
        self.assertFalse(report['hasDemonstratedAdvantage'])
        self.assertFalse(report['next']['registered'])

    def test_missing_refunds_and_invalid_input_fail_honestly(self):
        rows = history()
        for r in rows: r.pop('reintegro')
        report = train_patterns(rows, '2027-01-01')
        self.assertEqual(report['refund']['updates'], 0)
        self.assertEqual(report['simulation']['refundDraws'], 0)
        self.assertIsNone(report['next']['reintegro'])
        self.assertTrue(all(r['reintegro'] is None and r['refundHit'] is None for r in report['trace']))
        self.assertTrue(all(math.isfinite(w) for w in report['main']['featureWeights']))
        for bad in (rows[::-1], rows+[rows[-1]], [{**rows[0], 'nums': [1]*6}]+rows[1:]):
            with self.assertRaises(ValueError): train_patterns(bad, '2027-01-01')
        with self.assertRaises(ValueError): train_patterns(rows, rows[-1]['date'])
        with self.assertRaises(ValueError): PatternLearner(49, 6/49, state={'featureWeights': [0.], 'numberBiases': [0.]*49, 'updates': 0})

    def test_control_supports_new_candidate_without_replacing_existing_trial(self):
        rows = history()
        now = datetime(2026, 1, 1, 12, tzinfo=ZoneInfo('Europe/Madrid'))
        target = '2026-01-02'
        champion = train(rows[:-1], target)
        state, _ = update_control(champion, rows[:-1], target, now)
        previous_champion = deepcopy(state['champion'])
        candidate = train_patterns(rows, target)
        state, _ = update_control(candidate, rows, target, now, state)
        self.assertEqual(state['champion'], previous_champion)
        self.assertEqual(state['challenger'], snapshot(candidate))
        self.assertEqual(scores(state['challenger'], rows, target), score_snapshot(candidate, rows, target))
        previous_trial = deepcopy(state['challenger'])
        state, _ = update_control(train_patterns(history(161), target), history(161), target, now, state)
        self.assertEqual(state['challenger'], previous_trial)
        self.assertEqual(len(state['records']), 1)
        self.assertEqual(state['champion'], previous_champion)
        with self.assertRaises(ValueError): scores(candidate, rows, rows[-1]['date'])
        with self.assertRaises(ValueError): scores(candidate, rows+[{'date': target}], target)

    def test_experimental_registration_is_immutable_and_settles_only_future_results(self):
        rows = history()
        report = train_patterns(rows, '2026-01-02')
        now = datetime(2026, 1, 1, 12, tzinfo=ZoneInfo('Europe/Madrid'))
        state, current, summary = register_experiment(report, rows, now, {'version': 1, 'predictions': []})
        self.assertFalse(current['productionPrediction'])
        self.assertEqual(summary['settled'], 0)
        changed = deepcopy(report);changed['next']['nums'] = [1, 2, 3, 4, 5, 6]
        repeated, same, _ = register_experiment(changed, rows, now, state)
        self.assertEqual(same, current)
        self.assertEqual(repeated, state)
        actual = {'date': '2026-01-02', 'nums': current['nums'], 'reintegro': current['reintegro']}
        later_rows = rows+[actual]
        later_report = train_patterns(later_rows, '2026-01-05')
        later = datetime(2026, 1, 3, 12, tzinfo=ZoneInfo('Europe/Madrid'))
        settled, _, totals = register_experiment(later_report, later_rows, later, state)
        self.assertEqual(totals['settled'], 1)
        self.assertEqual(totals['mainHits'], 6)
        for field, value in current.items(): self.assertEqual(settled['predictions'][0][field], value)
        with self.assertRaises(ValueError): register_experiment(report, rows, later, {'version': 1, 'predictions': []})
        corrected = deepcopy(later_rows);corrected[-1]['nums'] = [1, 2, 3, 4, 5, 6]
        with self.assertRaises(ValueError): register_experiment(later_report, corrected, later, settled)
        with self.assertRaises(ValueError): register_experiment(report, rows, now, {'version': 0, 'predictions': []})


if __name__ == '__main__': unittest.main()
