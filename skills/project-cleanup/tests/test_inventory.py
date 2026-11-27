"""Synthetic fixtures only; no production data or Git operations."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "inventory.py"
spec = importlib.util.spec_from_file_location("project_cleanup_inventory", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()

    def file(self, name, data=b"abc"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_categories_and_totals(self):
        self.file("src/main.py", b"12345")
        self.file("build/output.bin", b"12")
        self.file("__pycache__/x.pyc", b"123")
        self.file("data/build/file.bin", b"1")
        self.file("node_modules/pkg/file", b"1234")
        self.file(".tmp/partial", b"123456")
        self.file(".git/objects/ignored", b"never count")
        result = m.inventory(self.root)
        self.assertEqual((result["files"], result["logical_bytes"]), (6, 21))
        self.assertEqual(result["categories"]["review_cache"]["logical_bytes"], 3)
        self.assertEqual(result["categories"]["protected_hint"]["logical_bytes"], 1)
        self.assertEqual(result["skipped"]["git_metadata"], 1)
        self.assertIsNone(result["reclaimable_bytes"])
        self.assertFalse(result["deletion_authorized"])
        self.assertEqual(result["status"], "OBSERVED")
        self.assertNotIn("src/main.py", json.dumps(result))
        self.assertNotIn("private_review_details", result)

    def test_protected_overrides_review(self):
        for name in ("build/secrets/file", "tmp/model.gguf", "dist/.env.local",
                     "tmp/backup.zip", "build/db.sqlite", "tmp/logs/a"):
            self.assertEqual(m.category(name.split("/")), "protected_hint")

    def test_named_protected_files_and_no_content_access(self):
        for name in ("tmp/credentials.json", "dist/password.txt", "build/access_token.txt",
                     "tmp/.netrc", "build/id_ecdsa", "build/.git-credentials"):
            self.file(name, b"synthetic")
            self.assertEqual(m.category(name.split("/")), "protected_hint")
        with patch("builtins.open", side_effect=AssertionError("content read")), \
                patch.object(Path, "open", side_effect=AssertionError("content read")), \
                patch.object(m.os, "open", side_effect=AssertionError("content read")):
            result = m.inventory(self.root, details=True)
        self.assertEqual(result["categories"]["protected_hint"]["files"], 6)
        self.assertEqual(result["private_review_details"], [])

    def test_sensitive_directory_never_enumerated(self):
        protected = self.file("build/.ssh/private", b"fixture").parent
        self.file("build/output.bin", b"ok")
        original = m.os.scandir

        def guarded(folder):
            self.assertNotEqual(Path(folder), protected)
            return original(folder)

        with patch.object(m.os, "scandir", side_effect=guarded):
            result = m.inventory(self.root, details=True)
        self.assertEqual(result["files"], 1)
        self.assertEqual(result["logical_bytes"], 2)
        self.assertEqual(result["skipped"]["sensitive_dirs"], 1)
        self.assertNotIn(".ssh", json.dumps(result))
        with self.assertRaisesRegex(m.InventoryError, "ROOT_PROTECTED_SCOPE"):
            m.inventory(protected)

    def test_profile_and_ancestor_refused(self):
        child = self.root / "profile"
        child.mkdir()
        with patch.object(Path, "home", return_value=child):
            for target in (self.root, child):
                with self.assertRaisesRegex(m.InventoryError, "ROOT_PROFILE_REFUSED"):
                    m.inventory(target)
        with patch.object(Path, "home", side_effect=RuntimeError("unavailable")):
            with self.assertRaisesRegex(m.InventoryError, "ROOT_PROFILE_UNKNOWN"):
                m.inventory(self.root)

    def test_details_are_bounded_and_relative(self):
        for i in range(25):
            self.file(f"build/{i}.bin", b"x" * (i + 1))
        self.file("data/build/private.bin", b"private")
        result = m.inventory(self.root, details=True)
        rows = result["private_review_details"]
        self.assertEqual(len(rows), 20)
        self.assertEqual(rows[0]["logical_bytes"], 25)
        self.assertTrue(all(x["relative_path"].startswith("build/") for x in rows))
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_top_level_groups_and_root_files(self):
        self.file('a/one', b'123')
        self.file('a/two', b'12')
        self.file('b/item', b'1')
        self.file('root.txt', b'12')
        result = m.inventory(self.root, details=True)
        self.assertEqual(result['private_top_level'], [
            {'relative_directory': 'a', 'files': 2, 'logical_bytes': 5},
            {'relative_directory': None, 'files': 1, 'logical_bytes': 2},
            {'relative_directory': 'b', 'files': 1, 'logical_bytes': 1}])
        self.assertTrue(result['private_top_level_complete'])
        with patch.object(m, 'MAX_TOP_LEVEL_GROUPS', 1):
            bounded = m.inventory(self.root, details=True)
        self.assertEqual(bounded['logical_bytes'], 8)
        self.assertFalse(bounded['private_top_level_complete'])
        self.assertEqual(len(bounded['private_top_level']), 1)

    def test_nested_git_excluded(self):
        self.file("nested/.git", b"gitdir: elsewhere")
        self.file("nested/build/file", b"not ours")
        result = m.inventory(self.root)
        self.assertEqual(result["files"], 0)
        self.assertEqual(result["skipped"]["nested_git"], 1)

    def test_entry_budget_is_partial(self):
        for i in range(4):
            self.file(str(i))
        result = m.inventory(self.root, max_entries=2)
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["entries_examined"], 2)
        self.assertEqual(result["limit"], "ENTRY_LIMIT")

    def test_depth_budget_is_partial(self):
        self.file("a/b/c")
        result = m.inventory(self.root, max_depth=1)
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["skipped"]["depth"], 1)

    def test_time_budget_is_partial(self):
        with patch.object(m.time, "monotonic", side_effect=[0, 31, 31]):
            result = m.inventory(self.root)
        self.assertEqual(result["limit"], "TIME_LIMIT")
        self.assertEqual(result["status"], "PARTIAL")

    def test_scandir_failure_is_partial_and_redacted(self):
        with patch.object(m.os, "scandir", side_effect=PermissionError("private")):
            result = m.inventory(self.root)
        self.assertEqual(result["skipped"]["errors"], 1)
        self.assertEqual(result["status"], "PARTIAL")
        self.assertNotIn("private", json.dumps(result))

    def test_invalid_root_or_limits(self):
        for root in (self.root / "missing", self.file("ordinary"), Path(self.root.anchor)):
            with self.assertRaises((OSError, m.InventoryError)):
                m.inventory(root)
        for kwargs in ({"max_entries": 0}, {"max_depth": 129}, {"max_seconds": -1}):
            with self.assertRaises(m.InventoryError):
                m.inventory(self.root, **kwargs)

    def test_windows_direntry_identity_requires_fresh_stat(self):
        entry = Mock()
        entry.path = str(self.root / 'file')
        hint = Mock(st_mode=0o100644, st_file_attributes=0, st_dev=0, st_ino=0, st_nlink=0)
        fresh = Mock(st_dev=7, st_ino=11, st_nlink=2)
        entry.stat.return_value = hint
        with patch.object(m.os, 'stat', return_value=fresh) as call:
            self.assertIs(m.entry_metadata(entry, True), fresh)
            call.assert_called_once_with(entry.path, follow_symlinks=False)
            call.reset_mock()
            self.assertIs(m.entry_metadata(entry, False), hint)
            call.assert_not_called()
            hint.st_file_attributes = 0x400
            with patch.object(m.stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400, create=True):
                self.assertIs(m.entry_metadata(entry, True), hint)
                call.assert_not_called()

    def test_parent_traversal_is_refused(self):
        with self.assertRaisesRegex(m.InventoryError, 'ROOT_PARENT_TRAVERSAL'):
            m.inventory(self.root / '..' / self.root.name)

    def test_pending_directory_budget(self):
        for name in ('a', 'b', 'c'):
            self.file(name + '/file')
        with patch.object(m, 'MAX_PENDING_DIRS', 1):
            result = m.inventory(self.root)
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertEqual(result['limit'], 'PENDING_DIRECTORY_LIMIT')

    def test_hardlink_identity_budget(self):
        for name in ('a', 'b'):
            file = self.file(name)
            try:
                os.link(file, file.with_suffix('.copy'))
            except OSError:
                self.skipTest('hardlinks unavailable')
        with patch.object(m, 'MAX_HARDLINK_IDENTITIES', 1):
            result = m.inventory(self.root)
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertEqual(result['limit'], 'HARDLINK_IDENTITY_LIMIT')

    def test_links_are_not_followed(self):
        target = self.file("data/item")
        try:
            (self.root / "link").symlink_to(target)
            (self.root / "dirlink").symlink_to(target.parent, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        result = m.inventory(self.root)
        self.assertEqual(result["files"], 1)
        self.assertEqual(result["skipped"]["links_reparse"], 2)
        with self.assertRaises(m.InventoryError):
            m.inventory(self.root / "dirlink")

    def test_hardlink_logical_not_physical(self):
        target = self.file("build/one")
        try:
            os.link(target, target.with_name("two"))
        except OSError:
            self.skipTest("hardlinks unavailable")
        result = m.inventory(self.root)
        self.assertEqual(result["logical_bytes"], 6)
        self.assertEqual(result["observed_hardlink_aliases"], 1)
        self.assertIsNone(result["reclaimable_bytes"])

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO unavailable")
    def test_special_file_is_not_opened(self):
        os.mkfifo(self.root / "pipe")
        result = m.inventory(self.root)
        self.assertEqual(result["skipped"]["special"], 1)
        self.assertEqual(result["files"], 0)

    def test_read_only_and_cli_status(self):
        path = self.file("build/cache", b"content")
        before = path.stat()
        result = subprocess.run([sys.executable, "-B", str(SOURCE), "--root",
                                 str(self.root)], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)["deletion_authorized"])
        self.assertEqual(path.read_bytes(), b"content")
        self.assertEqual(path.stat().st_mtime_ns, before.st_mtime_ns)
        result = subprocess.run([sys.executable, "-B", str(SOURCE), "--root",
                                 str(self.root / "missing")], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
