"""Offline checks for focused NVIDIA Tier 1 evidence, not a substitute for CI."""
import copy
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import check_nvidia_tier1 as n


def fixture(passed=True):
    status = "passed" if passed else "failed"
    return {"version": n.VERSION, "workflow": {"tier": 1, "stages": {
        "validation": {"status": status},
        "llm": {"status": "skipped", "reason": "LLM checks disabled by --no-llm."}}},
        "incomplete_scans": [], "total_skipped": 0, "overall_passed": passed,
        "overall_status": status, "results": [
            {"validator": n.CHECKS[0], "passed": passed, "status": status,
             "skipped": False, "incomplete_scans": [], "findings": []},
            {"validator": n.CHECKS[1], "passed": True, "status": "passed",
             "skipped": False, "incomplete_scans": [], "findings": [],
             "quality": {"overall_score": 82.5}}]}


class EvidenceTests(unittest.TestCase):
    def test_pass(self):
        self.assertEqual(n.checked_report(fixture(), 0)["focused_verdict"], "PASS")

    def test_fail_is_not_pass(self):
        self.assertEqual(n.checked_report(fixture(False), 1)["focused_verdict"], "FAIL")

    def test_extra_tier(self):
        data = fixture()
        data["workflow"]["tier"] = 2
        with self.assertRaisesRegex(n.InstallCheckError, "SCOPE"):
            n.checked_report(data, 0)

    def test_llm_enabled(self):
        data = fixture()
        data["workflow"]["stages"]["llm"] = {"status": "enabled"}
        with self.assertRaisesRegex(n.InstallCheckError, "SCOPE"):
            n.checked_report(data, 0)

    def test_missing_validator(self):
        data = fixture()
        data["results"].pop()
        with self.assertRaisesRegex(n.InstallCheckError, "CHECKS"):
            n.checked_report(data, 0)

    def test_skipped_validator(self):
        data = fixture()
        data["results"][0]["skipped"] = True
        with self.assertRaisesRegex(n.InstallCheckError, "INCOMPLETE"):
            n.checked_report(data, 0)

    def test_bad_score(self):
        for score in (float("nan"), 101, -1, True, "82"):
            data = fixture()
            data["results"][1]["quality"]["overall_score"] = score
            with self.assertRaisesRegex(n.InstallCheckError, "SCORE"):
                n.checked_report(data, 0)

    def test_exit_mismatch(self):
        data = fixture(False)
        data["workflow"]["stages"]["validation"]["status"] = "passed"
        with self.assertRaisesRegex(n.InstallCheckError, "EXIT"):
            n.checked_report(data, 0)

    def test_no_raw_finding_content(self):
        data = fixture()
        data["results"][0]["findings"] = [
            {"check": "metadata_author", "severity": "low", "message": "private synthetic path"},
            {"check": "unsafe/path", "severity": "high"}]
        result = n.checked_report(data, 0)
        self.assertEqual(result["findings"], [{"check": "metadata_author", "severity": "low"}])
        self.assertNotIn("private", str(result))


if __name__ == "__main__":
    unittest.main()
