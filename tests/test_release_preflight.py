"""T09.02 — изолированные тесты предварительной проверки релизов."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import release_preflight as module


class ReleasePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = pathlib.Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "example@example.invalid")
        self.config = {
            "schema_version": 1,
            "version_file": "VERSION",
            "release_notes": ["CHANGELOG.md", "CHANGELOG.en.md"],
            "build": {"not_applicable_reason": "This fixture has no build outputs."},
            "tests": [self.check("unit", "import sys; sys.exit(0)")],
        }
        (self.repo / "VERSION").write_text("0.0.8\n", encoding="utf-8")
        (self.repo / "CHANGELOG.md").write_text("## 0.0.8 — Исправление\n", encoding="utf-8")
        (self.repo / "CHANGELOG.en.md").write_text("## 0.0.8 — Change\n", encoding="utf-8")
        self.commit_config()

    def check(self, ident, code, *, timeout=15, cwd="."):
        return {"id": ident, "argv": [sys.executable, "-c", code], "cwd": cwd, "timeout_seconds": timeout}

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    def commit_config(self):
        (self.repo / "release-checks.json").write_text(
            json.dumps(self.config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        self.git("add", ".")
        self.git("commit", "-qm", "Подготовлена проверочная конфигурация релиза")
        self.sha = self.git("rev-parse", "HEAD")

    def test_plan_is_read_only(self):
        self.config["tests"] = [self.check("write-marker", "open('marker','w').write('bad')")]
        self.commit_config()
        result = module.preflight(self.repo, "0.0.8")
        self.assertEqual(result["preflight_status"], "PASS")
        self.assertEqual(result["checks_status"], "NOT_RUN")
        self.assertEqual(result["stage"], "PREPARED")
        self.assertFalse((self.repo / "marker").exists())
        self.assertEqual(result["release_readiness"], "NOT_VERIFIED")

    def test_execution_checks_exit_code(self):
        result = module.preflight(self.repo, "0.0.8", execute=True, expected_commit=self.sha)
        self.assertEqual(result["stage"], "VALIDATED")
        self.assertEqual(result["checks_status"], "PASS")
        self.assertEqual(result["build_status"], "NOT_APPLICABLE")
        self.assertEqual(result["tests_status"], "PASS")
        self.assertEqual(result["executed_checks"][0]["exit_code"], 0)
        self.assertEqual(result["release_readiness"], "NOT_VERIFIED")

    def test_failed_test_blocks(self):
        self.config["tests"] = [self.check("bad", "import sys; sys.exit(7)")]
        self.commit_config()
        r = module.preflight(self.repo, "0.0.8", execute=True)
        self.assertEqual(r["checks_status"], "BLOCKED")
        self.assertEqual(r["stage"], "BLOCKED")
        self.assertEqual(r["executed_checks"][0]["exit_code"], 7)
        self.assertIn("CHECK_FAIL", r["problems"])

    def test_failed_step_stops_following_checks(self):
        self.config["tests"] = [
            self.check("first", "import sys; sys.exit(1)"),
            self.check("second", "open('unexpected','w').write('x')"),
        ]
        self.commit_config()
        r = module.preflight(self.repo, "0.0.8", execute=True)
        self.assertEqual(len(r["executed_checks"]), 1)
        self.assertFalse((self.repo / "unexpected").exists())

    def test_build_failure_prevents_tests(self):
        self.config["build"] = [self.check("build", "import sys;sys.exit(3)")]
        self.config["tests"] = [self.check("test", "open('unexpected','w').write('x')")]
        self.commit_config()
        r = module.preflight(self.repo, "0.0.8", execute=True)
        self.assertEqual(r["build_status"], "BLOCKED")
        self.assertEqual(r["tests_status"], "BLOCKED")
        self.assertFalse((self.repo / "unexpected").exists())

    def test_version_mismatch_blocks(self):
        r = module.preflight(self.repo, "0.0.9")
        self.assertIn("VERSION_MISMATCH", r["problems"])
        self.assertEqual(r["stage"], "BLOCKED")

    def test_missing_release_notes_version_blocks(self):
        (self.repo / "CHANGELOG.en.md").write_text("## 0.0.7 — Old\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "Сломано соответствие номера переводу")
        r = module.preflight(self.repo, "0.0.8")
        self.assertIn("RELEASE_NOTES_VERSION_MISSING", r["problems"])

    def test_dirty_worktree_prevents_execution(self):
        (self.repo / "untracked").write_text("x", encoding="utf-8")
        r = module.preflight(self.repo, "0.0.8", execute=True)
        self.assertIn("WORKTREE_DIRTY", r["problems"])
        self.assertFalse(r["executed_checks"])

    def test_outdated_commit_prevents_execution(self):
        prev = self.sha
        (self.repo / "NEXT").write_text("changed", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "Добавлен ещё один коммит")
        r = module.preflight(self.repo, "0.0.8", execute=True, expected_commit=prev)
        self.assertIn("HEAD_CHANGED", r["problems"])
        self.assertEqual(r["checks_status"], "NOT_RUN")

    def test_empty_tests_rejected(self):
        self.config["tests"] = []
        self.commit_config()
        with self.assertRaisesRegex(module.PreflightError, "CONFIG_CHECKS_INVALID"):
            module.preflight(self.repo, "0.0.8")

    def test_no_build_without_reason_rejected(self):
        self.config["build"] = []
        self.commit_config()
        with self.assertRaisesRegex(module.PreflightError, "CONFIG_BUILD_REASON_REQUIRED"):
            module.preflight(self.repo, "0.0.8")

    def test_unknown_config_fields_rejected(self):
        self.config["unrecognized"] = True
        self.commit_config()
        with self.assertRaisesRegex(module.PreflightError, "CONFIG_SCHEMA_INVALID"):
            module.preflight(self.repo, "0.0.8")

    def test_invalid_timeout_rejected(self):
        self.config["tests"][0]["timeout_seconds"] = True
        self.commit_config()
        with self.assertRaisesRegex(module.PreflightError, "CONFIG_TIMEOUT_INVALID"):
            module.preflight(self.repo, "0.0.8")

    def test_duplicate_check_id_rejected(self):
        self.config["tests"].append(self.config["tests"][0].copy())
        self.commit_config()
        with self.assertRaisesRegex(module.PreflightError, "CONFIG_STEP_ID"):
            module.preflight(self.repo, "0.0.8")

    def test_escaping_working_directory_rejected(self):
        self.config["tests"][0]["cwd"] = ".."
        self.commit_config()
        with self.assertRaisesRegex(module.PreflightError, "CONFIG_UNSAFE_PATH"):
            module.preflight(self.repo, "0.0.8")

    def test_duplicate_json_key_rejected(self):
        (self.repo / "release-checks.json").write_text('{"x":1,"x":2}', encoding="utf-8")
        with self.assertRaisesRegex(module.PreflightError, "CONFIG_DUPLICATE_KEY"):
            module.preflight(self.repo, "0.0.8")

    def test_uncommitted_config_blocks(self):
        self.config["tests"][0]["id"] = "changed"
        (self.repo / "release-checks.json").write_text(json.dumps(self.config), encoding="utf-8")
        r = module.preflight(self.repo, "0.0.8", execute=True)
        self.assertIn("WORKTREE_DIRTY", r["problems"])

    def test_check_creating_untracked_file_blocks(self):
        self.config["tests"] = [self.check("write-marker", "open('marker','w').write('bad')")]
        self.commit_config()
        r = module.preflight(self.repo, "0.0.8", execute=True)
        self.assertIn("WORKTREE_DIRTY_AFTER_CHECKS", r["problems"])
        self.assertEqual(r["stage"], "BLOCKED")

    def test_missing_executable_blocks(self):
        self.config["tests"][0]["argv"] = ["__unknown_tessera_executable_xyz__"]
        self.commit_config()
        r = module.preflight(self.repo, "0.0.8", execute=True)
        self.assertEqual(r["executed_checks"][0]["status"], "START_FAILED")
        self.assertEqual(r["stage"], "BLOCKED")

    def test_timeout_blocks(self):
        self.config["tests"][0] = self.check("slow", "import time;time.sleep(3)", timeout=1)
        self.commit_config()
        r = module.preflight(self.repo, "0.0.8", execute=True)
        self.assertEqual(r["executed_checks"][0]["status"], "TIMEOUT")
        self.assertIn("CHECK_TIMEOUT", r["problems"])

    def test_real_build_and_tests_run_in_order(self):
        self.config["build"] = [self.check("build", "import sys;sys.exit(0)")]
        self.commit_config()
        r = module.preflight(self.repo, "0.0.8", execute=True)
        self.assertEqual(r["build_status"], "PASS")
        self.assertEqual(r["tests_status"], "PASS")
        self.assertEqual([x["kind"] for x in r["executed_checks"]], ["build", "tests"])

    def test_never_changes_git_tags(self):
        before = self.git("tag", "-l")
        module.preflight(self.repo, "0.0.8", execute=True)
        self.assertEqual(self.git("tag", "-l"), before)


if __name__ == "__main__":
    unittest.main()
