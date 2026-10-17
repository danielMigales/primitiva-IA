from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path
import sys
import unittest
from zoneinfo import ZoneInfo

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from calidad_datos import inspect_history


def recent():
    start=date(2026,7,1)
    return [{'date':(start+timedelta(days=i)).isoformat(),'nums':[1,2,3,4,5,6],'reintegro':2}
            for i in range((date(2026,10,15)-start).days+1)
            if (start+timedelta(days=i)).weekday() in (0,3,5)]


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,17,20,0,tzinfo=ZoneInfo('Europe/Madrid'))

    def test_complete_history_and_official_matching_snapshot(self):
        rows=recent();proof={**rows[-1],'source':'SELAE','url':'https://www.loteriasyapuestas.es/documento.pdf'}
        report=inspect_history(rows,self.now,[proof])
        self.assertTrue(report['valid']);self.assertEqual(report['fullyVerifiedDraws'],1)
        self.assertEqual(report['missingRecentDates'],[]);self.assertEqual(report['pendingDates'],[])
        proof['reintegro']=9
        self.assertEqual(inspect_history(rows,self.now,[proof])['fullyVerifiedDraws'],0)

    def test_internal_gap_blocks_training_but_unpublished_future_draw_does_not(self):
        rows=recent();rows=[r for r in rows if r['date']!='2026-10-12']
        self.assertFalse(inspect_history(rows,self.now)['valid'])
        self.assertIn('2026-10-12',inspect_history(rows,self.now)['missingRecentDates'])
        after=self.now.replace(hour=22)
        report=inspect_history(recent(),after)
        self.assertTrue(report['valid']);self.assertEqual(report['pendingDates'],['2026-10-17'])

    def test_duplicate_invalid_future_numbers_and_refund_are_errors(self):
        rows=recent()
        cases=[rows+[{**rows[-1],'date':'2026-10-14'}],rows+[rows[-1]],[{**rows[0],'date':'2026-02-30'}]+rows[1:],
               [{**rows[0],'date':'2027-01-01'}]+rows[1:],
               [{**rows[0],'nums':[1]*6}]+rows[1:],
               [{**rows[0],'reintegro':True}]+rows[1:]]
        for case in cases:
            report=inspect_history(case,self.now)
            self.assertFalse(report['valid']);self.assertTrue(report['errors'])

    def test_missing_refund_is_reported_and_not_invented(self):
        rows=recent();rows[0].pop('reintegro')
        report=inspect_history(rows,self.now)
        self.assertTrue(report['valid']);self.assertEqual(report['refundMissing'],1)
        self.assertNotIn('reintegro',rows[0])

    def test_gap_scope_is_explicit_and_input_is_unchanged(self):
        rows=recent()[1:];original=deepcopy(rows)
        report=inspect_history(rows,self.now)
        self.assertEqual(rows,original);self.assertIn('90',report['calendarScope'])
