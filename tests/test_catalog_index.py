import base64
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import catalog_index as c


def index():
    return {"schema_version": 1, "repository": c.REPO, "skills": [
        {"id": "alpha", "path": "skills/alpha", "version": "0.0.1",
         "ref": "refs/tags/alpha/v0.0.1"}]}


def encoded(obj):
    return json.dumps(obj).encode()


class CatalogIndexTests(unittest.TestCase):
    def test_exact_repository_source(self):
        rows = c.check_source(ROOT)
        self.assertGreaterEqual(len(rows), 1)

    def test_invalid_index(self):
        for change in ({"schema_version": True}, {"repository": "different/repo"},
                       {"skills": []}, {"extra": 1}):
            with self.subTest(change=change), self.assertRaises(c.CatalogError):
                c.parse_index(encoded({**index(), **change}))
        for change in ({"id": "../alpha"}, {"path": "skills/beta"}, {"version": "0.00.1"},
                       {"ref": "refs/heads/main"}, {"ref": "refs/tags/beta/v0.0.1"}):
            obj = index()
            obj["skills"][0].update(change)
            with self.subTest(change=change), self.assertRaises(c.CatalogError):
                c.parse_index(encoded(obj))
        obj = index()
        obj["skills"] *= 2
        with self.assertRaises(c.CatalogError):
            c.parse_index(encoded(obj))
        with self.assertRaises(c.CatalogError):
            c.parse_index(b'{"schema_version":1,"schema_version":1}')

    def test_source_version_and_extra_skill(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            (root / "skills/alpha").mkdir(parents=True)
            (root / "CATALOG.json").write_bytes(encoded(index()))
            (root / "VERSION").write_text("0.0.99")
            (root / "skills/alpha/SKILL.md").write_text("fixture")
            version = root / "skills/alpha/VERSION"
            version.write_text("0.0.2")
            with self.assertRaisesRegex(c.CatalogError, "SOURCE_VERSION"):
                c.check_source(root)
            version.write_text("0.0.1")
            self.assertEqual(c.check_source(root), index()["skills"])
            (root / "skills/beta").mkdir()
            with self.assertRaisesRegex(c.CatalogError, "SKILL_SET"):
                c.check_source(root)

    def test_latest_numeric_not_lexical(self):
        refs = [{"ref": "refs/tags/" + name} for name in
                ("v0.0.9", "v0.0.100", "v0.0.99", "v0.1.0", "alpha/v9.9.9", "v9.0.0-rc")]
        self.assertEqual(c.select_tag(refs), "0.1.0")
        self.assertEqual(c.select_tag(refs[:3]), "0.0.100")
        with self.assertRaises(c.CatalogError):
            c.select_tag(refs[:1] * 2)

    def fixture(self):
        api = {}
        def blob(raw):
            sha = hashlib.sha1(("blob %d\0" % len(raw)).encode() + raw).hexdigest()
            api["git/blobs/" + sha] = {"sha": sha, "encoding": "base64", "size": len(raw),
                                      "content": base64.b64encode(raw).decode()}
            return sha
        def row(name, sha, kind="blob"):
            return {"path": name, "sha": sha, "type": kind,
                    "mode": "100644" if kind == "blob" else "040000"}
        def tree(sha, rows):
            api["git/trees/" + sha] = {"sha": sha, "truncated": False, "tree": rows}
        def tag(name, sha, commit):
            api["git/ref/tags/" + name] = {"ref": "refs/tags/" + name,
                                            "object": {"type": "tag", "sha": sha}}
            api["git/tags/" + sha] = {"sha": sha, "tag": name, "message": "fixture",
                                     "object": {"type": "commit", "sha": commit}}
        api["git/matching-refs/tags/v"] = [{"ref": "refs/tags/v0.0.99"}]
        tag("v0.0.99", "a"*40, "b"*40)
        tag("alpha/v0.0.1", "c"*40, "d"*40)
        api["git/commits/"+"b"*40] = {"sha": "b"*40, "tree": {"sha": "e"*40}}
        api["git/commits/"+"d"*40] = {"sha": "d"*40, "tree": {"sha": "f"*40}}
        tree("e"*40, [row("VERSION", blob(b"0.0.99\n")),
                      row("CATALOG.json", blob(encoded(index()))), row("skills", "1"*40, "tree")])
        tree("f"*40, [row("skills", "2"*40, "tree")])
        tree("1"*40, [row("alpha", "3"*40, "tree")])
        tree("2"*40, [row("alpha", "3"*40, "tree")])
        tree("3"*40, [row("VERSION", blob(b"0.0.1\n")), row("SKILL.md", blob(b"fixture"))])
        return api

    def test_exact_tag_and_tree(self):
        api = self.fixture()
        result = c.resolve(api.__getitem__)
        self.assertEqual(result["catalog_commit"], "b"*40)
        self.assertEqual(result["skills"][0]["tree"], "3"*40)
        self.assertEqual(result["skills"][0]["commit"], "d"*40)
        self.assertFalse(result["install_authorized"])
        self.assertEqual(result["local_state"], "NOT_VERIFIED")
        self.assertEqual(c.resolve(api.__getitem__, "0.0.99")["api_calls"], result["api_calls"]-2)

    def test_ref_annotation_and_direct_target_required(self):
        for path, replacement in (
            ("git/ref/tags/v0.0.99", {"ref": "refs/tags/v0.0.99", "object": {"type": "commit", "sha": "b"*40}}),
            ("git/tags/"+"a"*40, {"sha": "a"*40, "tag": "v0.0.99", "message": "fixture",
                                  "object": {"type": "tag", "sha": "c"*40}})):
            api = self.fixture()
            api[path] = replacement
            with self.assertRaises(c.CatalogError):
                c.resolve(api.__getitem__)

    def test_truncated_or_mismatched_tree(self):
        api = self.fixture()
        api["git/trees/"+"2"*40]["truncated"] = True
        with self.assertRaisesRegex(c.CatalogError, "TREE"):
            c.resolve(api.__getitem__)
        api = self.fixture()
        api["git/trees/"+"2"*40]["tree"][0]["sha"] = "4"*40
        with self.assertRaisesRegex(c.CatalogError, "SKILL_TREE_MISMATCH"):
            c.resolve(api.__getitem__)

    def test_blob_corruption(self):
        api = self.fixture()
        path = next(k for k in api if k.startswith("git/blobs/"))
        api[path]["content"] = base64.b64encode(b"0.0.98\n").decode()
        with self.assertRaisesRegex(c.CatalogError, "BLOB_HASH"):
            c.resolve(api.__getitem__)

    def test_no_fallback_to_main_or_older_tag(self):
        api = self.fixture()
        api["git/matching-refs/tags/v"].append({"ref": "refs/tags/v0.1.0"})
        calls = []
        def get(path):
            calls.append(path)
            if path not in api:
                raise c.CatalogError("API_FAILED")
            return api[path]
        with self.assertRaisesRegex(c.CatalogError, "API_FAILED"):
            c.resolve(get)
        self.assertEqual(calls, ["git/matching-refs/tags/v", "git/ref/tags/v0.1.0"])

    def test_persistent_ref_move_and_new_catalog_tag_blocked(self):
        for target in ("git/ref/tags/alpha/v0.0.1", "git/matching-refs/tags/v"):
            api = self.fixture()
            hits = 0
            def get(path):
                nonlocal hits
                if path == target:
                    hits += 1
                    if hits == 2:
                        if target.endswith("/v"):
                            return [*api[path], {"ref": "refs/tags/v0.1.0"}]
                        return {**api[path], "object": {"type": "tag", "sha": "9"*40}}
                return api[path]
            with self.subTest(target=target), self.assertRaisesRegex(c.CatalogError, "CHANGED"):
                c.resolve(get)
