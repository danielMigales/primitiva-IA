import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audit_history", ROOT / "scripts/auditar_historico.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "data").mkdir()
        self.history = self.root / "data/sorteos.json"
        self.rows = [{"date": d, "nums": [1, 2, 3, 4, 5, 6], "reintegro": 9}
                     for d in ("2026-10-08", "2026-10-10", "2026-10-12")]
        self.save()

    def save(self):
        self.history.write_text(json.dumps({"draws": self.rows, "reintegro_coverage": {"total": 2, "with_reintegro": 2}}))
        self.before = self.history.read_bytes()

    def official(self, day):
        return {"date": day.isoformat(), "nums": [1, 2, 3, 4, 5, 6], "reintegro": 9,
                "sourceUrl": audit.source.official_url(day), "sourceType": "official-press-pdf", "sourceSha256": "a"*64}

    def run_audit(self, fetch, limit=20):
        code = audit.audit(root=self.root, limit=limit, delay=0, fetch=fetch)
        self.assertEqual(self.history.read_bytes(), self.before)
        self.report = json.loads((self.root / "data/auditoria-historico.json").read_text())
        return code

    def test_resume_and_metadata_warning_without_rewriting(self):
        fetch = Mock(side_effect=self.official)
        self.assertEqual(self.run_audit(fetch, 1), 0)
        self.assertEqual(self.report["summary"]["pending"], 2)
        self.assertEqual(self.run_audit(fetch), 0)
        self.assertEqual(fetch.call_count, 3)
        self.assertTrue(self.report["fullyVerified"])
        self.assertEqual(self.report["structural"]["warnings"][0]["actualTotal"], 3)

    def test_conflict_keeps_official_evidence_but_never_confirms(self):
        self.assertEqual(self.run_audit(lambda d: {**self.official(d), "reintegro": 8}), 1)
        self.assertEqual(self.report["summary"]["conflict"], 3)
        proofs = json.loads((self.root / "data/verificacion-sorteos.json").read_text())["draws"]
        self.assertEqual(proofs, [])
        self.assertEqual(self.report["draws"][0]["conflictingFields"], ["reintegro"])

    def test_missing_document_is_unverified_and_not_retried_each_run(self):
        fetch = Mock(return_value=None)
        self.assertEqual(self.run_audit(fetch), 0)
        self.assertEqual(self.run_audit(fetch), 0)
        self.assertEqual(fetch.call_count, 3)
        self.assertFalse(self.report["fullyVerified"])
        self.assertEqual(self.report["summary"]["document-not-found"], 3)

    def test_access_error_stops_batch_and_is_retriable(self):
        fetch = Mock(side_effect=RuntimeError("source unavailable"))
        self.assertEqual(self.run_audit(fetch), 1)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(self.report["summary"]["pending"], 2)
        self.assertEqual(self.run_audit(self.official), 0)
        self.assertTrue(self.report["fullyVerified"])

    def test_invalid_history_stops_before_download(self):
        self.rows.append(self.rows[0])
        self.save()
        fetch = Mock()
        self.assertEqual(self.run_audit(fetch), 1)
        fetch.assert_not_called()
        self.assertEqual(self.report["status"], "invalid-history")

    def test_changed_record_requires_new_comparison(self):
        self.run_audit(self.official)
        self.rows[0]["reintegro"] = 8
        self.save()
        fetch = Mock(side_effect=self.official)
        self.assertEqual(self.run_audit(fetch), 1)
        self.assertEqual(fetch.call_count, 1)
        self.assertFalse(self.report["fullyVerified"])

    def test_missing_historical_reintegro_is_not_full_match(self):
        del self.rows[0]["reintegro"]
        self.save()
        self.run_audit(self.official)
        self.assertEqual(self.report["summary"]["numbers-only"], 1)
        self.assertFalse(self.report["fullyVerified"])

    def test_explicit_recheck_conflict_removes_previous_proof(self):
        self.run_audit(self.official)
        code = audit.audit(root=self.root, delay=0,
                           fetch=lambda d: {**self.official(d), "reintegro": 8},
                           dates={"2026-10-12"})
        self.assertEqual(code, 1)
        self.run_audit(self.official)
        self.assertEqual(self.report["summary"]["conflict"], 1)
        proofs = json.loads((self.root / "data/verificacion-sorteos.json").read_text())["draws"]
        self.assertEqual(len(proofs), 2)


if __name__ == "__main__":
    unittest.main()
