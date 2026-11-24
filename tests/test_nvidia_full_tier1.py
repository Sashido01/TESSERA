"""Offline report and redaction-adapter contract regression tests."""
import copy
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_nvidia_full_tier1 as f


class FullTier1Tests(unittest.TestCase):
    def report(self):
        return {"version": f.VERSION, "workflow": {"tier": 1, "stages": {"llm": {
            "status": "skipped", "reason": "LLM checks disabled by --no-llm."}}},
            "overall_passed": True, "incomplete_scans": [], "results": [
            {"validator": name, "status": "passed", "passed": True, "skipped": False,
             "incomplete_scans": [], "findings": [],
             "scanners": dict([f.SCANNERS[name]]) if name in f.SCANNERS else {}}
            for name in sorted(f.VALIDATORS)]}

    def test_all_rows_not_certification(self):
        r = f.summary(self.report(), 0)
        self.assertEqual(len(r["validators"]), 13)
        self.assertEqual(r["certification"], "NOT_VERIFIED")
        self.assertEqual(r["semgrep"], "NOT_RUN")

    def test_missing_validator_rejected(self):
        r = self.report()
        r["results"].pop()
        with self.assertRaisesRegex(f.InstallCheckError, "VALIDATORS"):
            f.summary(r, 0)

    def test_unexpected_scanner_version_rejected(self):
        r = self.report()
        next(x for x in r["results"] if x["validator"] == "Security Scan")["scanners"] = {
            "skillspector": "2.13.6"}
        with self.assertRaisesRegex(f.InstallCheckError, "SCANNER_VERSION"):
            f.summary(r, 0)

    def test_incomplete_scanner_rejected(self):
        r = self.report()
        next(x for x in r["results"] if x["validator"] == "Secrets Detection")["incomplete_scans"] = ["gitleaks"]
        with self.assertRaisesRegex(f.InstallCheckError, "SCANNER_INCOMPLETE"):
            f.summary(r, 0)

    def test_incomplete_non_scanner_visible(self):
        r = self.report()
        next(x for x in r["results"] if x["validator"] == "Harness Compatibility")["skipped"] = True
        self.assertEqual(f.summary(r, 0)["coverage"], "PARTIAL")

    def test_findings_only_aggregate(self):
        r = self.report()
        r["overall_passed"] = False
        row = next(x for x in r["results"] if x["validator"] == "Security Scan")
        row.update({"status": "failed", "passed": False,
                    "findings": [{"severity": "high", "message": "synthetic private text"}]})
        result = f.summary(r, 1)
        self.assertEqual(result["policy_verdict"], "FAIL")
        self.assertEqual(result["validators"]["Security Scan"]["findings"]["high"], 1)
        self.assertNotIn("synthetic private text", str(result))

    def test_exit_mismatch(self):
        with self.assertRaisesRegex(f.InstallCheckError, "EXIT_MISMATCH"):
            f.summary(self.report(), 1)


if __name__ == "__main__":
    unittest.main()
