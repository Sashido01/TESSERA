# Inventory

[Русский — оригинал](INVENTORY.md) | **English — translation**

`python -B scripts/inventory.py --root <project-root>` accepts an explicitly selected ordinary directory. Do not select a drive root or user profile. Metadata walk: no file contents, Git, writes or network. Links, reparse points, entries on another st_dev, .git, nested Git worktrees and special files are excluded. Trusted stable filesystem only; equal st_dev does not exclude bind mounts; parent substitution and races are not guaranteed prevented. Not a sandbox.

Defaults: at most 200000 entries, 64 levels and 30 seconds between operations (cannot interrupt a blocked system call). Configurable limits; exit 0 OBSERVED, 1 PARTIAL on errors/budget, 2 BLOCKED for invalid root/arguments. OBSERVED covers only the defined scope with explicit exclusions, not the entire disk, an atomic snapshot or full Git inventory. Do not extrapolate PARTIAL.

`logical_bytes` sums st_size per ordinary file name. Hardlink aliases count separately in logical bytes; observed aliases do not mean physical savings. Sparse files, compression, reflinks, deduplication, ACLs and external links prevent deriving reclaimed space from st_size. Measure free space before/after on the same volume under comparable load; background activity can affect the delta. Do not attribute the entire delta to cleanup without controls.

review_cache, review_build, review_dependency and review_temp are hints, not permission. protected_hint includes data, backups, evidence, models, logs, secret-like names/extensions; other remains UNKNOWN. Even ignored files are not proved reproducible. A real plan verifies tracked/ignored/untracked status, lockfiles, current builds, consumers, permissions and authorization.

`--details` adds up to 20 private relative paths of large REVIEW files (absent by default). Never publish them in logs, Issues or Git. Compare aggregates before/after under identical limits and exclusions; record skipped items. Empty output does not establish a clean project. Track scanning duration and rebuild cost; do not discard useful caches merely to reduce size.

Additional limits: 8192 pending directories and 100000 unique hardlink identities; overflow yields PARTIAL. Explicit .. in root is refused. Per [Python os.DirEntry.stat](https://docs.python.org/3.14/library/os.html#os.DirEntry.stat), Windows returns zero for st_dev/st_ino/st_nlink; use separate os.stat(follow_symlinks=False) for ordinary entries, not recognized reparse points. Extra metadata cost for correctness; actual Windows runtime remains required.

Private details also report up to 20 largest top-level directory groups (null denotes root files). Aggregation keeps at most 8192 groups; private_top_level_complete=false marks omitted groups, not a change to the aggregate inventory. A directory group is not an approved deletion target.

Scope hardening: known credential-store directories are not enumerated; excluded subtrees have unknown size and a separate sensitive_dirs count. Explicit roots within such directories or Git metadata, the detected user profile and its ancestors are refused. If the profile cannot be determined, return BLOCKED rather than changing the host environment. Protected filename hints additionally cover credential/password/token stems, key names and common credential filenames. Regression tests guard against content opens; this is not a security sandbox or an exhaustive sensitive-name detector.

BLOCKED contains a fixed machine reason (e.g. ROOT_PROFILE_UNKNOWN or LIMIT_INVALID); OS errors with paths are never printed. Do not fix missing authority by modifying the sandbox; use a separately authorized trusted process.
