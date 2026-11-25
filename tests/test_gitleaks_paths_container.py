import collections
import io
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import gitleaks_frame as f
import check_gitleaks_paths_container as c
import check_gitleaks_container as transport


class PathsContainerTests(unittest.TestCase):
    def test_all_categories(self):
        records = [(n, b"x") for n in range(10)]
        stream = io.BytesIO()
        digest = f.encode(records, stream, mode="paths")
        self.assertEqual(f.decode(io.BytesIO(stream.getvalue()), mode="paths"), (records, digest))
        with self.assertRaises(ValueError):
            f.decode(io.BytesIO(stream.getvalue()))

    def test_empty_paths(self):
        stream = io.BytesIO()
        digest = f.encode([], stream, mode="paths")
        self.assertEqual(f.decode(io.BytesIO(stream.getvalue()), mode="paths"), ([], digest))
        self.assertEqual(list(c.batches([])), [[]])

    def test_bad_categories(self):
        for n in (-1, 10, True):
            with self.assertRaises(ValueError):
                f.encode([(n, b"x")], io.BytesIO(), mode="paths")

    def test_distinct_fixed_entrypoint(self):
        args = transport.args_for("fixture", pathlib.PurePosixPath("/tmp/stage"), mode="paths")
        self.assertIn("check_gitleaks_paths_container", args[-1])
        self.assertIn("--network=none", args)
        with self.assertRaises(RuntimeError):
            transport.args_for("fixture", pathlib.PurePosixPath("/tmp/stage"), mode="unknown")

    def test_batch_limits(self):
        with mock.patch.object(c, "BATCH_COUNT", 3), mock.patch.object(c, "BATCH_BYTES", 4):
            self.assertEqual([len(x) for x in c.batches([(0, b"xx")] * 7)], [2, 2, 2, 1])
        with mock.patch.object(c, "MAX_TARGETS", 1), self.assertRaises(RuntimeError):
            list(c.batches([(0, b"x")] * 2))

    def test_report(self):
        report = {"digest": "d", "version": c.VERSION, "negative_fixtures": 5,
                  "fixture_top_level_entries_unchanged": "PASS",
                  "results": c.rows(collections.Counter({2: 1}), collections.Counter({2: 1}))}
        coverage, counts = c.validate(report, [(2, b"x")], "d")
        self.assertEqual(coverage[2], counts[2])
        self.assertEqual(len(report["results"]), 10)
        for change in ({"digest": "wrong"}, {"results": report["results"][:-1]},
                       {"results": report["results"][::-1]}, {"negative_fixtures": 0}):
            with self.assertRaises(RuntimeError):
                c.validate({**report, **change}, [(2, b"x")], "d")
        report["results"][0]["findings"] = 1
        with self.assertRaises(RuntimeError):
            c.validate(report, [(2, b"x")], "d")

    def test_short_write(self):
        class Short(io.BytesIO):
            def write(self, data):
                return max(0, len(data) - 1)
        with self.assertRaisesRegex(ValueError, "SHORT_WRITE"):
            f.encode([(0, b"x")], Short(), mode="paths")

    def test_snapshot_changes(self):
        a = c.path_snapshot({"x": b"a"}, {"oid": 1}, {("rule", "oid")}, 1)
        self.assertNotEqual(a, c.path_snapshot({"x": b"b"}, {"oid": 1}, {("rule", "oid")}, 1))
        self.assertNotEqual(a, c.path_snapshot({"x": b"a"}, {"oid": 1}, set(), 1))


if __name__ == "__main__":
    unittest.main()
