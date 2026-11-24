import collections
import io
import threading
import time
from unittest import mock
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import gitleaks_frame as f
import check_gitleaks_container as c


class FrameTests(unittest.TestCase):
    def sample(self):
        b = io.BytesIO()
        digest = f.encode([(0, b"test"), (1, b"")], b)
        return b.getvalue(), digest

    def test_roundtrip(self):
        raw, digest = self.sample()
        self.assertEqual(f.decode(io.BytesIO(raw)), ([(0, b"test"), (1, b"")], digest))

    def test_truncation_and_trailing(self):
        raw, _ = self.sample()
        for bad in [raw[:n] for n in range(len(raw))] + [raw + b"x"]:
            with self.assertRaises(ValueError):
                f.decode(io.BytesIO(bad))

    def test_invalid_content(self):
        for record in [(2, b"x"), (0, b"\0"), (0, b"\xff"), (0, b"x" * (f.MAX_FILE + 1))]:
            with self.assertRaises(ValueError):
                f.encode([record], io.BytesIO())

    def test_invalid_header(self):
        for count, total in [(0, 0), (2049, 0), (1, f.MAX_TOTAL + 1)]:
            with self.assertRaises(ValueError):
                f.decode(io.BytesIO(f.HEADER.pack(b"TSG1", count, total)))

    def test_invalid_record_length(self):
        with self.assertRaises(ValueError):
            f.decode(io.BytesIO(f.HEADER.pack(b"TSG1", 1, 0) + f.RECORD.pack(0, 1)))

    def test_category_changes_digest(self):
        a, b = io.BytesIO(), io.BytesIO()
        self.assertNotEqual(f.encode([(0, b"x")], a), f.encode([(1, b"x")], b))

    def test_profile(self):
        args = c.args_for("fixture", pathlib.Path("/tmp/stage"))
        for x in ("--network=none", "--read-only", "--user=65534:65534",
                  "--cap-drop=ALL", "--log-driver=none", "--memory=512m", "--pids-limit=64"):
            self.assertIn(x, args)
        self.assertEqual(args.count("--mount"), 1)
        self.assertNotIn("--privileged", args)

    def test_parity(self):
        host = dict.fromkeys(("version", "files", "scanned_nonempty", "empty", "bytes_scanned",
                              "by_rule", "findings", "clean_fixture", "negative_allow_fixture",
                              "fixture_redaction", "fixture_top_level_entries_unchanged"), 1)
        report = {**host, "digest": "a"}
        c.verify(report, host, "a")
        for change in ({"digest": "b"}, {"files": 2}, {"extra": "x"}):
            with self.assertRaisesRegex(RuntimeError, "PARITY"):
                c.verify({**report, **change}, host, "a")


    def test_parallel_scan_exact_coverage(self):
        barrier = threading.Barrier(2, timeout=5)
        visited = []
        def scan(cli, temp, env, data):
            visited.append(data)
            if data in (b"a", b"b"):
                barrier.wait()
            return collections.Counter({"fixture-rule": 1}), b"", b""
        with mock.patch.object(c, "scan", side_effect=scan):
            result = c.scan_records(None, None, {}, [(0, b"a"), (1, b"b"), (0, b""),
                                                   (0, b"c"), (1, b"d")], time.monotonic())
        self.assertCountEqual(visited, [b"a", b"b", b"c", b"d"])
        self.assertEqual(result, {("other", "fixture-rule"): 2, ("tests", "fixture-rule"): 2})

    def test_parallel_scan_failure_stops_next_window(self):
        visited = []
        def scan(cli, temp, env, data):
            visited.append(data)
            if data == b"a":
                raise RuntimeError("synthetic failure")
            return collections.Counter(), b"", b""
        with mock.patch.object(c, "scan", side_effect=scan), self.assertRaisesRegex(RuntimeError, "synthetic"):
            c.scan_records(None, None, {}, [(0, b"a"), (0, b"b"), (0, b"c")], time.monotonic())
        self.assertNotIn(b"c", visited)

    def test_parallel_scan_expired_deadline(self):
        with mock.patch.object(c, "scan") as scan, self.assertRaisesRegex(RuntimeError, "TIMEOUT"):
            c.scan_records(None, None, {}, [(0, b"a")], time.monotonic() - c.SCAN_SECONDS - 1)
        scan.assert_not_called()


if __name__ == "__main__":
    unittest.main()
