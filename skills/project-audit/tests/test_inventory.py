"""Deterministic helper checks; not agent behavioral evals."""
from __future__ import annotations
import sys
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'inventory.py'
cached = sys.modules.get('inventory')
if cached is not None and Path(getattr(cached, '__file__', '') or '.').resolve() != PATH:
    raise RuntimeError('Unexpected cached test module')
sys.path.insert(0, str(PATH.parent))
try:
    import inventory as module
finally:
    sys.path.pop(0)
if Path(module.__file__).resolve() != PATH:
    raise RuntimeError('Unexpected test module origin')


class InventoryTests(unittest.TestCase):
    def test_import_origin(self):
        self.assertEqual(Path(module.__file__).resolve(), PATH)

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve() / 'project'
        self.root.mkdir()

    def put(self, name, content=b'abc'):
        file = self.root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content)
        return file

    def test_nested_counts_and_markers(self):
        self.put('src/main.py')
        self.put('README.md', b'hello')
        self.put('VERSION', b'0.0.1')
        r = module.inventory(self.root)
        self.assertEqual((r['regular_files'], r['regular_file_bytes']), (3, 13))
        self.assertEqual(r['markers'], ['README.md', 'VERSION'])
        self.assertEqual(r['extensions'], {'(none)': 1, '.md': 1, '.py': 1})
        self.assertEqual(r['status'], 'SCOPED_COMPLETE')
        self.assertEqual(r['content_integrity'], 'NOT_VERIFIED')

    def test_deterministic_unchanged_tree(self):
        self.put('b.py'); self.put('a.py')
        self.assertEqual(module.inventory(self.root), module.inventory(self.root))

    def test_metadata_change_detected(self):
        f = self.put('x')
        a = module.inventory(self.root)['metadata_sha256']
        f.write_bytes(b'longer')
        self.assertNotEqual(a, module.inventory(self.root)['metadata_sha256'])

    def test_empty_directory_changes_metadata_digest(self):
        a = module.inventory(self.root)['metadata_sha256']
        (self.root / 'empty').mkdir()
        r = module.inventory(self.root)
        self.assertEqual(r['directories'], ['empty'])
        self.assertNotEqual(a, r['metadata_sha256'])

    def test_reparse_flag_detected(self):
        from types import SimpleNamespace
        import stat
        info = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        self.assertTrue(module.is_redirect(info))

    def test_default_exclusions_visible(self):
        self.put('.git/config'); self.put('node_modules/example/x.js')
        self.put('src.py')
        r = module.inventory(self.root)
        self.assertEqual(r['excluded_subtrees'], 2)
        self.assertEqual(r['regular_files'], 1)
        self.assertEqual({g['reason'] for g in r['gaps']}, {'DEFAULT_EXCLUSION'})

    def test_limit_never_returns_arbitrary_partial_directory(self):
        for n in ['a','b','c']: self.put(n)
        r = module.inventory(self.root, max_entries=2)
        self.assertEqual(r['status'], 'PARTIAL')
        self.assertEqual(r['regular_files'], 0)
        self.assertEqual(r['gaps'], [{'path': '.', 'reason': 'ENTRY_LIMIT'}])

    def test_exact_entry_limit_is_complete(self):
        self.put('a'); self.put('b')
        result = module.inventory(self.root, max_entries=2)
        self.assertEqual(result['status'], 'SCOPED_COMPLETE')
        self.assertEqual(result['examined_entries'], 2)
        self.assertEqual(result['pending_directories'], 0)

    def test_windows_zero_cached_directory_identity(self):
        from contextlib import contextmanager
        from types import SimpleNamespace
        self.put('nested/deeper/child.py')
        real_scandir = os.scandir

        class CachedEntry:
            def __init__(self, entry):
                self.name, self.path = entry.name, entry.path
                self.entry = entry

            def stat(self, **kwargs):
                info = self.entry.stat(**kwargs)
                if self.entry.is_dir(follow_symlinks=False):
                    return SimpleNamespace(st_mode=info.st_mode, st_dev=0, st_ino=0,
                                           st_file_attributes=getattr(info, 'st_file_attributes', 0))
                return info

        @contextmanager
        def scan(directory):
            with real_scandir(directory) as entries:
                yield (CachedEntry(entry) for entry in entries)

        with patch.object(module.os, 'scandir', side_effect=scan):
            result = module.inventory(self.root)
        self.assertEqual(result['status'], 'SCOPED_COMPLETE')
        self.assertEqual(result['regular_files'], 1)
        self.assertEqual(result['directories'], ['nested', 'nested/deeper'])
        self.assertEqual(result['gaps'], [])

    def test_other_device_is_not_traversed(self):
        from types import SimpleNamespace
        self.put('mounted/child.py')
        actual = (self.root / 'mounted').lstat()
        other = SimpleNamespace(st_mode=actual.st_mode, st_dev=self.root.lstat().st_dev + 1,
                                st_ino=actual.st_ino)
        with patch.object(module, 'directory_stat', return_value=other), \
                patch.object(module.os, 'scandir', wraps=os.scandir) as scan:
            result = module.inventory(self.root)
        self.assertEqual(scan.call_count, 1)
        self.assertEqual(result['regular_files'], 0)
        self.assertEqual(result['gaps'], [{'path': 'mounted', 'reason': 'DEVICE_BOUNDARY'}])

    def test_refreshed_directory_redirect_is_not_traversed(self):
        from types import SimpleNamespace
        import stat
        self.put('nested/child.py')
        redirect = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        with patch.object(module, 'directory_stat', return_value=redirect), \
                patch.object(module.os, 'scandir', wraps=os.scandir) as scan:
            result = module.inventory(self.root)
        self.assertEqual(scan.call_count, 1)
        self.assertEqual(result['regular_files'], 0)
        self.assertEqual(result['gaps'], [{'path': 'nested', 'reason': 'REDIRECTION_NOT_FOLLOWED'}])

    def test_refreshed_directory_stat_failure_is_reported(self):
        self.put('nested/child.py')
        with patch.object(module, 'directory_stat', side_effect=PermissionError):
            result = module.inventory(self.root)
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertEqual(result['regular_files'], 0)
        self.assertEqual(result['gaps'], [{'path': 'nested', 'reason': 'STAT_UNAVAILABLE'}])

    def test_refreshed_directory_replaced_by_file_is_reported(self):
        import stat
        from types import SimpleNamespace
        self.put('nested/child.py')
        with patch.object(module, 'directory_stat', return_value=SimpleNamespace(st_mode=stat.S_IFREG)):
            result = module.inventory(self.root)
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertEqual(result['regular_files'], 0)
        self.assertEqual(result['gaps'], [{'path': 'nested', 'reason': 'DIRECTORY_CHANGED'}])

    def test_depth_limit_visible(self):
        self.put('a/b/c.py')
        r = module.inventory(self.root, max_depth=0)
        self.assertEqual(r['status'], 'PARTIAL')
        self.assertEqual(r['gaps'], [{'path': 'a', 'reason': 'DEPTH_LIMIT'}])

    def test_symlink_not_followed(self):
        target = self.root.parent / 'outside'
        target.mkdir(); (target / 'private').write_text('private')
        try:
            (self.root / 'redirect').symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        r = module.inventory(self.root)
        self.assertEqual(r['regular_files'], 0)
        self.assertEqual(r['gaps'], [{'path': 'redirect', 'reason': 'REDIRECTION_NOT_FOLLOWED'}])

    def test_root_symlink_rejected(self):
        link = self.root.parent / 'link'
        try:
            link.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        with self.assertRaisesRegex(module.InventoryError, 'ROOT_INVALID'):
            module.inventory(link)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO not supported')
    def test_special_file_not_opened(self):
        os.mkfifo(self.root / 'pipe')
        r = module.inventory(self.root)
        self.assertEqual(r['gaps'], [{'path': 'pipe', 'reason': 'SPECIAL_FILE_NOT_READ'}])

    def test_no_file_content_read(self):
        text_payload = b'INVENTORY_TEXT_PAYLOAD'
        binary_payload = b'\x00\xffINVENTORY_BINARY_PAYLOAD'
        self.put('payload.txt', text_payload)
        self.put('nested/input.bin', binary_payload)
        with (
            patch.object(Path, 'open', side_effect=AssertionError('content read')),
            patch('builtins.open', side_effect=AssertionError('content read')),
            patch('io.open', side_effect=AssertionError('content read')),
            patch.object(os, 'open', side_effect=AssertionError('content read')),
        ):
            r = module.inventory(self.root)
        self.assertEqual(r['regular_files'], 2)
        self.assertEqual(r['regular_file_bytes'], len(text_payload) + len(binary_payload))
        self.assertEqual(r['content_integrity'], 'NOT_VERIFIED')
        self.assertEqual([f['path'] for f in r['files']], ['nested/input.bin', 'payload.txt'])
        self.assertNotIn('INVENTORY_TEXT_PAYLOAD', str(r))
        self.assertNotIn('INVENTORY_BINARY_PAYLOAD', str(r))
        self.assertNotIn(str(self.root), str(r))

    def test_unreadable_directory_reported(self):
        with patch.object(module.os, 'scandir', side_effect=PermissionError):
            r = module.inventory(self.root)
        self.assertEqual(r['status'], 'PARTIAL')
        self.assertEqual(r['gaps'], [{'path': '.', 'reason': 'DIRECTORY_UNAVAILABLE'}])

    def test_invalid_limits_and_missing_root(self):
        with self.assertRaisesRegex(module.InventoryError, 'LIMIT_INVALID'):
            module.inventory(self.root, max_entries=0)
        with self.assertRaisesRegex(module.InventoryError, 'ROOT_UNAVAILABLE'):
            module.inventory(self.root / 'missing')

    def test_same_size_same_mtime_content_change_not_detected(self):
        f = self.put('file.txt', b'abc')
        info = f.stat()
        a = module.inventory(self.root)['metadata_sha256']
        f.write_bytes(b'xyz')
        os.utime(f, ns=(info.st_atime_ns, info.st_mtime_ns))
        b = module.inventory(self.root)
        self.assertEqual(a, b['metadata_sha256'])
        self.assertEqual(b['content_integrity'], 'NOT_VERIFIED')


if __name__ == '__main__':
    unittest.main()
