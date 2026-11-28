#!/usr/bin/env python3
"""Read-only comparison of exact raw trees and gh-transformed staging.

Supports a deliberately narrow scalar frontmatter subset, not arbitrary YAML.
Unsupported syntax fails closed. No client, lockfile, or apply authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import stat
import sys

from catalog_index import CatalogError, REPO, require
from profile_plan import (Budget, aliases, disjoint, identity, inventory, metadata,
                          ordinary_root, read_file, read_resolution, recheck_ancestors,
                          recheck_tree)
from skill_tree import snapshot_raw

KEYS = {"name", "description", "license", "compatibility"}
KEY = re.compile(r"([a-z][a-z0-9-]*):(?: (.*))?\Z")
MAX_HEADER = 16 * 1024


def scalar(value):
    # Plain strings only, or simple quoted strings without escape semantics.
    require(bool(value) and value == value.strip(), "GH_HEADER_SCALAR")
    if value[0] in ("'", '"'):
        require(len(value) >= 2 and value[-1] == value[0]
                and value[0] not in value[1:-1] and "\\" not in value[1:-1],
                "GH_HEADER_SCALAR")
        return value[1:-1]
    require(value[0] not in "!&*{}[]|>@`#%?:-"
            and not re.search(r"[:][ \t]|[ \t]#|:$", value)
            and not re.fullmatch(r"(?i:null|true|false|yes|no|on|off|~|[+-]?[0-9.]+)", value),
            "GH_HEADER_SCALAR")
    return value


def split(data):
    require(data.startswith(b"---\n") and b"\r" not in data[:MAX_HEADER],
            "GH_HEADER_FORMAT")
    head, sep, body = data[4:].partition(b"\n---\n")
    require(bool(sep) and 0 < len(head) <= MAX_HEADER, "GH_HEADER_FORMAT")
    lines = head.decode("utf-8").split("\n")
    require(all(line and not any(ord(ch) < 32 for ch in line)
                and line == line.rstrip() for line in lines), "GH_HEADER_FORMAT")
    return lines, body.lstrip(b"\n")


def parse(data):
    lines, body = split(data)
    values, tracking = {}, None
    i = 0
    while i < len(lines):
        match = KEY.fullmatch(lines[i])
        require(match is not None, "GH_HEADER_KEY")
        name, value = match.groups()
        require(name not in values and (name in KEYS or name == "metadata"),
                "GH_HEADER_KEY")
        i += 1
        if name == "metadata":
            require(tracking is None and value is None, "GH_METADATA_FORMAT")
            tracking = {}
            indent = None
            while i < len(lines) and lines[i].startswith(" "):
                line = lines[i]
                width = len(line) - len(line.lstrip(" "))
                if indent is None:
                    indent = width
                require(width == indent and width in (2, 4), "GH_METADATA_FORMAT")
                item = KEY.fullmatch(line[width:])
                require(item is not None and item[2] is not None
                        and item[1] not in tracking, "GH_METADATA_FORMAT")
                tracking[item[1]] = scalar(item[2])
                i += 1
            require(bool(tracking), "GH_METADATA_FORMAT")
        else:
            require(value is not None, "GH_HEADER_SCALAR")
            continuation = []
            indent = None
            while i < len(lines) and lines[i].startswith(" "):
                line = lines[i]
                width = len(line) - len(line.lstrip(" "))
                if indent is None:
                    indent = width
                require(width == indent and width in (2, 4), "GH_HEADER_SCALAR")
                continuation.append(line[width:])
                i += 1
            if value == ">-":
                require(bool(continuation), "GH_HEADER_SCALAR")
                # Folded block, no blank or more-indented lines accepted.
                values[name] = " ".join(continuation)
            else:
                require(not continuation, "GH_HEADER_SCALAR")
                values[name] = scalar(value)
    require({"name", "description"} <= values.keys(), "GH_HEADER_REQUIRED")
    return values, tracking, body


def compare_header(raw, installed, row):
    original, old_tracking, body = parse(raw)
    actual, tracking, actual_body = parse(installed)
    require(old_tracking is None and original == actual
            and original["name"] == row["id"], "GH_HEADER_CHANGED")
    expected = {"github-repo": "https://github.com/" + REPO,
                "github-path": row["path"], "github-ref": row["ref"],
                "github-pinned": row["ref"], "github-tree-sha": row["tree"]}
    require(tracking == expected, "GH_METADATA_MISMATCH")
    require(actual_body == (body if not body or body.endswith(b"\n") else body + b"\n"),
            "GH_BODY_CHANGED")


def verify(raw_root, stage, raw_resolution):
    resolution = read_resolution(raw_resolution)
    roots = [ordinary_root(p) for p in (raw_root, stage)]
    disjoint(roots)
    budget = Budget()
    identities = [identity(metadata(p)) for p in roots]
    selected = {row["id"] for row in resolution["skills"]}
    require(not any(aliases(p, selected, budget) for p in roots), "GH_NAME_ALIAS")
    observed, proofs = [], []
    for row in resolution["skills"]:
        original, installed = (p / row["id"] for p in roots)
        captured = {}
        version, tree, raw_digest, raw_rows = snapshot_raw(original, budget, capture=captured)
        require(version == row["version"] and tree == row["tree"], "GH_RAW_TREE_MISMATCH")
        stage_rows = inventory(installed, budget)
        require(set(raw_rows) == set(stage_rows), "GH_INVENTORY_MISMATCH")
        records = []
        for name, info in sorted(stage_rows.items()):
            budget.check()
            old = raw_rows[name]
            require(stat.S_IFMT(info.st_mode) == stat.S_IFMT(old.st_mode)
                    and stat.S_IMODE(info.st_mode) == stat.S_IMODE(old.st_mode),
                    "GH_MODE_MISMATCH")
            mode = stat.S_IMODE(info.st_mode)
            if stat.S_ISDIR(info.st_mode):
                records.append([name, "dir", mode])
                continue
            recheck_ancestors(original, original / name, raw_rows)
            recheck_ancestors(installed, installed / name, stage_rows)
            before = captured[name]
            after = read_file(installed / name, info, budget)
            if name == "SKILL.md":
                compare_header(before, after, row)
            else:
                require(before == after, "GH_FILE_CHANGED")
            records.append([name, "file", mode, len(after), hashlib.sha256(after).hexdigest()])
        digest = hashlib.sha256(json.dumps(records, separators=(",", ":")).encode()).hexdigest()
        observed.extend(((original, raw_rows), (installed, stage_rows)))
        proofs.append({"id": row["id"], "version": version, "ref": row["ref"],
                       "tree": tree, "tag_object": row["tag_object"], "commit": row["commit"],
                       "raw_sha256": raw_digest, "stage_sha256": digest})
    for root in roots:
        ordinary_root(root)
    require([identity(metadata(p)) for p in roots] == identities
            and not any(aliases(p, selected, budget) for p in roots), "GH_ROOT_CHANGED")
    for root, rows in observed:
        recheck_tree(root, rows, budget)
    return {"status": "GH_STAGE_MATCHES_SUPPLIED_RAW_TREE", "skills": proofs,
            "operation": resolution["operation"], "selection": resolution["selection"],
            "bytes_read": budget.read, "apply_authorized": False,
            "resolution_authenticity": "NOT_VERIFIED", "live_ref_freshness": "NOT_VERIFIED",
            "lockfile": "NOT_VERIFIED", "snapshot_atomic": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "stage", "resolution"):
        parser.add_argument("--" + name, required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        path = args.resolution
        ordinary_root(path.parent)
        info = metadata(path)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                and 0 < info.st_size <= 128 * 1024, "GH_RESOLUTION")
        disjoint([ordinary_root(args.raw), ordinary_root(args.stage), path.parent])
        result = verify(args.raw, args.stage, read_file(path, info))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, CatalogError) else "GH_RUNTIME"),
              file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
