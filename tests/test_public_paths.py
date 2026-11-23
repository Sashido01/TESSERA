import importlib.util
import pathlib
import tempfile
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / "tools" / "check_public_paths.py"
spec = importlib.util.spec_from_file_location("check_public_paths", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PublicPathsTests(unittest.TestCase):
    def test_repository_contains_no_absolute_paths(self):
        self.assertEqual(module.scan(PATH.parents[1]), [])

    def test_rejects_drive_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "README.md").write_text("Рабочая папка: X:\\private\\project\n", encoding="utf-8")
            self.assertEqual(len(module.scan(root)), 1)

    def test_rejects_home_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "README.md").write_text("Папка: /home/someone/projects/\n", encoding="utf-8")
            self.assertEqual(len(module.scan(root)), 1)

    def test_ignores_external_pinned_validator_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            external = root / ".external" / "agentskills"
            external.mkdir(parents=True)
            (external / "README.md").write_text("External test-only path: X:\\\\private\\\\project", encoding="utf-8")
            self.assertEqual(module.scan(root), [])

    def test_allows_placeholders(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "README.md").write_text("Каталог: <project-root>/skills/\n", encoding="utf-8")
            self.assertEqual(module.scan(root), [])


if __name__ == "__main__":
    unittest.main()
