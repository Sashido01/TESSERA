"""Disposable journal fixtures: no user-profile writes."""
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import profile_journal as j
from catalog_index import CatalogError, REPO


class JournalTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name).resolve()
        self.record = {"schema_version": 1, "repository": REPO, "id": "alpha",
                       "operation": "update", "phase": "PREPARED",
                       "old_version": "0.0.1", "new_version": "0.0.2",
                       "old_sha256": "a"*64, "new_sha256": "b"*64}

    def append(self, phase):
        return j.append(self.root, {**self.record, "phase": phase})

    def test_update_sequence(self):
        for phase in j.PHASES:
            result = self.append(phase)
            self.assertFalse(result["apply_authorized"])
        self.assertEqual([x["phase"] for x in j.scan(self.root)], list(j.PHASES))

    def test_install_skips_old_phase(self):
        self.record.update(operation="install", old_version=None, old_sha256=None)
        for phase in ("PREPARED", "NEW_MOVED", "VERIFIED"):
            self.append(phase)
        self.assertFalse((self.root / j.FILES[1]).exists())

    def test_duplicate_preserves_original(self):
        self.append("PREPARED")
        path = self.root / j.FILES[0]
        before = path.read_bytes()
        with self.assertRaises(CatalogError):
            self.append("PREPARED")
        self.assertEqual(path.read_bytes(), before)

    def test_gap_blocked(self):
        self.append("PREPARED")
        with self.assertRaisesRegex(CatalogError, "JOURNAL_PHASE_ORDER"):
            self.append("NEW_MOVED")

    def test_changed_record_blocked(self):
        self.append("PREPARED")
        self.record["new_sha256"] = "c"*64
        with self.assertRaisesRegex(CatalogError, "JOURNAL_RECORD_CHANGED"):
            self.append("OLD_MOVED")

    def test_partial_record_retained(self):
        path = self.root / j.FILES[0]
        path.write_bytes(b"{")
        with self.assertRaises(ValueError):
            self.append("PREPARED")
        self.assertEqual(path.read_bytes(), b"{")

    def test_unknown_entry_blocked(self):
        (self.root / "other").write_bytes(b"keep")
        with self.assertRaisesRegex(CatalogError, "JOURNAL_UNKNOWN_ENTRY"):
            self.append("PREPARED")

    def test_fsync_failure_leaves_evidence(self):
        with mock.patch.object(j.os, "fsync", side_effect=OSError("fixture failure")):
            with self.assertRaises(OSError):
                self.append("PREPARED")
        self.assertTrue((self.root / j.FILES[0]).exists())

    def test_existing_destination_at_open_not_overwritten(self):
        real_open = j.os.open
        path = self.root / j.FILES[0]
        def collision(target, flags, *args):
            if flags & j.os.O_EXCL:
                path.write_bytes(b"collision")
            return real_open(target, flags, *args)
        with mock.patch.object(j.os, "open", side_effect=collision):
            with self.assertRaises(FileExistsError):
                self.append("PREPARED")
        self.assertEqual(path.read_bytes(), b"collision")


if __name__ == "__main__":
    unittest.main()
