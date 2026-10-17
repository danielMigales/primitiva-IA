from copy import deepcopy
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from analizar_patrones import analyze, choose_rule, main_hit_distribution, test_rules
from modelo_adaptativo import train
from control_modelo import update_control


def rows(count=350,last=date(2026,10,17)):
    days=[]
    while len(days)<count:
        if last.weekday() in (0,3,5):days.append(last)
        last-=timedelta(days=1)
    return [{'date':d.isoformat(),'nums':sorted(((i+j*7)%49)+1 for j in range(6)),'reintegro':i%10}
            for i,d in enumerate(reversed(days))]


class AnalysisTests(unittest.TestCase):
    def test_latest_result_is_reviewed_before_recent_scans(self):
        history=rows();original=deepcopy(history)
        pred={'target':history[-1]['date'],'nums':history[-1]['nums'],'reintegro':history[-1]['reintegro'],'strategyVersion':2}
        result=analyze(history,[pred],'2026-10-19','2026-10-17T22:25:00+02:00')
        self.assertEqual(result['latestResult']['matched'],history[-1]['nums'])
        self.assertTrue(result['latestResult']['refundHit'])
        self.assertEqual([x['draws'] for x in result['recentScans']],[20,50])
        self.assertEqual(history,original)
        self.assertEqual(result['pipeline'][0],'latest-result-review')
        self.assertFalse(result['hasDemonstratedPredictiveAdvantage'])
        self.assertLess(result['ruleEvaluation']['channels']['main']['selectionThrough'],result['ruleEvaluation']['channels']['main']['validationFrom'])

    def test_future_result_cannot_change_any_prior_rule_prediction(self):
        history=rows();modified=deepcopy(history)
        modified[-1]['nums']=[1,2,3,4,5,6];modified[-1]['reintegro']=9
        a=test_rules(history);b=test_rules(modified)
        for first,second in zip(a['trace'],b['trace']):
            self.assertLess(first['historyUntil'],first['date'])
            for rule in first['rules']:
                self.assertEqual(first['rules'][rule]['nums'],second['rules'][rule]['nums'])
                self.assertEqual(first['rules'][rule]['reintegro'],second['rules'][rule]['reintegro'])

    def test_exact_random_reference_and_constant_pattern_not_an_improvement(self):
        dist=main_hit_distribution(10)
        self.assertAlmostEqual(sum(dist),1.,places=10)
        self.assertAlmostEqual(sum(k*p for k,p in enumerate(dist)),10*36/49,places=10)
        history=rows()
        for row in history:row.update(nums=[1,2,3,4,5,6],reintegro=2)
        result=analyze(history,[],'2026-10-19','2026-10-17T22:25:00+02:00')
        self.assertLess(result['recentScans'][0]['topNumbers'][0]['adjustedP'],.05)
        self.assertFalse(result['ruleEvaluation']['historicalSignal'])
        self.assertFalse(result['hasDemonstratedPredictiveAdvantage'])

    def test_small_sample_does_not_claim_validation_or_invent_refunds(self):
        history=rows(120)
        for r in history:r.pop('reintegro')
        result=analyze(history,[],'2026-10-19','2026-10-17T22:25:00+02:00')
        self.assertEqual(result['ruleEvaluation']['status'],'insufficient-history')
        self.assertIsNone(choose_rule(history,'hot20',True))
        self.assertFalse(result['ruleEvaluation']['historicalSignal'])


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name);(self.work/'data').mkdir()
        (self.work/'data/reto-estrategia-activa.json').write_bytes((ROOT/'data/reto-estrategia-activa.json').read_bytes())
        (self.work/'data/pronosticos-patrones.json').write_text('{"version":1,"predictions":[]}')
        self.history=rows(150)
        self.registry=self.work/'data/reto-predictor.json';self.registry.write_text(json.dumps({'predictions':[],'revisions':[{'preserve':True}]}))
        self.write_history(self.history)
        now=datetime(2026,10,17,22,5,tzinfo=ZoneInfo('Europe/Madrid'))
        control,_=update_control(train(self.history,'2026-10-19'),self.history,'2026-10-19',now)
        (self.work/'data/control-modelo.json').write_text(json.dumps(control))

    def write_history(self,history,proof=True):
        (self.work/'data/sorteos.json').write_text(json.dumps({'draws':history}))
        proofs=[{**history[-1],'source':'SELAE','url':'https://www.loteriasyapuestas.es/official.pdf'}] if proof else []
        (self.work/'data/verificacion-sorteos.json').write_text(json.dumps({'draws':proofs}))

    def run_generator(self):
        class Clock(datetime):
            @classmethod
            def now(cls,tz=None):return cls(2026,10,17,22,6,tzinfo=ZoneInfo('Europe/Madrid')).astimezone(tz)
        before=Path.cwd()
        try:
            os.chdir(self.work)
            with patch('datetime.datetime',Clock):
                return runpy.run_path(str(ROOT/'scripts/generar_reto.py'),run_name='__main__')
        finally:os.chdir(before)

    def test_missing_latest_result_waits_without_training_or_registering(self):
        self.write_history(self.history[:-1])
        before=self.registry.read_bytes();control=(self.work/'data/control-modelo.json').read_bytes()
        with patch('modelo_adaptativo.train',side_effect=AssertionError('No training before latest result')):
            with self.assertRaises(SystemExit) as stopped:self.run_generator()
        self.assertEqual(stopped.exception.code,0)
        self.assertEqual(self.registry.read_bytes(),before)
        self.assertEqual((self.work/'data/control-modelo.json').read_bytes(),control)
        report=json.loads((self.work/'data/analisis-patrones.json').read_text())
        self.assertEqual(report['status'],'waiting-result');self.assertIn('2026-10-17',report['pendingDates'])

    def test_unverified_latest_result_waits(self):
        self.write_history(self.history,False)
        with self.assertRaises(SystemExit):self.run_generator()
        self.assertEqual(json.loads((self.work/'data/analisis-patrones.json').read_text())['status'],'waiting-verification')
        self.assertEqual(json.loads(self.registry.read_text())['predictions'],[])

    def test_analysis_precedes_training_and_registration_and_preserves_existing(self):
        events=[]
        import analizar_patrones,modelo_adaptativo,validar_reto
        real_analyze=analizar_patrones.analyze;real_train=modelo_adaptativo.train;real_validate=validar_reto.validate_prediction
        def analyze_first(*args,**kwargs):events.append('analysis');return real_analyze(*args,**kwargs)
        def train_after(*args,**kwargs):events.append('train');return real_train(*args,**kwargs)
        def register_last(*args,**kwargs):events.append('register');return real_validate(*args,**kwargs)
        with patch('analizar_patrones.analyze',analyze_first),patch('modelo_adaptativo.train',train_after),patch('validar_reto.validate_prediction',register_last):self.run_generator()
        self.assertEqual(events,['analysis','train','register'])
        entry=json.loads(self.registry.read_text())['predictions'][0]
        self.assertEqual(entry['analysisUntil'],'2026-10-17');self.assertEqual(entry['historyUntil'],'2026-10-17')
        saved=self.registry.read_bytes()
        with self.assertRaises(SystemExit):self.run_generator()
        self.assertEqual(self.registry.read_bytes(),saved)
