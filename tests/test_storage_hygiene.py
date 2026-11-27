"""TESSERA source-only storage policy, including committed Git tree evidence."""
import os
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
MAX_BLOB = 1024 * 1024
MAX_TREE_OUTPUT = 4 * 1024 * 1024
GENERATED = frozenset({
    b"__pycache__", b".pytest_cache", b".mypy_cache", b".ruff_cache",
    b".cache", b".venv", b"venv", b"node_modules", b".tox", b".nox",
    b"build", b"dist", b".tmp", b".tessera-local", b".external",
})
SUFFIXES = (b".pyc", b".pyo", b".tmp", b".log", b".exe", b".dll",
            b".pyd", b".whl", b".zip", b".tar", b".tar.gz", b".bak")
OID = re.compile(rb"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def assess(raw):
    """Report codes/counts only; this is TESSERA policy, not a deletion plan."""
    if not raw or len(raw) > MAX_TREE_OUTPUT or not raw.endswith(b"\0"):
        raise ValueError("STORAGE_TREE_FRAME_INVALID")
    violations = []
    names = set()
    total = 0
    for row in raw[:-1].split(b"\0"):
        header, separator, path = row.partition(b"\t")
        fields = header.split()
        if not separator or len(fields) != 4 or not path or path in names:
            raise ValueError("STORAGE_TREE_RECORD_INVALID")
        mode, kind, oid, size = fields
        if not OID.fullmatch(oid):
            raise ValueError("STORAGE_TREE_OID_INVALID")
        names.add(path)
        if kind != b"blob" or mode not in {b"100644", b"100755"}:
            violations.append("STORAGE_NON_SOURCE_ENTRY")
            continue
        if not size.isdigit() or len(size) > 20:
            raise ValueError("STORAGE_TREE_SIZE_INVALID")
        count = int(size)
        total += count
        if count > MAX_BLOB:
            violations.append("STORAGE_BLOB_BUDGET")
        parts = path.lower().split(b"/")
        if any(part in GENERATED for part in parts) or parts[-1].endswith(SUFFIXES):
            violations.append("STORAGE_GENERATED_FILE")
    return {"entries": len(names), "logical_blob_bytes": total,
            "violations": violations, "deletion_authorized": False}


def record(path, size, mode=b"100644", kind=b"blob"):
    return b" ".join((mode, kind, b"a" * 40, str(size).encode())) + b"\t" + path + b"\0"


class StorageHygieneTests(unittest.TestCase):
    def test_policy_rejects_generated_and_oversized(self):
        raw = record(b"src/code.py", 50) + record(b"build/file", 1) + record(b"src/a.PYC", 1)
        raw += record(b"big.txt", MAX_BLOB + 1)
        self.assertEqual(assess(raw)["violations"], [
            "STORAGE_GENERATED_FILE", "STORAGE_GENERATED_FILE", "STORAGE_BLOB_BUDGET"])

    def test_policy_preserves_source_and_reports_bytes(self):
        result = assess(record(b"src/a.py", 12) + record(b"README.md", 8))
        self.assertEqual(result["logical_blob_bytes"], 20)
        self.assertEqual(result["violations"], [])
        self.assertFalse(result["deletion_authorized"])

    def test_malformed_and_nonregular(self):
        for raw in (b"", record(b"a", 1)[:-1], record(b"a", 1) * 2, b"bad\0"):
            with self.assertRaises(ValueError):
                assess(raw)
        self.assertEqual(assess(record(b"link", 1, mode=b"120000"))["violations"],
                         ["STORAGE_NON_SOURCE_ENTRY"])

    def test_exact_checked_out_tree(self):
        # Trusted CI checkout only; do not discard inherited Git restrictions.
        self.assertFalse(any(key.upper().startswith("GIT_") and key.upper() != "GIT_PAGER"
                             for key in os.environ), "STORAGE_GIT_CONTEXT_UNSAFE")
        proc = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-r", "-l", "-z", "HEAD"],
                              stdin=subprocess.DEVNULL, capture_output=True,
                              timeout=20, check=False)
        self.assertEqual(proc.returncode, 0, "STORAGE_GIT_FAILED")
        result = assess(proc.stdout)
        self.assertEqual(result["violations"], [])


if __name__ == "__main__":
    unittest.main()
