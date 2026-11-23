import importlib.util
import pathlib
import tempfile
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / "tools" / "check_translations.py"
spec = importlib.util.spec_from_file_location("check_translations", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TranslationCoverageTests(unittest.TestCase):
    def test_repository_translation_pairs(self):
        self.assertEqual(module.validate(PATH.parents[1]), [])

    def test_missing_english_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            for name in module.ROOT_DOCS:
                original = root / name
                original.parent.mkdir(parents=True, exist_ok=True)
                original.write_text("# Русский\n", encoding="utf-8")
            self.assertTrue(any("Нет английского перевода" in e for e in module.validate(root)))

    def test_new_skill_requires_translation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            folder = root / "skills" / "example"
            folder.mkdir(parents=True)
            discovered = module.pairs(root)
            self.assertIn(folder / "SKILL.md", discovered)
            self.assertEqual(discovered[folder / "SKILL.md"], folder / "references" / "SKILL.en.md")

    def test_orphan_english_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "extra.en.md").write_text("# Translation\n", encoding="utf-8")
            self.assertTrue(any("без русского оригинала" in e for e in module.validate(root)))

    def test_skill_translation_must_not_define_second_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            skill = root / "skills" / "demo"
            refs = skill / "references"
            refs.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "# Навык\n\n[English](references/SKILL.en.md)\n", encoding="utf-8"
            )
            (refs / "SKILL.en.md").write_text(
                "---\nname: demo\n---\n\n[Русский](../SKILL.md)\n", encoding="utf-8"
            )
            self.assertTrue(any("frontmatter" in e for e in module.validate(root)))


if __name__ == "__main__":
    unittest.main()
