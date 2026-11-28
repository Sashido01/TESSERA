"""Integrated transaction fixtures on actual temporary directories."""
import os
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from profile_transaction_fixture import run_fixture
from catalog_index import CatalogError


@unittest.skipUnless(os.name == "nt" or sys.platform == "linux", "unsupported platform")
class TransactionFixtureTests(unittest.TestCase):
    def test_update_complete(self):
        result = run_fixture()
        self.assertEqual(result["phases"], ["PREPARED", "OLD_MOVED", "NEW_MOVED", "VERIFIED"])
        self.assertEqual(result["layout"], {"profile": "NEW", "stage": "ABSENT", "backup": "OLD"})
        self.assertTrue(result["unselected_preserved"])
        self.assertFalse(result["apply_authorized"])

    def test_install_complete(self):
        result = run_fixture("install")
        self.assertEqual(result["phases"], ["PREPARED", "NEW_MOVED", "VERIFIED"])
        self.assertEqual(result["layout"], {"profile": "NEW", "stage": "ABSENT", "backup": "ABSENT"})

    def test_update_interruptions(self):
        cases = {
            "prepared": ("NOT_STARTED", ["PREPARED"]),
            "old_move": ("OLD_IN_BACKUP", ["PREPARED"]),
            "old_record": ("OLD_IN_BACKUP", ["PREPARED", "OLD_MOVED"]),
            "new_move": ("NEW_PRESENT_OLD_RETAINED", ["PREPARED", "OLD_MOVED"]),
            "new_record": ("NEW_PRESENT_OLD_RETAINED", ["PREPARED", "OLD_MOVED", "NEW_MOVED"]),
        }
        for point, (state, phases) in cases.items():
            with self.subTest(point=point):
                result = run_fixture(interrupt=point)
                self.assertEqual(result["state"], state)
                self.assertEqual(result["phases"], phases)
                self.assertTrue(result["unselected_preserved"])
                self.assertEqual(result["interruption"], "SIMULATED")

    def test_install_interruptions(self):
        for point in ("prepared", "new_move", "new_record"):
            with self.subTest(point=point):
                result = run_fixture("install", interrupt=point)
                self.assertEqual(result["state"], "NOT_STARTED" if point == "prepared" else "NEW_PRESENT")
                self.assertEqual(result["layout"]["backup"], "ABSENT")

    def test_invalid_operation(self):
        with self.assertRaises(CatalogError):
            run_fixture("other")

    def test_invalid_interrupt(self):
        with self.assertRaises(CatalogError):
            run_fixture("install", interrupt="old_move")


if __name__ == "__main__":
    unittest.main()
