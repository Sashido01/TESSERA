"""Real forced child exit, then independent process inspection."""
import os
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from profile_crash_fixture import run_crash_fixture
from catalog_index import CatalogError


@unittest.skipUnless(os.name == "nt" or sys.platform == "linux", "unsupported platform")
class CrashFixtureTests(unittest.TestCase):
    def test_update_boundaries(self):
        for point, expected in (("prepared", "NOT_STARTED"),
                                ("old_move", "OLD_IN_BACKUP"),
                                ("old_record", "OLD_IN_BACKUP"),
                                ("new_move", "NEW_PRESENT_OLD_RETAINED"),
                                ("new_record", "NEW_PRESENT_OLD_RETAINED")):
            with self.subTest(point=point):
                result = run_crash_fixture(point=point)
                self.assertEqual(result["state"], expected)
                self.assertEqual(result["interruption"], "PROCESS_KILLED")
                self.assertNotEqual(result["child_exitcode"], 0)
                self.assertTrue(result["fresh_process_observation"])
                self.assertTrue(result["unselected_preserved"])
                self.assertFalse(result["apply_authorized"])

    def test_install_boundaries(self):
        for point in ("prepared", "new_move", "new_record"):
            with self.subTest(point=point):
                result = run_crash_fixture("install", point)
                self.assertEqual(result["state"], "NOT_STARTED" if point == "prepared" else "NEW_PRESENT")
                self.assertEqual(result["layout"]["backup"], "ABSENT")

    def test_invalid_boundary(self):
        with self.assertRaises(CatalogError):
            run_crash_fixture("install", "old_move")


if __name__ == "__main__":
    unittest.main()
