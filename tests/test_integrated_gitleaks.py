import json
import pathlib
import tempfile
import unittest
import sys
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import check_integrated_gitleaks as g


class IntegratedGitleaksTests(unittest.TestCase):
    def test_argument_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder).resolve()
            cwd = root / "redaction-control"
            cwd.mkdir()
            config = root / "redaction-control.toml"
            config.touch()
            args = g.PREFIX + [str(config), "--no-git"]
            self.assertEqual(g.arguments(args, cwd, root), config)
            self.assertIsNone(g.arguments(["version"], cwd, root))
            for bad in (args + ["--debug"], args[:-1], ["detect"], g.PREFIX + [str(config), "--no-git"]):
                if bad == args:
                    continue
                with self.assertRaises(RuntimeError):
                    g.arguments(bad, cwd, root)
            with self.assertRaises(RuntimeError):
                g.arguments(args, root, root)

    def test_snapshot_and_empty_dir(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder).resolve()
            (root / "empty").mkdir()
            (root / "file").write_bytes(b"x")
            self.assertEqual(g.snapshot(root), ({"file": b"x"}, {"empty"}))

    def test_snapshot_rejects_link_and_git(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder).resolve()
            (root / "file").touch()
            (root / "link").symlink_to(root / "file")
            with self.assertRaises(RuntimeError):
                g.snapshot(root)
            (root / "link").unlink()
            (root / ".git").mkdir()
            with self.assertRaises(RuntimeError):
                g.snapshot(root)

    def test_config(self):
        g.config_ok(b'[extend]\nuseDefault=true\n[[rules]]\nid="fixture"\ndescription="fixture"\nregex="x"\n')
        for bad in (b'[extend]\npath="/etc/passwd"', b'foo=1', b'[[rules]]\nid="fixture"\nregex="x"'):
            with self.assertRaises(RuntimeError):
                g.config_ok(bad)

    def test_sanitize(self):
        row = {"RuleID": "fixture", "Description": "control", "File": "./probe.txt",
               "StartLine": 1, "Tags": ["secret"], "Secret": "REDACTED", "Match": "raw", "Line": "raw"}
        clean = json.loads(g.sanitize(10, json.dumps([row]).encode(), {"probe.txt": b"x\n"}))
        self.assertNotIn("Match", clean[0])
        self.assertNotIn("Line", clean[0])
        self.assertEqual(json.loads(g.sanitize(0, b"null", {})), [])
        for bad in ({"File": "../probe.txt"}, {"Secret": "raw"}, {"StartLine": True}, {"Tags": 1}):
            with self.assertRaises(RuntimeError):
                g.sanitize(10, json.dumps([{**row, **bad}]).encode(), {"probe.txt": b"x\n"})

    def test_profile(self):
        args = g.docker_args("fixture", pathlib.Path("/tmp/stage"), False)
        for flag in ("--network=none", "--read-only", "--cap-drop=ALL", "--user=65534:65534", "--log-driver=none"):
            self.assertIn(flag, args)
        self.assertEqual(args.count("--mount"), 1)
        self.assertIn("/stage/input", args)

    def test_cleanup_after_start_failure(self):
        with mock.patch.object(g, "invoke", side_effect=[(0, b"id"), TimeoutError(), (0, b"")]) as invoke:
            with self.assertRaises(TimeoutError):
                g.run_container(pathlib.Path("/tmp/stage"), pathlib.Path("/tmp"), False)
            self.assertEqual(invoke.call_args_list[-1].args[0][:2], ["rm", "--force"])

    def test_cleanup_failure_blocks(self):
        with mock.patch.object(g, "invoke", side_effect=[(0, b"id"), (0, b"[]"), (1, b""), (0, b"")]):
            with self.assertRaisesRegex(RuntimeError, "CLEANUP"):
                g.run_container(pathlib.Path("/tmp/stage"), pathlib.Path("/tmp"), False)


if __name__ == "__main__":
    unittest.main()
