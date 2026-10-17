import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from modelo_adaptativo import train


def history(count=150):
    return [{'date':(date(2025,1,1)+timedelta(days=3*i)).isoformat(),
             'nums':[1,2,3,4,5,6],'reintegro':2} for i in range(count)]


class ModelTests(unittest.TestCase):
    def test_learns_from_errors_and_ranks_persistent_signal(self):
        rows=history()
        report=train(rows,'2026-10-17')
        self.assertEqual(report['next']['nums'],[1,2,3,4,5,6])
        self.assertEqual(report['next']['reintegro'],2)
        self.assertGreater(report['main']['numberBiases'][0],report['main']['numberBiases'][10])
        last=report['lastUpdates'][-1]
        self.assertNotEqual(last['weightsBefore'],last['weightsAfter'])
        self.assertGreater(last['biasChangeL1'],0)
        self.assertFalse(report['hasDemonstratedAdvantage'])
        self.assertLess(report['evaluation']['mainBrier'],report['evaluation']['uniformBrier'])

    def test_future_draw_does_not_change_previous_prediction(self):
        rows=history()
        first=train(rows[:-1],rows[-1]['date'])
        changed=[*rows[:-1],{**rows[-1],'nums':[40,41,42,43,44,45],'reintegro':8}]
        second=train(changed,'2026-10-17')
        self.assertEqual(first['next']['nums'],second['lastUpdates'][-1]['predictedNumbers'])
        self.assertEqual(first['next']['reintegro'],second['lastUpdates'][-1]['refundPredicted'])
        self.assertEqual(first['main']['featureWeights'],second['lastUpdates'][-1]['weightsBefore'])
        self.assertNotEqual(first['main']['featureWeights'],second['main']['featureWeights'])

    def test_reproducible_and_missing_refunds_are_not_labels(self):
        rows=history()
        for r in rows:
            r.pop('reintegro')
        a=train(rows,'2026-10-17');b=train(rows,'2026-10-17')
        self.assertEqual(a,b)
        self.assertEqual(a['refund']['updates'],0)
        self.assertEqual(a['evaluation']['refundDraws'],0)
        self.assertIsNone(a['evaluation']['refundBrier'])
        self.assertTrue(all(math.isfinite(x) for x in a['main']['featureWeights']))

    def test_recency_baseline_matches_archived_v2(self):
        from evaluar_metodos import load_current_recency
        rank,_=load_current_recency()
        rows=history()
        for i,r in enumerate(rows):
            r['nums']=sorted({((i*3+j*7)%49)+1 for j in range(6)})
        report=train(rows,'2026-10-17')
        start=max(120,int(len(rows)*.8))
        hits=sum(len({x['number'] for x in rank(rows[:i])[:6]} & set(rows[i]['nums'])) for i in range(start,len(rows)))
        self.assertEqual(report['evaluation']['recencyHits'],hits)

    def test_invalid_history_fails_closed(self):
        rows=history()
        for invalid in (rows+[rows[-1]], [{**rows[0],'nums':[1]*6}]+rows[1:], rows[::-1]):
            with self.assertRaises(ValueError):train(invalid,'2026-10-17')
        with self.assertRaises(ValueError):train(rows,rows[-1]['date'])

    def test_generator_registers_v3_and_does_not_replace_existing(self):
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp);(work/'data').mkdir()
            (work/'data/reto-estrategia-activa.json').write_bytes((ROOT/'data/reto-estrategia-activa.json').read_bytes())
            (work/'data/sorteos.json').write_text(json.dumps({'draws':history()}))
            registry=work/'data/reto-predictor.json'
            registry.write_text(json.dumps({'predictions':[],'revisions':[{'preserve':True}]}))
            cmd=[sys.executable,str(ROOT/'scripts/generar_reto.py')]
            result=subprocess.run(cmd,cwd=work,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            saved=registry.read_bytes()
            entry=json.loads(saved)['predictions'][0]
            self.assertEqual(entry['strategyVersion'],3)
            self.assertEqual(entry['algorithm'],'online-logistic-v1')
            self.assertEqual(json.loads(saved)['revisions'],[{'preserve':True}])
            result=subprocess.run(cmd,cwd=work,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(saved,registry.read_bytes())
            report=json.loads((work/'data/modelo-adaptativo.json').read_text())
            self.assertFalse(report['next']['registered'])
            self.assertEqual(report['modelId'],entry['modelId'])
            config=work/'data/reto-estrategia-activa.json'
            obj=json.loads(config.read_text());obj['strategy']['parameters']['learningRate']=99
            config.write_text(json.dumps(obj))
            result=subprocess.run(cmd,cwd=work,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(saved,registry.read_bytes())
