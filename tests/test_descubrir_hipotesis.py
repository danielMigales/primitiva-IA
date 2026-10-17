from copy import deepcopy
from datetime import date, timedelta
import math
from pathlib import Path
import random
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from descubrir_hipotesis import build_atoms, condition_applies, discover, score_model, test_rule, interval_mask
from control_modelo import scores, snapshot


def history(count=650, periodic=False):
    rng=random.Random(31)
    return [{'date':(date(2018,1,1)+timedelta(days=3*i)).isoformat(),
             'nums':([1,2,3,4,5,6] if i%2==0 else [10,11,12,13,14,15]) if periodic else sorted(rng.sample(range(1,50),6)),
             'reintegro':i%2 if periodic else rng.randrange(10)} for i in range(count)]


class DiscoveryTests(unittest.TestCase):
    def test_generates_hypotheses_and_joins_conditions_from_data(self):
        rows=history();original=deepcopy(rows)
        report=discover(rows,'2026-10-19')
        self.assertEqual(report['status'],'searched')
        self.assertGreater(report['search']['hypothesesEvaluated'],report['search']['atomicConditions']*49)
        self.assertTrue(any(len(r['conditions'])>1 for r in report['rules']))
        self.assertEqual(rows,original)
        self.assertLess(report['protocol']['discoveryThrough'],report['protocol']['confirmationFrom'])
        self.assertLess(report['protocol']['confirmationThrough'],report['protocol']['auditFrom'])
        self.assertFalse(report['hasDemonstratedAdvantage'])
        survivors={r['id'] for r in report['rules'] if r['audit']['passed']}
        used={r['id'] for key in ('main','refund') for r in report[key]['rules']}
        self.assertEqual(used,survivors)
        self.assertEqual(report['next']['patternPredictionAvailable'],bool(survivors))

    def test_atom_bits_match_frozen_condition_execution_without_future_data(self):
        rows=history();first=int(len(rows)*.6)
        atoms,_,_=build_atoms(rows,first)
        for i in (first, len(rows)-1, len(rows)):
            for atom in atoms:
                self.assertEqual(bool((atom['_mask']>>i)&1),condition_applies(atom,rows[:i]),(i,atom))

    def test_audit_outcomes_cannot_change_discovery_confirmation_or_prior_predictions(self):
        rows=history();a=discover(rows,'2026-10-19')
        changed=deepcopy(rows)
        for r in changed[-10:]:r.update(nums=[40,41,42,43,44,45],reintegro=9)
        b=discover(changed,'2026-10-19')
        for x,y in zip(a['rules'],b['rules']):
            self.assertEqual(x['id'],y['id']);self.assertEqual(x['discovery'],y['discovery']);self.assertEqual(x['confirmation'],y['confirmation'])
        for x,y in zip(a['trace'][:-9],b['trace'][:-9]):
            self.assertEqual(x['nums'],y['nums']);self.assertEqual(x['reintegro'],y['reintegro'])
        self.assertTrue(all(r['historyUntil']<r['date'] for r in a['trace']))

    def test_detects_a_strong_synthetic_periodic_rule_and_predicts_hidden_targets(self):
        rows=history(periodic=True);report=discover(rows,'2026-10-19')
        self.assertGreater(report['search']['confirmed'],0)
        self.assertGreater(report['search']['survivedFinalAudit'],0)
        self.assertGreater(report['finalEvaluation']['mainHits'],report['finalEvaluation']['draws']*5)
        self.assertEqual(report['next']['nums'],[1,2,3,4,5,6])
        self.assertFalse(report['hasDemonstratedAdvantage'])

    def test_frozen_model_reproduces_proposal_and_control_can_use_it(self):
        rows=history();report=discover(rows,'2026-10-19');model=snapshot(report)
        original=deepcopy(model)
        probabilities=scores(model,rows,'2026-10-19')
        chosen=sorted(n+1 for n in sorted(range(49),key=lambda n:(-probabilities[0][n],n))[:6])
        refund=min(range(10),key=lambda n:(-probabilities[1][n],n))
        self.assertEqual(chosen,report['next']['nums']);self.assertEqual(refund,report['next']['reintegro'])
        self.assertEqual(probabilities,score_model(model,rows,'2026-10-19'))
        self.assertEqual(model,original)
        with self.assertRaises(ValueError):scores(model,rows,rows[-1]['date'])

    def test_multiplicity_correction_and_missing_refunds(self):
        rule={'channel':'main','number':1,'_mask':interval_mask(0,100),'estimatedProbability':.3,'discovery':{'effect':.1}}
        # Fixed toy universe, with positive conditional contrast.
        labels=interval_mask(0,30)|interval_mask(100,110)
        a=test_rule(rule,labels,interval_mask(0,200),1)
        b=test_rule(rule,labels,interval_mask(0,200),100)
        self.assertGreaterEqual(b['adjustedPBound'],a['adjustedPBound'])
        self.assertAlmostEqual(b['adjustedPBound'],min(1,a['adjustedPBound']*100))
        rows=history()
        for r in rows:r.pop('reintegro')
        report=discover(rows,'2026-10-19')
        self.assertFalse(any(r['channel']=='refund' for r in report['rules']))
        self.assertEqual(report['finalEvaluation']['refundDraws'],0)
        self.assertTrue(all(math.isfinite(r['discovery']['score']) for r in report['rules']))

    def test_insufficient_and_invalid_history(self):
        self.assertEqual(discover(history(150),'2026-10-19')['status'],'insufficient-history')
        with self.assertRaises(ValueError):discover(history()[::-1],'2026-10-19')
        rows=history()
        with self.assertRaises(ValueError):discover(rows,rows[-1]['date'])


if __name__=='__main__':unittest.main()
