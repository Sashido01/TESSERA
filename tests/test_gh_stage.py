"""UP02.02 restricted frontmatter and whole-tree comparison regressions."""
import json
import pathlib
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import gh_stage as g
import profile_plan as p
import skill_tree as t


class GhStageTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name).resolve()
        self.raw, self.stage = root / "raw", root / "stage"
        skill = self.raw / "alpha"
        skill.mkdir(parents=True)
        self.original = b"---\nname: alpha\ndescription: >-\n  First line\n  second line.\nlicense: MIT\n---\n\nBody\n"
        (skill / "SKILL.md").write_bytes(self.original)
        (skill / "VERSION").write_bytes(b"0.0.2\n")
        (skill / "data.txt").write_bytes(b"fixture")
        shutil.copytree(self.raw, self.stage)
        tree = t.snapshot_raw(skill, p.Budget())[1]
        ref = "refs/tags/alpha/v0.0.2"
        self.row = {"id": "alpha", "path": "skills/alpha", "version": "0.0.2",
                    "ref": ref, "tag_object": "a"*40, "commit": "b"*40, "tree": tree}
        self.resolution = json.dumps({"status": "RESOLVED", "repository": p.REPO,
            "install_authorized": False, "operation": "update", "selection": "EXPLICIT",
            "catalog_skill_count": 1, "selected_count": 1, "unselected_count": 0,
            "skills": [self.row]}).encode()
        self.installed = ("---\ndescription: First line second line.\nlicense: MIT\nmetadata:\n"
                          "    github-path: skills/alpha\n"
                          "    github-pinned: " + ref + "\n"
                          "    github-ref: " + ref + "\n"
                          "    github-repo: https://github.com/Sashido01/TESSERA\n"
                          "    github-tree-sha: " + tree + "\nname: alpha\n---\nBody\n").encode()
        self.path = self.stage / "alpha" / "SKILL.md"
        self.path.write_bytes(self.installed)

    def verify(self):
        return g.verify(self.raw, self.stage, self.resolution)

    def test_exact_transformation_and_profile_digest(self):
        result = self.verify()
        _, digest = p.snapshot(self.stage / "alpha", p.inventory(self.stage / "alpha", p.Budget()), p.Budget())
        self.assertEqual(result["skills"][0]["stage_sha256"], digest)
        self.assertFalse(result["apply_authorized"])
        self.assertEqual(result["lockfile"], "NOT_VERIFIED")

    def test_modified_description(self):
        self.path.write_bytes(self.installed.replace(b"First line", b"Other line"))
        with self.assertRaisesRegex(p.CatalogError, "GH_HEADER_CHANGED"):
            self.verify()

    def test_wrong_ref(self):
        self.path.write_bytes(self.installed.replace(b"github-ref: refs/tags/alpha", b"github-ref: refs/tags/other"))
        with self.assertRaisesRegex(p.CatalogError, "GH_METADATA_MISMATCH"):
            self.verify()

    def test_duplicate_key(self):
        self.path.write_bytes(self.installed.replace(b"metadata:", b"name: alpha\nmetadata:"))
        with self.assertRaisesRegex(p.CatalogError, "GH_HEADER_KEY"):
            self.verify()

    def test_extra_metadata(self):
        self.path.write_bytes(self.installed.replace(b"metadata:", b"metadata:\n    local-path: other"))
        with self.assertRaisesRegex(p.CatalogError, "GH_METADATA_MISMATCH"):
            self.verify()

    def test_body_change(self):
        self.path.write_bytes(self.installed.replace(b"Body", b"Other"))
        with self.assertRaisesRegex(p.CatalogError, "GH_BODY_CHANGED"):
            self.verify()

    def test_other_file_change(self):
        (self.stage / "alpha" / "data.txt").write_bytes(b"changed")
        with self.assertRaisesRegex(p.CatalogError, "GH_FILE_CHANGED"):
            self.verify()

    def test_extra_file(self):
        (self.stage / "alpha" / "extra").write_bytes(b"x")
        with self.assertRaisesRegex(p.CatalogError, "GH_INVENTORY_MISMATCH"):
            self.verify()

    def test_raw_tree_change(self):
        (self.raw / "alpha" / "data.txt").write_bytes(b"changed")
        with self.assertRaisesRegex(p.CatalogError, "GH_RAW_TREE_MISMATCH"):
            self.verify()

    def test_unsupported_yaml_alias(self):
        self.path.write_bytes(self.installed.replace(b"license: MIT", b"license: *alias"))
        with self.assertRaisesRegex(p.CatalogError, "GH_HEADER_SCALAR"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
