"""T11.01: fail-closed wrapper tests for the pinned upstream skills-ref CLI."""
from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reference_runner", ROOT / "tools" / "check_reference_skills.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReferenceRunnerTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = pathlib.Path(tmp.name).resolve()
        self.root = base / "project"
        self.source = base / "upstream" / "skills-ref" / "src"
        self.root.mkdir()
        self.source.mkdir(parents=True)
        package = self.source / "skills_ref"
        package.mkdir()
        for name in ("__init__.py", "cli.py", "validator.py", "parser.py"):
            (package / name).write_text("# reference fixture\n", encoding="utf-8")
        self.skill = self.root / "skills" / "microversion-release"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("---\nname: microversion-release\n"
                                              "description: Test\n---\n", encoding="utf-8")
        self.calls = []

    def good(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, "Valid skill: fixture\n", "")

    def inspect(self, runner=None):
        return module.inspect(self.root, self.source, runner=runner or self.good)

    def test_passing_reference_check_is_explicit_and_sandboxed(self):
        self.assertEqual(self.inspect(), [])
        self.assertEqual(len(self.calls), 1)
        argv, kwargs = self.calls[0]
        self.assertEqual(argv[1:5], ["-P", "-m", "skills_ref.cli", "validate"])
        self.assertEqual(argv[-1], str(self.skill))
        self.assertEqual(kwargs["env"]["PYTHONPATH"], str(self.source))
        self.assertEqual(kwargs["env"]["PYTHONSAFEPATH"], "1")
        self.assertEqual(kwargs["env"]["PYTHONNOUSERSITE"], "1")
        self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
        self.assertTrue(kwargs["capture_output"])
        self.assertFalse(kwargs["check"])
        self.assertEqual(kwargs["timeout"], module.TIMEOUT)

    def test_missing_upstream_source_rejected(self):
        self.assertIn("REFERENCE_ROOT_OR_SOURCE_MISSING",
                      module.inspect(self.root, self.source / "missing", runner=self.good))
        self.assertFalse(self.calls)

    def test_incomplete_upstream_rejected(self):
        (self.source / "skills_ref" / "validator.py").unlink()
        self.assertEqual(self.inspect(), ["REFERENCE_UPSTREAM_SOURCE_INVALID"])
        self.assertFalse(self.calls)

    def test_missing_skills_rejected(self):
        import shutil
        shutil.rmtree(self.root / "skills")
        self.assertEqual(self.inspect(), ["REFERENCE_SKILLS_DIRECTORY_INVALID"])
        self.assertFalse(self.calls)

    def test_invalid_skill_name_rejected(self):
        self.skill.rename(self.skill.parent / "UPPER")
        self.assertEqual(self.inspect(), ["REFERENCE_SKILL_DIRECTORY_INVALID"])
        self.assertFalse(self.calls)

    def test_symlink_skill_rejected(self):
        destination = self.root / "elsewhere"
        destination.mkdir()
        import shutil
        shutil.rmtree(self.skill)
        try:
            self.skill.symlink_to(destination, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unsupported")
        self.assertEqual(self.inspect(), ["REFERENCE_SKILL_DIRECTORY_INVALID"])
        self.assertFalse(self.calls)

    def test_symlink_skill_file_rejected(self):
        dest = self.root / "source_skill.md"
        (self.skill / "SKILL.md").rename(dest)
        try:
            (self.skill / "SKILL.md").symlink_to(dest)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unsupported")
        self.assertEqual(self.inspect(), ["REFERENCE_SKILL_FILE_INVALID:microversion-release"])
        self.assertFalse(self.calls)

    def test_nonzero_result_rejected(self):
        def failure(argv, **kwargs):
            return subprocess.CompletedProcess(argv, 1, "", "secret user path")
        self.assertEqual(self.inspect(failure), ["REFERENCE_VALIDATION_FAILED:microversion-release"])

    def test_unexpected_success_output_rejected(self):
        def fake(argv, **kwargs):
            return subprocess.CompletedProcess(argv, 0, "not a validator\n", "")
        self.assertEqual(self.inspect(fake), ["REFERENCE_OUTPUT_UNEXPECTED:microversion-release"])

    def test_timeout_rejected(self):
        def timeout(argv, **kwargs):
            raise subprocess.TimeoutExpired(argv, 1)
        self.assertEqual(self.inspect(timeout), ["REFERENCE_TIMEOUT:microversion-release"])

    def test_missing_tool_rejected(self):
        def absent(argv, **kwargs):
            raise FileNotFoundError("test")
        self.assertEqual(self.inspect(absent), ["REFERENCE_EXECUTION_UNAVAILABLE:microversion-release"])

    def test_more_than_100_skills_rejected(self):
        for i in range(100):
            (self.skill.parent / f"test-{i:03}").mkdir()
        self.assertEqual(self.inspect(), ["REFERENCE_SKILL_COUNT_INVALID"])
        self.assertFalse(self.calls)


if __name__ == "__main__":
    unittest.main()
