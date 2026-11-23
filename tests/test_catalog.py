import importlib.util
import pathlib
import tempfile
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / "tools" / "validate_skills.py"
spec = importlib.util.spec_from_file_location("validate_skills", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CatalogTests(unittest.TestCase):
    def test_real_catalog(self):
        self.assertEqual(module.validate(PATH.parents[1]), [])

    def test_missing_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / "skills" / "example").mkdir(parents=True)
            self.assertTrue(module.validate(root))

    def test_valid_minimal_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            folder = root / "skills" / "example"
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text(
                "---\nname: example\ndescription: Explains something.\n---\n\n# Example\n",
                encoding="utf-8",
            )
            (folder / "README.md").write_text("# Example\n", encoding="utf-8")
            self.assertEqual(module.validate(root), [])

    def test_name_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            folder = root / "skills" / "example"
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text(
                "---\nname: wrong\ndescription: A test.\n---\n", encoding="utf-8"
            )
            (folder / "README.md").write_text("# Example\n", encoding="utf-8")
            self.assertTrue(any("name" in e for e in module.validate(root)))


if __name__ == "__main__":
    unittest.main()
