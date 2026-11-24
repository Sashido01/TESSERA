import pathlib
import subprocess
import sys
import tempfile
import unittest

RUNNER = pathlib.Path(__file__).resolve().parents[1] / "tools" / "run_skill_tests.py"


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "skills").mkdir()

    def add(self, name, *, passing=True, tests=True):
        skill = self.root / "skills" / name
        skill.mkdir()
        if tests:
            folder = skill / "tests"
            folder.mkdir()
            (folder / "test_example.py").write_text(
                "import unittest\nclass Example(unittest.TestCase):\n"
                f"    def test_case(self): self.assertTrue({passing})\n", encoding="utf-8")
        return skill

    def invoke(self):
        return subprocess.run([sys.executable, "-B", str(RUNNER), "--repo", str(self.root), "-q"],
                              capture_output=True, text=True, check=False)

    def test_two_skills_same_test_filename(self):
        self.add("alpha")
        self.add("beta")
        r = self.invoke()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("alpha: RUN", r.stdout)
        self.assertIn("beta: RUN", r.stdout)
        self.assertEqual(r.stderr.count("Ran 1 test"), 2)

    def test_failure_does_not_skip_independent_skill(self):
        self.add("alpha", passing=False)
        self.add("beta")
        r = self.invoke()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("beta: RUN", r.stdout)

    def test_instruction_only_skill(self):
        self.add("alpha", tests=False)
        self.add("beta")
        r = self.invoke()
        self.assertEqual(r.returncode, 0)
        self.assertIn("alpha: NO_AUTOMATED_TESTS", r.stdout)

    def test_no_tests_fails(self):
        self.add("alpha", tests=False)
        self.assertNotEqual(self.invoke().returncode, 0)

    def test_empty_tests_directory_fails(self):
        (self.add("alpha", tests=False) / "tests").mkdir()
        self.assertNotEqual(self.invoke().returncode, 0)

    def test_no_discovered_tests_fails(self):
        skill = self.add("alpha")
        (skill / "tests" / "test_example.py").write_text("# no actual tests\n", encoding="utf-8")
        r = self.invoke()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("SKILL_TEST_NONE_DISCOVERED", r.stderr)

    def test_all_skipped_tests_fail(self):
        skill = self.add("alpha")
        (skill / "tests" / "test_example.py").write_text(
            'import unittest\nclass Example(unittest.TestCase):\n'
            '    @unittest.skip("unavailable")\n    def test_case(self): pass\n', encoding="utf-8")
        r = self.invoke()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("SKILL_TEST_NO_ORDINARY_EXECUTION", r.stderr)

    def test_expected_failure_only_fails(self):
        skill = self.add("alpha")
        (skill / "tests" / "test_example.py").write_text(
            'import unittest\nclass Example(unittest.TestCase):\n'
            '    @unittest.expectedFailure\n    def test_case(self): self.fail("known failure")\n', encoding="utf-8")
        r = self.invoke()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("SKILL_TEST_NO_ORDINARY_EXECUTION", r.stderr)

    def test_mixed_pass_and_skip_passes(self):
        skill = self.add("alpha")
        with (skill / "tests" / "test_example.py").open("a", encoding="utf-8") as f:
            f.write('    @unittest.skip("unavailable")\n    def test_optional(self): pass\n')
        self.assertEqual(self.invoke().returncode, 0)

    def test_symlink_tests_rejected(self):
        alpha = self.add("alpha")
        beta = self.add("beta", tests=False)
        try:
            (beta / "tests").symlink_to(alpha / "tests", target_is_directory=True)
        except OSError:
            self.skipTest("symlink unavailable")
        self.assertNotEqual(self.invoke().returncode, 0)


if __name__ == "__main__":
    unittest.main()
