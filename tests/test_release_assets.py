"""T09.06: stream actual asset bytes; never equate digest metadata with provenance."""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import release_assets, release_certificate, release_publication, release_report

REPO = "Sashido01/TESSERA"
TAG = "v0.0.12"
BYTES = b"tessera byte integrity test\n"
DIGEST = "sha256:" + hashlib.sha256(BYTES).hexdigest()
URL = f"https://github.com/{REPO}/releases/download/{TAG}/package.bin"


def asset(*, name="package.bin", content=BYTES, digest=DIGEST, url=URL):
    return {"name": name, "size": len(content), "reported_digest": digest, "browser_download_url": url}


class AssetsTests(unittest.TestCase):
    def stream(self, content=BYTES):
        return lambda _url: io.BytesIO(content)

    def verify(self, info=None, *, data=BYTES, cap=1024):
        return release_assets.verify_asset_stream(
            REPO, TAG, info or asset(), maximum_bytes=cap, stream_factory=self.stream(data)
        )

    def test_bytes_and_sha256_pass(self):
        result = self.verify()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["bytes_verified"], len(BYTES))
        self.assertEqual(result["sha256"], DIGEST)
        self.assertEqual(result["sha256_source"], "github_release_metadata")

    def test_corrupted_bytes_rejected(self):
        corrupted = b"X" + BYTES[1:]
        with self.assertRaisesRegex(release_assets.AssetVerificationError, "ASSET_SHA256_MISMATCH"):
            self.verify(data=corrupted)

    def test_truncated_download_rejected(self):
        with self.assertRaisesRegex(release_assets.AssetVerificationError, "ASSET_SIZE_MISMATCH"):
            self.verify(data=BYTES[:-1])

    def test_long_download_rejected(self):
        with self.assertRaisesRegex(release_assets.AssetVerificationError, "ASSET_DOWNLOAD_TOO_LARGE"):
            self.verify(data=BYTES + b"!")

    def test_missing_digest_rejected_before_download(self):
        with self.assertRaisesRegex(release_assets.AssetVerificationError, "ASSET_DIGEST_REQUIRED"):
            self.verify(info=asset(digest=None))

    def test_wrong_digest_format_rejected(self):
        with self.assertRaisesRegex(release_assets.AssetVerificationError, "ASSET_DIGEST_REQUIRED"):
            self.verify(info=asset(digest="sha256:not-a-hash"))

    def test_declared_size_limit_rejected(self):
        with self.assertRaisesRegex(release_assets.AssetVerificationError, "ASSET_SIZE_INVALID_OR_EXCEEDS_LIMIT"):
            self.verify(cap=3)

    def test_boolean_maximum_rejected(self):
        with self.assertRaisesRegex(release_assets.AssetVerificationError, "ASSET_LIMIT_INVALID"):
            release_assets.verify_asset_stream(REPO, TAG, asset(), maximum_bytes=True)

    def test_http_not_allowed(self):
        with self.assertRaises(release_assets.AssetVerificationError):
            self.verify(info=asset(url=URL.replace("https://", "http://")))

    def test_lookalike_host_not_allowed(self):
        with self.assertRaises(release_assets.AssetVerificationError):
            self.verify(info=asset(url=URL.replace("github.com", "github.com.evil.example")))

    def test_embedded_credentials_not_allowed(self):
        with self.assertRaises(release_assets.AssetVerificationError):
            self.verify(info=asset(url=URL.replace("github.com/", "user:pw@github.com/")))

    def test_wrong_repo_url_rejected(self):
        with self.assertRaisesRegex(release_assets.AssetVerificationError, "ASSET_URL_MISMATCH"):
            self.verify(info=asset(url=URL.replace(REPO, "other/repository")))

    def test_wrong_tag_url_rejected(self):
        with self.assertRaisesRegex(release_assets.AssetVerificationError, "ASSET_URL_MISMATCH"):
            self.verify(info=asset(url=URL.replace(TAG, "v0.0.9")))

    def test_wrong_asset_name_url_rejected(self):
        with self.assertRaisesRegex(release_assets.AssetVerificationError, "ASSET_URL_MISMATCH"):
            self.verify(info=asset(url=URL.replace("package.bin", "other.bin")))

    def test_query_url_rejected(self):
        with self.assertRaises(release_assets.AssetVerificationError):
            self.verify(info=asset(url=URL + "?redirect=1"))

    def test_malicious_asset_name_rejected(self):
        with self.assertRaises(release_assets.AssetVerificationError):
            self.verify(info=asset(name="../secret"))

    def test_untrusted_redirect_rejected(self):
        handler = release_assets.RestrictRedirects()
        with self.assertRaises(release_assets.AssetVerificationError):
            handler.redirect_request(None, None, 302, "Moved", {}, "https://evil.example/data")

    def test_trusted_cdn_redirect_url_allowed(self):
        release_assets.check_url("https://release-assets.githubusercontent.com/some/object?token=test", initial=False)

    def test_no_assets_is_explicit_not_applicable(self):
        result = release_assets.verify_release_assets(REPO, TAG, [], stream_factory=self.stream())
        self.assertEqual(result["asset_content_verification"], "NO_RELEASE_ASSETS")
        self.assertEqual(result["verified_assets"], [])

    def test_group_valid(self):
        result = release_assets.verify_release_assets(
            REPO, TAG, [asset()], maximum_bytes=1024, stream_factory=self.stream()
        )
        self.assertEqual(result["asset_content_verification"], "PASS")
        self.assertEqual(len(result["verified_assets"]), 1)

    def test_group_fails_on_first_bad_digest(self):
        result = release_assets.verify_release_assets(
            REPO, TAG, [asset(digest="sha256:" + "0" * 64), asset(name="other.bin", url=URL.replace("package.bin", "other.bin"))],
            maximum_bytes=1024, stream_factory=self.stream()
        )
        self.assertEqual(result["asset_content_verification"], "BLOCKED")
        self.assertEqual(len(result["verified_assets"]), 0)
        self.assertIn("ASSET_SHA256_MISMATCH", result["problems"])

    def test_group_rejects_duplicate_name(self):
        result = release_assets.verify_release_assets(
            REPO, TAG, [asset(), asset()], maximum_bytes=1024, stream_factory=self.stream()
        )
        self.assertEqual(result["asset_content_verification"], "BLOCKED")
        self.assertIn("ASSET_DUPLICATE_NAME", result["problems"])

    def test_group_rejects_unhashable_name_gracefully(self):
        result = release_assets.verify_release_assets(
            REPO, TAG, [{"name": ["bad"]}], maximum_bytes=1024, stream_factory=self.stream()
        )
        self.assertEqual(result["asset_content_verification"], "BLOCKED")

    def test_group_rejects_too_many_assets(self):
        result = release_assets.verify_release_assets(REPO, TAG, [asset()] * 21)
        self.assertIn("ASSET_LIST_INVALID", result["problems"])

    def test_unexpected_stream_error_blocks(self):
        class Bad:
            def read(self, n):
                raise OSError("connection lost")
            def close(self):
                pass
        with self.assertRaisesRegex(release_assets.AssetVerificationError, "ASSET_DOWNLOAD_FAILED"):
            release_assets.verify_asset_stream(
                REPO, TAG, asset(), maximum_bytes=1024, stream_factory=lambda _: Bad()
            )

    def test_download_is_not_invoked_if_digest_missing(self):
        def fail(_):
            raise AssertionError("download unexpectedly invoked")
        with self.assertRaises(release_assets.AssetVerificationError):
            release_assets.verify_asset_stream(
                REPO, TAG, asset(digest=None), maximum_bytes=1024, stream_factory=fail
            )

    def test_metadata_passes_through_browser_download_url(self):
        data = {
            "id": 10, "tag_name": TAG, "draft": False, "prerelease": False,
            "published_at": "2026-11-24T12:00:00Z",
            "html_url": f"https://github.com/{REPO}/releases/tag/{TAG}",
            "assets": [{
                "name": "package.bin", "size": len(BYTES),
                "state": "uploaded", "digest": DIGEST,
                "browser_download_url": URL,
            }],
        }
        result = release_publication.validate_release(data, repository=REPO, tag=TAG)
        self.assertEqual(result["asset_metadata"][0]["browser_download_url"], URL)


class ReportAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = pathlib.Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.invalid")
        self.git("remote", "add", "origin", f"https://github.com/{REPO}.git")
        (self.repo / "VERSION").write_text("0.0.12\n", encoding="utf-8")
        (self.repo / "CHANGELOG.md").write_text("## 0.0.12 — Испытание\n", encoding="utf-8")
        (self.repo / "CHANGELOG.en.md").write_text("## 0.0.12 — Test\n", encoding="utf-8")
        plan = {
            "schema_version": 1, "version_file": "VERSION",
            "release_notes": ["CHANGELOG.md", "CHANGELOG.en.md"],
            "build": {"not_applicable_reason": "No binary build artifact in this fixture."},
            "tests": [{"id": "test", "argv": [sys.executable, "-c", "pass"],
                       "cwd": ".", "timeout_seconds": 10}]
        }
        (self.repo / "release-checks.json").write_text(json.dumps(plan), encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "Сохранена тестовая версия")
        self.git("tag", "-a", TAG, "-m", "Релиз для проверки байтов")

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), *args], capture_output=True,
            text=True, check=True
        ).stdout.strip()

    def publication(self):
        return {
            "publication_status": "SOURCE_RELEASE_PUBLISHED",
            "release_id": 101,
            "release_url": f"https://github.com/{REPO}/releases/tag/{TAG}",
            "asset_metadata": [asset()],
            "problems": [],
        }

    def test_verify_assets_requires_explicit_publication(self):
        with self.assertRaisesRegex(release_report.InspectionError, "ASSETS_REQUIRE"):
            release_report.build_report(self.repo, "0.0.12", verify_assets=True)

    def test_default_report_no_download(self):
        with mock.patch.object(release_report, "verify_release_assets", side_effect=AssertionError):
            report = release_report.build_report(self.repo, "0.0.12")
        self.assertEqual(report["publication_asset_content_verification"], "NOT_PERFORMED")

    def test_explicit_bytes_proof(self):
        with mock.patch.object(release_report, "verify_github_publication", return_value=self.publication()), \
             mock.patch.object(release_report, "verify_release_assets", return_value={
                 "asset_content_verification": "PASS",
                 "verified_assets": [{"name": "package.bin", "sha256": DIGEST,
                                      "bytes_verified": len(BYTES), "status": "PASS"}],
                 "problems": [],
             }):
            result = release_report.build_report(
                self.repo, "0.0.12", verify_publication=True, verify_assets=True,
                github_repo=REPO,
            )
        self.assertEqual(result["publication_asset_content_verification"], "PASS")
        self.assertEqual(result["stage"], "SOURCE_RELEASE_ASSETS_VERIFIED")
        self.assertEqual(result["release_readiness"], "NOT_VERIFIED")
        self.assertEqual(result["artifact_provenance"], "NOT_VERIFIED")

    def test_bad_bytes_block_report(self):
        with mock.patch.object(release_report, "verify_github_publication", return_value=self.publication()), \
             mock.patch.object(release_report, "verify_release_assets", return_value={
                 "asset_content_verification": "BLOCKED",
                 "verified_assets": [],
                 "problems": ["ASSET_SHA256_MISMATCH"],
             }):
            report = release_report.build_report(
                self.repo, "0.0.12", verify_publication=True, verify_assets=True,
                github_repo=REPO,
            )
        self.assertEqual(report["evidence_status"], "BLOCKED")
        self.assertIn("ASSET_SHA256_MISMATCH", report["problems"])

    def test_certificate_does_not_claim_artifact_provenance(self):
        original = {
            "requested_version": "0.0.12",
            "requested_tag": TAG,
            "target_commit_sha": "a" * 40,
            "local_tag_object_sha": "b" * 40,
            "local_tag_status": "PASS",
            "remote_tag_status": "PASS",
            "ci_status": "PASS",
            "publication_status": "SOURCE_RELEASE_PUBLISHED",
            "publication_asset_content_verification": "PASS",
            "verified_assets": [{"name": "package.bin", "sha256": DIGEST}],
            "evidence_status": "PASS",
            "problems": [],
        }
        manifest = release_certificate.make_certificate(original)
        self.assertEqual(manifest["publication_evidence_status"], "SOURCE_ASSETS_BYTES_VERIFIED")
        self.assertEqual(manifest["checks"]["asset_content_verification"], "PASS")
        self.assertEqual(manifest["checks"]["artifact_provenance"], "NOT_VERIFIED")
        self.assertFalse(manifest["signed"])
        self.assertEqual(manifest["application_release_readiness"], "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
