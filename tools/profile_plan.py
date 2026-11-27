#!/usr/bin/env python3
"""Read-only comparison of selected skills with independently supplied staging trees."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import stat
import sys
import time
import unicodedata

from catalog_index import CatalogError, REPO, MAX_SKILLS, decode, oid, require, selection, version

MAX_ENTRIES = 512
MAX_BYTES = 16 * 1024 * 1024
MAX_FILE = 2 * 1024 * 1024
MAX_DEPTH = 8
MAX_ROOT_ENTRIES = 4096
MAX_TOTAL_READ = 128 * 1024 * 1024
MAX_SECONDS = 60
REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
WINDOWS = os.name == "nt"
PORTABLE = re.compile(r"[A-Za-z0-9._-]{1,128}\Z")
DEVICE = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])\Z", re.I)


class Budget:
    def __init__(self):
        self.deadline = time.monotonic() + MAX_SECONDS
        self.read = 0

    def check(self, size=0):
        self.read += size
        require(self.read <= MAX_TOTAL_READ and time.monotonic() < self.deadline,
                "PROFILE_BUDGET")


def reparse(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & REPARSE)


def cross_identity(info):
    # Windows path-stat and descriptor-stat ctime/mode details may differ.
    comparable_time = getattr(info, "st_birthtime_ns", None) if WINDOWS else info.st_ctime_ns
    return (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode), info.st_nlink,
            info.st_size, info.st_mtime_ns, comparable_time)


def identity(info):
    return (*cross_identity(info), info.st_mode, info.st_ctime_ns,
            getattr(info, "st_file_attributes", None))


def metadata(path):
    info = path.lstat()
    require(info.st_ino != 0 and not reparse(info), "PROFILE_LINK_OR_IDENTITY")
    return info


def ordinary_root(path):
    require(path.is_absolute() and ".." not in path.parts and path != pathlib.Path(path.anchor),
            "PROFILE_ROOT")
    for component in (*reversed(path.parents), path):
        require(stat.S_ISDIR(metadata(component).st_mode), "PROFILE_ROOT")
    return path


def disjoint(roots):
    for i, a in enumerate(roots):
        for b in roots[i+1:]:
            require(not a.is_relative_to(b) and not b.is_relative_to(a)
                    and not a.samefile(b), "PROFILE_OVERLAPPING_ROOTS")


def valid_name(name):
    return (PORTABLE.fullmatch(name) is not None and name not in (".", "..")
            and not name.endswith(".") and name.casefold() not in {".git", ".env", ".ssh"}
            and DEVICE.fullmatch(name.split(".", 1)[0]) is None)


def aliases(root, selected, budget):
    found = {name: [] for name in selected}
    with os.scandir(root) as entries:
        for count, item in enumerate(entries, 1):
            budget.check()
            require(count <= MAX_ROOT_ENTRIES, "PROFILE_ROOT_LIMIT")
            key = unicodedata.normalize("NFKC", item.name).rstrip(" .").casefold()
            if key in found:
                found[key].append(item.name)
    return {name for name, matches in found.items() if matches and matches != [name]}


def recheck_ancestors(root, path, rows):
    require(path.is_relative_to(root), "PROFILE_SCOPE")
    chain = [root, *[parent for parent in reversed(path.parents)
                     if parent != root and parent.is_relative_to(root)]]
    if path != root:
        chain.append(path)
    for component in chain:
        name = component.relative_to(root).as_posix() if component != root else ""
        require(identity(metadata(component)) == identity(rows[name]), "PROFILE_CHANGED")


def recheck_tree(root, rows, budget):
    ordinary_root(root)
    # Parents precede children; do not rely on a root directory timestamp alone.
    for name, info in sorted(rows.items(), key=lambda row: (row[0].count("/"), row[0])):
        budget.check()
        require(identity(metadata(root / name)) == identity(info), "PROFILE_CHANGED")


def inventory(root, budget):
    ordinary_root(root)
    root_info = metadata(root)
    require(stat.S_ISDIR(root_info.st_mode), "PROFILE_SKILL_DIRECTORY")
    rows = {"": root_info}
    total = 0
    pending = [(root, 0)]
    while pending:
        folder, depth = pending.pop()
        require(depth < MAX_DEPTH, "PROFILE_DEPTH")
        names = set()
        recheck_ancestors(root, folder, rows)
        with os.scandir(folder) as entries:
            for entry in entries:
                budget.check()
                require(len(rows) < MAX_ENTRIES and valid_name(entry.name)
                        and entry.name.casefold() not in names, "PROFILE_ENTRY")
                names.add(entry.name.casefold())
                path = folder / entry.name
                info = metadata(path)
                require(info.st_dev == root_info.st_dev, "PROFILE_DEVICE_BOUNDARY")
                relative = path.relative_to(root).as_posix()
                rows[relative] = info
                if stat.S_ISDIR(info.st_mode):
                    pending.append((path, depth + 1))
                else:
                    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                            and 0 <= info.st_size <= MAX_FILE, "PROFILE_SPECIAL_FILE")
                    total += info.st_size
                    require(total <= MAX_BYTES, "PROFILE_BYTE_LIMIT")
        recheck_ancestors(root, folder, rows)
    return rows


def shape(rows):
    return {name: (stat.S_IFMT(info.st_mode), stat.S_IMODE(info.st_mode),
                   info.st_size if stat.S_ISREG(info.st_mode) else None)
            for name, info in rows.items()}


def read_file(path, expected, budget=None):
    if budget is not None:
        budget.check(expected.st_size)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and not reparse(before) and before.st_ino
                and cross_identity(before) == cross_identity(expected), "PROFILE_CHANGED")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(expected.st_size + 1)
        require(len(data) == expected.st_size and identity(os.fstat(fd)) == identity(before),
                "PROFILE_CHANGED")
    finally:
        os.close(fd)
    require(identity(metadata(path)) == identity(expected), "PROFILE_CHANGED")
    if budget is not None:
        budget.check()
    return data


def snapshot(root, rows, budget):
    require("SKILL.md" in rows and "VERSION" in rows
            and all(stat.S_ISREG(rows[n].st_mode) for n in ("SKILL.md", "VERSION"))
            and rows["VERSION"].st_size <= 64, "PROFILE_SKILL_METADATA")
    records = []
    installed_version = None
    for name, info in sorted(rows.items()):
        if stat.S_ISDIR(info.st_mode):
            records.append([name, "dir", stat.S_IMODE(info.st_mode)])
        else:
            recheck_ancestors(root, root / name, rows)
            data = read_file(root / name, info, budget)
            if name == "VERSION":
                installed_version = data.decode("utf-8").strip()
                version(installed_version)
            records.append([name, "file", stat.S_IMODE(info.st_mode), len(data), hashlib.sha256(data).hexdigest()])
    recheck_tree(root, rows, budget)
    digest = hashlib.sha256(json.dumps(records, separators=(",", ":")).encode()).hexdigest()
    return installed_version, digest


def read_resolution(raw):
    obj = decode(raw, 128 * 1024)
    require(isinstance(obj, dict) and obj.get("status") == "RESOLVED"
            and obj.get("repository") == REPO and obj.get("install_authorized") is False
            and obj.get("operation") in ("install", "update")
            and obj.get("selection") in ("EXPLICIT", "ALL"), "PROFILE_RESOLUTION")
    rows = obj.get("skills")
    require(isinstance(rows, list) and 0 < len(rows) <= MAX_SKILLS
            and all(isinstance(row, dict) for row in rows), "PROFILE_RESOLUTION")
    names = [row.get("id") for row in rows]
    selection(names, False)
    count = obj.get("catalog_skill_count")
    require(type(count) is int and len(rows) <= count <= MAX_SKILLS and
            obj.get("selected_count") == len(rows) and obj.get("unselected_count") == count - len(rows)
            and (obj["selection"] != "ALL" or count == len(rows)), "PROFILE_RESOLUTION")
    for row in rows:
        name = row["id"]
        version(row.get("version"))
        require(row.get("path") == "skills/" + name and row.get("ref") ==
                "refs/tags/" + name + "/v" + row["version"], "PROFILE_RESOLUTION")
        for key in ("tag_object", "tree", "commit"):
            oid(row.get(key))
    return obj


def one(profile, stage, baseline, row, operation, budget, observed_trees, absent_targets):
    name = row["id"]
    new = stage / name
    new_rows = inventory(new, budget)
    observed_trees.append((new, new_rows))
    new_version, new_digest = snapshot(new, new_rows, budget)
    require(new_version == row["version"], "PROFILE_STAGE_VERSION")
    result = {"id": name, "desired_version": new_version, "stage_sha256": new_digest}
    target = profile / name
    try:
        metadata(target)
    except FileNotFoundError:
        absent_targets.append(target)
        return {**result, "decision": "PLAN_INSTALL", "reason": "ABSENT"}
    target_rows = inventory(target, budget)
    observed_trees.append((target, target_rows))
    old = baseline / name if baseline is not None else None
    observed = None
    if shape(target_rows) == shape(new_rows):
        observed = snapshot(target, target_rows, budget)
        observed_version, observed_digest = observed
        if observed_digest == new_digest:
            return {**result, "decision": "SKIP_MATCHING_STAGE", "observed_version": observed_version}
    if operation == "install":
        return {**result, "decision": "BLOCKED", "reason": "EXISTING_DIFFERENT"}
    if old is None:
        return {**result, "decision": "BLOCKED", "reason": "BASELINE_REQUIRED"}
    old_rows = inventory(old, budget)
    observed_trees.append((old, old_rows))
    if shape(target_rows) != shape(old_rows):
        return {**result, "decision": "BLOCKED", "reason": "LOCAL_STRUCTURE_DIFFERS"}
    old_version, old_digest = snapshot(old, old_rows, budget)
    observed_version, observed_digest = observed or snapshot(target, target_rows, budget)
    if observed_digest != old_digest:
        return {**result, "decision": "BLOCKED", "reason": "LOCAL_BYTES_DIFFER"}
    if version(old_version) >= version(new_version):
        return {**result, "decision": "BLOCKED", "reason": "NON_ADVANCING_VERSION"}
    return {**result, "decision": "PLAN_UPDATE", "observed_version": observed_version,
            "baseline_sha256": old_digest}


def plan(profile, stage, baseline, raw_resolution):
    resolution = read_resolution(raw_resolution)
    budget = Budget()
    roots = [ordinary_root(p) for p in (profile, stage, baseline) if p is not None]
    disjoint(roots)
    root_ids = [identity(metadata(p)) for p in roots]
    decisions = []
    selected = {row["id"] for row in resolution["skills"]}
    ambiguous = set().union(*(aliases(p, selected, budget) for p in roots))
    observed_trees, absent_targets = [], []
    for row in resolution["skills"]:
        try:
            budget.check()
            require(row["id"] not in ambiguous, "PROFILE_NAME_ALIAS")
            decisions.append(one(profile, stage, baseline, row, resolution["operation"], budget,
                                 observed_trees, absent_targets))
        except (CatalogError, OSError, UnicodeError) as exc:
            decisions.append({"id": row["id"], "decision": "BLOCKED",
                              "reason": str(exc) if isinstance(exc, CatalogError) else "PROFILE_UNREADABLE"})
    budget.check()
    for root in roots:
        ordinary_root(root)
    require([identity(metadata(p)) for p in roots] == root_ids, "PROFILE_ROOT_CHANGED")
    require(set().union(*(aliases(p, selected, budget) for p in roots)) == ambiguous,
            "PROFILE_NAME_ALIAS_CHANGED")
    for root, rows in observed_trees:
        recheck_tree(root, rows, budget)
    for target in absent_targets:
        budget.check()
        try:
            metadata(target)
        except FileNotFoundError:
            continue
        raise CatalogError("PROFILE_TARGET_APPEARED")
    budget.check()
    return {"status": "PLAN_ONLY", "operation": resolution["operation"], "selection": resolution["selection"],
            "decisions": decisions, "apply_authorized": False, "source_authenticity": "NOT_VERIFIED",
            "exclusive_access": "NOT_VERIFIED", "snapshot_atomic": False, "bytes_read": budget.read}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("profile", "stage", "resolution"):
        parser.add_argument("--" + name, required=True, type=pathlib.Path)
    parser.add_argument("--baseline", type=pathlib.Path)
    args = parser.parse_args()
    try:
        path = args.resolution
        ordinary_root(path.parent)
        info = metadata(path)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 < info.st_size <= 128*1024,
                "PROFILE_RESOLUTION")
        result = plan(args.profile, args.stage, args.baseline, read_file(path, info))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("BLOCKED: " + (str(exc) if isinstance(exc, CatalogError) else "PROFILE_RUNTIME"), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 1 if any(row["decision"] == "BLOCKED" for row in result["decisions"]) else 0


if __name__ == "__main__":
    sys.exit(main())
