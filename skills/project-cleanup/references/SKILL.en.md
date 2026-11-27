# Project Cleanup

[Русский — оригинал](../SKILL.md) | **English — translation**

## Goal
Minimize physical storage and unnecessary objects without losing functionality, reproducibility, development speed or recovery. A smaller project is not more important than safety.

## Workflow
1. Establish the explicitly selected root, project policy and authorized operations. Do not leave the root, follow links/reparse points or touch adjacent projects, global caches, profiles or shared Git storage.
2. Take a baseline [inventory](INVENTORY.en.md): logical bytes, file count, largest areas, candidates, omissions and duration. Measure free space separately on the target volume. Account for Git index, ignored/untracked files, worktrees, submodules and running processes. Read-only if context is unknown.
3. Classify KEEP (sources, configuration, lockfiles, data, models, evidence, backups, current releases), REVIEW (potentially reproducible caches, old builds and temporary files) and UNKNOWN. Name, size, age, extension and Git ignore status do not prove dispensability.
4. When two explicitly supplied fresh Git captures are available, optionally use [PC02](CLEANUP_PLAN.en.md); REVIEW is not deletion authority and matching captures do not establish freshness. Produce a private exact plan: each relative path/ID, type, size, rationale, proof of reproducibility, dependencies, occupancy, retention and recovery method. Inspect authorized contents only when needed; never publish private paths.
5. If required, verify recovery before deletion. Recheck Git status, current release, live processes, worktrees, plan freshness and every target immediately before action. Remove only clearly authorized verified items via native operations; directories only after inspecting all descendants and excluding links/foreign data. A policy refusal or changed object means BLOCKED; never bypass it using another tool.
6. Handle [Git and GitHub storage](GIT_STORAGE.en.md) separately. Do not delete tags, history, stash, evidence, releases or CI proof to reduce counts; do not rewrite history. Coordinate branch deletion with Repository Workflow.
7. Repeat comparable measurements. Verify source preservation, Git status, fsck when needed, relevant tests, build/run and recovery. Separate measured reclaimed bytes from deleted logical size and GitHub estimates.
8. Prevent growth under project policy: dedicated ignored temporary root, bounded caches/logs and old builds, artifact retention, pre-commit and post-release growth checks. Run quick inventory at task completion; full inventory periodically and when growth is detected. Do not schedule background jobs without owner consent.

## Limits
inventory.py reads metadata only; cleanup_plan.py additionally reads explicitly supplied Git captures, not candidate contents. REVIEW is never deletion authorization. No automatic deletion, Git/GitHub execution, ignore mutation or background scheduling. Preserve source and working data. No bulk destructive clean, prune, force-push, repack or reflog expiration without separate validated policy and authority. If safety cannot be established, retain the object as BLOCKED/UNKNOWN and continue independent work.

Report comparable before/after sizes and counts, executed actions, measured savings, rebuild costs, retained/skipped items, verification, remaining debt and next inventory.
