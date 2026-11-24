import pathlib
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


if __name__ == "__main__":
    unittest.main()
