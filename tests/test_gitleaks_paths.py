"""Offline tests for the exact path rules and Git tree inventory."""
import pathlib
import sys
import unittest
import tempfile
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_gitleaks_paths as p

A = "a" * 40


class PathRuleTests(unittest.TestCase):
    def test_path_scan_rejects_extra_file(self):
        with tempfile.TemporaryDirectory() as folder:
            def unexpected(args, **kwargs):
                target = pathlib.Path(args[2])
                (target.parent / "unexpected.json").write_bytes(b"synthetic")
                return None
            with patch.object(p.subprocess, "run", side_effect=unexpected):
                with self.assertRaisesRegex(p.InstallCheckError, "SOURCE_MUTATED"):
                    p.scan_rule(pathlib.Path("gitleaks"), pathlib.Path(folder), {},
                                "kubernetes-secret-yaml", b"fixture")

    def test_path_scan_rejects_changed_input(self):
        with tempfile.TemporaryDirectory() as folder:
            def unexpected(args, **kwargs):
                pathlib.Path(args[2]).write_bytes(b"changed")
                return None
            with patch.object(p.subprocess, "run", side_effect=unexpected):
                with self.assertRaisesRegex(p.InstallCheckError, "SOURCE_MUTATED"):
                    p.scan_rule(pathlib.Path("gitleaks"), pathlib.Path(folder), {},
                                "kubernetes-secret-yaml", b"fixture")

    def test_rules(self):
        for file, rule in (("a.PHP", "freemius-secret-key"),
                           ("a.hcl", "hashicorp-tf-password"),
                           ("a.zip.yaml", "kubernetes-secret-yaml"),
                           ("pkg/NuGet.config", "nuget-config-password"),
                           ("a.PFX", "pkcs12-file")):
            with self.subTest(file=file):
                self.assertEqual(p.matching(file), [rule])

    def test_nonmatching(self):
        self.assertEqual(p.matching("README.md"), [])
        self.assertEqual(p.matching("sample.yml.txt"), [])

    def test_tree_pair(self):
        raw = f"100644 blob {A}\told.yml\0".encode()
        self.assertEqual(p.tree_pairs(raw, {A: 15}), {("kubernetes-secret-yaml", A)})

    def test_pair_deduplicated(self):
        raw = f"100644 blob {A}\ta.yml\0" + f"100755 blob {A}\tb.yaml\0"
        self.assertEqual(len(p.tree_pairs(raw.encode(), {A: 15})), 1)

    def test_symlink_blocked(self):
        with self.assertRaisesRegex(p.InstallCheckError, "UNSUPPORTED"):
            p.tree_pairs(f"120000 blob {A}\told.yml\0".encode(), {A: 15})


if __name__ == "__main__":
    unittest.main()
