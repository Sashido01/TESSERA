"""T09.05: strict publication metadata, Git remote identity and evidence manifest."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import release_publication, release_certificate, release_report, release_ci

REPOSITORY = "Sashido01/TESSERA"
TAG = "v0.0.11"


def release_metadata():
    return {
        "id": 321,
        "tag_name": TAG,
        "name": "TESSERA v0.0.11",
        "draft": False,
        "prerelease": False,
        "published_at": "2026-11-23T21:59:00Z",
        "html_url": f"https://github.com/{REPOSITORY}/releases/tag/{TAG}",
        "target_commitish": "main",  # This field must not be used as commit evidence.
        "assets": [],
    }


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.data = release_metadata()

    def check(self):
        return release_publication.validate_release(self.data, repository=REPOSITORY, tag=TAG)

    def assert_problem(self, code):
        result = self.check()
        self.assertEqual(result["publication_status"], "BLOCKED")
        self.assertIn(code, result["problems"])

    def test_published_source_release_without_assets(self):
        result = self.check()
        self.assertEqual(result["publication_status"], "SOURCE_RELEASE_PUBLISHED")
        self.assertEqual(result["release_readiness"], "NOT_VERIFIED")
        self.assertEqual(result["asset_content_verification"], "NOT_PERFORMED")

    def test_wrong_tag_rejected(self):
        self.data["tag_name"] = "v0.0.99"
        self.assert_problem("PUBLICATION_TAG_MISMATCH")

    def test_draft_rejected(self):
        self.data["draft"] = True
        self.assert_problem("PUBLICATION_DRAFT_OR_UNKNOWN")

    def test_missing_draft_rejected(self):
        del self.data["draft"]
        self.assert_problem("PUBLICATION_DRAFT_OR_UNKNOWN")

    def test_prerelease_not_stable_publication(self):
        self.data["prerelease"] = True
        self.assert_problem("PUBLICATION_IS_PRERELEASE")

    def test_missing_prerelease_rejected(self):
        del self.data["prerelease"]
        self.assert_problem("PUBLICATION_PRERELEASE_UNKNOWN")

    def test_bad_release_id_rejected(self):
        self.data["id"] = True
        self.assert_problem("PUBLICATION_ID_INVALID")

    def test_missing_published_at_rejected(self):
        self.data["published_at"] = None
        self.assert_problem("PUBLICATION_DATE_INVALID")

    def test_invalid_published_at_rejected(self):
        self.data["published_at"] = "not-a-time"
        self.assert_problem("PUBLICATION_DATE_INVALID")

    def test_alternate_domain_rejected(self):
        self.data["html_url"] = "https://example.com/Sashido01/TESSERA/releases/tag/v0.0.11"
        self.assert_problem("PUBLICATION_URL_MISMATCH")

    def test_wrong_release_page_rejected(self):
        self.data["html_url"] = "https://github.com/Sashido01/TESSERA/releases/tag/v0.0.10"
        self.assert_problem("PUBLICATION_URL_MISMATCH")

    def test_no_assets_array_rejected(self):
        self.data["assets"] = None
        self.assert_problem("PUBLICATION_ASSETS_INVALID")

    def test_uploaded_asset_digest_is_only_reported(self):
        self.data["assets"] = [
            {"name": "source.zip", "state": "uploaded", "size": 123, "digest": "sha256:" + "a" * 64}
        ]
        result = self.check()
        self.assertEqual(result["publication_status"], "SOURCE_RELEASE_PUBLISHED")
        self.assertEqual(result["asset_content_verification"], "NOT_PERFORMED")
        self.assertEqual(result["asset_metadata"][0]["reported_digest"], "sha256:" + "a" * 64)

    def test_invalid_asset_digest_rejected(self):
        self.data["assets"] = [{"name": "source.zip", "state": "uploaded", "size": 1, "digest": "sha256:wrong"}]
        self.assert_problem("PUBLICATION_ASSET_DIGEST_INVALID")

    def test_missing_asset_upload_rejected(self):
        self.data["assets"] = [{"name": "source.zip", "state": "starter", "size": 1}]
        self.assert_problem("PUBLICATION_ASSET_NOT_READY")

    def test_duplicate_asset_rejected(self):
        self.data["assets"] = [
            {"name": "a.zip", "state": "uploaded", "size": 10},
            {"name": "a.zip", "state": "uploaded", "size": 10},
        ]
        self.assert_problem("PUBLICATION_ASSET_NAME_INVALID")

    def test_invalid_repository_rejected(self):
        with self.assertRaises(release_publication.PublicationError):
            release_publication.valid_repository("--owner/project")

    def test_invalid_tag_rejected(self):
        for tag in ("v1.02.3", "--bad", "v0.1", "a/../../v0.1.0"):
            with self.subTest(tag=tag), self.assertRaises(release_publication.PublicationError):
                release_publication.valid_tag(tag)

    def test_namespaced_tag_allowed(self):
        release_publication.valid_tag("microversion-release/v0.0.11")

    def test_explicit_github_query_and_endpoint(self):
        urls = []
        def get(url):
            urls.append(url)
            return self.data
        result = release_publication.verify_github_publication(REPOSITORY, TAG, request_json=get)
        self.assertEqual(result["publication_status"], "SOURCE_RELEASE_PUBLISHED")
        self.assertEqual(urls, [
            f"https://api.github.com/repos/{REPOSITORY}/releases/tags/{TAG}"
        ])

    def test_default_transport_preserves_release_queries(self):
        for tag, endpoint_tag in ((TAG, TAG),
                                  ("microversion-release/" + TAG,
                                   "microversion-release%2F" + TAG)):
            with self.subTest(tag=tag), mock.patch.object(
                    release_ci.urllib.request, "build_opener") as builder:
                endpoint = f"https://api.github.com/repos/{REPOSITORY}/releases/tags/{endpoint_tag}"
                response = builder.return_value.open.return_value.__enter__.return_value
                response.geturl.return_value = endpoint
                data = release_metadata()
                data.update({"tag_name": tag,
                             "html_url": f"https://github.com/{REPOSITORY}/releases/tag/{tag}"})
                response.read.return_value = json.dumps(data).encode("utf-8")
                result = release_publication.verify_github_publication(REPOSITORY, tag)
                self.assertEqual(result["publication_status"], "SOURCE_RELEASE_PUBLISHED")
                self.assertEqual(builder.return_value.open.call_args.args[0].full_url, endpoint)
                self.assertIsInstance(builder.call_args.args[0], release_ci.NoAPIRedirect)

    def test_default_transport_rejects_release_redirect(self):
        with mock.patch.object(release_ci.urllib.request, "build_opener") as builder:
            response = builder.return_value.open.return_value.__enter__.return_value
            response.geturl.return_value = "https://example.invalid/other"
            result = release_publication.verify_github_publication(REPOSITORY, TAG)
            self.assertEqual(result["publication_status"], "BLOCKED")
            response.read.assert_not_called()

    def test_unavailable_api_is_blocked_not_published(self):
        def unavailable(url):
            raise release_publication.CIEvidenceError("CI_API_UNAVAILABLE")
        result = release_publication.verify_github_publication(REPOSITORY, TAG, request_json=unavailable)
        self.assertEqual(result["publication_status"], "BLOCKED")
        self.assertIn("PUBLICATION_QUERY_FAILED_OR_MISSING", result["problems"])


class RemoteIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], text=True, capture_output=True, check=True)

    def test_matching_https_origin(self):
        self.git("remote", "add", "origin", "https://github.com/Sashido01/TESSERA.git")
        self.assertEqual(release_publication.verify_github_remote_identity(self.root, "origin", REPOSITORY), "PASS")

    def test_matching_ssh_origin(self):
        self.git("remote", "add", "origin", "git@github.com:Sashido01/TESSERA.git")
        self.assertEqual(release_publication.verify_github_remote_identity(self.root, "origin", REPOSITORY), "PASS")

    def test_mismatching_repository_rejected(self):
        self.git("remote", "add", "origin", "https://github.com/other/repo.git")
        self.assertEqual(release_publication.verify_github_remote_identity(self.root, "origin", REPOSITORY), "BLOCKED")

    def test_lookalike_host_rejected(self):
        self.git("remote", "add", "origin", "https://github.com.evil.example/Sashido01/TESSERA.git")
        self.assertEqual(release_publication.verify_github_remote_identity(self.root, "origin", REPOSITORY), "BLOCKED")

    def test_local_remote_rejected_for_github_publication(self):
        self.git("remote", "add", "origin", str(self.root))
        self.assertEqual(release_publication.verify_github_remote_identity(self.root, "origin", REPOSITORY), "BLOCKED")

    def test_malformed_port_rejected(self):
        self.git("remote", "add", "origin", "https://github.com:invalid/Sashido01/TESSERA.git")
        self.assertEqual(release_publication.verify_github_remote_identity(self.root, "origin", REPOSITORY), "BLOCKED")

    def test_multiple_urls_rejected(self):
        self.git("remote", "add", "origin", "https://github.com/Sashido01/TESSERA.git")
        self.git("config", "--add", "remote.origin.url", "https://github.com/other/repo.git")
        self.assertEqual(release_publication.verify_github_remote_identity(self.root, "origin", REPOSITORY), "BLOCKED")

    def test_missing_remote_rejected(self):
        self.assertEqual(release_publication.verify_github_remote_identity(self.root, "origin", REPOSITORY), "BLOCKED")


class CertificateTests(unittest.TestCase):
    def base_report(self):
        return {
            "requested_version": "0.0.11",
            "requested_tag": TAG,
            "target_commit_sha": "a" * 40,
            "local_tag_object_sha": "b" * 40,
            "local_tag_status": "PASS",
            "remote_tag_status": "PASS",
            "ci_status": "PASS",
            "ci_run_id": 45263207157,
            "ci_run_attempt": 1,
            "publication_status": "SOURCE_RELEASE_PUBLISHED",
            "publication_release_id": 123,
            "publication_url": f"https://github.com/{REPOSITORY}/releases/tag/{TAG}",
            "evidence_status": "PASS",
            "problems": [],
        }

    def test_source_release_certificate_when_all_evidence_exists(self):
        cert = release_certificate.make_certificate(self.base_report())
        self.assertEqual(cert["publication_evidence_status"], "SOURCE_RELEASE_PUBLISHED")
        self.assertEqual(cert["application_release_readiness"], "NOT_VERIFIED")
        self.assertFalse(cert["signed"])

    def test_no_release_is_not_released(self):
        report = self.base_report()
        report["publication_status"] = "NOT_CHECKED"
        cert = release_certificate.make_certificate(report)
        self.assertEqual(cert["publication_evidence_status"], "TAG_AND_CI_VERIFIED")

    def test_only_metadata_is_incomplete(self):
        report = self.base_report()
        report["ci_status"] = "NOT_CHECKED"
        self.assertEqual(release_certificate.make_certificate(report)["publication_evidence_status"], "INCOMPLETE")

    def test_remote_missing_is_incomplete(self):
        report = self.base_report()
        report["remote_tag_status"] = "NOT_CHECKED"
        self.assertEqual(release_certificate.make_certificate(report)["publication_evidence_status"], "INCOMPLETE")

    def test_failures_block(self):
        report = self.base_report()
        report["problems"] = ["PUBLICATION_REMOTE_IDENTITY_MISMATCH"]
        self.assertEqual(release_certificate.make_certificate(report)["publication_evidence_status"], "BLOCKED")

    def test_digest_deterministic_and_not_signature(self):
        a = release_certificate.make_certificate(self.base_report())
        b = release_certificate.make_certificate(self.base_report())
        self.assertEqual(a, b)
        evidence = {key: value for key, value in a.items() if key != "evidence_sha256"}
        digest = hashlib.sha256(
            json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.assertEqual(a["evidence_sha256"], "sha256:" + digest)
        self.assertFalse(a["signed"])


class PublicationReportIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.invalid")
        self.git("remote", "add", "origin", "https://github.com/Sashido01/TESSERA.git")
        (self.root / "VERSION").write_text("0.0.11\n", encoding="utf-8")
        (self.root / "CHANGELOG.md").write_text("## 0.0.11 — Тест\n", encoding="utf-8")
        (self.root / "CHANGELOG.en.md").write_text("## 0.0.11 — Test\n", encoding="utf-8")
        config = {
            "schema_version": 1, "version_file": "VERSION",
            "release_notes": ["CHANGELOG.md", "CHANGELOG.en.md"],
            "build": {"not_applicable_reason": "Test-only source repository has no build artifact."},
            "tests": [{"id": "test", "argv": [sys.executable, "-c", "pass"], "cwd": ".", "timeout_seconds": 10}],
        }
        (self.root / "release-checks.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        self.git("add", ".")
        self.git("commit", "-qm", "Создана проверочная версия")
        self.sha = self.git("rev-parse", "HEAD")
        self.git("tag", "-a", TAG, "-m", "Релиз проверки публикации")

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            text=True, capture_output=True, check=True
        ).stdout.strip()

    def test_publication_not_queried_by_default(self):
        with mock.patch.object(release_report, "verify_github_publication", side_effect=AssertionError):
            report = release_report.build_report(self.root, "0.0.11")
        self.assertEqual(report["publication_status"], "NOT_CHECKED")
        self.assertEqual(report["release_readiness"], "NOT_VERIFIED")

    def test_source_release_metadata_without_remote_ci_is_not_final(self):
        payload = release_publication.validate_release(release_metadata(), repository=REPOSITORY, tag=TAG)
        with mock.patch.object(release_report, "verify_github_publication", return_value=payload):
            report = release_report.build_report(
                self.root, "0.0.11", verify_publication=True, github_repo=REPOSITORY
            )
        self.assertEqual(report["publication_status"], "SOURCE_RELEASE_PUBLISHED")
        self.assertEqual(report["stage"], "SOURCE_RELEASE_METADATA_VERIFIED")
        self.assertEqual(release_certificate.make_certificate(report)["publication_evidence_status"], "INCOMPLETE")
        self.assertEqual(report["release_readiness"], "NOT_VERIFIED")

    def test_failed_publication_query_blocks(self):
        with mock.patch.object(release_report, "verify_github_publication", return_value={
            "publication_status": "BLOCKED", "problems": ["PUBLICATION_QUERY_FAILED_OR_MISSING"],
        }):
            report = release_report.build_report(
                self.root, "0.0.11", verify_publication=True, github_repo=REPOSITORY
            )
        self.assertEqual(report["stage"], "BLOCKED")
        self.assertIn("PUBLICATION_QUERY_FAILED_OR_MISSING", report["problems"])

    def test_unrelated_github_origin_blocks_and_skips_network(self):
        self.git("remote", "set-url", "origin", "https://github.com/other/repo.git")
        with mock.patch.object(release_report, "verify_github_publication", side_effect=AssertionError):
            report = release_report.build_report(
                self.root, "0.0.11", verify_publication=True, github_repo=REPOSITORY
            )
        self.assertEqual(report["stage"], "BLOCKED")
        self.assertIn("PUBLICATION_REMOTE_IDENTITY_MISMATCH", report["problems"])

    def test_full_evidence_source_release_metadata(self):
        payload = release_publication.validate_release(release_metadata(), repository=REPOSITORY, tag=TAG)
        with mock.patch.object(release_report, "verify_github_publication", return_value=payload), \
             mock.patch.object(release_report, "verify_github_ci", return_value={
                 "ci_status": "PASS", "problems": [], "observed_commit_sha": self.sha, "run_attempt": 1
             }), \
             mock.patch.object(release_report, "verify_remote_tag", return_value={
                 "remote_tag_status": "PASS", "remote_publication": "TAG_REF_VERIFIED",
                 "expected_commit_sha": self.sha,
                 "local_tag_object_sha": self.git("rev-parse", "refs/tags/" + TAG),
                 "remote_tag_object_sha": self.git("rev-parse", "refs/tags/" + TAG),
                 "problems": []
             }):
            report = release_report.build_report(
                self.root, "0.0.11",
                verify_publication=True, verify_ci=True, verify_remote=True,
                github_repo=REPOSITORY, run_id=123
            )
        self.assertEqual(report["stage"], "SOURCE_RELEASE_METADATA_AND_CI_VERIFIED")
        self.assertEqual(report["evidence_status"], "PASS")
        cert = release_certificate.make_certificate(report)
        self.assertEqual(cert["publication_evidence_status"], "SOURCE_RELEASE_PUBLISHED")
        self.assertEqual(cert["application_release_readiness"], "NOT_VERIFIED")

    def test_certificate_json_serializable_without_local_paths(self):
        report = release_report.build_report(self.root, "0.0.11")
        cert = release_certificate.make_certificate(report)
        encoded = json.dumps(cert, ensure_ascii=False)
        self.assertNotIn(str(self.root), encoded)
        self.assertIn("evidence_sha256", cert)


if __name__ == "__main__":
    unittest.main()
