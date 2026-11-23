import importlib.util
import pathlib
import tempfile
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "install.py"
spec = importlib.util.spec_from_file_location("skill_installer", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InstallerTests(unittest.TestCase):
    def test_platform_directory_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            for platform, expected in (
                ("codex", ".agents/skills"), ("harness", ".dsh/skills"),
                ("claude", ".claude/skills"), ("hermes", ".hermes/skills"),
                ("shared", ".agents/skills"),
            ):
                with self.subTest(platform=platform):
                    got = module.destination(platform, root, None)
                    self.assertEqual(got, root / expected / "microversion-release")

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            target = module.run("codex", root, None, False)
            self.assertFalse(target.exists())

    def test_real_install_is_explicit_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            target = module.run("claude", root, None, True)
            self.assertTrue((target / "SKILL.md").is_file())
            with self.assertRaises(module.InstallError):
                module.run("claude", root, None, True)

    def test_generic_requires_explicit_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            with self.assertRaises(module.InstallError):
                module.destination("generic", root, None)
            self.assertEqual(module.destination("generic", None, root), root / "microversion-release")

    def test_ambiguous_target_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            with self.assertRaises(module.InstallError):
                module.destination("codex", root, root)


if __name__ == "__main__":
    unittest.main()
