"""T10.01 safety checks for isolated, official GitHub CLI local installation."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "official_local_install", ROOT / "tools" / "check_official_local_install.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class OfficialInstallTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = pathlib.Path(temp.name) / "repo"
        self.repo.mkdir()
        self.skill = self.repo / "skills" / "microversion-release"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text(
            "---\nname: microversion-release\ndescription: Format test\n---\n"
            "The skill body must survive an install.\n",
            encoding="utf-8",
        )
        ref = self.skill / "references" / "INTEGRATION.md"
        ref.parent.mkdir()
        ref.write_text("Reference bytes stay identical.\n", encoding="utf-8")
        self.calls = []

    def fake(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        if argv[1:] == ["version"]:
            return subprocess.CompletedProcess(argv, 0,
                "gh version 2.105.0 (2026-11-17)\n", "")
        if argv[1:3] == ["skill", "install"]:
            if "--pin" in argv:
                return subprocess.CompletedProcess(argv, 1, "", "pin incompatible with local")
            source = pathlib.Path(argv[3]) / "skills" / mod.SKILL
            dest = pathlib.Path(argv[argv.index("--dir") + 1]) / mod.SKILL
            shutil.copytree(source, dest, dirs_exist_ok=True)
            installed = dest / "SKILL.md"
            content = installed.read_text(encoding="utf-8")
            installed.write_text(content.replace(
                "\n---\n", "\nmetadata:\n  local-path: source\n---\n", 1
            ), encoding="utf-8")
            return subprocess.CompletedProcess(argv, 0, "Installed microversion-release", "")
        if argv[1:3] == ["skill", "list"]:
            return subprocess.CompletedProcess(
                argv, 0, json.dumps([{"skillName": "microversion-release"}]), ""
            )
        raise AssertionError("Unexpected invocation:" + str(argv))

    def test_complete_synthetic_isolation_contract(self):
        result = mod.inspect(self.repo, pathlib.Path(sys.executable), runner=self.fake)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["local_pin"], "NOT_SUPPORTED")
        self.assertEqual(result["remote_pinned_install"], "NOT_VERIFIED")
        self.assertEqual(len(self.calls), 4)
        for _, opts in self.calls:
            env = opts["env"]
            self.assertEqual(env["GH_PROMPT_DISABLED"], "1")
            self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
            self.assertNotIn("GITHUB_TOKEN", env)
            self.assertNotIn("GH_TOKEN", env)
            self.assertIs(opts["stdin"], subprocess.DEVNULL)
            self.assertTrue(opts["capture_output"])
        self.assertNotIn("local-path:",
                         (self.skill / "SKILL.md").read_text(encoding="utf-8"))

    def test_reject_existing_destination(self):
        target = self.repo / "target"
        (target / mod.SKILL).mkdir(parents=True)
        marker = target / mod.SKILL / "owner.txt"
        marker.write_text("KEEP", encoding="utf-8")
        with self.assertRaisesRegex(mod.InstallCheckError, "INSTALL_TARGET_ALREADY_EXISTS"):
            mod.safe_destination(target, mod.SKILL)
        self.assertEqual(marker.read_text(encoding="utf-8"), "KEEP")

    def test_reject_destination_symlink(self):
        target = self.repo / "actual"
        target.mkdir()
        alias = self.repo / "alias"
        try:
            alias.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        with self.assertRaisesRegex(mod.InstallCheckError, "INSTALL_TARGET_SYMLINK"):
            mod.safe_destination(alias, mod.SKILL)

    def test_reject_source_symlink(self):
        target = self.repo / "outside"
        target.write_text("source", encoding="utf-8")
        try:
            (self.skill / "linked.txt").symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        with self.assertRaisesRegex(mod.InstallCheckError, "INSTALL_SYMLINK_FORBIDDEN"):
            mod.tree_fingerprint(self.repo / "skills")

    def test_fingerprint_changes_with_content(self):
        first = mod.tree_fingerprint(self.repo / "skills")
        (self.skill / "references" / "INTEGRATION.md").write_text(
            "Different reference", encoding="utf-8"
        )
        self.assertNotEqual(first, mod.tree_fingerprint(self.repo / "skills"))

    def test_version_mismatch_stops_before_install(self):
        def bad_version(argv, **kwargs):
            if argv[1:] == ["version"]:
                return subprocess.CompletedProcess(argv, 0, "gh version 2.101.0 (old)\n", "")
            return self.fake(argv, **kwargs)
        with self.assertRaisesRegex(mod.InstallCheckError, "INSTALL_CLI_VERSION_MISMATCH"):
            mod.inspect(self.repo, pathlib.Path(sys.executable), runner=bad_version)
        self.assertFalse(self.calls)

    def test_install_failure_is_explicit(self):
        def failure(argv, **kwargs):
            if argv[1:3] == ["skill", "install"]:
                return subprocess.CompletedProcess(argv, 1, "", "private path and password")
            return self.fake(argv, **kwargs)
        with self.assertRaisesRegex(mod.InstallCheckError, "INSTALL_OFFICIAL_LOCAL_FAILED"):
            mod.inspect(self.repo, pathlib.Path(sys.executable), runner=failure)

    def test_discovery_failure_is_explicit(self):
        def missing(argv, **kwargs):
            if argv[1:3] == ["skill", "list"]:
                return subprocess.CompletedProcess(argv, 0, "[]", "")
            return self.fake(argv, **kwargs)
        with self.assertRaisesRegex(mod.InstallCheckError, "INSTALL_CLI_DISCOVERY_FAILED"):
            mod.inspect(self.repo, pathlib.Path(sys.executable), runner=missing)

    def test_pin_conflict_must_not_be_silently_accepted(self):
        def accepts_pin(argv, **kwargs):
            if "--pin" in argv:
                return subprocess.CompletedProcess(argv, 0, "", "")
            return self.fake(argv, **kwargs)
        with self.assertRaisesRegex(mod.InstallCheckError, "INSTALL_LOCAL_PIN_NOT_REJECTED"):
            mod.inspect(self.repo, pathlib.Path(sys.executable), runner=accepts_pin)

    def test_missing_cli_is_blocked(self):
        with self.assertRaisesRegex(mod.InstallCheckError, "INSTALL_INPUT_UNAVAILABLE"):
            mod.inspect(self.repo, self.repo / "missing", runner=self.fake)
        self.assertFalse(self.calls)

    def test_official_binary_reused(self):
        ci = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        self.assertIn("tools/check_official_local_install.py", ci)
        self.assertIn("gh_2.105.0_linux_amd64/bin/gh", ci)


if __name__ == "__main__":
    unittest.main()
