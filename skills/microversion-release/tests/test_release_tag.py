import importlib.util
import pathlib
import subprocess
import tempfile
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "release_tag.py"
spec = importlib.util.spec_from_file_location("release_tag", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReleaseTagTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
