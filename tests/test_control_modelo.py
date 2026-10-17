from copy import deepcopy
from datetime import date, datetime, timedelta
import sys
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from control_modelo import decision, sign_p, scores, update_control
from modelo_adaptativo import train


def rows(count):
    return [{'date':(date(2025,1,1)+timedelta(days=3*i)).isoformat(),
             'nums':sorted(((i+j*7)%49)+1 for j in range(6)), 'reintegro':i%10} for i in range(count)]


def recorded_time(target):
    return datetime.fromisoformat(target).replace(tzinfo=ZoneInfo('Europe/Madrid'))-timedelta(hours=12)


def trial(challenger=.05, champion=.1, uniform=.11, hits=2, refund_hits=1):
    return {'result':{channel:{'challengerLoss':challenger,'championLoss':champion,'uniformLoss':uniform,
                              'challengerHits':hits if channel=='main' else refund_hits,'championHits':1 if channel=='main' else 0}
                      for channel in ('main','refund')}}


class ControlTests(unittest.TestCase):
    def test_requires_sixty_prospective_results(self):
        self.assertEqual(decision([trial()]*59,1)['status'],'collecting')
        self.assertEqual(decision([{}]*60,1)['draws'],0)

    def test_accepts_only_consistent_improvement_against_both_references(self):
        accepted=decision([trial() for _ in range(60)],1)
        self.assertEqual(accepted['status'],'accepted')
        for bad in (trial(challenger=.12),trial(champion=.01),trial(uniform=.01),trial(hits=0),trial(refund_hits=0)):
            self.assertEqual(decision([bad]*60,1)['status'],'rejected')
        tied=decision([trial(challenger=.1,champion=.1)]*60,1)
        self.assertEqual(tied['status'],'rejected')
        mixed=[trial() if i%2 else trial(challenger=.12) for i in range(60)]
        self.assertEqual(decision(mixed,1)['status'],'rejected')
        self.assertLess(decision([trial()]*60,2)['perComparisonAlpha'],accepted['perComparisonAlpha'])
        self.assertEqual(sign_p([0]*60),1)

    def test_frozen_weights_and_existing_shadow_predictions_are_preserved(self):
        first=rows(120);target=rows(121)[-1]['date']
        report=train(first,target)
        state,_=update_control(report,first,target,recorded_time(target))
        self.assertIsNone(state['challenger'])
        champion=deepcopy(state['champion'])
        current=rows(121);next_target=rows(122)[-1]['date']
        report=train(current,next_target)
        state,_=update_control(report,current,next_target,recorded_time(next_target),state)
        self.assertEqual(state['champion'],champion)
        self.assertEqual(len(state['records']),1)
        self.assertEqual(state['assessment']['draws'],0)
        saved=deepcopy(state['records'][0])
        repeated,_=update_control(report,current,next_target,recorded_time(next_target),state)
        self.assertEqual(repeated['records'][0],saved)
        self.assertEqual(repeated['champion'],champion)
        next_rows=rows(122);new_target=rows(123)[-1]['date']
        next_report=train(next_rows,new_target)
        settled,_=update_control(next_report,next_rows,new_target,recorded_time(new_target),state)
        self.assertEqual(settled['assessment']['draws'],1)
        self.assertEqual(settled['champion'],champion)
        self.assertEqual(settled['challenger'],state['challenger'])
        for key in ('champion','challenger','recordedAt'):
            self.assertEqual(settled['records'][0][key],saved[key])
        self.assertIn('result',settled['records'][0])
        corrected=deepcopy(next_rows);corrected[-1]['reintegro']=(corrected[-1]['reintegro']+1)%10
        with self.assertRaises(ValueError):
            update_control(train(corrected,new_target),corrected,new_target,recorded_time(new_target),settled)
        self.assertNotEqual(scores(champion,next_rows,new_target),scores(next_report,next_rows,new_target))

    def test_retroactive_shadow_registration_is_rejected(self):
        initial=rows(120);target=rows(121)[-1]['date']
        state,_=update_control(train(initial,target),initial,target,recorded_time(target))
        current=rows(121);target=rows(122)[-1]['date']
        with self.assertRaises(ValueError):
            update_control(train(current,target),current,target,datetime.fromisoformat(target+'T22:00:00').replace(tzinfo=ZoneInfo('Europe/Madrid')),state)
        with self.assertRaises(ValueError):scores(state['champion'],current,current[-1]['date'])

    def test_failed_or_accepted_trial_changes_weights_only_when_approved(self):
        initial=rows(120);target=rows(121)[-1]['date']
        state,_=update_control(train(initial,target),initial,target,recorded_time(target))
        current=rows(121);target=rows(122)[-1]['date']
        state,_=update_control(train(current,target),current,target,recorded_time(target),state)
        champion=deepcopy(state['champion']);candidate=deepcopy(state['challenger'])
        for passed in (True,False):
            case=deepcopy(state)
            case['records']=[{'epoch':1,'target':'2024-01-01','result':trial(challenger=.05 if passed else .2)['result']} for _ in range(60)]
            finished,_=update_control(train(current,target),current,target,recorded_time(target),case)
            self.assertEqual(finished['decisions'][-1]['status'],'accepted' if passed else 'rejected')
            self.assertEqual(finished['champion'],candidate if passed else champion)
            again,_=update_control(train(current,target),current,target,recorded_time(target),finished)
            self.assertEqual(len(again['decisions']),1)
