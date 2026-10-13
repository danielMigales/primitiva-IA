import copy
from datetime import date, timedelta
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluar_metodos import bayesian_cdm_adaptation, evaluate, holm_adjust, knn_prediction


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "data/evaluacion-metodos-config.json").read_text())
        self.config.update(minimumTrainingDraws=5, testDraws=6, knnNeighbors=3,
                           knnTrainingPairs=6, randomReferenceReplicates=20)
        self.rows = [{"date": (date(2020,1,1)+timedelta(days=i)).isoformat(),
                      "nums": sorted((i*7+j)%49+1 for j in range(6))} for i in range(20)]

    def test_predictions_are_six_distinct_valid_numbers(self):
        for fn in (bayesian_cdm_adaptation, knn_prediction):
            nums = fn(self.rows)
            self.assertEqual(len(set(nums)), 6)
            self.assertTrue(all(type(n) is int and 1<=n<=49 for n in nums))

    def test_future_result_cannot_change_earlier_predictions(self):
        original = evaluate(self.rows, self.config)
        changed = copy.deepcopy(self.rows)
        changed[-1]["nums"] = [1,2,3,4,5,6]
        modified = evaluate(changed, self.config)
        self.assertEqual(original["trace"][:-1], modified["trace"][:-1])
        self.assertEqual(original["trace"][-1]["methods"].keys(), modified["trace"][-1]["methods"].keys())
        for key in original["methods"]:
            self.assertEqual(original["trace"][-1]["methods"][key]["nums"], modified["trace"][-1]["methods"][key]["nums"])

    def test_reproducible_and_equal_number_of_predictions(self):
        first = evaluate(self.rows, self.config)
        self.assertEqual(first, evaluate(self.rows, self.config))
        for summary in first["methods"].values():
            self.assertEqual(summary["draws"], 6)
            self.assertEqual(sum(summary["histogram0to6"]), 6)
        self.assertTrue(all(r["historyUntil"]<r["target"] for r in first["trace"]))

    def test_uniform_prior_is_frequency_ranking_not_a_new_signal(self):
        history = [{"date": "2020-01-01", "nums": [6,7,8,9,10,11]}]*10
        self.assertEqual(bayesian_cdm_adaptation(history), [6,7,8,9,10,11])
        self.assertEqual(bayesian_cdm_adaptation(history, 100), [6,7,8,9,10,11])

    def test_holm_controls_the_comparison_family(self):
        adjusted = holm_adjust({"a": .01, "b": .02, "c": .8})
        self.assertAlmostEqual(adjusted["a"], .03)
        self.assertAlmostEqual(adjusted["b"], .04)
        self.assertAlmostEqual(adjusted["c"], .8)

    def test_duplicate_dates_are_rejected(self):
        self.rows[-1]["date"] = self.rows[-2]["date"]
        with self.assertRaises(ValueError):
            evaluate(self.rows, self.config)


if __name__ == "__main__":
    unittest.main()
