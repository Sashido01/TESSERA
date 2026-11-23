import importlib.util
import pathlib
import tempfile
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / "tools" / "check_repository_version.py"
spec = importlib.util.spec_from_file_location("repo_version_check", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RepositoryVersionTests(unittest.TestCase):
    def test_expected_work_microversions(self):
        cases = [
            ("0.0.0", "0.0.1"),
            ("0.0.98", "0.0.99"),
            ("0.0.99", "0.0.100"),
            ("0.0.100", "0.0.101"),
            ("0.99.99", "0.99.100"),
            ("1.0.99", "1.0.100"),
        ]
        for old, new in cases:
            with self.subTest(old=old):
                self.assertEqual(module.check_transition(old, new), [])

    def test_release_milestones(self):
        cases = [
            ("0.0.99", "0.1.0"),
            ("0.0.107", "0.1.0"),
            ("0.1.99", "0.2.0"),
            ("0.99.99", "1.0.0"),
            ("0.99.151", "1.0.0"),
            ("1.99.100", "2.0.0"),
        ]
        for old, new in cases:
            with self.subTest(old=old):
                self.assertEqual(module.check_transition(old, new), [])

    def test_rejects_skips_and_early_release(self):
        for old, new in [
            ("0.0.4", "0.0.6"),
            ("0.0.4", "0.1.0"),
            ("0.0.98", "0.1.0"),
            ("0.0.99", "0.1.1"),
            ("0.0.100", "0.0.100"),
            ("0.99.98", "1.0.0"),
        ]:
            with self.subTest(old=old, new=new):
                self.assertTrue(module.check_transition(old, new))

    def test_bootstrap_requires_first_microversion(self):
        self.assertEqual(module.check_transition(None, "0.0.1"), [])
        self.assertTrue(module.check_transition(None, "0.0.0"))
        self.assertTrue(module.check_transition(None, "0.1.0"))

    def test_invalid_version_strings(self):
        for value in ("", "0.0", "v0.0.1", "01.0.1", "0.100.1", "0.0.-1"):
            with self.subTest(value=value):
                self.assertTrue(module.check_transition("0.0.0", value))

    def test_changelog_both_languages_required(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            (root / "CHANGELOG.md").write_text("## 0.0.1 — Изменения\n", encoding="utf-8")
            self.assertTrue(module.check_changelogs(root, "0.0.1"))
            (root / "CHANGELOG.en.md").write_text("## 0.0.1 — Updates\n", encoding="utf-8")
            self.assertEqual(module.check_changelogs(root, "0.0.1"), [])

    def test_commit_is_human_readable_russian(self):
        self.assertEqual(module.check_commit_title("Закреплена микроверсионность каталога"), [])
        self.assertTrue(module.check_commit_title("bump: 0.0.1"))
        self.assertTrue(module.check_commit_title("fix: updated"))


if __name__ == "__main__":
    unittest.main()
