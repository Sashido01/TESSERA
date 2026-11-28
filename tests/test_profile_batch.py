"""Real temporary raw trees, transformed stages and batch plan observations."""
import json
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import profile_batch as b
import profile_plan as p
import skill_tree as t
import gh_stage as g
from catalog_index import REPO, CatalogError


class BatchTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name).resolve()
        self.profile, self.raw, self.stage, self.old_raw, self.old = [
            root / x for x in ("profile", "raw", "stage", "old-raw", "old")]
        for path in (self.profile, self.raw, self.stage, self.old_raw, self.old):
            path.mkdir()
        self.new_rows = [self.skill(self.raw, self.stage, name, "0.0.2")
                         for name in ("alpha", "beta", "gamma")]
        self.old_rows = [self.skill(self.old_raw, self.old, name, "0.0.1")
                         for name in ("alpha", "beta")]
        other = self.profile / "other"
        other.mkdir()
        (other / "marker").write_bytes(b"untouched")

    def skill(self, raw, stage, name, ver):
        folder = raw / name
        folder.mkdir()
        (folder / "VERSION").write_bytes((ver + "\n").encode())
        (folder / "SKILL.md").write_bytes(
            ("---\nname: " + name + "\ndescription: >-\n  Fixture description.\n"
             "license: MIT\n---\n\nBody\n").encode())
        (folder / "data.txt").write_bytes(("fixture " + ver).encode())
        shutil.copytree(folder, stage / name)
        tree = t.snapshot_raw(folder, p.Budget())[1]
        ref = "refs/tags/" + name + "/v" + ver
        (stage / name / "SKILL.md").write_bytes(
            ("---\ndescription: Fixture description.\nlicense: MIT\nmetadata:\n"
             "    github-path: skills/" + name + "\n"
             "    github-pinned: " + ref + "\n    github-ref: " + ref +
             "\n    github-repo: https://github.com/" + REPO +
             "\n    github-tree-sha: " + tree + "\nname: " + name + "\n---\nBody\n").encode())
        return {"id": name, "version": ver, "path": "skills/" + name, "ref": ref,
                "tree": tree, "tag_object": "a"*40, "commit": "b"*40}

    def resolution(self, rows, operation="update", all_skills=False):
        return json.dumps({"status": "RESOLVED", "repository": REPO,
                           "install_authorized": False, "operation": operation,
                           "selection": "ALL" if all_skills else "EXPLICIT",
                           "catalog_skill_count": 3, "selected_count": len(rows),
                           "unselected_count": 3-len(rows), "skills": rows}).encode()

    def preflight(self, rows=None, old=None, operation="update", all_skills=False):
        rows = self.new_rows if rows is None else rows
        kwargs = {} if old is None else {"baseline": self.old, "baseline_raw": self.old_raw,
                                        "baseline_resolution": self.resolution(old)}
        return b.preflight(self.profile, self.stage, self.raw,
                           self.resolution(rows, operation, all_skills), **kwargs)

    def test_all_mixed_update_install_skip(self):
        shutil.copytree(self.old / "alpha", self.profile / "alpha")
        shutil.copytree(self.stage / "gamma", self.profile / "gamma")
        result = self.preflight(old=self.old_rows, all_skills=True)
        self.assertEqual([(r["id"], r["operation"]) for r in result["records"]],
                         [("alpha", "update"), ("beta", "install")])
        self.assertEqual([r["id"] for r in result["skipped"]], ["gamma"])
        self.assertFalse(result["apply_authorized"])
        self.assertEqual(result["source_authenticity"], "NOT_VERIFIED")
        self.assertEqual((self.profile / "alpha" / "VERSION").read_bytes(), b"0.0.1\n")
        self.assertFalse((self.profile / "beta").exists())
        self.assertEqual((self.profile / "other" / "marker").read_bytes(), b"untouched")

    def test_single_install_does_not_read_unselected(self):
        with mock.patch.object(g, "snapshot_raw", wraps=g.snapshot_raw) as read:
            result = self.preflight(self.new_rows[:1], operation="install")
        self.assertEqual([r["id"] for r in result["records"]], ["alpha"])
        self.assertEqual([call.args[0].name for call in read.call_args_list], ["alpha"])
        self.assertFalse((self.profile / "alpha").exists())

    def test_two_matching_skills_noop(self):
        for name in ("alpha", "beta"):
            shutil.copytree(self.stage / name, self.profile / name)
        result = self.preflight(self.new_rows[:2])
        self.assertEqual(result["records"], [])
        self.assertEqual([r["id"] for r in result["skipped"]], ["alpha", "beta"])

    def test_one_local_edit_blocks_entire_plan(self):
        shutil.copytree(self.old / "beta", self.profile / "beta")
        path = self.profile / "beta" / "data.txt"
        path.write_bytes(b"local edit")
        with self.assertRaisesRegex(CatalogError, "BATCH_PLAN_BLOCKED"):
            self.preflight(old=self.old_rows)
        self.assertFalse((self.profile / "alpha").exists())
        self.assertEqual(path.read_bytes(), b"local edit")

    def test_baseline_must_have_independent_pin(self):
        shutil.copytree(self.old / "alpha", self.profile / "alpha")
        with self.assertRaisesRegex(CatalogError, "BATCH_BASELINE_PROOF_REQUIRED"):
            self.preflight(old=self.old_rows[1:])
        self.assertEqual((self.profile / "alpha" / "VERSION").read_bytes(), b"0.0.1\n")

    def test_tampered_old_raw_blocks(self):
        shutil.copytree(self.old / "alpha", self.profile / "alpha")
        (self.old_raw / "alpha" / "data.txt").write_bytes(b"changed")
        with self.assertRaisesRegex(CatalogError, "GH_RAW_TREE_MISMATCH"):
            self.preflight(old=self.old_rows)

    def test_new_stage_mutation_blocks(self):
        (self.stage / "beta" / "data.txt").write_bytes(b"changed")
        with self.assertRaisesRegex(CatalogError, "GH_FILE_CHANGED"):
            self.preflight()
        self.assertFalse((self.profile / "alpha").exists())

    def test_proof_digest_must_match_plan(self):
        real = b.plan
        def changed(*args):
            result = real(*args)
            result["decisions"][0]["stage_sha256"] = "c"*64
            return result
        with mock.patch.object(b, "plan", side_effect=changed):
            with self.assertRaisesRegex(CatalogError, "BATCH_STAGE_CHANGED"):
                self.preflight()

    def test_old_proof_digest_must_match_plan(self):
        shutil.copytree(self.old / "alpha", self.profile / "alpha")
        real = b.plan
        def changed(*args):
            result = real(*args)
            result["decisions"][0]["baseline_sha256"] = "c"*64
            return result
        with mock.patch.object(b, "plan", side_effect=changed):
            with self.assertRaisesRegex(CatalogError, "BATCH_BASELINE_CHANGED"):
                self.preflight(old=self.old_rows)

    def test_old_proof_cannot_include_unselected(self):
        with self.assertRaisesRegex(CatalogError, "BATCH_BASELINE_SELECTION"):
            self.preflight(self.new_rows[:1], old=self.old_rows)

    def test_overlapping_roots_blocked(self):
        with self.assertRaisesRegex(CatalogError, "OVERLAPPING"):
            b.preflight(self.profile, self.stage, self.stage, self.resolution(self.new_rows))

    def test_raw_proof_uses_same_read_for_tree_and_comparison(self):
        # The comparison must not re-read a different raw file after hashing it.
        with mock.patch.object(g, "read_file", wraps=g.read_file) as read:
            self.preflight(self.new_rows[:1])
        self.assertTrue(read.call_args_list)
        self.assertTrue(all(call.args[0].is_relative_to(self.stage) for call in read.call_args_list))


if __name__ == "__main__":
    unittest.main()
