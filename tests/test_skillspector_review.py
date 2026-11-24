"""Offline report contract tests. Actual scanner execution is separate."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_skillspector_review as s


class SkillSpectorTests(unittest.TestCase):
    def report(self):
        return {"execution_successful": True,
                "metadata": {"skillspector_version": s.VERSION, "llm_requested": False,
                             "llm_available": False, "meta_analysis_applied": False,
                             "inference_usage": []},
                "analysis_completeness": {
                    "execution_successful": True, "status": "complete", "is_complete": True,
                    "total_components": 1, "scanned_components": 1, "fully_inspected_files": 1,
                    "partially_inspected_files": 0, "entirely_uninspected_files": 0,
                    "coverage_percent": 100, "findings_before_filtering": 0,
                    "findings_after_filtering": 0, "ledger_exceptions": [], "scope_exclusions": []},
                "components": [{"path": "SKILL.md", "size_bytes": 100}],
                "issues": [], "suppressed_count": 0,
                "risk_assessment": {"score": 0, "severity": "LOW"}}

    def check(self, data, rc=0, expected=None):
        return s.summary(data, rc, {"SKILL.md": 100} if expected is None else expected)

    def test_clean(self):
        self.assertEqual(self.check(self.report())["analysis_status"], "complete")

    def test_llm_rejected(self):
        data = self.report()
        data["metadata"]["llm_requested"] = True
        with self.assertRaisesRegex(s.InstallCheckError, "PROVENANCE"):
            self.check(data)

    def test_inference_rejected(self):
        data = self.report()
        data["metadata"]["inference_usage"] = [{}]
        with self.assertRaisesRegex(s.InstallCheckError, "PROVENANCE"):
            self.check(data)

    def test_false_complete_rejected(self):
        with self.assertRaisesRegex(s.InstallCheckError, "FALSE_COMPLETE"):
            self.check(self.report(), expected={"SKILL.md": 100, "extra.md": 5})

    def test_wrong_size_rejected(self):
        with self.assertRaisesRegex(s.InstallCheckError, "COMPONENT_MISMATCH"):
            self.check(self.report(), expected={"SKILL.md": 101})

    def test_execution_failure_rejected(self):
        with self.assertRaisesRegex(s.InstallCheckError, "EXECUTION"):
            self.check(self.report(), rc=2)

    def test_partial_is_retained(self):
        data = self.report()
        data["analysis_completeness"].update({"status": "partial", "is_complete": False,
            "fully_inspected_files": 0, "partially_inspected_files": 1,
            "scanned_components": 0, "coverage_percent": 0})
        self.assertEqual(self.check(data)["analysis_status"], "partial")

    def test_findings_sanitized(self):
        data = self.report()
        data["issues"] = [{"id": "P1", "severity": "HIGH", "finding": "raw text"}]
        data["analysis_completeness"].update({"findings_before_filtering": 1,
                                             "findings_after_filtering": 1})
        result = self.check(data)
        self.assertEqual(result["findings"], 1)
        self.assertNotIn("raw text", str(result))


if __name__ == "__main__":
    unittest.main()
