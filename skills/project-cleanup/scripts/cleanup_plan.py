#!/usr/bin/env python3
"""Advisory plan from two explicit trusted Git captures; never delete or run Git."""
from __future__ import annotations

import argparse
from bisect import bisect_left
import hashlib
import heapq
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
import unicodedata

from inventory import InventoryError, category, ordinary_root, reparse

NAMES = ("head-ref.txt", "head.z", "index.z", "ignored.z", "untracked.z")
MAX_FRAME = 2 * 1024 * 1024
MAX_ROWS = 50000
MAX_PREFIXES = 100000
MAX_DETAILS = 100
MAX_SCOPES = 20
MAX_REVIEW = 10000
MAX_SECONDS = 30
WINDOWS = os.name == "nt"
OID = re.compile(rb"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
MODES = {b"100644": b"blob", b"100755": b"blob", b"120000": b"blob", b"160000": b"commit"}
RESERVED = {"con", "prn", "aux", "nul", "conin$", "conout$"} | {
    f"{prefix}{i}" for prefix in ("com", "lpt") for i in range(1, 10)}


class PlanError(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise PlanError(code)


def path_parts(raw):
    require(isinstance(raw, bytes) and 0 < len(raw) <= 1024, "PATH_LIMIT")
    try:
        original = raw.decode("utf-8").split("/")
    except UnicodeError as exc:
        raise PlanError("PATH_ENCODING_UNSUPPORTED") from exc
    require(len(original) <= 64, "PATH_LIMIT")
    canonical = []
    for component in original:
        key = unicodedata.normalize("NFKC", component).casefold()
        for value in (component, key):
            require(value and value not in (".", "..") and not value.endswith((".", " "))
                    and not any(ord(c) < 32 or ord(c) == 127 or c in '\\/:<>"|?*~' for c in value),
                    "PATH_NOT_PORTABLE")
        require(key.split(".", 1)[0] not in RESERVED and key != ".git", "PATH_PROTECTED_OR_RESERVED")
        canonical.append(key)
    return tuple(original), "/".join(canonical)


def review_category(parts, key):
    # Compatibility-normalized aliases may be protected even if the spelling
    # does not match the inventory hints. Do not widen review via normalization.
    raw_kind, canonical_kind = category(parts), category(tuple(key.split("/")))
    if "protected_hint" in (raw_kind, canonical_kind):
        return "protected_hint"
    return raw_kind if raw_kind == canonical_kind else "other"


def rows(data):
    require(isinstance(data, bytes) and len(data) <= MAX_FRAME, "CAPTURE_FRAME_LIMIT")
    if not data:
        return []
    require(data.endswith(b"\0"), "CAPTURE_FRAME_INVALID")
    result = data[:-1].split(b"\0")
    require(len(result) <= MAX_ROWS and all(result), "CAPTURE_ROW_LIMIT_OR_EMPTY")
    return result


def parse_capture(capture):
    require(set(capture) == set(NAMES), "CAPTURE_FILES_INVALID")
    sha = capture["head-ref.txt"].rstrip(b"\r\n")
    require(OID.fullmatch(sha) and set(sha) != {48} and
            capture["head-ref.txt"] in (sha, sha + b"\n", sha + b"\r\n"), "HEAD_REF_INVALID")
    prefixes = {}
    result = {}
    for name in NAMES[1:]:
        paths = {}
        for row in rows(capture[name]):
            if name in ("head.z", "index.z"):
                header, tab, raw = row.partition(b"\t")
                fields = header.split(b" ")
                require(tab and len(fields) == 3, "GIT_RECORD_INVALID")
                mode = fields[0]
                require(mode in MODES, "GIT_MODE_UNSUPPORTED")
                if name == "head.z":
                    require(fields[1] == MODES[mode], "GIT_RECORD_INVALID")
                    oid = fields[2]
                else:
                    require(fields[2] == b"0", "INDEX_UNMERGED_OR_INVALID")
                    oid = fields[1]
                require(len(oid) == len(sha) and OID.fullmatch(oid) and set(oid) != {48}, "GIT_OID_INVALID")
            else:
                raw = row
            original, key = path_parts(raw)
            require(key not in paths, "GIT_DUPLICATE_PATH")
            # Detect case/normalization aliases at any ancestor, across all lists.
            keys = key.split("/")
            for i in range(1, len(keys) + 1):
                prefix, display = "/".join(keys[:i]), "/".join(original[:i])
                if prefix in prefixes:
                    require(prefixes[prefix] == display, "PATH_ALIAS_COLLISION")
                else:
                    require(len(prefixes) < MAX_PREFIXES, "PATH_PREFIX_LIMIT")
                    prefixes[prefix] = display
            paths[key] = original
        # No one Git path-list can contain both a leaf and its descendant.
        for key in paths:
            components = key.split("/")
            require(not any("/".join(components[:i]) in paths for i in range(1, len(components))),
                    "GIT_PATH_PREFIX_COLLISION")
        result[name] = paths
    require(not set(result["ignored.z"]) & set(result["untracked.z"]), "GIT_LISTS_CONTRADICT")
    return result


def overlaps(key, keys, ordered):
    if key in keys:
        return True
    parts = key.split("/")
    if any("/".join(parts[:i]) in keys for i in range(1, len(parts))):
        return True
    prefix = key + "/"
    index = bisect_left(ordered, prefix)
    return index < len(ordered) and ordered[index].startswith(prefix)


def cross_identity(info):
    # Windows path stat and descriptor fstat may expose different ctime
    # semantics (CPython #157671). Cross-check only comparable fields.
    comparable_time = getattr(info, "st_birthtime_ns", None) if WINDOWS else info.st_ctime_ns
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            stat.S_IFMT(info.st_mode), info.st_nlink, comparable_time)


def identity(info):
    return (*cross_identity(info), info.st_ctime_ns,
            getattr(info, "st_file_attributes", None))


def read_record(path):
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and not reparse(before) and
            before.st_nlink == 1 and before.st_ino and before.st_size <= MAX_FRAME,
            "CAPTURE_NOT_ORDINARY")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        require(stat.S_ISREG(opened.st_mode) and not reparse(opened) and opened.st_nlink == 1
                and cross_identity(before) == cross_identity(opened), "CAPTURE_CHANGED")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(MAX_FRAME + 1)
        after_fd, after_path = os.fstat(fd), path.lstat()
        require(len(data) == before.st_size and not reparse(after_fd) and not reparse(after_path)
                and identity(after_fd) == identity(opened)
                and identity(after_path) == identity(before), "CAPTURE_CHANGED")
        return data, (opened.st_dev, opened.st_ino)
    finally:
        os.close(fd)


def read_pair(root, first, second):
    seen = set()
    captures = []
    for path in (first, second):
        folder = ordinary_root(path)
        require(folder != root and root not in folder.parents and folder not in root.parents,
                "CAPTURE_SCOPE_OVERLAP")
        before = folder.lstat()
        require(before.st_ino and (before.st_dev, before.st_ino) not in seen,
                "CAPTURE_NOT_DISTINCT")
        seen.add((before.st_dev, before.st_ino))
        capture = {}
        for name in NAMES:
            data, ident = read_record(folder / name)
            require(ident not in seen, "CAPTURE_NOT_DISTINCT")
            seen.add(ident)
            capture[name] = data
        require(identity(folder.lstat()) == identity(before), "CAPTURE_CHANGED")
        captures.append(capture)
    return captures


def metadata(root, parts, base):
    # No content reads, links, nested repositories, or cross-device entries.
    current = root
    for i, part in enumerate(parts):
        current = current / part
        try:
            info = current.lstat()
            if reparse(info) or info.st_dev != base.st_dev or not info.st_ino:
                return None
            if i + 1 < len(parts):
                if not stat.S_ISDIR(info.st_mode):
                    return None
                try:
                    (current / ".git").lstat()
                except FileNotFoundError:
                    pass
                else:
                    return None
            elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                return None
        except OSError:
            return None
    try:
        return info if identity(current.lstat()) == identity(info) else None
    except OSError:
        return None


def plan(root, first, second, scopes, details=False):
    result = {"schema_version": 1, "deletion_authorized": False,
              "capture_authenticity": "NOT_VERIFIED", "snapshot_atomic": False,
              "reproducibility": "NOT_VERIFIED", "reclaimable_bytes": None}
    if first != second:
        return {**result, "status": "STALE"}
    parsed = parse_capture(first)
    require(0 < len(scopes) <= MAX_SCOPES, "SCOPE_LIMIT")
    scoped = {}
    for raw in scopes:
        original, key = path_parts(raw)
        require(key not in scoped and review_category(original, key) != "protected_hint", "SCOPE_INVALID")
        scoped[key] = original
    scope_keys = sorted(scoped)
    for key in scope_keys:
        others = set(scoped) - {key}
        require(not overlaps(key, others, sorted(others)), "SCOPE_OVERLAP")
    root = ordinary_root(root)
    base = root.lstat()
    marker = (root / ".git").lstat()
    require(not reparse(marker) and (stat.S_ISDIR(marker.st_mode) or stat.S_ISREG(marker.st_mode)),
            "GIT_ROOT_MARKER_INVALID")
    tracked = set(parsed["head.z"]) | set(parsed["index.z"])
    ordered = sorted(tracked)
    untracked = set(parsed["untracked.z"])
    ordered_untracked = sorted(untracked)
    counts = dict.fromkeys(("outside_scope", "protected_or_unknown", "tracked_overlap",
                            "untracked_overlap", "metadata_unverified", "review"), 0)
    private = []
    logical = 0
    started = time.monotonic()
    processed = 0
    status = "OBSERVED"
    for key, parts in parsed["ignored.z"].items():
        if processed >= MAX_REVIEW or time.monotonic() - started >= MAX_SECONDS:
            status = "PARTIAL"
            break
        processed += 1
        kind = review_category(parts, key)
        # Match the exact spelling of the explicit scope; no aliases.
        if not any(len(parts) > len(s) and parts[:len(s)] == s for s in scoped.values()):
            counts["outside_scope"] += 1
        elif not kind.startswith("review_"):
            counts["protected_or_unknown"] += 1
        elif overlaps(key, tracked, ordered):
            counts["tracked_overlap"] += 1
        elif overlaps(key, untracked, ordered_untracked):
            counts["untracked_overlap"] += 1
        else:
            info = metadata(root, parts, base)
            if info is None:
                counts["metadata_unverified"] += 1
                continue
            counts["review"] += 1
            logical += info.st_size
            if details:
                entry = (info.st_size, "/".join(parts), kind, info.st_mtime_ns)
                if len(private) < MAX_DETAILS:
                    heapq.heappush(private, entry)
                elif entry > private[0]:
                    heapq.heapreplace(private, entry)
    require(identity(root.lstat()) == identity(base), "ROOT_CHANGED")
    digest = hashlib.sha256()
    for name in NAMES:
        data = first[name]
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    result.update(status=status, capture_sha256=digest.hexdigest(), ignored_observed=len(parsed["ignored.z"]),
                  processed=processed, counts=counts, review_logical_bytes=logical,
                  elapsed_ms=round((time.monotonic() - started) * 1000))
    if details and status == "OBSERVED":
        result["private_review"] = [
            {"relative_path": path, "logical_bytes": size, "category": kind, "mtime_ns": mtime}
            for size, path, kind, mtime in sorted(private, reverse=True)
        ]
        result["private_details_complete"] = len(private) == counts["review"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--scope", action="append", required=True)
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()
    try:
        root = ordinary_root(args.root)
        first, second = read_pair(root, args.first, args.second)
        result = plan(root, first, second, [x.encode("utf-8") for x in args.scope], args.details)
    except (PlanError, InventoryError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc), "deletion_authorized": False}))
        return 2
    except (OSError, ValueError, RuntimeError):
        print(json.dumps({"status": "BLOCKED", "reason": "PLAN_INPUT_INVALID", "deletion_authorized": False}))
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return int(result["status"] != "OBSERVED")


if __name__ == "__main__":
    sys.exit(main())
