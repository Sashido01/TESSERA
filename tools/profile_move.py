"""No-overwrite directory move primitive for isolated transaction fixtures.

Caller must provide exclusively controlled roots. This is not a profile updater,
authorization mechanism, or protection against hostile ancestor replacement.
"""
from __future__ import annotations

import ctypes
import os
import pathlib
import stat
import sys

from catalog_index import NAME, require
from profile_plan import (Budget, aliases, disjoint, identity, inventory, metadata,
                          ordinary_root, recheck_tree, snapshot)


def absent(path):
    try:
        metadata(path)
    except FileNotFoundError:
        return
    raise FileExistsError("MOVE_DESTINATION_EXISTS")


def native_move(source, destination, name, source_info, destination_info):
    """No fallback to a potentially overwriting POSIX rename."""
    if os.name == "nt":
        require(identity(metadata(source)) == identity(source_info)
                and identity(metadata(destination)) == identity(destination_info),
                "MOVE_ROOT_CHANGED")
        # Python documents that Windows rename fails if destination exists.
        os.rename(source / name, destination / name)
        return
    require(sys.platform == "linux", "MOVE_PLATFORM_UNSUPPORTED")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    first = os.open(source, flags)
    try:
        second = os.open(destination, flags)
        try:
            require(identity(os.fstat(first)) == identity(source_info)
                    and identity(os.fstat(second)) == identity(destination_info),
                    "MOVE_ROOT_CHANGED")
            libc = ctypes.CDLL(None, use_errno=True)
            operation = getattr(libc, "renameat2", None)
            require(operation is not None, "MOVE_NOREPLACE_UNAVAILABLE")
            operation.argtypes = [ctypes.c_int, ctypes.c_char_p,
                                  ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
            operation.restype = ctypes.c_int
            leaf = os.fsencode(name)
            if operation(first, leaf, second, leaf, 1) != 0:  # RENAME_NOREPLACE
                code = ctypes.get_errno()
                raise OSError(code, "MOVE_NOREPLACE_FAILED")
        finally:
            os.close(second)
    finally:
        os.close(first)


def move_verified(source: pathlib.Path, destination: pathlib.Path, name, expected):
    """Move one expected tree; retain evidence on failure, never auto-reverse."""
    require(isinstance(name, str) and len(name) <= 64 and NAME.fullmatch(name),
            "MOVE_NAME")
    roots = [ordinary_root(p) for p in (source, destination)]
    disjoint(roots)
    first, second = [metadata(p) for p in roots]
    require(first.st_dev == second.st_dev, "MOVE_CROSS_DEVICE")
    budget = Budget()
    require(not any(aliases(p, {name}, budget) for p in roots), "MOVE_ALIAS")
    target, output = source / name, destination / name
    absent(output)
    rows = inventory(target, budget)
    require(rows[""].st_dev == first.st_dev, "MOVE_CROSS_DEVICE")
    require(snapshot(target, rows, budget) == expected, "MOVE_SOURCE_CHANGED")
    for root in roots:
        ordinary_root(root)
    require(identity(metadata(source)) == identity(first)
            and identity(metadata(destination)) == identity(second), "MOVE_ROOT_CHANGED")
    recheck_tree(target, rows, budget)
    absent(output)
    native_move(source, destination, name, first, second)
    # A failure here may follow a successful move. Never retry automatically.
    for root, original in zip(roots, (first, second)):
        info = metadata(ordinary_root(root))
        require((info.st_dev, info.st_ino) == (original.st_dev, original.st_ino),
                "MOVE_ROOT_CHANGED_AFTER")
    absent(target)
    result = inventory(output, budget)
    require((result[""].st_dev, result[""].st_ino) ==
            (rows[""].st_dev, rows[""].st_ino), "MOVE_IDENTITY_AFTER")
    require(snapshot(output, result, budget) == expected, "MOVE_POSTCHECK")
    return {"status": "MOVED_NO_REPLACE", "directory_durability": "NOT_VERIFIED",
            "exclusive_access": "NOT_VERIFIED", "apply_authorized": False}
