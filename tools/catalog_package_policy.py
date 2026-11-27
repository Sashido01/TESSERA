"""Versioned source ZIP contract for the read-only skill update tools."""
from __future__ import annotations

import re

from catalog_index import CatalogError, parse_index

UPDATE_FILES = frozenset({
    "CATALOG.json", "UPDATE.md", "UPDATE.en.md",
    "docs/PROFILE_UPDATE_PLAN.md", "docs/PROFILE_UPDATE_PLAN.en.md",
    "tools/catalog_index.py", "tools/profile_plan.py", "tools/skill_tree.py",
})
GH_STAGE_FILE = "tools/gh_stage.py"


def update_files(version):
    return UPDATE_FILES | ({GH_STAGE_FILE} if tuple(map(int, version.split("."))) >= (0, 0, 98) else set())


BASE_FILES = frozenset({"LICENSE", "README.md", "README.en.md", "VERSION"})
SKILL_FILE = re.compile(
    r"skills/([a-z0-9]+(?:-[a-z0-9]+)*)/"
    r"(?:SKILL\.md|README\.md|README\.en\.md|LICENSE\.txt|VERSION|"
    r"CHANGELOG\.md|CHANGELOG\.en\.md|references/[A-Za-z0-9._-]+\.md|"
    r"scripts/[A-Za-z0-9._-]+\.py)\Z"
)


def requires_update_files(version: str) -> bool:
    return tuple(map(int, version.split("."))) >= (0, 0, 97)


def allowed_member(name: str, version: str) -> bool:
    return name in BASE_FILES or name in update_files(version) or bool(SKILL_FILE.fullmatch(name))


def check_update_catalog(names, index_bytes, skill_versions, version):
    """Check only verified archive bytes; never execute bundled code."""
    names = set(names)
    if not update_files(version).issubset(names) or not BASE_FILES.issubset(names):
        raise CatalogError("UPDATE_FILES_MISSING")
    if any(not allowed_member(name, version) for name in names):
        raise CatalogError("UPDATE_FILE_NOT_ALLOWED")
    rows = parse_index(index_bytes)
    actual = {name.split("/")[1] for name in names if name.startswith("skills/")}
    if actual != {row["id"] for row in rows} or actual != set(skill_versions):
        raise CatalogError("UPDATE_SKILL_SET_MISMATCH")
    for row in rows:
        if (skill_versions[row["id"]] != row["version"]
                or row["path"] + "/SKILL.md" not in names):
            raise CatalogError("UPDATE_SKILL_VERSION_MISMATCH")
