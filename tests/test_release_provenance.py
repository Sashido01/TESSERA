"""T09.07: explicit signed provenance verification and negative trust tests."""
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
from core import release_provenance as provenance
from core import release_certificate, release_report

REPO = "Sashido01/TESSERA"
TAG = "v0.0.13"
COMMIT = "a" * 40
WORKFLOW = REPO + "/.github/workflows/build.yml"
CONTENT = b"tessera-attestation-fixture\n"
DIGEST = "sha256:" + hashlib.sha256(CONTENT).hexdigest()


def metadata():
    return {"name": "package.bin", "size": len(CONTENT), "reported_digest": DIGEST}


def gh_payload(digest=DIGEST, predicate=provenance.PREDICATE, certificate="signed certificate"):
    return json.dumps([{
        "verificationResult": {
            "signature": {"certificate": certificate},
            "statement": {
                "predicateType": predicate,
                "subject": [{"name": "package.bin", "digest": {"sha256": digest.removeprefix("sha256:")}}],
                "predicate": {"buildDefinition": {"buildType": "untrusted-for-policy"}},
            },
        }
    }])


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = pathlib.Path(self.temp.name) / "package.bin"
        self.path.write_bytes(CONTENT)
        self.commands = []
        self.version_commands = []

    def good_runner(self, argv, **kwargs):
        self.commands.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, gh_payload(), "")

    def verify(self, runner=None, version_text="gh version 2.105.0 (2026-11-18)",
               version_rc=0, version_error=None, **kwargs):
        actual_runner = runner or self.good_runner

        def verified_runner(argv, **call_kwargs):
            if argv == ["gh", "--version"]:
                self.version_commands.append((argv, call_kwargs))
                if version_error is not None:
                    raise version_error
                return subprocess.CompletedProcess(argv, version_rc, version_text, "secret-error")
            return actual_runner(argv, **call_kwargs)

        params = {
            "repository": REPO,
            "tag": TAG,
            "source_commit": COMMIT,
            "signer_workflow": WORKFLOW,
            "artifact_file": self.path,
            "asset_metadata": metadata(),
            "max_bytes": 1024,
            "runner": verified_runner,
        }
        params.update(kwargs)
        return provenance.verify_release_provenance(**params)

    def test_verified_attestation_links_subject_commit_tag_and_signer(self):
        result = self.verify()
        self.assertEqual(result["provenance_status"], "PASS")
        self.assertTrue(result["signed_attestation"])
        self.assertEqual(result["gh_version"], "2.105.0")
        self.assertEqual(self.version_commands[0][0], ["gh", "--version"])
        self.assertEqual(self.version_commands[0][1]["timeout"], 10)
        self.assertEqual(result["artifact_provenance"], "GITHUB_ATTESTATION_VERIFIED")
        self.assertEqual(result["asset_sha256"], DIGEST)
        self.assertEqual(result["application_release_readiness"], "NOT_VERIFIED")
        command = self.commands[0][0]
        self.assertEqual(command[:3], ["gh", "attestation", "verify"])
        self.assertIn("--source-digest", command)
        self.assertEqual(command[command.index("--source-digest") + 1], COMMIT)
        self.assertEqual(command[command.index("--source-ref") + 1], "refs/tags/" + TAG)
        self.assertEqual(command[command.index("--signer-workflow") + 1], WORKFLOW)
        self.assertIn("--deny-self-hosted-runners", command)
        self.assertFalse(self.commands[0][1]["check"])


    def test_exact_minimum_gh_version_is_allowed(self):
        result = self.verify(version_text="gh version 2.102.0 (2026-09-30)")
        self.assertEqual(result["provenance_status"], "PASS")
        self.assertEqual(result["gh_version"], "2.102.0")

    def test_old_gh_versions_fail_closed_before_attestation(self):
        for version in ("2.50.0", "2.101.0", "1.999.999"):
            with self.subTest(version=version):
                self.commands.clear()
                self.version_commands.clear()
                result = self.verify(version_text="gh version " + version)
                self.assertEqual(result["provenance_status"], "BLOCKED")
                self.assertIn("PROVENANCE_VERIFIER_VERSION_UNSAFE", result["problems"])
                self.assertFalse(result["signed_attestation"])
                self.assertFalse(self.commands)

    def test_unknown_gh_version_fails_closed(self):
        for banner in ("unexpected", "gh version 2.105.0-rc.1", "gh version 2.105",
                       "gh version 2.105.0 malicious", "gh version 2.105.0" + "x" * 5000):
            with self.subTest(banner=banner[:35]):
                self.commands.clear()
                result = self.verify(version_text=banner)
                self.assertIn("PROVENANCE_VERIFIER_VERSION_UNKNOWN", result["problems"])
                self.assertFalse(self.commands)

    def test_gh_version_command_error_fails_closed_and_hides_stderr(self):
        result = self.verify(version_rc=1)
        self.assertEqual(result["provenance_status"], "BLOCKED")
        self.assertIn("PROVENANCE_VERIFIER_VERSION_UNKNOWN", result["problems"])
        self.assertNotIn("secret-error", json.dumps(result))
        self.assertFalse(self.commands)

    def test_gh_version_command_unavailable_fails_closed(self):
        result = self.verify(version_error=FileNotFoundError("untrusted absolute path"))
        self.assertIn("PROVENANCE_VERIFIER_UNAVAILABLE", result["problems"])
        self.assertNotIn("untrusted absolute path", json.dumps(result))
        self.assertFalse(self.commands)

    def test_gh_version_probe_timeout_fails_closed(self):
        result = self.verify(version_error=subprocess.TimeoutExpired(["gh", "--version"], 10))
        self.assertIn("PROVENANCE_VERIFIER_TIMEOUT", result["problems"])
        self.assertFalse(self.commands)

    def test_missing_file_does_not_run_even_gh_version_probe(self):
        self.path.unlink()
        with self.assertRaisesRegex(provenance.ProvenanceError, "PROVENANCE_FILE_MISMATCH"):
            self.verify()
        self.assertFalse(self.version_commands)

    def test_gh_version_parser_is_strict(self):
        self.assertEqual(provenance.parse_gh_version("gh version 2.105.0 (2026-11-18)\\nref\\n".replace("\\n", "\n")),
                         (2, 105, 0))
        self.assertEqual(provenance.parse_gh_version("gh version 3.0.0"), (3, 0, 0))
        self.assertIsNone(provenance.parse_gh_version("fake gh version 2.105.0"))
        self.assertIsNone(provenance.parse_gh_version("gh version 2.102.0-dev"))
        self.assertIsNone(provenance.parse_gh_version("gh version " + "0" * 1000))

    def test_only_specific_workflow_allowed(self):
        with self.assertRaisesRegex(provenance.ProvenanceError, "PROVENANCE_SIGNER_MISMATCH"):
            self.verify(signer_workflow="other/repo/.github/workflows/build.yml")

    def test_non_workflow_signer_rejected(self):
        with self.assertRaisesRegex(provenance.ProvenanceError, "PROVENANCE_SIGNER_INVALID"):
            self.verify(signer_workflow=REPO + "/.github/workflows/../../bad.yml")

    def test_wrong_source_commit_rejected(self):
        with self.assertRaisesRegex(provenance.ProvenanceError, "PROVENANCE_SOURCE_SHA_INVALID"):
            self.verify(source_commit="HEAD")

    def test_untrusted_repository_rejected(self):
        with self.assertRaises(Exception):
            self.verify(repository="--owner/repo")

    def test_missing_artifact_rejected_before_cli(self):
        self.path.unlink()
        with self.assertRaisesRegex(provenance.ProvenanceError, "PROVENANCE_FILE_MISMATCH"):
            self.verify()
        self.assertFalse(self.commands)

    def test_local_artifact_digest_mismatch_rejected(self):
        self.path.write_bytes(b"tampered payload of same size")
        with self.assertRaises(provenance.ProvenanceError):
            self.verify()
        self.assertFalse(self.commands)

    def test_local_artifact_size_mismatch_rejected(self):
        self.path.write_bytes(b"short")
        with self.assertRaisesRegex(provenance.ProvenanceError, "PROVENANCE_FILE_SIZE_MISMATCH"):
            self.verify()

    def test_expected_digest_missing_rejected(self):
        m = metadata()
        m["reported_digest"] = None
        with self.assertRaisesRegex(provenance.ProvenanceError, "PROVENANCE_EXPECTED_DIGEST_MISSING"):
            self.verify(asset_metadata=m)

    def test_name_mismatch_rejected(self):
        m = metadata()
        m["name"] = "another.bin"
        with self.assertRaisesRegex(provenance.ProvenanceError, "PROVENANCE_FILE_MISMATCH"):
            self.verify(asset_metadata=m)

    def test_limit_rejected(self):
        with self.assertRaisesRegex(provenance.ProvenanceError, "PROVENANCE_ASSET_SIZE_INVALID"):
            self.verify(max_bytes=1)

    def test_boolean_limit_rejected(self):
        with self.assertRaisesRegex(provenance.ProvenanceError, "PROVENANCE_LIMIT_INVALID"):
            self.verify(max_bytes=True)

    def test_symlink_rejected(self):
        other = pathlib.Path(self.temp.name) / "source"
        other.write_bytes(CONTENT)
        self.path.unlink()
        self.path.symlink_to(other)
        with self.assertRaisesRegex(provenance.ProvenanceError, "PROVENANCE_FILE_MISMATCH"):
            self.verify()

    def test_failed_cryptographic_verifier_blocks(self):
        def fail(argv, **kwargs):
            return subprocess.CompletedProcess(argv, 1, "", "failure details are secret")
        result = self.verify(runner=fail)
        self.assertIn("PROVENANCE_SIGNATURE_VERIFICATION_FAILED", result["problems"])
        self.assertNotIn("failure details are secret", json.dumps(result))
        self.assertEqual(result["provenance_status"], "BLOCKED")

    def test_missing_gh_blocks(self):
        def absent(argv, **kwargs):
            raise FileNotFoundError("gh")
        result = self.verify(runner=absent)
        self.assertIn("PROVENANCE_VERIFIER_UNAVAILABLE", result["problems"])

    def test_timeout_blocks(self):
        def timeout(argv, **kwargs):
            raise subprocess.TimeoutExpired(argv, 1)
        result = self.verify(runner=timeout)
        self.assertIn("PROVENANCE_VERIFIER_TIMEOUT", result["problems"])

    def test_invalid_json_blocks_even_on_zero_exit(self):
        result = self.verify(runner=lambda argv, **kw: subprocess.CompletedProcess(argv, 0, "{}", ""))
        self.assertIn("PROVENANCE_VERIFIER_OUTPUT_INVALID", result["problems"])

    def test_valid_json_with_wrong_digest_blocks(self):
        payload = gh_payload("sha256:" + "0" * 64)
        result = self.verify(runner=lambda argv, **kw: subprocess.CompletedProcess(argv, 0, payload, ""))
        self.assertIn("PROVENANCE_VERIFIER_OUTPUT_INVALID", result["problems"])

    def test_unexpected_predicate_blocks(self):
        payload = gh_payload(predicate="https://spdx.dev/Document/v2.3")
        result = self.verify(runner=lambda argv, **kw: subprocess.CompletedProcess(argv, 0, payload, ""))
        self.assertIn("PROVENANCE_VERIFIER_OUTPUT_INVALID", result["problems"])

    def test_missing_certificate_blocks(self):
        payload = gh_payload(certificate="")
        result = self.verify(runner=lambda argv, **kw: subprocess.CompletedProcess(argv, 0, payload, ""))
        self.assertIn("PROVENANCE_VERIFIER_OUTPUT_INVALID", result["problems"])

    def test_empty_attestations_block(self):
        result = self.verify(runner=lambda argv, **kw: subprocess.CompletedProcess(argv, 0, "[]", ""))
        self.assertIn("PROVENANCE_VERIFIER_OUTPUT_INVALID", result["problems"])

    def test_larger_than_bounded_output_blocks(self):
        self.assertFalse(provenance.verify_gh_json("x" * (provenance.MAX_CLI_OUTPUT + 1), expected_digest=DIGEST))

    def test_mutated_artifact_during_cli_blocks(self):
        def mutate(argv, **kwargs):
            self.path.write_bytes(b"x" * len(CONTENT))
            return subprocess.CompletedProcess(argv, 0, gh_payload(), "")
        result = self.verify(runner=mutate)
        self.assertIn("PROVENANCE_ARTIFACT_CHANGED_DURING_VERIFICATION", result["problems"])

    def test_report_does_not_expose_local_absolute_path(self):
        result = self.verify()
        self.assertNotIn(str(self.path), json.dumps(result))

    def test_no_shell_and_no_interactive_prompt(self):
        self.verify()
        argv, kwargs = self.commands[0]
        self.assertEqual(kwargs["env"]["GH_PROMPT_DISABLED"], "1")
        self.assertEqual(kwargs["env"]["GH_HOST"], "github.com")
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertTrue(isinstance(argv, list))


class ReportProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = pathlib.Path(self.temp.name) / "repository"
        self.repo.mkdir()
        self.file = pathlib.Path(self.temp.name) / "package.bin"
        self.file.write_bytes(CONTENT)
        self.git("init", "-q")
        self.git("config", "user.name", "Tester")
        self.git("config", "user.email", "tester@example.invalid")
        self.git("remote", "add", "origin", "https://github.com/" + REPO + ".git")
        (self.repo / "VERSION").write_text("0.0.13\n", encoding="utf-8")
        (self.repo / "CHANGELOG.md").write_text("## 0.0.13 — Provenance\n", encoding="utf-8")
        (self.repo / "CHANGELOG.en.md").write_text("## 0.0.13 — Provenance\n", encoding="utf-8")
        config = {
            "schema_version": 1, "version_file": "VERSION",
            "release_notes": ["CHANGELOG.md", "CHANGELOG.en.md"],
            "build": {"not_applicable_reason": "No executable output in this test-only project."},
            "tests": [{"id": "test", "argv": [sys.executable, "-c", "pass"], "cwd": ".", "timeout_seconds": 10}],
        }
        (self.repo / "release-checks.json").write_text(json.dumps(config), encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "Коммит релиза")
        self.sha = self.git("rev-parse", "HEAD")
        self.git("tag", "-a", TAG, "-m", "Тег тестовой версии")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True, text=True).stdout.strip()

    def metadata_release(self):
        return {
            "publication_status": "SOURCE_RELEASE_PUBLISHED",
            "release_id": 10,
            "release_url": "https://github.com/" + REPO + "/releases/tag/" + TAG,
            "asset_metadata": [metadata()],
            "problems": [],
        }

    def test_provenance_not_requested_by_default(self):
        with mock.patch.object(release_report, "verify_release_provenance", side_effect=AssertionError):
            report = release_report.build_report(self.repo, "0.0.13")
        self.assertEqual(report["provenance_status"], "NOT_CHECKED")

    def test_provenance_requires_release_verification(self):
        with self.assertRaisesRegex(release_report.InspectionError, "PROVENANCE_REQUIRES_PUBLICATION"):
            release_report.build_report(self.repo, "0.0.13", verify_provenance=True)

    def test_provenance_requires_specific_file_and_workflow(self):
        with self.assertRaisesRegex(release_report.InspectionError, "PROVENANCE_REQUIRES_FILE"):
            release_report.build_report(
                self.repo, "0.0.13", verify_publication=True,
                verify_provenance=True, github_repo=REPO
            )

    def test_no_release_blocks_without_running_gh(self):
        with mock.patch.object(release_report, "verify_github_publication", return_value={
            "publication_status": "BLOCKED", "problems": ["PUBLICATION_QUERY_FAILED_OR_MISSING"]
        }), mock.patch.object(release_report, "verify_release_provenance", side_effect=AssertionError):
            report = release_report.build_report(
                self.repo, "0.0.13", github_repo=REPO, verify_publication=True,
                verify_provenance=True, artifact_file=self.file, signer_workflow=WORKFLOW
            )
        self.assertIn("PROVENANCE_REQUIRES_PUBLISHED_RELEASE", report["problems"])

    def test_wrong_asset_name_blocks(self):
        with mock.patch.object(release_report, "verify_github_publication", return_value={
            **self.metadata_release(), "asset_metadata": [{"name": "other.bin"}]
        }), mock.patch.object(release_report, "verify_release_provenance", side_effect=AssertionError):
            report = release_report.build_report(
                self.repo, "0.0.13", github_repo=REPO, verify_publication=True,
                verify_provenance=True, artifact_file=self.file, signer_workflow=WORKFLOW
            )
        self.assertIn("PROVENANCE_RELEASE_ASSET_MISSING", report["problems"])

    def test_verified_provenance_remains_partial_without_ci(self):
        result = {
            "provenance_status": "PASS", "artifact_provenance": "GITHUB_ATTESTATION_VERIFIED",
            "local_artifact_integrity": "PASS", "signer_workflow": WORKFLOW,
            "source_commit_sha": self.sha, "source_ref": "refs/tags/" + TAG,
            "asset_name": "package.bin", "asset_sha256": DIGEST,
            "bytes_verified": len(CONTENT), "problems": []
        }
        with mock.patch.object(release_report, "verify_github_publication", return_value=self.metadata_release()), \
             mock.patch.object(release_report, "verify_release_provenance", return_value=result):
            report = release_report.build_report(
                self.repo, "0.0.13", github_repo=REPO, verify_publication=True,
                verify_provenance=True, artifact_file=self.file, signer_workflow=WORKFLOW
            )
        self.assertEqual(report["provenance_status"], "PASS")
        self.assertEqual(report["artifact_provenance"], "GITHUB_ATTESTATION_VERIFIED")
        self.assertEqual(report["stage"], "PROVENANCE_VERIFIED_PARTIAL")
        self.assertEqual(report["release_readiness"], "NOT_VERIFIED")

    def test_failed_attestation_blocks_everything(self):
        with mock.patch.object(release_report, "verify_github_publication", return_value=self.metadata_release()), \
             mock.patch.object(release_report, "verify_release_provenance", return_value={
                 "provenance_status": "BLOCKED", "problems": ["PROVENANCE_SIGNATURE_VERIFICATION_FAILED"]
             }):
            report = release_report.build_report(
                self.repo, "0.0.13", github_repo=REPO, verify_publication=True,
                verify_provenance=True, artifact_file=self.file, signer_workflow=WORKFLOW
            )
        self.assertEqual(report["evidence_status"], "BLOCKED")
        self.assertIn("PROVENANCE_SIGNATURE_VERIFICATION_FAILED", report["problems"])

    def test_certificate_has_attestation_but_is_itself_unsigned(self):
        report = {
            "requested_version": "0.0.13", "requested_tag": TAG,
            "target_commit_sha": self.sha, "local_tag_object_sha": "b" * 40,
            "local_tag_status": "PASS", "remote_tag_status": "PASS", "ci_status": "PASS",
            "publication_status": "SOURCE_RELEASE_PUBLISHED",
            "publication_asset_content_verification": "NOT_PERFORMED",
            "artifact_provenance": "GITHUB_ATTESTATION_VERIFIED",
            "provenance_status": "PASS", "local_artifact_integrity": "PASS",
            "provenance_signer_workflow": WORKFLOW,
            "provenance_source_commit": self.sha,
            "provenance_source_ref": "refs/tags/" + TAG,
            "provenance_verified_asset": {"name": "package.bin", "sha256": DIGEST},
            "evidence_status": "PASS", "problems": []
        }
        certificate = release_certificate.make_certificate(report)
        self.assertEqual(certificate["publication_evidence_status"], "SOURCE_ASSET_ATTESTATION_VERIFIED")
        self.assertTrue(certificate["checks"]["attestation_signature_verified"])
        self.assertFalse(certificate["signed"])
        self.assertEqual(certificate["application_release_readiness"], "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
