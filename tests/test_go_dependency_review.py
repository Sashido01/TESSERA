"""Offline tests for the Go build metadata contract."""
import pathlib
import hashlib
import io
import tarfile
import tempfile
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

    def test_unversioned_module_is_explicit_coverage_gap(self):
        report = self.parse("\tdep\texample.org/unversioned\t(devel)\n")
        self.assertEqual(report["unversioned_modules"], ["example.org/unversioned"])
        self.assertEqual(report["dependency_coverage"], "PARTIAL")
        self.assertNotIn(("example.org/unversioned", "(devel)"), report["modules"])

    def test_versioned_replacement_resolves_devel(self):
        report = self.parse("\tdep\texample.org/unversioned\t(devel)\n"
                            "\t=>\texample.org/fork\tv1.2.3\n")
        self.assertEqual(report["unversioned_modules"], [])
        self.assertIn(("example.org/fork", "v1.2.3"), report["modules"])

    def test_unknown_version_fails_closed(self):
        with self.assertRaisesRegex(g.InstallCheckError, "VERSION_UNVERIFIED"):
            self.parse("\tdep\texample.org/unversioned\tunknown\n")

    def test_pinned_file_build_root(self):
        raw = (f"binary: go1.24.11\n\tpath\tcommand-line-arguments\n"
               f"\tdep\t{self.root}\t(devel)\t\n"
               "\tdep\texample.org/module\tv1.2.3\n").encode()
        report = g.parse_build(raw, self.root, self.version, self.commit,
                               verified_file_build=True)
        self.assertEqual(report["root_build_version"], "NOT_RECORDED")
        self.assertEqual(report["root_version_source"], "PINNED_ARCHIVE_RELEASE_METADATA_ONLY")
        self.assertIn((self.root, self.version), report["modules"])
        self.assertEqual(report["unversioned_modules"], [])
        with self.assertRaisesRegex(g.InstallCheckError, "ROOT_MODULE_NOT_RECORDED"):
            g.parse_build(raw, self.root, self.version, self.commit)

    def test_file_build_wrong_entrypoint_rejected(self):
        raw = (f"binary: go1.24.11\n\tpath\tother\n"
               f"\tdep\t{self.root}\t(devel)\n"
               "\tdep\texample.org/module\tv1.2.3\n").encode()
        with self.assertRaisesRegex(g.InstallCheckError, "ROOT_MODULE_NOT_RECORDED"):
            g.parse_build(raw, self.root, self.version, self.commit, verified_file_build=True)

    def test_binary_archive_binding(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            archive, binary = root / "test.tar.gz", root / "binary"
            data = b"test-only binary contents"
            binary.write_bytes(data)
            with tarfile.open(archive, "w:gz") as tar:
                member = tarfile.TarInfo("binary")
                member.size = len(data)
                tar.addfile(member, io.BytesIO(data))
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(g.verify_binary(archive, binary, digest, "binary"),
                             hashlib.sha256(data).hexdigest())
            with self.assertRaisesRegex(g.InstallCheckError, "ARCHIVE_DIGEST_MISMATCH"):
                g.verify_binary(archive, binary, "0" * 64, "binary")
            binary.write_bytes(b"changed")
            with self.assertRaisesRegex(g.InstallCheckError, "BINARY_DIGEST_MISMATCH"):
                g.verify_binary(archive, binary, digest, "binary")

    def test_local_replacement_blocked(self):
        with self.assertRaisesRegex(g.InstallCheckError, "REPLACEMENT"):
            self.parse("\t=>\t../local\t(devel)\n")


if __name__ == "__main__":
    unittest.main()
