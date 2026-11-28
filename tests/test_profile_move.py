"""Real directory moves in isolated fixtures; no production profile access."""
import errno
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import profile_move as m
from profile_plan import Budget, inventory, snapshot
from catalog_index import CatalogError


@unittest.skipUnless(os.name == "nt" or sys.platform == "linux", "unsupported platform")
class MoveTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name).resolve()
        self.source, self.destination = root / "source", root / "destination"
        self.source.mkdir()
        self.destination.mkdir()
        self.skill = self.source / "alpha"
        self.skill.mkdir()
        (self.skill / "VERSION").write_bytes(b"0.0.2\n")
        (self.skill / "SKILL.md").write_bytes(b"fixture\n")
        budget = Budget()
        self.expected = snapshot(self.skill, inventory(self.skill, budget), budget)

    def move(self):
        return m.move_verified(self.source, self.destination, "alpha", self.expected)

    def test_move_retains_identity_and_bytes(self):
        before = self.skill.stat().st_ino
        result = self.move()
        self.assertEqual(result["status"], "MOVED_NO_REPLACE")
        self.assertFalse(result["apply_authorized"])
        self.assertFalse(self.skill.exists())
        self.assertEqual((self.destination / "alpha").stat().st_ino, before)
        self.assertEqual((self.destination / "alpha" / "SKILL.md").read_bytes(), b"fixture\n")

    def test_empty_destination_not_replaced(self):
        (self.destination / "alpha").mkdir()
        with self.assertRaises(FileExistsError):
            self.move()
        self.assertTrue(self.skill.exists())
        self.assertTrue((self.destination / "alpha").is_dir())

    def test_nonempty_destination_not_replaced(self):
        target = self.destination / "alpha"
        target.mkdir()
        (target / "marker").write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            self.move()
        self.assertEqual((target / "marker").read_bytes(), b"keep")

    def test_native_collision_refused(self):
        target = self.destination / "alpha"
        target.mkdir()
        with self.assertRaises(OSError):
            m.native_move(self.source, self.destination, "alpha",
                          m.metadata(self.source), m.metadata(self.destination))
        self.assertTrue(self.skill.exists())
        self.assertTrue(target.is_dir())

    def test_changed_source_refused(self):
        (self.skill / "SKILL.md").write_bytes(b"local edit")
        with self.assertRaisesRegex(CatalogError, "MOVE_SOURCE_CHANGED"):
            self.move()
        self.assertTrue(self.skill.exists())

    def test_invalid_name_refused(self):
        with self.assertRaisesRegex(CatalogError, "MOVE_NAME"):
            m.move_verified(self.source, self.destination, "../alpha", self.expected)

    def test_overlapping_roots_refused(self):
        with self.assertRaisesRegex(CatalogError, "PROFILE_OVERLAPPING_ROOTS"):
            m.move_verified(self.source, self.skill, "alpha", self.expected)

    def test_failure_does_not_retry(self):
        with mock.patch.object(m, "native_move", side_effect=OSError(errno.EIO, "fixture")) as call:
            with self.assertRaises(OSError):
                self.move()
            self.assertEqual(call.call_count, 1)
        self.assertTrue(self.skill.exists())

    def test_unrelated_skill_untouched(self):
        other = self.source / "other"
        other.mkdir()
        (other / "marker").write_bytes(b"keep")
        self.move()
        self.assertEqual((other / "marker").read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
