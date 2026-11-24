"""Offline contract tests for exact dependency inventory and OSV responses."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_dependency_review as d


class DependencyReviewTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(d.canonical("PyYAML"), "pyyaml")
        self.assertEqual(d.canonical("some_pkg"), "some-pkg")

    def test_locked_platform(self):
        h = "a" * 64
        text = f"click==8.3.1 --hash=sha256:{h}\ncolorama==0.4.6; sys_platform == 'win32' --hash=sha256:{h}"
        self.assertEqual(d.pinned_lock(text, "linux"), {"click": "8.3.1"})

    def test_unpinned_rejected(self):
        with self.assertRaisesRegex(d.InstallCheckError, "UNSUPPORTED"):
            d.pinned_lock("click>=8", "linux")

    def test_empty_results(self):
        self.assertEqual(d.query([{"commit": "a" * 40}], request=lambda _: {"results": [{}]}), [[]])

    def test_results_alignment(self):
        with self.assertRaisesRegex(d.InstallCheckError, "COVERAGE"):
            d.query([{"commit": "a" * 40}], request=lambda _: {"results": []})

    def test_invalid_id(self):
        with self.assertRaisesRegex(d.InstallCheckError, "ID"):
            d.query([{"commit": "a" * 40}], request=lambda _: {"results": [{"vulns": [{"id": "invalid/raw"}]}]})

    def test_pagination(self):
        def reply(queries):
            if "page_token" not in queries[0]:
                return {"results": [{"vulns": [{"id": "CVE-2020-0001"}], "next_page_token": "fixture"}]}
            return {"results": [{"vulns": [{"id": "GHSA-test-0000-0000"}]}]}
        self.assertEqual(d.query([{"commit": "a" * 40}], request=reply),
                         [["CVE-2020-0001", "GHSA-test-0000-0000"]])

    def test_pagination_loop_blocked(self):
        with self.assertRaisesRegex(d.InstallCheckError, "PAGINATION"):
            d.query([{"commit": "a" * 40}],
                    request=lambda _: {"results": [{"next_page_token": "fixture"}]})


if __name__ == "__main__":
    unittest.main()
