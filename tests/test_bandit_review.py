"""Offline report-contract tests; actual Bandit runs separately in CI."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_bandit_review as b


class BanditReviewTests(unittest.TestCase):
    def report(self):
        return {"errors": [], "metrics": {"fixture.py": {"loc": 1},
                "_totals": {"loc": 1}}, "results": []}

    def finding(self):
        return {"filename": "fixture.py", "test_id": "B307",
                "issue_severity": "MEDIUM", "issue_confidence": "HIGH",
                "code": "synthetic raw source", "issue_text": "private raw message"}

    def test_clean(self):
        self.assertEqual(b.summarize(self.report(), 0, {"fixture.py"})["verdict"],
                         "NO_FINDINGS")

    def test_findings_sanitized(self):
        data = self.report()
        data["results"] = [self.finding()]
        result = b.summarize(data, 1, {"fixture.py"})
        self.assertEqual(result["findings"], 1)
        self.assertEqual(result["by_rule"][0]["rule"], "B307")
        self.assertNotIn("raw", str(result))

    def test_incomplete_scan(self):
        data = self.report()
        data["errors"] = [{"reason": "syntax error"}]
        with self.assertRaisesRegex(b.InstallCheckError, "INCOMPLETE"):
            b.summarize(data, 0, {"fixture.py"})

    def test_missing_file(self):
        with self.assertRaisesRegex(b.InstallCheckError, "COVERAGE"):
            b.summarize(self.report(), 0, {"fixture.py", "other.py"})

    def test_exit_mismatch(self):
        with self.assertRaisesRegex(b.InstallCheckError, "EXIT"):
            b.summarize(self.report(), 1, {"fixture.py"})

    def test_unknown_rule(self):
        data = self.report()
        row = self.finding()
        row["test_id"] = "unknown raw string"
        data["results"] = [row]
        with self.assertRaisesRegex(b.InstallCheckError, "FINDING"):
            b.summarize(data, 1, {"fixture.py"})

    def test_wrong_file(self):
        data = self.report()
        row = self.finding()
        row["filename"] = "other.py"
        data["results"] = [row]
        with self.assertRaisesRegex(b.InstallCheckError, "FINDING"):
            b.summarize(data, 1, {"fixture.py"})

    def test_scope(self):
        self.assertEqual(b.scope("skills/fixture/tests/test_example.py"), "tests")
        self.assertEqual(b.scope("tests/test_example.py"), "tests")
        self.assertEqual(b.scope("core/example.py"), "runtime")


if __name__ == "__main__":
    unittest.main()
