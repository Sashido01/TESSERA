import importlib.util
import pathlib
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "core" / "release_inspect.py"
spec = importlib.util.spec_from_file_location("release_inspect", SOURCE)
inspect_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspect_module)


class ReleaseInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = pathlib.Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "example@example.invalid")
        (self.repo / "VERSION").write_text("0.1.0\n", encoding="utf-8")
        self.git("add", "VERSION")
        self.git("commit", "-qm", "Подготовлена первая проверенная версия")
        self.first_sha = self.git("rev-parse", "HEAD")

    def git(self, *args):
        p = subprocess.run(["git", "-C", str(self.repo), *args], text=True, capture_output=True, check=True)
        return p.stdout.strip()

    def test_missing_tag_blocks(self):
        r = inspect_module.inspect(self.repo, "0.1.0")
        self.assertEqual(r["inspection_status"], "BLOCKED")
        self.assertIn("RELEASE_NOT_TAGGED", r["problems"])
        self.assertEqual(r["release_readiness"], "NOT_VERIFIED")

    def test_annotated_tag_verifies_but_does_not_prove_tests(self):
        self.git("tag", "-a", "v0.1.0", "-m", "Релиз 0.1.0 — подготовлена проверяемая версия")
        r = inspect_module.inspect(self.repo, "0.1.0")
        self.assertEqual(r["inspection_status"], "PASS")
        self.assertTrue(r["tag_annotated"])
        self.assertTrue(r["tag_has_annotation"])
        self.assertEqual(r["tag_target_commit_sha"], self.first_sha)
        self.assertEqual(r["release_readiness"], "NOT_VERIFIED")
        self.assertEqual(r["remote_publication"], "NOT_CHECKED")

    def test_historical_release_verified_after_new_commit(self):
        self.git("tag", "-a", "v0.1.0", "-m", "Релиз 0.1.0 — проверка")
        (self.repo / "VERSION").write_text("0.1.1\n", encoding="utf-8")
        self.git("add", "VERSION")
        self.git("commit", "-qm", "Добавлена следующая рабочая версия")
        current = inspect_module.inspect(self.repo, "0.1.0")
        self.assertIn("VERSION_MISMATCH", current["problems"])
        historical = inspect_module.inspect(self.repo, "0.1.0", commit=self.first_sha)
        self.assertEqual(historical["inspection_status"], "PASS")

    def test_lightweight_tag_rejected(self):
        self.git("tag", "v0.1.0")
        r = inspect_module.inspect(self.repo, "0.1.0")
        self.assertIn("TAG_NOT_ANNOTATED", r["problems"])

    def test_tag_target_mismatch_rejected(self):
        self.git("tag", "-a", "v0.1.0", "-m", "Релиз 0.1.0 — первая версия")
        (self.repo / "VERSION").write_text("0.1.0\n", encoding="utf-8")
        (self.repo / "OTHER").write_text("other", encoding="utf-8")
        self.git("add", "OTHER")
        self.git("commit", "-qm", "Добавлен дополнительный файл")
        r = inspect_module.inspect(self.repo, "0.1.0")
        self.assertIn("TAG_WRONG_COMMIT", r["problems"])

    def test_version_mismatch_rejected(self):
        self.git("tag", "-a", "v0.1.1", "-m", "Релиз 0.1.1 — пример несовпадения")
        r = inspect_module.inspect(self.repo, "0.1.1")
        self.assertIn("VERSION_MISMATCH", r["problems"])

    def test_version_missing_rejected(self):
        self.git("rm", "-q", "VERSION")
        self.git("commit", "-qm", "Удалён файл версии для проверки")
        self.git("tag", "-a", "v0.1.0", "-m", "Релиз 0.1.0 — отсутствует VERSION")
        r = inspect_module.inspect(self.repo, "0.1.0")
        self.assertIn("VERSION_MISSING_IN_COMMIT", r["problems"])

    def test_namespaced_tag(self):
        self.git("tag", "-a", "microversion-release/v0.1.0", "-m", "Релиз навыка — проверка")
        r = inspect_module.inspect(self.repo, "0.1.0", prefix="microversion-release/")
        self.assertEqual(r["inspection_status"], "PASS")

    def add_skill_version(self, name="project-audit", version="0.0.1"):
        skill = self.repo / "skills" / name
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")
        (skill / "VERSION").write_text(version + "\n", encoding="utf-8")
        self.git("add", "skills")
        self.git("commit", "-qm", "Independent skill fixture")
        return self.git("rev-parse", "HEAD")

    def test_independent_skill_scope_uses_committed_nested_version(self):
        sha = self.add_skill_version()
        self.git("tag", "-a", "project-audit/v0.0.1", "-m", "Independent skill fixture")
        result = inspect_module.inspect(self.repo, "0.0.1", skill="project-audit")
        self.assertEqual(result["inspection_status"], "PASS")
        self.assertEqual(result["version_in_commit"], "0.0.1")
        self.assertEqual(result["version_path"], "skills/project-audit/VERSION")
        self.assertEqual(result["tag_target_commit_sha"], sha)
        self.assertEqual(result["release_readiness"], "NOT_VERIFIED")
        self.assertIn("VERSION_MISMATCH",
                      inspect_module.inspect(self.repo, "0.0.1", prefix="project-audit/")["problems"])

    def test_independent_skill_wrong_version_is_rejected(self):
        self.add_skill_version()
        self.git("tag", "-a", "project-audit/v0.0.2", "-m", "Wrong version fixture")
        result = inspect_module.inspect(self.repo, "0.0.2", skill="project-audit")
        self.assertIn("VERSION_MISMATCH", result["problems"])

    def test_independent_skill_missing_directory_is_rejected(self):
        self.git("tag", "-a", "project-audit/v0.1.0", "-m", "Missing skill fixture")
        result = inspect_module.inspect(self.repo, "0.1.0", skill="project-audit")
        self.assertIn("SKILL_DEFINITION_MISSING_OR_INVALID", result["problems"])
        self.assertIn("SKILL_VERSION_FILE_MISSING_OR_INVALID", result["problems"])

    def test_independent_skill_historical_version(self):
        first = self.add_skill_version()
        self.git("tag", "-a", "project-audit/v0.0.1", "-m", "First version fixture")
        self.add_skill_version(version="0.0.2")
        self.assertEqual(inspect_module.inspect(self.repo, "0.0.1", commit=first,
                                                skill="project-audit")["inspection_status"], "PASS")
        self.assertIn("VERSION_MISMATCH",
                      inspect_module.inspect(self.repo, "0.0.1", skill="project-audit")["problems"])

    def test_independent_skill_rejects_invalid_or_ambiguous_scope(self):
        for name in ("", "../escape", "alpha/beta", "Alpha"):
            with self.subTest(name=name), self.assertRaisesRegex(inspect_module.InspectionError, "SKILL_SCOPE_INVALID"):
                inspect_module.inspect(self.repo, "0.0.1", skill=name)
        with self.assertRaisesRegex(inspect_module.InspectionError, "SKILL_SCOPE_INVALID"):
            inspect_module.inspect(self.repo, "0.0.1", prefix="legacy/", skill="project-audit")

    def test_independent_skill_version_symlink_rejected(self):
        self.add_skill_version()
        file = self.repo / "skills/project-audit/VERSION"
        file.unlink()
        try:
            file.symlink_to("../../VERSION")
        except (OSError, NotImplementedError):
            self.skipTest("symlink unavailable")
        self.git("add", "skills/project-audit/VERSION")
        self.git("commit", "-qm", "Symlink fixture")
        self.git("tag", "-a", "project-audit/v0.1.0", "-m", "Symlink fixture")
        result = inspect_module.inspect(self.repo, "0.1.0", skill="project-audit")
        self.assertIn("SKILL_VERSION_FILE_MISSING_OR_INVALID", result["problems"])

    def test_dirty_worktree_does_not_fake_release_readiness(self):
        self.git("tag", "-a", "v0.1.0", "-m", "Релиз 0.1.0 — проверка")
        (self.repo / "UNTRACKED").write_text("changed", encoding="utf-8")
        r = inspect_module.inspect(self.repo, "0.1.0")
        self.assertFalse(r["worktree_clean"])
        self.assertEqual(r["release_readiness"], "NOT_VERIFIED")

    def test_invalid_input_rejected(self):
        for version in ("", "v0.1.0", "01.1.0", "0.1.-1"):
            with self.subTest(version=version):
                with self.assertRaises(inspect_module.InspectionError):
                    inspect_module.tag_name(version)
        with self.assertRaises(inspect_module.InspectionError):
            inspect_module.tag_name("0.1.0", "bad prefix/")

    def test_nested_directory_rejected(self):
        nested = self.repo / "nested"
        nested.mkdir()
        with self.assertRaisesRegex(inspect_module.InspectionError, "корень"):
            inspect_module.inspect(nested, "0.1.0")

    def test_commit_parameter_requires_full_sha(self):
        with self.assertRaisesRegex(inspect_module.InspectionError, "полный SHA"):
            inspect_module.inspect(self.repo, "0.1.0", commit="HEAD")

    def test_nested_annotated_tag_rejected(self):
        self.git("tag", "-a", "inner", "-m", "inner annotation")
        self.git("tag", "-a", "v0.1.0", "-m", "outer annotation", "inner")
        r = inspect_module.inspect(self.repo, "0.1.0")
        self.assertEqual(r["inspection_status"], "BLOCKED")
        self.assertIn("TAG_TARGET_NOT_COMMIT", r["problems"])

    def test_alias_tag_name_rejected(self):
        self.git("tag", "-a", "other", "-m", "other annotation")
        self.git("update-ref", "refs/tags/v0.1.0", self.git("rev-parse", "refs/tags/other"))
        r = inspect_module.inspect(self.repo, "0.1.0")
        self.assertIn("TAG_NAME_MISMATCH", r["problems"])

    def test_replacement_commit_not_used(self):
        self.git("tag", "-a", "v0.1.0", "-m", "first annotation")
        (self.repo / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        self.git("add", "VERSION")
        self.git("commit", "-qm", "replacement")
        self.git("replace", self.first_sha, self.git("rev-parse", "HEAD"))
        r = inspect_module.inspect(self.repo, "0.1.0", commit=self.first_sha)
        self.assertEqual(r["inspection_status"], "PASS")
        self.assertEqual(r["version_in_commit"], "0.1.0")

    def test_inherited_git_context_rejected(self):
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_CONFIG_COUNT", "GIT_REPLACE_REF_BASE",
                    "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0", "GIT_CONFIG_KEY_unexpected"):
            with self.subTest(key=key), patch.dict(os.environ, {key: "unexpected"}):
                with self.assertRaisesRegex(inspect_module.InspectionError, "GIT_CONTEXT_UNSAFE"):
                    inspect_module.inspect(self.repo, "0.1.0")

    def test_context_names_never_echo_unknown_suffixes_or_values(self):
        with patch.dict(os.environ, {"GIT_CONFIG_COUNT": "synthetic private value",
                                     "GIT_CONFIG_KEY_0": "synthetic private value",
                                     "GIT_CONFIG_VALUE_private_marker": "synthetic private value",
                                     "GIT_PAGER": "synthetic private value"}, clear=True):
            self.assertEqual(inspect_module.blocking_context_names(),
                             ["GIT_CONFIG_COUNT", "GIT_CONFIG_INDEXED_OTHER", "GIT_CONFIG_KEY_0"])
            with patch.object(inspect_module.subprocess, "run") as run:
                with self.assertRaisesRegex(inspect_module.InspectionError, "GIT_CONTEXT_UNSAFE"):
                    inspect_module.git(self.repo, "status")
                run.assert_not_called()

    def test_local_git_minimal_environment_and_timeout(self):
        with patch.dict(os.environ, {"TESSERA_PRIVATE_MARKER": "synthetic",
                                     "SSH_AUTH_SOCK": "synthetic", "GIT_AUTHOR_NAME": "synthetic"}):
            with patch.object(inspect_module.subprocess, "run") as run:
                run.return_value = subprocess.CompletedProcess([], 0, "ok", "")
                inspect_module.git(self.repo, "status")
                args, kwargs = run.call_args
                self.assertIn("--no-replace-objects", args[0])
                self.assertIn("--no-optional-locks", args[0])
                self.assertEqual(kwargs["timeout"], 30)
                for key in ("TESSERA_PRIVATE_MARKER", "SSH_AUTH_SOCK", "GIT_AUTHOR_NAME"):
                    self.assertNotIn(key, kwargs["env"])
                self.assertIn("TESSERA_PRIVATE_MARKER", os.environ)
                run.side_effect = subprocess.TimeoutExpired("git", 30)
                with self.assertRaisesRegex(inspect_module.InspectionError, "TIMEOUT"):
                    inspect_module.git(self.repo, "status")

    def test_tag_ref_change_detected(self):
        self.git("tag", "-a", "v0.1.0", "-m", "first annotation")
        actual = inspect_module.git
        def moved(repo, *args, **kwargs):
            result = actual(repo, *args, **kwargs)
            if args[:2] == ("cat-file", "-p"):
                self.git("tag", "-f", "-a", "v0.1.0", "-m", "different annotation")
            return result
        with patch.object(inspect_module, "git", side_effect=moved):
            r = inspect_module.inspect(self.repo, "0.1.0")
        self.assertIn("TAG_REF_CHANGED", r["problems"])

    def test_current_head_change_detected(self):
        self.git("tag", "-a", "v0.1.0", "-m", "first annotation")
        actual = inspect_module.git
        def moved(repo, *args, **kwargs):
            result = actual(repo, *args, **kwargs)
            if args[:2] == ("cat-file", "-p"):
                self.git("commit", "--allow-empty", "-qm", "fixture new HEAD")
            return result
        with patch.object(inspect_module, "git", side_effect=moved):
            r = inspect_module.inspect(self.repo, "0.1.0")
        self.assertIn("HEAD_CHANGED", r["problems"])

    def test_commit_parameter_rejects_tag_object_sha(self):
        self.git("tag", "-a", "v0.1.0", "-m", "first annotation")
        with self.assertRaisesRegex(inspect_module.InspectionError, "COMMIT_SHA_NOT_DIRECT"):
            inspect_module.inspect(self.repo, "0.1.0", commit=self.git("rev-parse", "refs/tags/v0.1.0"))

    def test_inspection_never_creates_tag(self):
        before = self.git("tag", "-l")
        inspect_module.inspect(self.repo, "0.1.0")
        self.assertEqual(self.git("tag", "-l"), before)


if __name__ == "__main__":
    unittest.main()
