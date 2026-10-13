import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from datetime import date, timedelta
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("update_data", ROOT / "update_data.py")
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class UpdateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dest = Path(temp.name) / "sorteos.json"
        self.rows = [{"date": (date(2026, 10, 12)-timedelta(days=i)).isoformat(),
                      "nums": [1, 2, 3, 4, 5, 6], "reintegro": 9} for i in range(2900)]
        self.dest.write_text(json.dumps({"draws": self.rows}))
        self.before = self.dest.read_bytes()
        self.start_patch = patch.object(updater, "DEST", self.dest)
        self.start_patch.start()
        self.addCleanup(self.start_patch.stop)
        class Clock(date):
            @classmethod
            def today(cls): return cls(2026, 10, 13)
        clock_patch = patch.object(updater.dt, "date", Clock)
        clock_patch.start()
        self.addCleanup(clock_patch.stop)

    def run_with(self, row):
        with patch.object(updater, "official", side_effect=lambda d: row if d.isoformat()=="2026-10-12" else None):
            return updater.main()

    def report(self):
        return json.loads(self.dest.with_name("estado-actualizacion.json").read_text())

    def test_unavailable_source_never_creates_verification(self):
        self.assertEqual(self.run_with(None), 0)
        self.assertEqual(self.dest.read_bytes(), self.before)
        self.assertEqual(self.report()["status"], "unavailable")
        self.assertFalse(self.dest.with_name("verificacion-sorteos.json").exists())

    def test_matching_result_confirms_without_rewriting_history(self):
        self.assertEqual(self.run_with(self.rows[0]), 0)
        self.assertEqual(self.dest.read_bytes(), self.before)
        verified = json.loads(self.dest.with_name("verificacion-sorteos.json").read_text())["draws"][0]
        self.assertEqual(verified["nums"], self.rows[0]["nums"])
        self.assertEqual(verified["source"], "SELAE")
        self.assertIn("checkedAt", verified)
        self.assertEqual(self.report()["status"], "confirmed")

    def test_reintegro_conflict_stops_without_overwriting(self):
        self.assertEqual(self.run_with({**self.rows[0], "reintegro": 8}), 1)
        self.assertEqual(self.dest.read_bytes(), self.before)
        self.assertEqual(self.report()["conflicts"][0]["field"], "reintegro")
        self.assertFalse(self.dest.with_name("verificacion-sorteos.json").exists())

    def test_number_conflict_stops_without_overwriting(self):
        self.assertEqual(self.run_with({**self.rows[0], "nums": [1,2,3,4,5,7]}), 1)
        self.assertEqual(self.dest.read_bytes(), self.before)
        self.assertEqual(self.report()["status"], "conflict")

    def test_html_is_not_an_official_json_result(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, n): return b'<html>Primitiva 1 2 3 4 5 6</html>'
        with patch.object(updater.urllib.request, "urlopen", return_value=Response()):
            self.assertIsNone(updater.official(date(2026, 10, 12)))

    def test_official_json_requires_exact_date_game_and_integer_numbers(self):
        class Response:
            def __init__(self, payload): self.payload = payload
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, n): return json.dumps(self.payload).encode()
        good = {"fecha_sorteo": "20261012", "combinacion": [1,2,3,4,5,6], "reintegro": 9}
        for change in ({"fecha_sorteo": "2026101234"}, {"game_id": "BONO"}, {"combinacion": [1,2,3,4,5,6.5]}):
            with self.subTest(change=change), patch.object(updater.urllib.request, "urlopen", return_value=Response({**good, **change})):
                self.assertIsNone(updater.official(date(2026, 10, 12)))
        with patch.object(updater.urllib.request, "urlopen", return_value=Response(good)):
            self.assertEqual(updater.official(date(2026, 10, 12))["nums"], good["combinacion"])


if __name__ == "__main__":
    unittest.main()
