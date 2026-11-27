#!/usr/bin/env python3
"""Read-only Git tree proof for exact raw staging; not an installation authority."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import stat
import sys

from catalog_index import CatalogError, require, oid, version
from profile_plan import (Budget, aliases, disjoint, identity, inventory, metadata,
                          ordinary_root, read_file, read_resolution, recheck_ancestors)


def git_oid(kind, data):
    return hashlib.sha1(f"{kind} {len(data)}\0".encode("ascii") + data).hexdigest()


def snapshot_raw(root, budget):
    """One read per file; derive both Git tree and profile snapshot identifiers."""
    ordinary_root(root)
    rows = inventory(root, budget)
    require("SKILL.md" in rows and "VERSION" in rows and
            all(stat.S_ISREG(rows[n].st_mode) for n in ("SKILL.md", "VERSION")) and
            rows["VERSION"].st_size <= 64, "TREE_SKILL_METADATA")
    children = {name: [] for name, info in rows.items() if stat.S_ISDIR(info.st_mode)}
    records = []
    hashes = {}
    actual_version = None
    for name, info in sorted(rows.items()):
        budget.check()
        if name:
            parent = name.rpartition("/")[0]
            require(parent in children, "TREE_STRUCTURE")
            children[parent].append(name)
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISDIR(info.st_mode):
            records.append([name, "dir", mode])
            continue
        # All published TESSERA skill blobs are ordinary mode 100644.
        require(stat.S_ISREG(info.st_mode) and not (mode & 0o111), "TREE_MODE")
        recheck_ancestors(root, root / name, rows)
        data = read_file(root / name, info, budget)
        if name == "VERSION":
            actual_version = data.decode("utf-8").strip()
            version(actual_version)
        hashes[name] = git_oid("blob", data)
        records.append([name, "file", mode, len(data), hashlib.sha256(data).hexdigest()])
    # Git sorts a directory as though its name ends in a slash.
    for folder in sorted(children, key=lambda n: (n.count("/") + bool(n), n), reverse=True):
        require(bool(children[folder]), "TREE_EMPTY_DIRECTORY")
        parts = []
        for name in sorted(children[folder], key=lambda n: n.rsplit("/", 1)[-1].encode("ascii") +
                           (b"/" if n in children else b"")):
            leaf = name.rsplit("/", 1)[-1].encode("ascii")
            mode = b"40000" if name in children else b"100644"
            parts.append(mode + b" " + leaf + b"\0" + bytes.fromhex(hashes[name]))
        hashes[folder] = git_oid("tree", b"".join(parts))
    # Recheck parents before descendants, not just the leaf path.
    ordinary_root(root)
    for name, info in sorted(rows.items(), key=lambda row: (row[0].count("/"), row[0])):
        budget.check()
        require(identity(metadata(root / name)) == identity(info), "TREE_CHANGED")
    digest = hashlib.sha256(json.dumps(records, separators=(",", ":")).encode()).hexdigest()
    return actual_version, hashes[""], digest, rows


def verify(stage, raw_resolution):
    resolution = read_resolution(raw_resolution)
    stage = ordinary_root(stage)
    budget = Budget()
    root_id = identity(metadata(stage))
    selected = {row["id"] for row in resolution["skills"]}
    require(not aliases(stage, selected, budget), "TREE_NAME_ALIAS")
    proofs = []
    observed = []
    for row in resolution["skills"]:
        root = stage / row["id"]
        actual_version, actual_tree, digest, entries = snapshot_raw(root, budget)
        require(actual_version == row["version"], "TREE_VERSION_MISMATCH")
        require(actual_tree == oid(row["tree"]), "TREE_OID_MISMATCH")
        proofs.append({"id": row["id"], "version": actual_version, "ref": row["ref"],
                       "tag_object": row["tag_object"], "commit": row["commit"],
                       "tree": actual_tree, "stage_sha256": digest})
        observed.append((root, entries))
    # Detect persistent changes to previously inspected trees across the batch.
    ordinary_root(stage)
    require(identity(metadata(stage)) == root_id and not aliases(stage, selected, budget),
            "TREE_STAGE_CHANGED")
    for root, entries in observed:
        ordinary_root(root)
        for name, info in sorted(entries.items(), key=lambda row: (row[0].count("/"), row[0])):
            budget.check()
            require(identity(metadata(root / name)) == identity(info), "TREE_CHANGED")
    return {"status": "RAW_TREE_MATCHES_SUPPLIED_OID", "operation": resolution["operation"],
            "selection": resolution["selection"], "skills": proofs, "bytes_read": budget.read,
            "resolution_authenticity": "NOT_VERIFIED", "live_ref_freshness": "NOT_VERIFIED",
            "gh_metadata": "NOT_VERIFIED", "apply_authorized": False,
            "snapshot_atomic": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, type=pathlib.Path)
    parser.add_argument("--resolution", required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        path = args.resolution
        ordinary_root(path.parent)
        info = metadata(path)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and
                0 < info.st_size <= 128 * 1024, "TREE_RESOLUTION")
        disjoint([ordinary_root(args.stage), path.parent])
        result = verify(args.stage, read_file(path, info))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, CatalogError) else "TREE_RUNTIME"), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
