import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import check_integrated_bandit as b


class IntegratedBanditTests(unittest.TestCase):
    def test_scope(self):
        files = {p: b"x" for p in ("a.py", "b.pyw", "tests/x.py", "scripts/test_a.py",
                                    "scripts/a_test.py", ".venv/x.py", "file.md", "test_tools/x.py")}
        self.assertEqual(b.eligible(files), {"a.py", "b.pyw", "test_tools/x.py"})

    def test_contract_recursive_and_named(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder).resolve()
            skill = root / "bandit-control"
            skill.mkdir()
            file = skill / "probe.py"
            file.write_text("answer=42\n")
            ini = root / "bandit.ini"
            ini.write_bytes(b"fixture")
            def args(targets, exclude):
                return targets + ["-f", "json", "-q", "-ll", "--exclude", exclude,
                                  "--ini", str(ini), "--ignore-nosec"]
            with mock.patch.object(b, "ini_ok"):
                actual = b.contract(args(["-r", str(skill)], b.exclusions(skill)), root, ini)
                self.assertEqual(actual[2], {"probe.py"})
                self.assertEqual(actual[1][1], b.TARGET)
                named = b.contract(args([str(file)], ""), root, ini)
                self.assertEqual(named[2], {"probe.py"})
                for bad in (args(["-r", str(skill)], ""), args([str(file), str(file)], ""),
                            args([str(file)], "")[:-1]):
                    with self.assertRaises(RuntimeError):
                        b.contract(bad, root, ini)

    def test_ini(self):
        with self.assertRaises(RuntimeError):
            b.ini_ok(b"[bandit]\nskips=B307\n")

    def test_report(self):
        skill = pathlib.Path("/tmp/skill")
        files = {"probe.py": b"eval('1+1')\n"}
        row = {"filename": b.TARGET + "/probe.py", "test_id": "B307", "test_name": "blacklist",
               "issue_text": "fixture", "issue_severity": "MEDIUM", "issue_confidence": "HIGH",
               "line_number": 1, "issue_cwe": {"id": 78}, "code": "raw source"}
        doc = {"errors": [], "metrics": {row["filename"]: {"loc": 1}, "_totals": {"loc": 1}}, "results": [row]}
        result = json.loads(b.sanitize(1, json.dumps(doc).encode(), set(files), skill, files))
        self.assertEqual(result["results"][0]["filename"], str(skill / "probe.py"))
        self.assertNotIn("code", result["results"][0])
        for bad in ({**doc, "metrics": {"_totals": {"loc": 1}}},
                    {**doc, "errors": [{}]}, {**doc, "results": [{**row, "line_number": True}]},
                    {**doc, "results": [{**row, "filename": "/etc/passwd"}]}):
            with self.assertRaises(RuntimeError):
                b.sanitize(1, json.dumps(bad).encode(), set(files), skill, files)

    def test_profile(self):
        args = b.docker_args("fixture", pathlib.Path("/tmp/stage"), pathlib.Path("/tmp/packages"), ["--version"])
        for flag in ("--network=none", "--read-only", "--cap-drop=ALL", "--user=65534:65534"):
            self.assertIn(flag, args)
        self.assertEqual(args.count("--mount"), 2)
        self.assertNotIn("--privileged", args)

    def test_cleanup(self):
        with mock.patch.object(b, "invoke", side_effect=[(0, b""), TimeoutError(), (0, b"")]) as invoke:
            with self.assertRaises(TimeoutError):
                b.run_container(pathlib.Path("/tmp/stage"), pathlib.Path("/tmp"),
                                pathlib.Path("/tmp/packages"), ["--version"])
            self.assertEqual(invoke.call_args_list[-1].args[0][:2], ["rm", "--force"])


if __name__ == "__main__":
    unittest.main()
