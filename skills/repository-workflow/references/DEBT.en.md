# Technical debt and repository hygiene

[Русский — оригинал](DEBT.md) | **English — translation**

Review at each work-cycle start, after merge/release and before reporting. Distinguish active work, defects, debt, accepted risks and incomplete requirements. Zero Issues or branches is not a goal in itself.

| Area | Check |
|---|---|
| Tasks | Overdue/lost, dependencies, duplicates, false COMPLETE, criteria |
| Branches | Active goal, PR, last commit, confirmed acceptance, unique work |
| Worktrees | Active executors, uncommitted data, locks, preservation |
| PRs | Conflicts, stale base, CI, duplicates, unresolved discussions |
| Actions | Queues, failures, cancellations, timeouts, skips, exact SHA, slow stages |
| Releases | VERSION/CHANGELOG, missing/wrong tag, protection, artifacts |
| Code/tests | Stubs, contextual TODOs, missing regressions, weak checks, duplication |
| Dependencies | Advisories, licenses, updates, support, applicability |
| Docs | Statuses, contradictions, stale instructions, owner actions |
| Resources | Logs, temporary directories and caches: assess, clean under policy |

Each finding: ID, source, observation, consequence, priority, dependency, closure criterion, status, evidence, next step. Use Project Audit when available for deep analysis, but not as a requirement for basic hygiene. Continue independent work while a blocker is being fixed. After correction rerun relevant checks and update original record. Close Issues only with confirmed outcome or explicitly agreed cancellation/duplicate linked to the source; do not hide incomplete debt. Remove only an authorized merged/preserved and unused branch; do not rely on age or ancestry alone after squash. Never remove others' worktrees, user files, tags or history.

## Native reconciliation (read only)

In the trusted local repository:
```bash
git status --short --branch
git branch -vv
git worktree list --porcelain
git tag --list
git remote
```
GitHub profile only for a selected, authorized remote:
```bash
gh issue list --state open --limit 100
gh pr list --state open --limit 100
gh run list --limit 30
gh run view <run-id>
```
List limits mean sampling; for exhaustive audit process all API pages. Check exact SHAs, workflow, attempts and required jobs. An old failed run after successful correction of the same task is historical evidence, not an open task. Do not delete historical runs. If remote or gh is unavailable continue locally. Review output for secrets and private paths before publication. These are executor commands, not an automated scanner.

For private reconciliation of two explicitly supplied binary `git worktree list --porcelain -z` captures optionally use [Worktree Inventory](WORKTREE_INVENTORY.en.md). OBSERVED does not prove current occupancy, zero matches do not authorize deletion. On STALE/error recheck, do not delete. Never publish raw captures.
