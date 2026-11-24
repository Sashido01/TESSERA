import pathlib
import sys
import tempfile
import unittest
from unittest import mock

PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "install.py"
# A test must exercise this checkout, not an unrelated installed/cached module.
cached = sys.modules.get("install")
if cached is not None and pathlib.Path(getattr(cached, "__file__", "") or ".").resolve() != PATH:
    raise RuntimeError("Unexpected cached test module")
sys.path.insert(0, str(PATH.parent))
try:
    import install as module
finally:
    sys.path.pop(0)
if pathlib.Path(module.__file__).resolve() != PATH:
    raise RuntimeError("Unexpected test module origin")


class InstallerTests(unittest.TestCase):
    def test_import_origin(self):
        self.assertEqual(pathlib.Path(module.__file__).resolve(), PATH)

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

    def make_link(self, link, target, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable")

    def test_project_parent_link_refused_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory).resolve()
            project, outside = base / "project", base / "outside"
            project.mkdir()
            outside.mkdir()
            self.make_link(project / ".agents", outside, directory=True)
            for apply in (False, True):
                with self.subTest(apply=apply):
                    with self.assertRaises(module.InstallError):
                        module.run("codex", project, None, apply)
                    self.assertEqual(list(outside.iterdir()), [])

    def test_dangling_project_parent_link_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory).resolve()
            self.make_link(root / ".dsh", root / "missing", directory=True)
            with self.assertRaises(module.InstallError):
                module.run("harness", root, None, True)
            self.assertFalse((root / "missing").exists())

    def test_source_links_refused_in_dry_run_and_apply(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory).resolve()
            src, project, external = root / "source", root / "project", root / "external"
            src.mkdir()
            project.mkdir()
            external.mkdir()
            (src / "scripts").mkdir()
            (src / "SKILL.md").write_text("test", encoding="utf-8")
            (external / "marker.txt").write_text("synthetic", encoding="utf-8")
            for is_dir, target in ((False, external / "marker.txt"), (True, external)):
                with self.subTest(is_dir=is_dir):
                    link = src / "scripts" / "linked"
                    self.make_link(link, target, directory=is_dir)
                    try:
                        with mock.patch.object(module, "__file__", str(src / "scripts" / "install.py")):
                            for apply in (False, True):
                                with self.assertRaises(module.InstallError):
                                    module.run("codex", project, None, apply)
                        self.assertFalse((project / ".agents").exists())
                    finally:
                        link.unlink()


if __name__ == "__main__":
    unittest.main()
