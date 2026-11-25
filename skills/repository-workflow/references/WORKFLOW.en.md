# Parallel development

[Русский — оригинал](WORKFLOW.md) | **English — translation**

## Profiles
LOCAL: Git, local checks, existing roadmap/register. GITHUB: native Issues and dependencies, PRs, Actions, Rulesets and optional Projects. SINGLE/MULTI: one switching agent or several isolated executors. MONOREPO: independent components and shared integration slot. BOOTSTRAP/EXISTING: new setup or careful improvement of existing workflow.

## Cycle
Inventory → process completed checks → select independent work → bounded change → fast checks → integration queue → current-base check → required acceptance → release under project policy → debt review. Begin with the main project, then each component; avoid idle waiting. Within each stream address blocking defects, P0, P1, P2. Do not assign beyond executor capacity or rerun expensive checks for an unchanged SHA without a reason.

## Branches and integration
Short-lived branch per coherent goal; fix failure in the same branch. Isolate worktree and mutable resources. Record dependencies and write scopes; an incomplete graph means uncertainty, not guaranteed independence. Intermediate commits need no accepted version number. One integration slot for shared VERSION/CHANGELOG; assign the next version from current main, then check the exact merge candidate. On GitHub use protection, strict CI, squash if agreed, expected PR HEAD verification. Use native merge queue if available; otherwise one coordinator without bypass. Never delete unfinished branches. Locally enforce the equivalent sequence without creating a remote automatically.

## New project setup
Plan and inventory first; do not overwrite existing files. Agree on goals, Git, minimal agent rules, README, task register, native verification and versioning. GitHub profile adds PRs, pinned Actions, least privilege, required checks, Rulesets and templates. Use only necessary components; reuse native configuration instead of building a complex platform. Test positive and negative cases in a disposable repository. Security setting changes and network actions require separate authorization.
