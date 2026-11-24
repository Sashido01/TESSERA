"""Offline report and redaction-adapter contract regression tests."""
import copy
import hashlib
from unittest import mock
import json
import subprocess
import tempfile
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_nvidia_full_tier1 as f


class FullTier1Tests(unittest.TestCase):
    def report(self):
        report = {"version": f.VERSION, "workflow": {"tier": 1, "stages": {"llm": {
            "status": "skipped", "reason": "LLM checks disabled by --no-llm."}}},
            "overall_passed": True, "incomplete_scans": [], "results": [
            {"validator": name, "status": "passed", "passed": True, "skipped": False,
             "incomplete_scans": [], "findings": [],
             "scanners": dict([f.SCANNERS[name]]) if name in f.SCANNERS else {}}
            for name in sorted(f.VALIDATORS)]}
        next(x for x in report["results"] if x["validator"] == "Code Risk Analysis")["scanners"]["semgrep"] = f.SEMGREP_VERSION
        return report

    def test_all_rows_not_certification(self):
        r = f.summary(self.report(), 0)
        self.assertEqual(len(r["validators"]), 13)
        self.assertEqual(r["certification"], "NOT_VERIFIED")
        self.assertEqual(r["semgrep"], "EXECUTED")

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


    def test_security_high_attribution_preserves_counts_and_policy(self):
        r = self.report()
        r["overall_passed"] = False
        row = next(x for x in r["results"] if x["validator"] == "Security Scan")
        row.update({"status": "failed", "passed": False, "findings": [
            {"severity": "high", "category": "SECURITY", "check_name": "skillspector_risk_score",
             "message": "synthetic private text"},
            {"severity": "HIGH", "category": "SECURITY", "check_name": "other"},
            {"severity": "medium", "category": "SECURITY", "check_name": "skillspector_risk_score"},
            {"severity": "critical", "category": "SECURITY", "check_name": "other"},
        ]})
        result = f.summary(r, 1)
        security = result["validators"]["Security Scan"]
        self.assertEqual(security["high_attribution"], {"aggregate_risk_gate": 1, "other_high": 1})
        self.assertEqual(security["findings"], {"critical": 1, "high": 2, "medium": 1, "low": 0, "info": 0})
        self.assertEqual(result["policy_verdict"], "FAIL")
        self.assertNotIn("synthetic private text", str(result))

    def test_security_high_attribution_does_not_trust_messages_or_unknown_category(self):
        r = self.report()
        r["overall_passed"] = False
        row = next(x for x in r["results"] if x["validator"] == "Security Scan")
        row.update({"status": "failed", "passed": False, "findings": [
            {"severity": "high", "category": "OTHER", "check_name": "skillspector_risk_score"},
            {"severity": "high", "message": "skillspector_risk_score"},
            {"severity": "high", "category": "SECURITY", "check_name": "skillspector_risk_score_suffix"},
        ]})
        security = f.summary(r, 1)["validators"]["Security Scan"]
        self.assertEqual(security["high_attribution"], {"aggregate_risk_gate": 0, "other_high": 3})

    def test_clean_security_high_attribution_is_zero(self):
        security = f.summary(self.report(), 0)["validators"]["Security Scan"]
        self.assertEqual(security["high_attribution"], {"aggregate_risk_gate": 0, "other_high": 0})


    def test_semgrep_version_required(self):
        for value in (None, "1.0.0"):
            r = self.report()
            scanners = next(x for x in r["results"] if x["validator"] == "Code Risk Analysis")["scanners"]
            scanners["semgrep"] = value
            with self.assertRaisesRegex(f.InstallCheckError, "SCANNER_VERSION:semgrep"):
                f.summary(r, 0)

    def test_semgrep_control_clean_and_positive(self):
        with tempfile.TemporaryDirectory() as folder:
            target = pathlib.Path(folder).resolve() / "probe.py"
            for detected in (False, True):
                report = {"errors": [], "paths": {"scanned": ["probe.py"]}, "results": (
                    [{"check_id": f.SEMGREP_CONTROL_RULE, "path": "probe.py"}] if detected else [])}
                f.semgrep_control_result(subprocess.CompletedProcess([], int(detected),
                    json.dumps(report).encode(), b""), target, detected=detected)

    def test_semgrep_control_rejects_errors_or_missing_coverage(self):
        with tempfile.TemporaryDirectory() as folder:
            target = pathlib.Path(folder).resolve() / "probe.py"
            for report, code in (({"errors": [{}], "paths": {"scanned": ["probe.py"]}, "results": []}, "REPORT"),
                                 ({"errors": [], "paths": {"scanned": []}, "results": []}, "COVERAGE")):
                with self.assertRaisesRegex(f.InstallCheckError, "SEMGREP_" + code):
                    f.semgrep_control_result(subprocess.CompletedProcess([], 0,
                        json.dumps(report).encode(), b""), target, detected=False)

    def test_semgrep_control_rejects_wrong_exit_or_rule(self):
        with tempfile.TemporaryDirectory() as folder:
            target = pathlib.Path(folder).resolve() / "probe.py"
            report = {"errors": [], "paths": {"scanned": ["probe.py"]},
                      "results": [{"check_id": "wrong", "path": "probe.py"}]}
            for rc, code in ((0, "EXIT"), (1, "FINDINGS")):
                with self.assertRaisesRegex(f.InstallCheckError, "SEMGREP_" + code):
                    f.semgrep_control_result(subprocess.CompletedProcess([], rc,
                        json.dumps(report).encode(), b""), target, detected=True)


    def test_semgrep_rules_sha256_pin(self):
        self.assertEqual(f.SEMGREP_RULES_SHA256,
                         "fff4537f6679a52c48e024e001b73e163b24587635a028e5c012583f19876abf")
        self.assertEqual(f.SEMGREP_RULES_SIZE, 3376)
        raw = b"synthetic exact rules"
        with mock.patch.object(f, "SEMGREP_RULES_SIZE", len(raw)), \
                mock.patch.object(f, "SEMGREP_RULES_SHA256", hashlib.sha256(raw).hexdigest()):
            f.semgrep_rules_ok(raw)
            for bad in (raw[:-1], raw+b"\n", b"x"+raw[1:]):
                with self.assertRaisesRegex(f.InstallCheckError, "SEMGREP_RULES"):
                    f.semgrep_rules_ok(bad)


if __name__ == "__main__":
    unittest.main()
