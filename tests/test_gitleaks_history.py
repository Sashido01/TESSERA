"""Offline object inventory validation; real history fixture runs in CI."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_gitleaks_history as h

A = "a" * 40
B = "b" * 40


class HistoryTests(unittest.TestCase):
    def test_blob_and_commit(self):
        self.assertEqual(h.blob_metadata(f"{A} blob 5\n{B} commit 10\n".encode(), {A, B}), {A: 5})

    def test_empty_blob(self):
        self.assertEqual(h.blob_metadata(f"{A} blob 0\n".encode(), {A}), {A: 0})

    def test_missing_object(self):
        with self.assertRaisesRegex(h.InstallCheckError, "MISSING"):
            h.blob_metadata(f"{A} missing\n".encode(), {A})

    def test_wrong_count(self):
        with self.assertRaisesRegex(h.InstallCheckError, "COUNT"):
            h.blob_metadata(f"{A} blob 5\n".encode(), {A, B})

    def test_duplicate(self):
        with self.assertRaisesRegex(h.InstallCheckError, "INVALID"):
            h.blob_metadata(f"{A} blob 5\n{A} blob 5\n".encode(), {A, B})

    def test_oversize(self):
        with self.assertRaisesRegex(h.InstallCheckError, "LIMIT"):
            h.blob_metadata(f"{A} blob {h.MAX_FILE + 1}\n".encode(), {A})

    def test_no_blobs(self):
        with self.assertRaisesRegex(h.InstallCheckError, "COVERAGE"):
            h.blob_metadata(f"{A} tree 1\n".encode(), {A})

    def test_unexpected_object(self):
        with self.assertRaisesRegex(h.InstallCheckError, "INVALID"):
            h.blob_metadata(f"{B} blob 1\n".encode(), {A})


if __name__ == "__main__":
    unittest.main()
