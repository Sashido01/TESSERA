"""T09.08: deterministic catalog source packages and annotated tag gates."""
from __future__ import annotations

import hashlib
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_catalog_package as package


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name) / "repo"
        self.root.mkdir()
        for name, value in {
            "VERSION": "0.0.14\n",
            "LICENSE": "Example test-only license\n",
            "README.md": "# Тестовый каталог\n",
            "README.en.md": "# Test catalog\n",
        }.items():
            (self.root / name).write_text(value, encoding="utf-8")
        skill = self.root / "skills" / "microversion-release"
        (skill / "references").mkdir(parents=True)
        (skill / "scripts").mkdir()
        (skill / "tests").mkdir()
        (skill / "SKILL.md").write_text("---\nname: microversion-release\n---\n", encoding="utf-8")
        (skill / "README.md").write_text("Описание навыка\n", encoding="utf-8")
        (skill / "references" / "POLICY.md").write_text("Правила\n", encoding="utf-8")
        (skill / "scripts" / "version.py").write_text("print('ok')\n", encoding="utf-8")
        (skill / "tests" / "test_version.py").write_text("excluded\n", encoding="utf-8")
        (self.root / "hidden.txt").write_text("not packaged\n", encoding="utf-8")
        self.sha = "a" * 40

    def zip(self):
        return package.package_bytes(self.root, "0.0.14", self.sha)

    def entries(self):
        with zipfile.ZipFile(io.BytesIO(self.zip())) as z:
            return {name: z.read(name) for name in z.namelist()}

    def test_deterministic_bytes(self):
        self.assertEqual(self.zip(), self.zip())

    def test_timestamp_changes_do_not_change_package(self):
        previous = self.zip()
        os.utime(self.root / "README.md", (100000000, 1800000000))
        self.assertEqual(previous, self.zip())

    def test_zip_has_only_runtime_files(self):
        items = self.entries()
        self.assertIn("TESSERA-0.0.14/skills/microversion-release/SKILL.md", items)
        self.assertIn("TESSERA-0.0.14/skills/microversion-release/scripts/version.py", items)
        self.assertNotIn("TESSERA-0.0.14/skills/microversion-release/tests/test_version.py", items)
        self.assertNotIn("TESSERA-0.0.14/hidden.txt", items)

    def test_version_and_manifest_bound_to_commit(self):
        items = self.entries()
        manifest = json.loads(items["TESSERA-0.0.14/MANIFEST.json"])
        self.assertEqual(manifest["source_commit_sha"], self.sha)
        self.assertEqual(manifest["catalog_version"], "0.0.14")
        self.assertEqual(manifest["artifact_kind"], "TESSERA_AGENT_SKILLS_CATALOG_SOURCE")
        for item in manifest["files"]:
            raw = items["TESSERA-0.0.14/" + item["path"]]
            self.assertEqual(item["bytes"], len(raw))
            self.assertEqual(item["sha256"], hashlib.sha256(raw).hexdigest())

    def test_zip_metadata_fixed(self):
        with zipfile.ZipFile(io.BytesIO(self.zip())) as z:
            for info in z.infolist():
                self.assertEqual(info.date_time, package.TIME)
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(info.create_system, 3)

    def test_archive_contains_license(self):
        self.assertIn("TESSERA-0.0.14/LICENSE", self.entries())

    def test_standalone_skill_license_is_packaged(self):
        skill = self.root / "skills" / "microversion-release"
        license_bytes = (self.root / "LICENSE").read_bytes()
        (skill / "LICENSE.txt").write_bytes(license_bytes)
        self.assertEqual(self.entries()["TESSERA-0.0.14/skills/microversion-release/LICENSE.txt"], license_bytes)

    def test_standalone_skill_license_symlink_rejected(self):
        skill = self.root / "skills" / "microversion-release"
        (skill / "LICENSE.txt").symlink_to(self.root / "LICENSE")
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_INVALID_FILE"):
            self.zip()

    def test_bad_version_rejected(self):
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_VERSION_INVALID"):
            package.package_bytes(self.root, "0.00.14", self.sha)

    def test_bad_source_sha_rejected(self):
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_COMMIT_INVALID"):
            package.package_bytes(self.root, "0.0.14", "HEAD")

    def test_repository_version_mismatch(self):
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_VERSION_MISMATCH"):
            package.package_bytes(self.root, "0.0.15", self.sha)

    def test_missing_skill_rejected(self):
        import shutil
        shutil.rmtree(self.root / "skills")
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_SKILLS_DIRECTORY_MISSING"):
            self.zip()

    def test_missing_skill_file_rejected(self):
        (self.root / "skills" / "microversion-release" / "SKILL.md").unlink()
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_INVALID_FILE"):
            self.zip()

    def test_bytecode_cache_is_not_silently_packaged(self):
        # This is the exact artifact generated when tests import runtime scripts.
        cache = self.root / "skills" / "microversion-release" / "scripts" / "__pycache__"
        cache.mkdir()
        (cache / "install.cpython-313.pyc").write_bytes(b"generated bytecode")
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_RUNTIME_FILE_INVALID"):
            self.zip()

    def test_unexpected_runtime_extension_rejected(self):
        (self.root / "skills" / "microversion-release" / "references" / "payload.exe").write_bytes(b"\0")
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_RUNTIME_FILE_INVALID"):
            self.zip()

    def test_bad_skill_name_rejected(self):
        skill = self.root / "skills" / "microversion-release"
        skill.rename(skill.parent / "MicroVersionRelease")
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_SKILL_DIRECTORY_INVALID"):
            self.zip()

    def test_symlink_file_rejected(self):
        original = self.root / "README.md"
        target = self.root / "README_target"
        original.rename(target)
        original.symlink_to(target)
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_INVALID_FILE"):
            self.zip()

    def test_symlink_runtime_directory_rejected(self):
        skill = self.root / "skills" / "microversion-release"
        directory = skill / "references"
        renamed = skill / "real-refs"
        directory.rename(renamed)
        directory.symlink_to(renamed, target_is_directory=True)
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_RUNTIME_DIRECTORY_INVALID"):
            self.zip()

    def test_file_over_4_megabytes_rejected(self):
        (self.root / "README.md").write_bytes(b"x" * (4 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_FILE_TOO_LARGE"):
            self.zip()

    def test_no_nested_or_absolute_paths_in_archive(self):
        for name in self.entries():
            self.assertNotIn("..", pathlib.PurePosixPath(name).parts)
            self.assertTrue(name.startswith("TESSERA-0.0.14/"))

    def test_changed_bytes_change_manifest_and_zip(self):
        before = hashlib.sha256(self.zip()).hexdigest()
        (self.root / "README.md").write_text("ИЗМЕНЕНИЕ\n", encoding="utf-8")
        self.assertNotEqual(before, hashlib.sha256(self.zip()).hexdigest())


class GitTagGateTests(PackageTests):
    def setUp(self):
        super().setUp()
        self.git("init", "-q")
        self.git("config", "user.email", "tester@example.invalid")
        self.git("config", "user.name", "Test Commit")
        (self.root / ".gitignore").write_text("dist/\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "Проверена сборка каталога")
        self.head = self.git("rev-parse", "HEAD")

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True, check=True, text=True,
        ).stdout.strip()

    def test_real_git_head_used_in_package(self):
        d = self.root / "dist"
        r = package.build(self.root, d, check_reproducible=True)
        self.assertEqual(r["source_commit_sha"], self.head)
        self.assertTrue(r["reproducibility_checked"])
        self.assertTrue((d / "TESSERA-catalog-v0.0.14.zip").exists())
        self.assertEqual(r["publication"], "NOT_PERFORMED")

    def test_no_tag_required_in_pr_build(self):
        result = package.build(self.root, self.root / "dist")
        self.assertFalse(result["annotated_tag_checked"])

    def test_annotated_tag_required_after_release(self):
        with self.assertRaises(package.PackageError):
            package.build(self.root, self.root / "dist", require_tag=True)

    def test_lightweight_tag_rejected(self):
        self.git("tag", "v0.0.14")
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_ANNOTATED_TAG_REQUIRED"):
            package.build(self.root, self.root / "dist", require_tag=True)

    def test_matching_annotated_tag_accepted(self):
        self.git("tag", "-a", "v0.0.14", "-m", "Тестовая версия 0.0.14")
        result = package.build(self.root, self.root / "dist", require_tag=True)
        self.assertTrue(result["annotated_tag_checked"])

    def test_wrong_tag_target_rejected(self):
        prev = self.head
        (self.root / "README.md").write_text("Обновлено\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git("commit", "-qm", "Дополнение")
        self.git("tag", "-a", "v0.0.14", prev, "-m", "Старый коммит")
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_TAG_COMMIT_MISMATCH"):
            package.build(self.root, self.root / "dist", require_tag=True)

    def test_dirty_tree_rejected(self):
        (self.root / "README.md").write_text("незакоммичено\n", encoding="utf-8")
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_DIRTY_WORKTREE"):
            package.build(self.root, self.root / "dist")

    def test_output_refused_if_already_exists(self):
        package.build(self.root, self.root / "dist")
        with self.assertRaisesRegex(package.PackageError, "PACKAGE_OUTPUT_EXISTS"):
            package.build(self.root, self.root / "dist")

    def test_build_does_not_create_tags(self):
        before = self.git("tag", "--list")
        package.build(self.root, self.root / "dist")
        self.assertEqual(before, self.git("tag", "--list"))


if __name__ == "__main__":
    unittest.main()
