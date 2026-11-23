import importlib.util
import pathlib
import subprocess
import sys
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "next_version.py"
spec = importlib.util.spec_from_file_location("next_version", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class VersionTests(unittest.TestCase):
    def test_work_commits_continue_past_99(self):
        pairs = {
            "0.0.0": "0.0.1",
            "0.0.98": "0.0.99",
            "0.0.99": "0.0.100",
            "0.0.100": "0.0.101",
            "0.1.99": "0.1.100",
            "0.99.99": "0.99.100",
            "0.1.130": "0.1.131",
            "v3.21.44": "3.21.45",
        }
        for source, expected in pairs.items():
            with self.subTest(source=source):
                self.assertEqual(module.next_version(source), expected)

    def test_release_after_finished_task(self):
        pairs = {
            "0.0.99": "0.1.0",
            "0.0.100": "0.1.0",
            "0.0.115": "0.1.0",
            "0.1.99": "0.2.0",
            "0.1.130": "0.2.0",
            "0.98.99": "0.99.0",
            "0.99.99": "1.0.0",
            "0.99.147": "1.0.0",
            "1.0.99": "1.1.0",
            "1.99.105": "2.0.0",
        }
        for source, expected in pairs.items():
            with self.subTest(source=source):
                self.assertEqual(module.next_version(source, mode="release"), expected)

    def test_work_commits_do_not_force_release(self):
        current = "0.0.98"
        for expected in ("0.0.99", "0.0.100", "0.0.101", "0.0.102"):
            current = module.next_version(current, mode="work")
            self.assertEqual(current, expected)
        self.assertEqual(module.next_version(current, mode="release"), "0.1.0")

    def test_normal_100_commit_cycle_with_release(self):
        current = "0.0.0"
        for _ in range(99):
            current = module.next_version(current)
        self.assertEqual(current, "0.0.99")
        self.assertEqual(module.next_version(current, mode="release"), "0.1.0")

    def test_no_early_release(self):
        for source in ("0.0.0", "0.0.98", "0.1.1"):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    module.next_version(source, mode="release")

    def test_invalid(self):
        for source in ("", "1", "1.2", "1.2.3.4", "x1.2.3", "1.-1.3", "1.100.1", "01.0.0"):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    module.next_version(source)
        with self.assertRaises(ValueError):
            module.next_version("0.0.99", mode="unknown")

    def test_cli_mode(self):
        for args, expected in (
            (["0.0.99"], "0.0.100"),
            (["v0.0.99", "--mode", "release"], "0.1.0"),
            (["0.99.105", "--mode", "release"], "1.0.0"),
        ):
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, str(PATH), *args], capture_output=True, text=True
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), expected)


if __name__ == "__main__":
    unittest.main()
