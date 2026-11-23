import importlib.util
import pathlib
import subprocess
import tempfile
import unittest

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

    def test_inspection_never_creates_tag(self):
        before = self.git("tag", "-l")
        inspect_module.inspect(self.repo, "0.1.0")
        self.assertEqual(self.git("tag", "-l"), before)


if __name__ == "__main__":
    unittest.main()
