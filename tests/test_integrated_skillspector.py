import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import check_integrated_skillspector as s


class IntegratedSkillSpectorTests(unittest.TestCase):
    def test_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder).resolve()
            skill = root / "skills" / "fixture"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("fixture")
            args = ["scan", str(skill), "--format", "json", "--no-llm"]
            self.assertEqual(s.contract(args, root), skill)
            self.assertIsNone(s.contract(["--version"], root))
            for bad in (args[:-1], args+["--baseline", "other"], ["scan", str(root), *args[2:]]):
                with self.assertRaises(RuntimeError):
                    s.contract(bad, root)

    def test_scope_link(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder).resolve()
            skill = root / "fixture"
            skill.mkdir()
            (skill / "SKILL.md").write_text("fixture")
            (root / "skills").mkdir()
            link = root / "skills" / "fixture"
            link.symlink_to(skill, target_is_directory=True)
            with self.assertRaises(RuntimeError):
                s.contract(["scan", str(link), "--format", "json", "--no-llm"], root)

    def test_docker_profile(self):
        args = s.docker_args("fixture", pathlib.PurePosixPath("/fixture-stage"), pathlib.PurePosixPath("/fixture-packages"), "fixture")
        self.assertEqual(args[-5:], ["scan", "/stage/fixture", "--format", "json", "--no-llm"])
        for flag in ("--network=none", "--read-only", "--cap-drop=ALL", "--memory=1g"):
            self.assertIn(flag, args)
        self.assertEqual(args.count("--mount"), 2)
        with self.assertRaises(RuntimeError):
            s.docker_args("fixture", pathlib.PurePosixPath("/fixture"), pathlib.PurePosixPath("/fixture/packages"), None)

    def test_report_coverage(self):
        good = {"analysis_status": "complete", "missing_files": 0, "coverage_percent": 100}
        with mock.patch.object(s, "summary", return_value=good):
            self.assertEqual(s.checked_report(0, b"{}", {}), good)
        for bad in ({**good, "missing_files": 1}, {**good, "coverage_percent": 99},
                    {**good, "analysis_status": "partial"}):
            with mock.patch.object(s, "summary", return_value=bad), self.assertRaises(RuntimeError):
                s.checked_report(0, b"{}", {})

    def test_cleanup_timeout(self):
        with mock.patch.object(s, "invoke", side_effect=[(0, b""), TimeoutError(), (0, b"")]) as run:
            with self.assertRaises(TimeoutError):
                s.run_container(pathlib.PurePosixPath("/fixture-stage"), pathlib.PurePosixPath("/fixture-home"),
                                pathlib.PurePosixPath("/fixture-packages"), None)
            self.assertEqual(run.call_args_list[-1].args[0][:2], ["rm", "--force"])


if __name__ == "__main__":
    unittest.main()
