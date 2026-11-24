import pathlib
import shutil
import subprocess
import tempfile
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_bandit_container as c


class BanditContainerTests(unittest.TestCase):
    def test_lock_subset(self):
        subset = (ROOT / "tools/bandit-requirements.txt").read_text()
        full = (ROOT / "tools/nvidia-tier1-requirements.txt").read_text()
        c.validate_lock(subset, full)
        for bad in (subset.replace("bandit==1.9.4", "bandit==1.9.3"), subset + "unknown==1.0 --hash=sha256:" + "a"*64,
                    "\n".join(x for x in subset.splitlines() if not x.startswith("rich=="))):
            with self.assertRaises(RuntimeError):
                c.validate_lock(bad, full)

    def test_profile(self):
        args = c.args_for("fixture", pathlib.Path("/tmp/stage"), pathlib.Path("/tmp/packages"))
        for flag in ("--network=none", "--read-only", "--cap-drop=ALL", "--user=65534:65534"):
            self.assertIn(flag, args)
        self.assertEqual(args.count("--mount"), 2)
        self.assertNotIn("--privileged", args)
        self.assertTrue(any("target=/packages,readonly" in x for x in args))

    def test_parity(self):
        host = {"execution": "PASS", "scanner": "bandit", "version": c.VERSION,
                "snapshot_sha256": "a", "catalog": {"files": 1, "findings": 0},
                "clean_fixture": "PASS", "negative_nosec_fixture": "PASS"}
        report = {k: v for k, v in host.items() if k not in ("execution", "scanner")}
        report["package_sha256"] = "b"
        c.parity(report, host, "a", "b")
        for change in ({"snapshot_sha256": "x"}, {"package_sha256": "x"},
                       {"catalog": {"files": True, "findings": 0}}, {"clean_fixture": "FAIL"}):
            with self.assertRaises(RuntimeError):
                c.parity({**report, **change}, host, "a", "b")


    def test_staged_import_closure(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = pathlib.Path(folder)
            for module in c.MODULES:
                shutil.copyfile(ROOT / "tools" / module, stage / module)
            result = subprocess.run([sys.executable, "-I", "-B", "-c",
                "import sys; sys.path.insert(0, sys.argv[1]); import check_bandit_container",
                str(stage)], cwd=stage, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))

    def test_diagnostics_allowlist(self):
        self.assertEqual(c.error_code(RuntimeError("BANDIT_CONTAINER_PARITY")), "BANDIT_CONTAINER_PARITY")
        self.assertEqual(c.error_code(RuntimeError("synthetic raw report")), "BANDIT_CONTAINER_FAILED")
        self.assertEqual(c.worker_error(b'{"error":"BANDIT_CONTAINER_VERSION"}'), "BANDIT_CONTAINER_VERSION")
        for raw in (b'{"error":"raw source"}', b'{"error":[]}', b'{"error":"BANDIT_CONTAINER_VERSION","raw":"x"}', b'invalid', b'x'*513):
            self.assertEqual(c.worker_error(raw), "BANDIT_CONTAINER_WORKER")


    def test_console_entry_version_contract(self):
        # Reproduce upstream 1.9.4 argparse %(prog)s behavior without installing Bandit.
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder).resolve()
            package = root / "bandit" / "cli"
            package.mkdir(parents=True)
            (root / "bandit" / "__init__.py").touch()
            (package / "__init__.py").touch()
            (package / "main.py").write_text(
                "import argparse\n"
                "def main():\n"
                "    parser = argparse.ArgumentParser()\n"
                "    parser.add_argument('--version', action='version', version='%(prog)s 1.9.4')\n"
                "    parser.parse_args()\n", encoding="utf-8")
            entry = c.ENTRY.replace("'/packages'", repr(str(root)))
            result = subprocess.run([sys.executable, "-I", "-B", "-c", entry, "--version"],
                                    cwd=root, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), b"bandit 1.9.4")


if __name__ == "__main__":
    unittest.main()
