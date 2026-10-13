import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validar_reto import validate_prediction


class RetoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        (self.work / "data").mkdir()
        self.existing = {
            "version": 1,
            "predictions": [
                {"target": "2026-10-12", "nums": [12, 17, 20, 24, 34, 40],
                 "window": 50, "historyUntil": "2026-10-10", "algorithm": "frozen-pair-50-v1"},
                {"target": "2026-10-15", "nums": [4, 10, 20, 22, 40, 45],
                 "window": 365, "created": "2026-10-12", "numberEvidence": [{"score": 1.2}]},
            ],
            "revisions": [{"target": "2026-10-15", "reason": "preserve prior registration"}],
        }
        self.registry = self.work / "data/reto-predictor.json"
        self.registry.write_text(json.dumps(self.existing))
        # 120 draws ending before a prospective Thursday; no network or real writes.
        self.rows = [{"date": (date(2026, 10, 12) - timedelta(days=i)).isoformat(),
                      "nums": [1, 2, 3, 4, 5, 6], "reintegro": i % 10}
                     for i in range(120)]
        (self.work / "data/sorteos.json").write_text(json.dumps({"draws": self.rows}))
        self.entry = {"target": "2026-10-22", "nums": [6, 5, 4, 3, 2, 1],
                      "created": "2026-10-12T10:00:00+02:00", "window": 50,
                      "historyUntil": "2026-10-12"}

    def manual(self, entries):
        return subprocess.run([sys.executable, str(ROOT / "scripts/guardar_reto.py")],
                              cwd=self.work, env={**os.environ, "REGISTRO_JSON": json.dumps(entries)},
                              capture_output=True, text=True)

    def test_supported_windows(self):
        for window in (5, 20, 50, 100, 365, 500, 1000, 99999):
            with self.subTest(window=window):
                validate_prediction({**self.entry, "window": window}, "2026-10-12", date(2026, 10, 13))

    def test_invalid_windows(self):
        for window in (0, 51, 366, True, "50", 50.0, None):
            with self.subTest(window=window), self.assertRaises(ValueError):
                validate_prediction({**self.entry, "window": window}, "2026-10-12", date(2026, 10, 13))

    def test_existing_guards(self):
        for change in ({"nums": [1]*6}, {"nums": [0, 2, 3, 4, 5, 6]},
                       {"created": "2026-10-12T10:00:00"},
                       {"created": "2026-10-14T10:00:00+00:00"},
                       {"target": "2026-10-12"}, {"historyUntil": "2026-10-22"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_prediction({**self.entry, **change}, "2026-10-12", date(2026, 10, 13))

    def test_manual_accepts_50_and_365_without_changing_history(self):
        entries = [self.entry, {**self.entry, "target": "2026-10-24", "window": 365}]
        result = self.manual({"predictions": entries})
        self.assertEqual(result.returncode, 0, result.stderr)
        saved = json.loads(self.registry.read_text())
        self.assertEqual(saved["predictions"][:2], self.existing["predictions"])
        self.assertEqual(saved["revisions"], self.existing["revisions"])
        self.assertEqual(saved["predictions"][2]["nums"], [1, 2, 3, 4, 5, 6])
        self.assertEqual(self.manual(entries).returncode, 0)
        self.assertEqual(json.loads(self.registry.read_text()), saved)
        before = self.registry.read_bytes()
        conflict = self.manual([{**self.entry, "nums": [1, 2, 3, 4, 5, 7]}])
        self.assertNotEqual(conflict.returncode, 0)
        self.assertEqual(self.registry.read_bytes(), before)

    def test_invalid_batch_is_not_written(self):
        before = self.registry.read_bytes()
        result = self.manual([self.entry, {**self.entry, "target": "2026-10-24", "window": 51}])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.registry.read_bytes(), before)

    def automatic(self, day, reject=False):
        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2026, 10, day, 12, tzinfo=timezone.utc).astimezone(tz)
        previous = Path.cwd()
        try:
            os.chdir(self.work)
            with patch("datetime.datetime", Clock), patch("validar_reto.datetime", Clock):
                if reject:
                    with patch("validar_reto.validate_prediction", side_effect=ValueError("blocked")):
                        runpy.run_path(str(ROOT / "scripts/generar_reto.py"), run_name="__main__")
                else:
                    runpy.run_path(str(ROOT / "scripts/generar_reto.py"), run_name="__main__")
        finally:
            os.chdir(previous)

    def test_automatic_validates_and_preserves_history(self):
        self.automatic(16)  # tomorrow is Saturday 17, not already registered
        saved = json.loads(self.registry.read_text())
        entry = saved["predictions"][-1]
        self.assertEqual(entry["window"], 365)
        self.assertEqual(entry["algorithm"], "unified-recency-z-30-90-365-v1")
        self.assertEqual(saved["predictions"][:-1], self.existing["predictions"])
        self.assertEqual(saved["revisions"], self.existing["revisions"])
        validate_prediction(entry, "2026-10-12", date(2026, 10, 16))
        # The same generated entry is accepted through the manual route.
        self.registry.write_text(json.dumps(self.existing))
        # Created must not be in the future relative to the real test clock.
        entry["created"] = self.entry["created"]
        self.assertEqual(self.manual([entry]).returncode, 0)

    def test_automatic_rejection_prevents_write(self):
        before = self.registry.read_bytes()
        with self.assertRaisesRegex(ValueError, "blocked"):
            self.automatic(16, reject=True)
        self.assertEqual(self.registry.read_bytes(), before)

    def test_automatic_noops(self):
        before = self.registry.read_bytes()
        for day in (13, 14):  # no draw tomorrow; then already registered 15th
            with self.assertRaises(SystemExit) as stopped:
                self.automatic(day)
            self.assertEqual(stopped.exception.code, 0)
            self.assertEqual(self.registry.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
