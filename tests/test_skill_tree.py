import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import profile_plan as p
import skill_tree as t


class SkillTreeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name).resolve()
        self.stage = self.root / "stage"
        self.skill = self.stage / "alpha"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_bytes(b"---\nname: alpha\ndescription: fixture\n---\n\n# Alpha\n")
        (self.skill / "VERSION").write_bytes(b"0.0.2\n")
        (self.skill / "a").mkdir()
        (self.skill / "a" / "nested.txt").write_bytes(b"fixture\x00\n")
        (self.skill / "a.txt").write_bytes(b"same prefix\n")
        (self.skill / ".hidden").write_bytes(b"")
        self.expected = t.snapshot_raw(self.skill, p.Budget())[1]

    def resolution(self, tree=None, names=("alpha",)):
        return json.dumps({"status": "RESOLVED", "repository": p.REPO,
                           "install_authorized": False, "operation": "update",
                           "selection": "EXPLICIT", "catalog_skill_count": 2,
                           "selected_count": len(names), "unselected_count": 2-len(names),
                           "skills": [{"id": name, "version": "0.0.2", "path": "skills/" + name,
                                       "ref": "refs/tags/" + name + "/v0.0.2", "tag_object": "a"*40,
                                       "commit": "b"*40, "tree": tree or self.expected} for name in names]}).encode()

    def verify(self, **kwargs):
        return t.verify(self.stage, self.resolution(**kwargs))

    def test_exact_git_tree_matches_actual_git_write_tree(self):
        if any(k.upper().startswith("GIT_") and k.upper() != "GIT_PAGER" for k in os.environ):
            raise RuntimeError("FIXTURE_GIT_CONTEXT_UNSAFE")
        env = {k: os.environ[k] for k in ("PATH", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT",
                                         "TEMP", "TMP", "TMPDIR", "LANG") if k in os.environ}
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
        repo = self.root / "git-fixture"
        shutil.copytree(self.skill, repo)
        def git(*args):
            return subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "core.filemode=false", *args],
                                  cwd=repo, env=env, capture_output=True, check=True, timeout=20).stdout.strip()
        git("init", "-q")
        git("add", "--", ".")
        actual = git("write-tree").decode("ascii")
        self.assertEqual(self.expected, actual)
        result = self.verify(tree=actual)
        self.assertEqual(result["skills"][0]["tree"], actual)
        self.assertFalse(result["apply_authorized"])
        self.assertEqual(result["resolution_authenticity"], "NOT_VERIFIED")
        _, digest = p.snapshot(self.skill, p.inventory(self.skill, p.Budget()), p.Budget())
        self.assertEqual(result["skills"][0]["stage_sha256"], digest)

    def test_same_size_content_change_rejected(self):
        (self.skill / "a.txt").write_bytes(b"evil prefix\n")
        with self.assertRaisesRegex(p.CatalogError, "OID_MISMATCH"):
            self.verify()

    def test_extra_and_empty_directory_rejected(self):
        extra = self.skill / "extra.txt"
        extra.write_bytes(b"extra")
        with self.assertRaisesRegex(p.CatalogError, "OID_MISMATCH"):
            self.verify()
        extra.unlink()
        (self.skill / "empty").mkdir()
        with self.assertRaisesRegex(p.CatalogError, "EMPTY_DIRECTORY"):
            self.verify()

    def test_gh_metadata_modified_skill_not_raw(self):
        (self.skill / "SKILL.md").write_bytes(b"---\nname: alpha\nmetadata: injected\n---\n# Alpha\n")
        with self.assertRaisesRegex(p.CatalogError, "OID_MISMATCH"):
            self.verify()

    def test_wrong_version_rejected_even_if_tree_matches(self):
        (self.skill / "VERSION").write_bytes(b"0.0.3\n")
        tree = t.snapshot_raw(self.skill, p.Budget())[1]
        with self.assertRaisesRegex(p.CatalogError, "VERSION_MISMATCH"):
            self.verify(tree=tree)

    def test_no_unselected_content_access(self):
        (self.stage / "beta").mkdir()
        (self.stage / "beta" / "private.txt").write_bytes(b"synthetic")
        with mock.patch.object(t, "read_file", wraps=t.read_file) as read:
            self.verify()
        self.assertFalse(any((self.stage / "beta") in x.args[0].parents for x in read.call_args_list))

    def test_unknown_alias_refused(self):
        (self.stage / "alpha").rename(self.stage / "ALPHA")
        with self.assertRaisesRegex(p.CatalogError, "NAME_ALIAS"):
            self.verify()

    def test_cross_skill_persistent_change_refused(self):
        shutil.copytree(self.skill, self.stage / "beta")
        original = t.snapshot_raw
        def changed(root, budget):
            result = original(root, budget)
            if root.name == "beta":
                (self.skill / "a.txt").write_bytes(b"persistent mutation")
            return result
        with mock.patch.object(t, "snapshot_raw", side_effect=changed):
            with self.assertRaisesRegex(p.CatalogError, "TREE_CHANGED"):
                self.verify(names=("alpha", "beta"))

    def test_hardlink_rejected(self):
        os.link(self.skill / "SKILL.md", self.root / "alias")
        with self.assertRaisesRegex(p.CatalogError, "SPECIAL_FILE"):
            self.verify()

    @unittest.skipIf(os.name == "nt", "POSIX executable bit fixture")
    def test_unexpected_executable_mode_rejected(self):
        (self.skill / "a.txt").chmod(0o755)
        with self.assertRaisesRegex(p.CatalogError, "TREE_MODE"):
            self.verify()
