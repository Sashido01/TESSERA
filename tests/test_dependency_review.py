"""Offline contract tests for exact dependency inventory and OSV responses."""
import base64
import hashlib
import importlib.metadata
import pathlib
import tempfile
from unittest import mock
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

    def license_fixture(self, root, raw):
        entry = importlib.metadata.PackagePath("tiktoken-0.13.0.dist-info/licenses/LICENSE")
        digest = hashlib.sha256(raw)
        encoded = base64.urlsafe_b64encode(digest.digest()).decode("ascii").rstrip("=")
        entry.hash = importlib.metadata.FileHash("sha256=" + encoded)
        entry.size = len(raw)
        path = root.joinpath(*entry.parts)
        path.parent.mkdir(parents=True)
        path.write_bytes(raw)
        dist = mock.Mock()
        dist.locate_file.return_value = root
        return dist, entry, path, digest.hexdigest()

    def test_installed_license_requires_record_and_upstream_match(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder).resolve()
            dist, entry, path, digest = self.license_fixture(root, b"synthetic license")
            with mock.patch.dict(d.LICENSE_PINS, {("tiktoken", "0.13.0"): ("LICENSE", digest)}):
                result = d.installed_license_evidence(dist, "tiktoken", "0.13.0", [entry])
                self.assertEqual(result["status"], "UPSTREAM_TEXT_MATCH")
                self.assertEqual(result["record_integrity"], "MATCH")
                self.assertNotIn("synthetic license", str(result))
                path.write_bytes(b"changed")
                result = d.installed_license_evidence(dist, "tiktoken", "0.13.0", [entry])
                self.assertEqual(result["status"], "RECORD_MISMATCH_OR_UNVERIFIED")

    def test_installed_license_differs_with_valid_record(self):
        with tempfile.TemporaryDirectory() as folder:
            dist, entry, _, _ = self.license_fixture(pathlib.Path(folder).resolve(), b"fixture")
            result = d.installed_license_evidence(dist, "tiktoken", "0.13.0", [entry])
            self.assertEqual(result["status"], "UPSTREAM_TEXT_DIFFERS")
            self.assertEqual(result["record_integrity"], "MATCH")

    def test_installed_license_rejects_unknown_and_ambiguous_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            dist, entry, _, _ = self.license_fixture(pathlib.Path(folder).resolve(), b"fixture")
            for entries in ([entry, entry], [importlib.metadata.PackagePath("../LICENSE")], []):
                with self.subTest(entries=entries):
                    result = d.installed_license_evidence(dist, "tiktoken", "0.13.0", entries)
                    self.assertEqual(result["status"], "RECORD_MISSING_OR_AMBIGUOUS")
            self.assertIsNone(d.installed_license_evidence(dist, "tiktoken", "0.13.1", [entry]))

    def test_installed_license_refuses_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder).resolve()
            dist, entry, path, _ = self.license_fixture(root, b"fixture")
            external = root / "outside"
            external.write_bytes(b"fixture")
            path.unlink()
            try:
                path.symlink_to(external)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation unavailable")
            result = d.installed_license_evidence(dist, "tiktoken", "0.13.0", [entry])
            self.assertEqual(result["status"], "REDIRECTED_PATH")


if __name__ == "__main__":
    unittest.main()
