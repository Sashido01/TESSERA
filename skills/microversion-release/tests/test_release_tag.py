import os
import pathlib
import sys
import subprocess
import tempfile
import unittest
from unittest import mock

PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "release_tag.py"
# A test must exercise this checkout, not an unrelated installed/cached module.
cached = sys.modules.get("release_tag")
if cached is not None and pathlib.Path(getattr(cached, "__file__", "") or ".").resolve() != PATH:
    raise RuntimeError("Unexpected cached test module")
sys.path.insert(0, str(PATH.parent))
try:
    import release_tag as module
finally:
    sys.path.pop(0)
if pathlib.Path(module.__file__).resolve() != PATH:
    raise RuntimeError("Unexpected test module origin")


class ReleaseTagTests(unittest.TestCase):
    def test_import_origin(self):
        self.assertEqual(pathlib.Path(module.__file__).resolve(), PATH)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = pathlib.Path(self.tmp.name)
        self.cmd("init", "-q")
        self.cmd("config", "user.name", "Test User")
        self.cmd("config", "user.email", "example@example.invalid")
        (self.repo / "README.md").write_text("# Test\n", encoding="utf-8")
        self.cmd("add", "README.md")
        self.cmd("commit", "-qm", "Добавлен проверочный репозиторий")

    def cmd(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True, text=True).stdout.strip()

    def test_missing_tag_rejected(self):
        with self.assertRaisesRegex(module.TagError, "RELEASE_NOT_TAGGED"):
            module.verify(self.repo, "0.1.0")

    def test_create_and_verify_annotated(self):
        sha = module.create(self.repo, "0.1.0", "Релиз 0.1.0 — проверена работа приложения")
        self.assertEqual(sha, module.verify(self.repo, "0.1.0"))
        self.assertEqual(self.cmd("cat-file", "-t", "refs/tags/v0.1.0"), "tag")
        self.assertEqual(sha, module.create(self.repo, "0.1.0", "Релиз повторно не создаётся"))

    def test_lightweight_tag_rejected(self):
        self.cmd("tag", "v0.1.0")
        with self.assertRaisesRegex(module.TagError, "не аннотирован"):
            module.verify(self.repo, "0.1.0")

    def test_wrong_target_rejected(self):
        module.create(self.repo, "0.1.0", "Релиз 0.1.0 — первая запись")
        (self.repo / "new.txt").write_text("changed", encoding="utf-8")
        self.cmd("add", "new.txt")
        self.cmd("commit", "-qm", "Добавлен дополнительный файл")
        with self.assertRaisesRegex(module.TagError, "не на HEAD"):
            module.verify(self.repo, "0.1.0")

    def test_namespaced_tag(self):
        sha = module.create(self.repo, "1.0.0", "Релиз навыка — закончена проверка", "microversion-release/")
        self.assertEqual(module.verify(self.repo, "1.0.0", "microversion-release/"), sha)

    def test_invalid_release_version(self):
        for number in ("0.0.0", "0.0.99", "0.0.100", "0.1.1", "v0.1.0", "../0.1.0"):
            with self.subTest(number=number):
                with self.assertRaises(module.TagError):
                    module.name_for(number)

    def test_existing_incorrect_tag_never_overwritten(self):
        self.cmd("tag", "v0.1.0")
        with self.assertRaisesRegex(module.TagError, "не аннотирован"):
            module.create(self.repo, "0.1.0", "Релиз 0.1.0 — всё готово")
        self.assertEqual(self.cmd("cat-file", "-t", "refs/tags/v0.1.0"), "commit")

    def test_expected_head_mismatch_refuses_before_tagging(self):
        previous = self.cmd("rev-parse", "HEAD")
        self.cmd("commit", "--allow-empty", "-qm", "Новый коммит")
        with self.assertRaisesRegex(module.TagError, "проверенным коммитом"):
            module.create(self.repo, "0.1.0", "Релиз — проверка SHA", expected_head=previous)
        self.assertEqual(self.cmd("tag", "--list", "v0.1.0"), "")

    def test_moved_head_does_not_tag_unverified_commit(self):
        previous = self.cmd("rev-parse", "HEAD")
        original = module.git

        def move_head(repo, *args, **kwargs):
            if args[0] == "tag":
                self.cmd("commit", "--allow-empty", "-qm", "Конкурентное изменение")
            return original(repo, *args, **kwargs)

        with mock.patch.object(module, "git", side_effect=move_head):
            with self.assertRaisesRegex(module.TagError, "проверенным коммитом"):
                module.create(self.repo, "0.1.0", "Релиз — проверка гонки")
        self.assertEqual(self.cmd("rev-parse", "refs/tags/v0.1.0^{commit}"), previous)
        self.assertNotEqual(self.cmd("rev-parse", "HEAD"), previous)

    def test_nested_tag_rejected(self):
        self.cmd("tag", "-a", "inner", "-m", "Внутренний тег")
        self.cmd("tag", "-a", "v0.1.0", "-m", "Внешний тег", "inner")
        with self.assertRaisesRegex(module.TagError, "не на HEAD напрямую"):
            module.verify(self.repo, "0.1.0")

    def test_alias_of_different_annotated_tag_rejected(self):
        self.cmd("tag", "-a", "other", "-m", "Другой тег")
        self.cmd("update-ref", "refs/tags/v0.1.0", self.cmd("rev-parse", "refs/tags/other"))
        with self.assertRaisesRegex(module.TagError, "имя объекта"):
            module.verify(self.repo, "0.1.0")

    def test_inherited_git_dir_and_worktree_cannot_redirect_tag(self):
        with tempfile.TemporaryDirectory() as folder:
            other = pathlib.Path(folder).resolve()
            subprocess.run(["git", "-C", str(other), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(other), "-c", "user.name=Test User",
                            "-c", "user.email=example@example.invalid", "commit",
                            "--allow-empty", "-qm", "Other fixture"], check=True)
            with mock.patch.dict(os.environ, {"GIT_DIR": str(other / ".git"),
                                              "GIT_WORK_TREE": str(self.repo.resolve())}):
                with self.assertRaisesRegex(module.TagError, "внешнее окружение"):
                    module.create(self.repo, "0.1.0", "Релиз — проверка окружения")
            self.assertEqual(self.cmd("tag", "--list"), "")
            result = subprocess.run(["git", "-C", str(other), "tag", "--list"],
                                    check=True, capture_output=True, text=True)
            self.assertEqual(result.stdout.strip(), "")

    def test_inherited_git_config_override_rejected(self):
        for overrides in ({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.worktree",
                           "GIT_CONFIG_VALUE_0": str(self.repo)},
                          {"GIT_NAMESPACE": "fixture"}, {"GIT_OBJECT_DIRECTORY": "fixture"}):
            with self.subTest(overrides=tuple(overrides)), mock.patch.dict(os.environ, overrides):
                with self.assertRaisesRegex(module.TagError, "внешнее окружение"):
                    module.verify(self.repo, "0.1.0")

    def test_git_child_receives_only_required_environment(self):
        with mock.patch.dict(os.environ, {"TESSERA_PRIVATE_FIXTURE": "synthetic marker",
                                          "GIT_COMMITTER_NAME": "Test Identity",
                                          "GIT_CONFIG_KEY_0": "core.worktree"}):
            with mock.patch.object(module.subprocess, "run") as run:
                run.return_value = subprocess.CompletedProcess([], 0, "", "")
                module.git(self.repo, "rev-parse", "HEAD")
                env = run.call_args.kwargs["env"]
                self.assertNotIn("TESSERA_PRIVATE_FIXTURE", env)
                self.assertNotIn("GIT_CONFIG_KEY_0", env)
                self.assertEqual(env["GIT_COMMITTER_NAME"], "Test Identity")
                self.assertEqual(set(env) - set(module.CHILD_ENV_KEYS), set())
                self.assertEqual(os.getenv("TESSERA_PRIVATE_FIXTURE"), "synthetic marker")


    def test_git_lookup_ignores_empty_and_relative_path(self):
        with self.assertRaisesRegex(module.TagError, "GIT_EXECUTABLE_NOT_FOUND"):
            module.git_executable({"PATH": os.pathsep.join(("", ".", "relative"))})

    def test_git_invocation_uses_absolute_executable_and_timeout(self):
        with mock.patch.object(module.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "", "")
            module.git(self.repo, "rev-parse", "HEAD")
            argv = run.call_args.args[0]
            kwargs = run.call_args.kwargs
            self.assertTrue(pathlib.Path(argv[0]).is_absolute())
            self.assertEqual(kwargs["timeout"], module.GIT_TIMEOUT)
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
            self.assertIs(kwargs["shell"], False)

    def test_git_timeout_does_not_expose_diagnostics(self):
        with mock.patch.object(module.subprocess, "run", side_effect=subprocess.TimeoutExpired(
                ["git"], 60, output=b"synthetic private stdout", stderr=b"synthetic private stderr")):
            with self.assertRaisesRegex(module.TagError, "GIT_TIMEOUT") as caught:
                module.git(self.repo, "rev-parse", "HEAD")
            self.assertNotIn("synthetic private", str(caught.exception))

    def test_git_failure_does_not_expose_diagnostics(self):
        with mock.patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess(
                [], 1, "synthetic private stdout", "synthetic private stderr")):
            with self.assertRaisesRegex(module.TagError, "GIT_EXECUTION_FAILED") as caught:
                module.git(self.repo, "rev-parse", "HEAD")
            self.assertNotIn("synthetic private", str(caught.exception))

    def test_git_output_limit_applies_even_if_failure_allowed(self):
        with mock.patch.object(module, "MAX_GIT_OUTPUT", 10), mock.patch.object(
                module.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "123456", "12345")):
            with self.assertRaisesRegex(module.TagError, "GIT_OUTPUT_LIMIT"):
                module.git(self.repo, "rev-parse", "HEAD", check=False)

    def test_git_unavailable_fails_closed(self):
        with mock.patch.object(module, "git_executable", side_effect=OSError("synthetic private path")):
            with self.assertRaisesRegex(module.TagError, "GIT_EXECUTION_FAILED") as caught:
                module.git(self.repo, "rev-parse", "HEAD")
            self.assertNotIn("synthetic private", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
