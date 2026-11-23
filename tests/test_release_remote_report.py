"""T09.03: проверка локального/удалённого тега и проверяемого отчёта."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import release_remote, release_report


class RemoteReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.repo = self.root / "project"
        self.repo.mkdir()
        self.remote = self.root / "remote.git"
        self.git("init", "-q")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.invalid")
        subprocess.run(["git", "init", "--bare", "-q", str(self.remote)], check=True)
        self.git("remote", "add", "origin", str(self.remote))
        self._write_plan()
        self.git("add", ".")
        self.git("commit", "-qm", "Подготовлен тестовый релиз")
        self.sha = self.git("rev-parse", "HEAD")

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            text=True, capture_output=True, check=True
        ).stdout.strip()

    def remote_git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.remote), *args],
            text=True, capture_output=True, check=True
        ).stdout.strip()

    def _write_plan(self):
        (self.repo / "VERSION").write_text("0.0.9\n", encoding="utf-8")
        (self.repo / "CHANGELOG.md").write_text("## 0.0.9 — Проверено\n", encoding="utf-8")
        (self.repo / "CHANGELOG.en.md").write_text("## 0.0.9 — Verified\n", encoding="utf-8")
        cfg = {
            "schema_version": 1, "version_file": "VERSION",
            "release_notes": ["CHANGELOG.md", "CHANGELOG.en.md"],
            "build": {"not_applicable_reason": "This skill fixture does not produce build artifacts."},
            "tests": [{
                "id": "unit", "argv": [sys.executable, "-c", "import sys;sys.exit(0)"],
                "cwd": ".", "timeout_seconds": 15
            }]
        }
        (self.repo / "release-checks.json").write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def make_tag(self, name="v0.0.9", message="Релиз 0.0.9 — проверен"):
        self.git("tag", "-a", name, "-m", message)

    def push_tag(self, name="v0.0.9"):
        self.git("push", "origin", f"refs/tags/{name}")

    def test_local_tag_missing_blocks_remote(self):
        report = release_remote.verify_remote_tag(self.repo, "0.0.9")
        self.assertEqual(report["remote_tag_status"], "BLOCKED")
        self.assertIn("LOCAL_TAG_INVALID", report["problems"])

    def test_remote_tag_missing(self):
        self.make_tag()
        report = release_remote.verify_remote_tag(self.repo, "0.0.9")
        self.assertIn("REMOTE_TAG_MISSING", report["problems"])

    def test_exact_annotated_object_verified(self):
        self.make_tag()
        self.push_tag()
        report = release_remote.verify_remote_tag(self.repo, "0.0.9")
        self.assertEqual(report["remote_tag_status"], "PASS")
        self.assertEqual(report["remote_publication"], "TAG_REF_VERIFIED")
        self.assertEqual(report["remote_tag_object_sha"], report["local_tag_object_sha"])
        self.assertEqual(report["github_release"], "NOT_CHECKED")

    def test_same_commit_different_annotated_tag_is_rejected(self):
        self.make_tag()
        self.push_tag()
        self.git("tag", "-d", "v0.0.9")  # Только в временном тестовом репозитории
        self.make_tag(message="Другая аннотация того же коммита")
        report = release_remote.verify_remote_tag(self.repo, "0.0.9")
        self.assertEqual(report["remote_tag_status"], "BLOCKED")
        self.assertIn("REMOTE_TAG_OBJECT_MISMATCH", report["problems"])

    def test_lightweight_remote_ref_rejected(self):
        self.make_tag()
        self.push_tag()
        self.remote_git("update-ref", "refs/tags/v0.0.9", self.sha)
        report = release_remote.verify_remote_tag(self.repo, "0.0.9")
        self.assertIn("REMOTE_TAG_OBJECT_MISMATCH", report["problems"])

    def test_invalid_remote_name_rejected(self):
        self.make_tag()
        with self.assertRaisesRegex(release_remote.InspectionError, "REMOTE_NAME_INVALID"):
            release_remote.verify_remote_tag(self.repo, "0.0.9", remote="--upload-pack=evil")

    def test_query_failure_is_not_tag_missing(self):
        self.make_tag()
        self.git("remote", "remove", "origin")
        report = release_remote.verify_remote_tag(self.repo, "0.0.9")
        self.assertIn("REMOTE_QUERY_FAILED", report["problems"])
        self.assertNotIn("REMOTE_TAG_MISSING", report["problems"])

    def test_bad_timeout_rejected(self):
        with self.assertRaisesRegex(release_remote.InspectionError, "REMOTE_TIMEOUT_INVALID"):
            release_remote.verify_remote_tag(self.repo, "0.0.9", timeout_seconds=True)

    def test_namespaced_tag(self):
        self.make_tag("microversion-release/v0.0.9")
        self.push_tag("microversion-release/v0.0.9")
        report = release_remote.verify_remote_tag(self.repo, "0.0.9", prefix="microversion-release/")
        self.assertEqual(report["remote_tag_status"], "PASS")

    def test_ref_verification_does_not_change_git_state(self):
        self.make_tag()
        self.push_tag()
        before = self.git("show-ref")
        report = release_remote.verify_remote_tag(self.repo, "0.0.9")
        self.assertEqual(report["remote_tag_status"], "PASS")
        self.assertEqual(self.git("show-ref"), before)

    def test_report_without_remote_does_not_need_network(self):
        self.make_tag()
        result = release_report.build_report(self.repo, "0.0.9")
        self.assertEqual(result["evidence_status"], "PASS")
        self.assertEqual(result["remote_tag_status"], "NOT_CHECKED")
        self.assertEqual(result["preflight_status"], "PASS")
        self.assertEqual(result["checks_status"], "NOT_RUN")
        self.assertEqual(result["release_readiness"], "NOT_VERIFIED")

    def test_remote_verified_report(self):
        self.make_tag()
        self.push_tag()
        report = release_report.build_report(self.repo, "0.0.9", verify_remote=True)
        self.assertEqual(report["evidence_status"], "PASS")
        self.assertEqual(report["remote_tag_status"], "PASS")
        self.assertEqual(report["stage"], "REMOTE_TAG_VERIFIED_CHECKS_NOT_RUN")
        self.assertEqual(report["github_release"], "NOT_CHECKED")
        self.assertEqual(report["release_readiness"], "NOT_VERIFIED")

    def test_report_explicitly_executes_real_tests(self):
        self.make_tag()
        report = release_report.build_report(self.repo, "0.0.9", execute_checks=True)
        self.assertEqual(report["checks_status"], "PASS")
        self.assertEqual(report["stage"], "LOCAL_TAG_VERIFIED_CHECKS_PASSED")
        self.assertEqual(len(report["executed_checks"]), 1)
        self.assertEqual(report["executed_checks"][0]["exit_code"], 0)
        self.assertEqual(report["release_readiness"], "NOT_VERIFIED")

    def test_report_combines_all_requested_proofs(self):
        self.make_tag()
        self.push_tag()
        report = release_report.build_report(self.repo, "0.0.9", verify_remote=True, execute_checks=True)
        self.assertEqual(report["stage"], "REMOTE_TAG_VERIFIED_CHECKS_PASSED")
        self.assertEqual(report["evidence_status"], "PASS")
        self.assertEqual(report["release_readiness"], "NOT_VERIFIED")

    def test_report_blocks_without_tag(self):
        report = release_report.build_report(self.repo, "0.0.9")
        self.assertEqual(report["evidence_status"], "BLOCKED")
        self.assertIn("RELEASE_NOT_TAGGED", report["problems"])

    def test_report_blocks_dirty_worktree(self):
        self.make_tag()
        (self.repo / "untracked").write_text("uncommitted", encoding="utf-8")
        report = release_report.build_report(self.repo, "0.0.9", execute_checks=True)
        self.assertEqual(report["evidence_status"], "BLOCKED")
        self.assertIn("WORKTREE_DIRTY", report["problems"])
        self.assertFalse(report["executed_checks"])

    def test_report_remote_mismatch_blocks(self):
        self.make_tag()
        self.push_tag()
        self.git("tag", "-d", "v0.0.9")  # Изолированный тест
        self.make_tag(message="Другой объект")
        report = release_report.build_report(self.repo, "0.0.9", verify_remote=True)
        self.assertEqual(report["evidence_status"], "BLOCKED")
        self.assertIn("REMOTE_TAG_OBJECT_MISMATCH", report["problems"])

    def test_historical_report_does_not_run_tests(self):
        self.make_tag()
        self.push_tag()
        old_sha = self.sha
        (self.repo / "VERSION").write_text("0.0.10\n", encoding="utf-8")
        self.git("add", "VERSION")
        self.git("commit", "-qm", "Добавлена следующая версия")
        report = release_report.build_report(
            self.repo, "0.0.9", commit=old_sha, verify_remote=True
        )
        self.assertEqual(report["evidence_status"], "PASS")
        self.assertTrue(report["is_historical_commit"])
        self.assertEqual(report["preflight_status"], "NOT_CHECKED_HISTORICAL")
        self.assertEqual(report["remote_tag_status"], "PASS")
        blocked = release_report.build_report(
            self.repo, "0.0.9", commit=old_sha, execute_checks=True
        )
        self.assertEqual(blocked["evidence_status"], "BLOCKED")
        self.assertIn("HISTORICAL_CHECKS_UNSUPPORTED", blocked["problems"])

    def test_markdown_reports_clearly_without_claiming_release(self):
        self.make_tag()
        report = release_report.build_report(self.repo, "0.0.9")
        rendered = release_report.markdown(report)
        self.assertIn("NOT_VERIFIED", rendered)
        self.assertIn("NOT_RUN", rendered)
        self.assertIn("0.0.9", rendered)

    def test_nonexistent_config_fails_closed(self):
        self.make_tag()
        self.git("rm", "-q", "release-checks.json")
        self.git("commit", "-qm", "Удалён план")
        report = release_report.build_report(self.repo, "0.0.9")
        self.assertEqual(report["evidence_status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
