#!/usr/bin/env python3
"""Read-only catalog verification and exact-pin resolution. Never installs skills."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time

REPO = "Sashido01/TESSERA"
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
VERSION = re.compile(r"(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]?)\.(0|[1-9][0-9]{0,8})\Z")
SHA = re.compile(r"[a-f0-9]{40}\Z")
MAX_INDEX = 64 * 1024
MAX_REPLY = 4 * 1024 * 1024
MAX_REFS = 4096
MAX_SKILLS = 100
MAX_CALLS = 640
MAX_SECONDS = 120


class CatalogError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise CatalogError(code)


def unique_pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, "CATALOG_DUPLICATE_KEY")
        result[key] = value
    return result


def decode(raw, limit):
    require(type(raw) is bytes and 0 < len(raw) <= limit, "CATALOG_SIZE")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs)


def version(value):
    require(isinstance(value, str) and VERSION.fullmatch(value), "CATALOG_VERSION")
    return tuple(map(int, value.split(".")))


def oid(value):
    require(isinstance(value, str) and SHA.fullmatch(value), "CATALOG_OID")
    return value


def parse_index(raw):
    obj = decode(raw, MAX_INDEX)
    require(isinstance(obj, dict) and set(obj) == {"schema_version", "repository", "skills"}
            and type(obj["schema_version"]) is int and obj["schema_version"] == 1
            and obj["repository"] == REPO, "CATALOG_SCHEMA")
    rows = obj["skills"]
    require(isinstance(rows, list) and 0 < len(rows) <= MAX_SKILLS, "CATALOG_SKILLS")
    names = []
    for row in rows:
        require(isinstance(row, dict) and set(row) == {"id", "path", "version", "ref"},
                "CATALOG_ENTRY")
        name = row["id"]
        require(isinstance(name, str) and len(name) <= 64 and NAME.fullmatch(name), "CATALOG_NAME")
        version(row["version"])
        require(row["path"] == "skills/" + name
                and row["ref"] == "refs/tags/" + name + "/v" + row["version"], "CATALOG_PIN")
        names.append(name)
    require(names == sorted(set(names)), "CATALOG_ORDER_OR_DUPLICATE")
    return rows


def check_source(root):
    root = pathlib.Path(root)
    rows = parse_index((root / "CATALOG.json").read_bytes())
    version((root / "VERSION").read_text(encoding="utf-8").strip())
    directory = root / "skills"
    require(directory.is_dir() and not directory.is_symlink(), "CATALOG_SOURCE")
    actual = []
    for child in directory.iterdir():
        require(child.is_dir() and not child.is_symlink(), "CATALOG_SOURCE")
        actual.append(child.name)
    require(sorted(actual) == [r["id"] for r in rows], "CATALOG_SKILL_SET")
    for row in rows:
        folder = root / row["path"]
        require((folder / "VERSION").is_file() and not (folder / "VERSION").is_symlink()
                and (folder / "VERSION").read_text(encoding="utf-8").strip() == row["version"]
                and (folder / "SKILL.md").is_file() and not (folder / "SKILL.md").is_symlink(),
                "CATALOG_SOURCE_VERSION")
    return rows


def select_tag(refs):
    require(isinstance(refs, list) and 0 < len(refs) <= MAX_REFS, "CATALOG_REF_LIMIT")
    found = {}
    for item in refs:
        require(isinstance(item, dict) and isinstance(item.get("ref"), str), "CATALOG_REF")
        ref = item["ref"]
        if not ref.startswith("refs/tags/v"):
            continue
        name = ref[len("refs/tags/v"):]
        if not VERSION.fullmatch(name):
            continue
        key = version(name)
        require(key not in found, "CATALOG_REF_DUPLICATE")
        found[key] = name
    require(bool(found), "CATALOG_NO_TAG")
    return found[max(found)]


def selection(skills, all_skills):
    """Explicit selection; never widen a mistyped or empty request."""
    require(type(all_skills) is bool and isinstance(skills, (list, tuple))
            and len(skills) <= MAX_SKILLS, "CATALOG_SELECTION")
    require((all_skills and not skills) or (not all_skills and bool(skills)),
            "CATALOG_SELECTION")
    require(all(isinstance(name, str) and len(name) <= 64 and NAME.fullmatch(name)
                for name in skills), "CATALOG_SELECTION_NAME")
    require(len(set(skills)) == len(skills), "CATALOG_SELECTION_DUPLICATE")
    return set(skills)


def resolve(get, requested=None, *, skills=(), all_skills=False, operation):
    """Resolve selected pins through a trusted read-only API. No fallback."""
    names = selection(skills, all_skills)
    require(operation in ("install", "update"), "CATALOG_OPERATION")
    if requested is not None:
        version(requested)
    cache = {}
    observed_refs = {}
    calls = 0

    def fresh(path):
        nonlocal calls
        require(calls < MAX_CALLS, "CATALOG_CALL_LIMIT")
        calls += 1
        return get(path)

    def fetch(path):
        if path not in cache:
            cache[path] = fresh(path)
        return cache[path]

    def annotated(ref):
        info = fetch("git/ref/" + ref.removeprefix("refs/"))
        require(isinstance(info, dict) and info.get("ref") == ref, "CATALOG_REF_MISMATCH")
        obj = info.get("object")
        require(isinstance(obj, dict) and obj.get("type") == "tag", "CATALOG_ANNOTATED_REQUIRED")
        tag_sha = oid(obj.get("sha"))
        observed_refs[ref] = tag_sha
        tag = fetch("git/tags/" + tag_sha)
        require(isinstance(tag, dict) and tag.get("sha") == tag_sha
                and tag.get("tag") == ref.removeprefix("refs/tags/")
                and isinstance(tag.get("message"), str) and tag["message"].strip(),
                "CATALOG_TAG_MISMATCH")
        target = tag.get("object")
        require(isinstance(target, dict) and target.get("type") == "commit", "CATALOG_DIRECT_COMMIT")
        return tag_sha, oid(target.get("sha"))

    def tree(commit):
        info = fetch("git/commits/" + commit)
        require(isinstance(info, dict) and info.get("sha") == commit
                and isinstance(info.get("tree"), dict), "CATALOG_COMMIT")
        return oid(info["tree"].get("sha"))

    def entries(sha):
        data = fetch("git/trees/" + sha)
        require(isinstance(data, dict) and data.get("sha") == sha
                and data.get("truncated") is False and isinstance(data.get("tree"), list)
                and len(data["tree"]) <= 4096, "CATALOG_TREE")
        result = {}
        for row in data["tree"]:
            require(isinstance(row, dict) and isinstance(row.get("path"), str)
                    and row["path"] not in result, "CATALOG_TREE_ENTRY")
            result[row["path"]] = row
        return result

    def entry(rows, name, kind, mode):
        row = rows.get(name)
        require(isinstance(row, dict) and row.get("type") == kind and row.get("mode") == mode,
                "CATALOG_TREE_ENTRY")
        return oid(row.get("sha"))

    def blob(rows, name):
        sha = entry(rows, name, "blob", "100644")
        data = fetch("git/blobs/" + sha)
        require(isinstance(data, dict) and data.get("sha") == sha and data.get("encoding") == "base64"
                and type(data.get("size")) is int and 0 <= data["size"] <= MAX_INDEX
                and isinstance(data.get("content"), str)
                and len(data["content"]) <= MAX_INDEX * 2, "CATALOG_BLOB")
        raw = base64.b64decode(data["content"].replace("\n", ""), validate=True)
        require(len(raw) == data["size"]
                and hashlib.sha1(("blob %d\0" % len(raw)).encode("ascii") + raw).hexdigest() == sha,
                "CATALOG_BLOB_HASH")
        return raw

    selected = requested if requested is not None else select_tag(fetch("git/matching-refs/tags/v"))
    version(selected)
    catalog_ref = "refs/tags/v" + selected
    tag_sha, commit = annotated(catalog_ref)
    root = entries(tree(commit))
    require(blob(root, "VERSION").decode("utf-8").strip() == selected, "CATALOG_ROOT_VERSION")
    rows = parse_index(blob(root, "CATALOG.json"))
    catalog_skills = entries(entry(root, "skills", "tree", "040000"))
    require(set(catalog_skills) == {row["id"] for row in rows}, "CATALOG_SKILL_SET")
    for row in rows:
        entry(catalog_skills, row["id"], "tree", "040000")
    require(names.issubset(catalog_skills), "CATALOG_UNKNOWN_SKILL")
    selected_rows = rows if all_skills else [row for row in rows if row["id"] in names]
    resolved = []
    for row in selected_rows:
        skill_tag, skill_commit = annotated(row["ref"])
        skill_root = entries(tree(skill_commit))
        skill_dirs = entries(entry(skill_root, "skills", "tree", "040000"))
        skill_tree = entry(skill_dirs, row["id"], "tree", "040000")
        require(skill_tree == entry(catalog_skills, row["id"], "tree", "040000"),
                "CATALOG_SKILL_TREE_MISMATCH")
        skill_files = entries(skill_tree)
        require(blob(skill_files, "VERSION").decode("utf-8").strip() == row["version"],
                "CATALOG_SOURCE_VERSION")
        entry(skill_files, "SKILL.md", "blob", "100644")
        resolved.append({**row, "tag_object": skill_tag, "commit": skill_commit, "tree": skill_tree})
    # A second live observation catches persistent ref changes; not atomic.
    for ref, tag_object in observed_refs.items():
        info = fresh("git/ref/" + ref.removeprefix("refs/"))
        require(isinstance(info, dict) and info.get("ref") == ref
                and isinstance(info.get("object"), dict)
                and info["object"].get("type") == "tag"
                and info["object"].get("sha") == tag_object, "CATALOG_REF_CHANGED")
    if requested is None:
        require(select_tag(fresh("git/matching-refs/tags/v")) == selected,
                "CATALOG_LATEST_CHANGED")
    return {"status": "RESOLVED", "repository": REPO, "catalog_ref": catalog_ref,
            "catalog_tag_object": tag_sha, "catalog_commit": commit, "skills": resolved,
            "operation": operation, "selection": "ALL" if all_skills else "EXPLICIT",
            "catalog_skill_count": len(rows), "selected_count": len(resolved),
            "unselected_count": len(rows) - len(resolved),
            "install_authorized": False, "local_state": "NOT_VERIFIED",
            "publication": "NOT_VERIFIED", "snapshot_atomic": False, "api_calls": calls}


def gh_transport(executable):
    require(executable.is_absolute() and executable.is_file(), "CATALOG_GH_PATH")
    deadline = time.monotonic() + MAX_SECONDS

    def get(path):
        require(re.fullmatch(r"git/(?:matching-refs/tags/v|ref/tags/[a-z0-9./-]+|(?:tags|commits|trees|blobs)/[a-f0-9]{40})", path),
                "CATALOG_ENDPOINT")
        remaining = deadline - time.monotonic()
        require(remaining > 0, "CATALOG_TIMEOUT")
        run = subprocess.run([str(executable), "api", "--hostname", "github.com",
                              "--method", "GET", "repos/" + REPO + "/" + path],
                             stdin=subprocess.DEVNULL, capture_output=True,
                             timeout=min(20, remaining), check=False)
        require(run.returncode == 0 and time.monotonic() < deadline, "CATALOG_API_FAILED")
        return decode(run.stdout, MAX_REPLY)
    return get


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    check = sub.add_parser("check")
    check.add_argument("--root", required=True, type=pathlib.Path)
    remote = sub.add_parser("resolve")
    remote.add_argument("--gh", required=True, type=pathlib.Path)
    remote.add_argument("--version", help="Exact catalog version, not an individual skill version")
    remote.add_argument("--operation", choices=("install", "update"), required=True)
    scope = remote.add_mutually_exclusive_group(required=True)
    scope.add_argument("--skill", action="append", default=[], help="Exact skill ID; repeat for a subset")
    scope.add_argument("--all", action="store_true", help="All skills in the selected catalog")
    args = parser.parse_args()
    try:
        if args.action == "check":
            result = {"status": "SOURCE_VERIFIED", "skills": check_source(args.root),
                      "publication": "NOT_VERIFIED", "install_authorized": False}
        else:
            result = resolve(gh_transport(args.gh), args.version, skills=args.skill,
                             all_skills=args.all, operation=args.operation)
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, CatalogError) else "CATALOG_RUNTIME"), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
