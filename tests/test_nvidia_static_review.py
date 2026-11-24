"""Offline contract checks; real upstream execution remains mandatory."""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_nvidia_static_review as n


class StaticReviewTests(unittest.TestCase):
    def report(self, passed=True):
        status = "passed" if passed else "failed"
        return {"version": n.VERSION, "workflow": {"tier": 1, "stages": {
            "validation": {"status": status},
            "llm": {"status": "skipped", "reason": "LLM checks disabled by --no-llm."}}},
            "incomplete_scans": [], "total_skipped": 0, "overall_passed": passed,
            "overall_status": status, "results": [
                {"validator": "Unicode Smuggling Detection", "passed": passed, "status": status,
                 "skipped": False, "incomplete_scans": [], "findings": [],
                 "summary": {"files_scanned": 1, "checks_performed": 1, "warnings": 0, "errors": int(not passed)}}]}

    def test_static_pass(self):
        result = n.static_review(self.report(), 0, expected=("Unicode Smuggling Detection",))
        self.assertEqual(result["Unicode Smuggling Detection"]["status"], "PASSED")

    def test_static_fail_is_retained(self):
        result = n.static_review(self.report(False), 1, expected=("Unicode Smuggling Detection",))
        self.assertEqual(result["Unicode Smuggling Detection"]["status"], "FAILED")

    def test_zero_coverage_blocked(self):
        data = self.report()
        data["results"][0]["summary"]["files_scanned"] = 0
        with self.assertRaisesRegex(n.InstallCheckError, "NO_SCAN_COVERAGE"):
            n.static_review(data, 0, expected=("Unicode Smuggling Detection",))

    def test_scope_cannot_enable_llm(self):
        data = self.report()
        data["workflow"]["stages"]["llm"] = {"status": "enabled"}
        with self.assertRaisesRegex(n.InstallCheckError, "SCOPE"):
            n.static_review(data, 0, expected=("Unicode Smuggling Detection",))

    def test_incomplete_scan_blocked(self):
        data = self.report()
        data["results"][0]["incomplete_scans"] = ["external"]
        with self.assertRaisesRegex(n.InstallCheckError, "INCOMPLETE"):
            n.static_review(data, 0, expected=("Unicode Smuggling Detection",))

    def test_unknown_finding_not_hidden_or_logged_raw(self):
        row = {"findings": [{"check": "unexpected/key", "severity": "medium",
                             "message": "synthetic sensitive raw content"}]}
        self.assertEqual(n.sanitized_findings([row], explain=True),
                         [{"check": "OTHER_CHECK", "severity": "medium", "reason": "UNCLASSIFIED"}])

    def test_localization_reason(self):
        self.assertEqual(n.reason({"message": "No limitations documented"}),
                         "LIMITATIONS_HEADING_MISSING")

    def test_harness_status_is_not_live_pass(self):
        path = pathlib.Path("/fixture/skill")
        data = {"harness_compatibility": {str(path): [{"harness": "codex", "status": "not_loaded",
            "verified_version": "0.166.0", "verified_date": "2026-11-01",
            "findings": [{"id": "CX-ROOT", "effect": "not_loaded", "message": "private raw"}]}]}}
        result = n.harness_review(data, path, "codex")
        self.assertEqual(result["status"], "not_loaded")
        self.assertEqual(result["live_agent"], "NOT_VERIFIED")
        self.assertNotIn("private", str(result))
        with self.assertRaisesRegex(n.InstallCheckError, "STATUS"):
            n.harness_review(data, path, "hermes")

    def test_locale_config_keeps_points_and_english(self):
        data = json.loads((ROOT / "tools/nvidia-quality-ru.json").read_text(encoding="utf-8"))
        self.assertEqual([x["points"] for x in data["expected_headers"]], [5, 5, 5])
        self.assertEqual([x["heading"] for x in data["expected_headers"]],
                         ["## Prerequisites", "## Limitations", "## Troubleshooting"])
        self.assertIn("## Requirements", data["expected_headers"][0]["alternatives"])
        self.assertIn("## Common Issues", data["expected_headers"][2]["alternatives"])
        self.assertIn("## FAQ", data["expected_headers"][2]["alternatives"])
        self.assertEqual(set(data), {"expected_headers", "error_handling"})
        self.assertEqual(set(data["error_handling"]["mentioned"]), {"terms"})
        self.assertIn("validation", data["error_handling"]["mentioned"]["terms"])
        self.assertIn("проверка", data["error_handling"]["mentioned"]["terms"])


if __name__ == "__main__":
    unittest.main()
