import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_skillspector_container as c


class SkillSpectorContainerTests(unittest.TestCase):
    def test_inventory_exact_and_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder).resolve()
            meta = root / "fixture-1.0.dist-info"
            meta.mkdir()
            (meta / "METADATA").write_text("Name: fixture\nVersion: 1.0\n")
            original = c.inventory(root, {"fixture": "1.0"})
            self.assertEqual(original["files"], 1)
            (meta / "METADATA").write_text("Name: fixture\nVersion: 2.0\n")
            self.assertNotEqual(c.inventory(root)["sha256"], original["sha256"])
            with self.assertRaises(RuntimeError):
                c.inventory(root, {"fixture": "1.0"})

    def test_link_and_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder).resolve()
            f = root / "a"
            f.write_bytes(b"abc")
            (root / "b").symlink_to(f)
            with self.assertRaises(RuntimeError):
                c.inventory(root)
            (root / "b").unlink()
            with mock.patch.object(c, "MAX_FILE", 2), self.assertRaises(RuntimeError):
                c.inventory(root)

    def test_exact_inventory_count(self):
        self.assertEqual(len(c.VERSIONS), 74)
        self.assertEqual(c.VERSIONS["skillspector"], c.VERSION)
        self.assertEqual(c.VERSIONS["cryptography"], "50.0.2")

    def test_profile(self):
        args = c.args_for("fixture", pathlib.Path("/fixture-stage"), pathlib.Path("/fixture-packages"))
        for flag in ("--network=none", "--read-only", "--cap-drop=ALL", "--user=65534:65534", "--memory=1g"):
            self.assertIn(flag, args)
        self.assertEqual(args.count("--mount"), 2)
        self.assertIn("-S", args)
        with self.assertRaises(RuntimeError):
            c.args_for("fixture", pathlib.Path("/fixture-stage"), pathlib.Path("/fixture-stage/sub"))

    def test_parity(self):
        host = {"execution": "PASS", "version": c.VERSION, "skills": {"fixture": {"risk_score": 22}},
                "clean_fixture": "PASS", "negative_fixture": "PASS", "llm": "DISABLED"}
        report = {k: v for k, v in host.items() if k != "execution"}
        report.update({"packages": {"sha256": "a"}, "source": {"sha256": "b"}})
        c.parity(report, host, {"sha256": "a"}, {"sha256": "b"})
        with self.assertRaises(RuntimeError):
            c.parity({**report, "skills": {"fixture": {"risk_score": 23}}}, host,
                     {"sha256": "a"}, {"sha256": "b"})

    def test_staged_import_closure(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = pathlib.Path(folder)
            for module in c.MODULES:
                shutil.copyfile(ROOT / "tools" / module, stage / module)
            run = subprocess.run([sys.executable, "-I", "-S", "-B", "-c",
                                  "import sys;sys.path.insert(0,sys.argv[1]);import check_skillspector_container",
                                  str(stage)], cwd=stage, capture_output=True, timeout=15)
            self.assertEqual(run.returncode, 0)

    def test_diagnostic_redaction(self):
        self.assertEqual(c.safe_error(RuntimeError("SP_DOCKER_PARITY")), "SP_DOCKER_PARITY")
        self.assertEqual(c.safe_error(RuntimeError("synthetic raw source")), "SP_DOCKER_FAILED")


if __name__ == "__main__":
    unittest.main()
