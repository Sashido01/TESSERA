"""Offline namespace report contract; live preflight is a separate Linux CI step."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_namespace_preflight as p


class NamespaceTests(unittest.TestCase):
    def report(self):
        return {"pid": 1, "network": "net:[123]", "blocked": True,
                "limits": {k: [v, v] for k, v in p.LIMITS.items()}}

    def test_valid_report(self):
        p.validate(self.report(), "net:[456]")

    def test_parent_network_or_unproven_block_rejected(self):
        for change in ({"network": "net:[456]"}, {"blocked": False}, {"network": "invalid"}):
            with self.subTest(change=change), self.assertRaisesRegex(RuntimeError, "NAMESPACE_CONTROL_FAILED"):
                p.validate({**self.report(), **change}, "net:[456]")

    def test_wrong_pid_or_limits_rejected(self):
        for change in ({"pid": 2}, {"limits": {}}, {"limits": {"CPU": [10, 11]}}):
            with self.subTest(change=change), self.assertRaisesRegex(RuntimeError, "NAMESPACE_CONTROL_FAILED"):
                p.validate({**self.report(), **change}, "net:[456]")

    def test_command_requires_namespace_and_hard_limits(self):
        argv = p.command("pass")
        self.assertEqual(argv[0], "/usr/bin/unshare")
        for option in ("--user", "--net", "--pid", "--fork", "--kill-child=SIGKILL", "/usr/bin/prlimit"):
            self.assertIn(option, argv)
        for key, value in p.LIMITS.items():
            self.assertIn(f"--{key.lower()}={value}:{value}", argv)


if __name__ == "__main__":
    unittest.main()
