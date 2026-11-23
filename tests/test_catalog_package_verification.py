"""T09.09: самостоятельная офлайн-проверка фактических байтов ZIP каталога."""
from __future__ import annotations

import io
import json
import pathlib
import stat
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_catalog_package as builder
import verify_catalog_package as verifier


class CatalogVerificationTests(unittest.TestCase):
    VERSION = "0.0.15"
    SHA = "a" * 40

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)
        source = self.root / "source"
        source.mkdir()
        for name, data in {
            "VERSION": self.VERSION + "\n",
            "LICENSE": "Test-only license\n",
            "README.md": "Русский оригинал\n",
            "README.en.md": "English translation\n",
        }.items():
            (source / name).write_text(data, encoding="utf-8")
        skill = source / "skills" / "microversion-release"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: microversion-release\n---\n", encoding="utf-8")
        self.source_bytes = builder.package_bytes(source, self.VERSION, self.SHA)
        self.archive = self.root / "catalog.zip"
        self.archive.write_bytes(self.source_bytes)
        self.prefix = "TESSERA-" + self.VERSION + "/"

    def check(self):
        return verifier.verify(self.archive, version=self.VERSION, source_commit=self.SHA)

    def rewrite(self, change):
        with zipfile.ZipFile(io.BytesIO(self.source_bytes), "r") as zf:
            items = [(entry.filename, zf.read(entry.filename), entry.compress_type,
                      entry.external_attr, entry.create_system) for entry in zf.infolist()]
        items = change(items)
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as zf:
            for name, body, compression, attributes, system in items:
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = compression
                info.external_attr = attributes
                info.create_system = system
                zf.writestr(info, body)
        self.archive.write_bytes(output.getvalue())

    def test_genuine_package_passes_without_provenance_claim(self):
        result = self.check()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["catalog_version"], self.VERSION)
        self.assertEqual(result["source_commit_sha_claim"], self.SHA)
        self.assertEqual(result["attestation"], "NOT_VERIFIED")
        self.assertEqual(result["publication"], "NOT_VERIFIED")

    def test_wrong_expected_source_rejected(self):
        with self.assertRaisesRegex(verifier.VerificationError, "MANIFEST_MISMATCH"):
            verifier.verify(self.archive, version=self.VERSION, source_commit="b" * 40)

    def test_corrupted_payload_rejected(self):
        self.rewrite(lambda rows: [(n, b"tampered" if n.endswith("/LICENSE") else b, c, a, s)
                                   for n, b, c, a, s in rows])
        with self.assertRaisesRegex(verifier.VerificationError, "FILE_SET_MISMATCH|DIGEST_MISMATCH"):
            self.check()

    def test_duplicated_name_rejected(self):
        self.rewrite(lambda rows: rows + [rows[0]])
        with self.assertRaisesRegex(verifier.VerificationError, "ENTRY_UNSAFE"):
            self.check()

    def test_traversal_path_rejected(self):
        self.rewrite(lambda rows: rows + [(self.prefix + "../escape", b"danger",
                                          zipfile.ZIP_STORED, 0o100644 << 16, 3)])
        with self.assertRaisesRegex(verifier.VerificationError, "ENTRY_UNSAFE"):
            self.check()

    def test_absolute_path_rejected(self):
        self.rewrite(lambda rows: rows + [("/tmp/outside", b"danger",
                                          zipfile.ZIP_STORED, 0o100644 << 16, 3)])
        with self.assertRaisesRegex(verifier.VerificationError, "ENTRY_UNSAFE"):
            self.check()

    def test_symlink_member_rejected(self):
        self.rewrite(lambda rows: [(n, b, c, (stat.S_IFLNK | 0o777) << 16, s)
                                   if n.endswith("/LICENSE") else (n, b, c, a, s)
                                   for n, b, c, a, s in rows])
        with self.assertRaisesRegex(verifier.VerificationError, "ENTRY_UNSAFE"):
            self.check()

    def test_compressed_member_rejected(self):
        self.rewrite(lambda rows: [(n, b, zipfile.ZIP_DEFLATED, a, s)
                                   if n.endswith("/LICENSE") else (n, b, c, a, s)
                                   for n, b, c, a, s in rows])
        with self.assertRaisesRegex(verifier.VerificationError, "ENTRY_UNSAFE"):
            self.check()

    def test_missing_manifest_rejected(self):
        self.rewrite(lambda rows: [row for row in rows if not row[0].endswith("/MANIFEST.json")])
        with self.assertRaisesRegex(verifier.VerificationError, "MANIFEST_MISSING"):
            self.check()

    def test_manifest_version_change_rejected(self):
        def change(rows):
            altered = []
            for n, b, c, a, s in rows:
                if n.endswith("/MANIFEST.json"):
                    obj = json.loads(b)
                    obj["catalog_version"] = "0.0.99"
                    b = json.dumps(obj).encode("utf-8")
                altered.append((n, b, c, a, s))
            return altered
        self.rewrite(change)
        with self.assertRaisesRegex(verifier.VerificationError, "MANIFEST_MISMATCH"):
            self.check()

    def test_archive_symlink_rejected(self):
        target = self.root / "real.zip"
        self.archive.rename(target)
        try:
            self.archive.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(verifier.VerificationError, "FILE_INVALID"):
            self.check()

    def test_broken_archive_rejected(self):
        self.archive.write_bytes(b"not a zip")
        with self.assertRaisesRegex(verifier.VerificationError, "ARCHIVE_UNREADABLE"):
            self.check()

    def test_invalid_versions_and_sha_rejected(self):
        with self.assertRaisesRegex(verifier.VerificationError, "VERSION_INVALID"):
            verifier.verify(self.archive, version="0.00.15", source_commit=self.SHA)
        with self.assertRaisesRegex(verifier.VerificationError, "SOURCE_SHA_INVALID"):
            verifier.verify(self.archive, version=self.VERSION, source_commit="HEAD")


if __name__ == "__main__":
    unittest.main()
