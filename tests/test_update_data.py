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
            url = "https://www.loteriasyapuestas.es/f/loterias/documentos/result.pdf"
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, n): return b'<html>Primitiva 1 2 3 4 5 6</html>'
        with patch.object(updater.urllib.request, "urlopen", return_value=Response()):
            with self.assertRaisesRegex(ValueError, "PDF oficial"):
                updater.official(date(2026, 10, 12))

    def pdf_text(self):
        return """En el sorteo de la Lotería Primitiva celebrado hoy lunes día 12 de octubre de 2026
la combinación ganadora ha correspondido a los siguientes números:
40 26 42 02 45 05 23 9 - - - - -
Complementario Reintegro JOKER: 4781884
La recaudación del sorteo ascendió a 4.801.230,00 euros
Reintegro 458.451 1,00"""

    def test_pdf_result_block_excludes_prize_table_and_joker(self):
        row = updater.parse_official_pdf_text(self.pdf_text(), date(2026, 10, 12))
        self.assertEqual(row, {"date": "2026-10-12", "nums": [2,5,26,40,42,45], "reintegro": 9})

    def test_pdf_labels_joined_to_digits_remain_separate_fields(self):
        text = self.pdf_text().replace("23 9 - - - - -\nComplementario Reintegro", "- - - - -Complementario23Reintegro9")
        row = updater.parse_official_pdf_text(text, date(2026,10,12))
        self.assertEqual(row["reintegro"], 9)
        self.assertEqual(row["nums"], [2,5,26,40,42,45])

    def test_pdf_requires_correct_game_date_and_unique_block(self):
        text = self.pdf_text()
        for changed in (text.replace("Lotería Primitiva", "BonoLoto"),
                        text.replace("12 de octubre", "10 de octubre"),
                        text+text,
                        text.replace("40 26 42 02 45 05", "40 40 42 02 45 05"),
                        text.replace("23 9 -", "23 10 -"),
                        text.replace("Reintegro JOKER", "JOKER")):
            with self.subTest(text=changed), self.assertRaises(ValueError):
                updater.parse_official_pdf_text(changed, date(2026, 10, 12))

    def test_pdf_date_must_match_requested_target(self):
        with self.assertRaises(ValueError):
            updater.parse_official_pdf_text(self.pdf_text(), date(2026, 10, 10))

    def test_url_is_official_dated_press_document(self):
        self.assertEqual(updater.official_url(date(2026,10,12)),
            "https://www.loteriasyapuestas.es/f/loterias/documentos/La%20Primitiva/Notas%20de%20prensa/NOTA_DE_PRENSA_LA_PRIMITIVA_LUNES_12_10_26.pdf")


if __name__ == "__main__":
    unittest.main()
