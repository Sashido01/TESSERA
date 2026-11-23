"""T11.02: unit and negative tests of the isolated official GitHub CLI dry-run runner."""
from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dry_run", ROOT / "tools" / "run_publish_dry_run.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SkillDryRunTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name)
        self.skill = self.root / "skills" / "microversion-release"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text(
            "---\nname: microversion-release\ndescription: Test format only\n---\n"
            "This is a test skill.\n", encoding="utf-8")
        self.calls = []

    def fake_runner(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        if argv[-1] == "version":
            return subprocess.CompletedProcess(argv, 0,
                "gh version 2.105.0 (2026-11-18)\nhttps://github.com/cli/cli/releases/tag/v2.105.0\n", "")
        if argv[:2] == ["git", "init"]:
            return subprocess.CompletedProcess(argv, 0, "", "")
        if argv[:2] == ["git", "remote"]:
            return subprocess.CompletedProcess(argv, 0, "", "")
        if argv[1:4] == ["skill", "publish", "--dry-run"]:
            file = pathlib.Path(argv[-1]) / "skills" / "microversion-release" / "SKILL.md"
            if "invalid-other-skill" in file.read_text(encoding="utf-8"):
                return subprocess.CompletedProcess(argv, 1, "", "validation failed")
            return subprocess.CompletedProcess(argv, 0, "", "Dry run complete. Use without --dry-run to publish.")
        raise AssertionError("unexpected command: " + str(argv))

    def test_actual_invocations_have_no_network_remote_or_tokens(self):
        result = module.run(self.root, pathlib.Path(sys.executable), runner=self.fake_runner)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["negative"], "REJECTED")
        self.assertEqual(result["github_release_publication"], "NOT_CHECKED")
        self.assertEqual(result["remote_security_diagnostics"], "NOT_CHECKED")
        self.assertEqual(len([a for a, _ in self.calls if a[1:4] == ["skill", "publish", "--dry-run"]]), 2)
        self.assertEqual([a[:2] for a, _ in self.calls if a and a[0] == "git"],
                         [["git", "init"], ["git", "remote"], ["git", "remote"]])
        for argv, kwargs in self.calls:
            env = kwargs["env"]
            self.assertNotIn("GH_TOKEN", env)
            self.assertNotIn("GITHUB_TOKEN", env)
            self.assertNotIn("GH_HOST", env)
            self.assertEqual(env["GH_PROMPT_DISABLED"], "1")
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
            self.assertTrue(kwargs["capture_output"])
            self.assertFalse(kwargs["check"])
        self.assertNotIn("invalid-other-skill",
                         (self.skill / "SKILL.md").read_text(encoding="utf-8"))

    def test_unknown_version_rejected_without_publish(self):
        def invalid(argv, **kwargs):
            if argv[-1] == "version":
                return subprocess.CompletedProcess(argv, 0, "gh version 2.101.0 (outdated)", "")
            return self.fake_runner(argv, **kwargs)
        with self.assertRaisesRegex(module.DryRunError, "DRY_RUN_CLI_VERSION_MISMATCH"):
            module.run(self.root, pathlib.Path(sys.executable), runner=invalid)
        self.assertFalse(any(a[1:4] == ["skill", "publish", "--dry-run"] for a, _ in self.calls))

    def test_missing_cli_rejected(self):
        with self.assertRaisesRegex(module.DryRunError, "DRY_RUN_INPUT_UNAVAILABLE"):
            module.run(self.root, self.root / "missing", runner=self.fake_runner)

    def test_positive_exit_error_rejected(self):
        def bad(argv, **kwargs):
            if argv[1:4] == ["skill", "publish", "--dry-run"]:
                return subprocess.CompletedProcess(argv, 1, "", "error")
            return self.fake_runner(argv, **kwargs)
        with self.assertRaisesRegex(module.DryRunError, "DRY_RUN_POSITIVE_FAILED"):
            module.run(self.root, pathlib.Path(sys.executable), runner=bad)

    def test_negative_false_success_rejected(self):
        def fake_success(argv, **kwargs):
            if argv[1:4] == ["skill", "publish", "--dry-run"]:
                return subprocess.CompletedProcess(argv, 0, "", "Dry run complete. Use without --dry-run to publish.")
            return self.fake_runner(argv, **kwargs)
        with self.assertRaisesRegex(module.DryRunError, "DRY_RUN_NEGATIVE_NOT_REJECTED"):
            module.run(self.root, pathlib.Path(sys.executable), runner=fake_success)

    def test_symlink_file_rejected_before_running(self):
        destination = self.root / "outside"
        (self.skill / "SKILL.md").rename(destination)
        try:
            (self.skill / "SKILL.md").symlink_to(destination)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unsupported")
        with self.assertRaisesRegex(module.DryRunError, "DRY_RUN_SKILL_INVALID"):
            module.run(self.root, pathlib.Path(sys.executable), runner=self.fake_runner)
        self.assertFalse(self.calls)

    def test_empty_skills_rejected(self):
        import shutil
        shutil.rmtree(self.skill)
        with self.assertRaisesRegex(module.DryRunError, "DRY_RUN_SKILL_COUNT_INVALID"):
            module.run(self.root, pathlib.Path(sys.executable), runner=self.fake_runner)

    def test_missing_name_for_negative_fixture_fails_closed(self):
        (self.skill / "SKILL.md").write_text("---\ndescription: Test\n---", encoding="utf-8")
        with self.assertRaisesRegex(module.DryRunError, "DRY_RUN_POSITIVE_FAILED"):
            module.run(self.root, pathlib.Path(sys.executable), runner=lambda argv, **kw:
                subprocess.CompletedProcess(argv, 0,
                  "gh version 2.105.0 (2026-11-18)\n" if argv[-1] == "version" else "",
                  "" if argv[-1] == "version" else "untrusted answer"))

    def test_official_tarball_sha_is_frozen(self):
        self.assertEqual(module.CLI_VERSION, "2.105.0")
        self.assertEqual(module.EXPECTED_SHA256,
                         "79e7ab5db738c48777b696e374f8b428f0647debfb424f44d2f426370407fe2f")
        ci = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        self.assertIn(module.EXPECTED_SHA256, ci)
        self.assertIn("gh_2.105.0_linux_amd64.tar.gz", ci)
        self.assertIn("python tools/run_publish_dry_run.py", ci)


if __name__ == "__main__":
    unittest.main()
