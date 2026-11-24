"""Offline checks for Gitleaks' bounded, redacted report contract."""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_gitleaks_review as g


class GitleaksReviewTests(unittest.TestCase):
    log = b"INF scanned ~15 bytes (15) in 1ms\nINF no leaks found\n"

    def parse(self, rows, rc=0, log=None, size=15):
        return g.parse_scan(json.dumps(rows).encode(), self.log if log is None else log, rc, size)

    def test_clean(self):
        self.assertEqual(self.parse([]), {})

    def test_null_clean(self):
        self.assertEqual(self.parse(None), {})

    def test_findings_aggregate_only(self):
        result = self.parse([{"RuleID": "aws-access-token", "Secret": "REDACTED",
                              "Match": "synthetic sensitive raw data"}], g.FINDINGS_EXIT)
        self.assertEqual(result, {"aws-access-token": 1})
        self.assertNotIn("sensitive", str(result))

    def test_missing_coverage(self):
        with self.assertRaisesRegex(g.InstallCheckError, "COVERAGE"):
            self.parse([], log=b"INF no leaks found\n")

    def test_zero_coverage(self):
        with self.assertRaisesRegex(g.InstallCheckError, "COVERAGE"):
            self.parse([], log=b"INF scanned ~0 bytes (0)\n")

    def test_partial_scan(self):
        with self.assertRaisesRegex(g.InstallCheckError, "INCOMPLETE"):
            self.parse([], log=self.log + b"WARN partial scan completed\n")

    def test_exit_mismatch(self):
        with self.assertRaisesRegex(g.InstallCheckError, "EXIT"):
            self.parse([], rc=g.FINDINGS_EXIT)

    def test_runtime_failure(self):
        with self.assertRaisesRegex(g.InstallCheckError, "EXECUTION"):
            self.parse([], rc=1)

    def test_unredacted_report(self):
        with self.assertRaisesRegex(g.InstallCheckError, "FINDING"):
            self.parse([{"RuleID": "aws-access-token", "Secret": "raw"}], g.FINDINGS_EXIT)

    def test_invalid_rule(self):
        with self.assertRaisesRegex(g.InstallCheckError, "FINDING"):
            self.parse([{"RuleID": "unexpected/raw", "Secret": "REDACTED"}], g.FINDINGS_EXIT)

    def test_malformed_report(self):
        with self.assertRaisesRegex(g.InstallCheckError, "REPORT"):
            self.parse({"unexpected": []})


if __name__ == "__main__":
    unittest.main()
