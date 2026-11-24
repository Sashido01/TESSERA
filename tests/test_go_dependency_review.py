"""Offline tests for the Go build metadata contract."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_go_dependency_review as g


class GoMetadataTests(unittest.TestCase):
    root, version, commit = g.ROOTS["gitleaks"]

    def parse(self, extra="", version=None):
        body = (f"binary: go1.24.11\n\tmod\t{self.root}\t{version or self.version}\n"
                "\tdep\texample.org/module\tv1.2.3\n" + extra)
        return g.parse_build(body.encode(), self.root, self.version, self.commit)

    def test_metadata(self):
        result = self.parse()
        self.assertIn(("example.org/module", "v1.2.3"), result["modules"])
        self.assertEqual(result["toolchain"], "1.24.11")

    def test_devel_root(self):
        self.assertEqual(self.parse(version="(devel)")["root_build_version"], "(devel)")

    def test_revision(self):
        self.assertEqual(self.parse(f"\tbuild\tvcs.revision={self.commit}\n")["source_revision"], "MATCH")

    def test_wrong_revision(self):
        with self.assertRaisesRegex(g.InstallCheckError, "REVISION"):
            self.parse("\tbuild\tvcs.revision=" + "a" * 40 + "\n")

    def test_wrong_root_version(self):
        with self.assertRaisesRegex(g.InstallCheckError, "ROOT"):
            self.parse(version="v8.0.0")

    def test_versioned_replacement(self):
        self.assertIn(("example.org/fork", "v2.0.0"),
                      self.parse("\t=>\texample.org/fork\tv2.0.0\n")["modules"])

    def test_local_replacement_blocked(self):
        with self.assertRaisesRegex(g.InstallCheckError, "REPLACEMENT"):
            self.parse("\t=>\t../local\t(devel)\n")


if __name__ == "__main__":
    unittest.main()
