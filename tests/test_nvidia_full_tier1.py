"""Offline report and redaction-adapter contract regression tests."""
import copy
import json
import subprocess
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


    def test_live_control_clean_and_detected(self):
        marker = b"nonfunctional-marker"
        f.control_result(subprocess.CompletedProcess([], 0, b"null", b""), marker, detected=False)
        row = {"RuleID": f.CONTROL_RULE, "Secret": "REDACTED", "File": "probe.txt"}
        f.control_result(subprocess.CompletedProcess([], 10, json.dumps([row]).encode(), b""),
                         marker, detected=True)

    def test_live_control_rejects_raw_marker(self):
        marker = b"nonfunctional-marker"
        row = {"RuleID": f.CONTROL_RULE, "Secret": "REDACTED", "File": "probe.txt"}
        for stdout, stderr in ((marker, b""), (json.dumps([row]).encode(), marker)):
            with self.subTest(channel="stdout" if stdout == marker else "stderr"):
                with self.assertRaisesRegex(f.InstallCheckError, "CONTROL_REDACTION"):
                    f.control_result(subprocess.CompletedProcess([], 10, stdout, stderr),
                                     marker, detected=True)

    def test_live_control_rejects_wrong_exit(self):
        with self.assertRaisesRegex(f.InstallCheckError, "CONTROL_EXIT"):
            f.control_result(subprocess.CompletedProcess([], 0, b"[]", b""),
                             b"nonfunctional-marker", detected=True)

    def test_live_control_rejects_wrong_finding(self):
        row = {"RuleID": f.CONTROL_RULE, "Secret": "REDACTED", "File": "probe.txt"}
        for change in ({"RuleID": "wrong"}, {"Secret": "not-redacted"}, {"File": "other.txt"}):
            with self.subTest(change=change):
                stdout = json.dumps([{**row, **change}]).encode()
                with self.assertRaisesRegex(f.InstallCheckError, "CONTROL_FINDING"):
                    f.control_result(subprocess.CompletedProcess([], 10, stdout, b""),
                                     b"nonfunctional-marker", detected=True)

    def test_live_control_rejects_findings_in_clean_fixture(self):
        with self.assertRaisesRegex(f.InstallCheckError, "CONTROL_CLEAN"):
            f.control_result(subprocess.CompletedProcess([], 0, b"[{}]", b""),
                             b"nonfunctional-marker", detected=False)


if __name__ == "__main__":
    unittest.main()
