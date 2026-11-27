"""UP01/UP02 source package contract, with legacy format compatibility."""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import build_catalog_package as builder
import verify_catalog_package as verifier
from catalog_package_policy import UPDATE_FILES, requires_update_files


class UpdatePackageTests(unittest.TestCase):
    VERSION = "0.0.97"
    SHA = "a" * 40

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.archive = self.root / "catalog.zip"
        for name in ("README.md", "README.en.md", "LICENSE"):
            self.write(name, "fixture\n")
        self.write("VERSION", self.VERSION + "\n")
        self.skill = "skills/alpha"
        self.write(self.skill + "/SKILL.md", "---\nname: alpha\n---\n")
        self.write(self.skill + "/VERSION", "0.0.1\n")
        for name in ("CHANGELOG.md", "CHANGELOG.en.md"):
            self.write(self.skill + "/" + name, "## 0.0.1\n")
        self.write(self.skill + "/tests/test_example.py", "# excluded fixture\n")
        self.index = {"schema_version": 1, "repository": "Sashido01/TESSERA",
                      "skills": [{"id": "alpha", "path": self.skill, "version": "0.0.1",
                                  "ref": "refs/tags/alpha/v0.0.1"}]}
        for name in UPDATE_FILES - {"CATALOG.json"}:
            self.write(name, "# fixture\n")
        self.write_index()
        self.prefix = "TESSERA-" + self.VERSION + "/"

    def write(self, name, data):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")

    def write_index(self):
        self.write("CATALOG.json", json.dumps(self.index))

    def build(self):
        return builder.package_bytes(self.source, self.VERSION, self.SHA)

    def verify(self, raw):
        self.archive.write_bytes(raw)
        return verifier.verify(self.archive, version=self.VERSION, source_commit=self.SHA)

    def repack(self, changes):
        # Recompute the manifest as an adversary could; semantic checks must still reject.
        with zipfile.ZipFile(io.BytesIO(self.build())) as archive:
            files = {name[len(self.prefix):]: archive.read(name) for name in archive.namelist()}
        manifest = json.loads(files.pop("MANIFEST.json"))
        changes(files)
        manifest["files"] = [{"path": name, "bytes": len(body),
                              "sha256": hashlib.sha256(body).hexdigest()}
                             for name, body in sorted(files.items())]
        files["MANIFEST.json"] = json.dumps(manifest).encode("utf-8")
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            for name, body in sorted(files.items()):
                entry = zipfile.ZipInfo(self.prefix + name)
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, body)
        return output.getvalue()

    def test_exact_update_files_and_legacy_exclusions(self):
        raw = self.build()
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names = {name[len(self.prefix):] for name in archive.namelist()}
        self.assertTrue(UPDATE_FILES.issubset(names))
        self.assertNotIn(self.skill + "/tests/test_example.py", names)
        self.assertEqual(raw, self.build())
        self.assertEqual(self.verify(raw)["status"], "PASS")

    def test_missing_update_file_refused_by_builder(self):
        (self.source / "tools/profile_plan.py").unlink()
        with self.assertRaisesRegex(builder.PackageError, "PACKAGE_INVALID_FILE"):
            self.build()

    def test_index_version_mismatch_refused_by_builder(self):
        self.index["skills"][0].update(version="0.0.2", ref="refs/tags/alpha/v0.0.2")
        self.write_index()
        with self.assertRaisesRegex(builder.PackageError, "PACKAGE_UPDATE_CATALOG_INVALID"):
            self.build()

    def test_missing_file_with_consistent_manifest_refused(self):
        raw = self.repack(lambda files: files.pop("tools/skill_tree.py"))
        with self.assertRaisesRegex(verifier.VerificationError, "CATALOG_UPDATE_CONTRACT_INVALID"):
            self.verify(raw)

    def test_unexpected_file_with_consistent_manifest_refused(self):
        raw = self.repack(lambda files: files.update({"other.py": b"# extra fixture"}))
        with self.assertRaisesRegex(verifier.VerificationError, "CATALOG_UPDATE_CONTRACT_INVALID"):
            self.verify(raw)

    def test_wrong_index_version_with_consistent_manifest_refused(self):
        self.index["skills"][0].update(version="0.0.2", ref="refs/tags/alpha/v0.0.2")
        raw = self.repack(lambda files: files.update({"CATALOG.json": json.dumps(self.index).encode()}))
        with self.assertRaisesRegex(verifier.VerificationError, "CATALOG_UPDATE_CONTRACT_INVALID"):
            self.verify(raw)

    def test_version_gate(self):
        for version in ("0.0.21", "0.0.96"):
            self.assertFalse(requires_update_files(version))
        for version in ("0.0.97", "0.0.100", "0.1.0", "1.0.0"):
            self.assertTrue(requires_update_files(version))


if __name__ == "__main__":
    unittest.main()
