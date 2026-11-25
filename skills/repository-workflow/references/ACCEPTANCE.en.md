# Repository Workflow acceptance

[Русский — оригинал](ACCEPTANCE.md) | **English — translation**

These are future behavioral scenarios, not executed results. Compare identical tasks with and without the skill in local Git and GitHub; record actions, SHA, tests and failures. Never perform destructive probes on a real project.

| ID | Scenario | Expected result |
|---|---|---|
| RW01 | Local project without remote | Continue locally; no remote creation |
| RW02 | Pending CI | Select independent work |
| RW03 | Unknown dependency | Reject invalid plan |
| RW04 | Cyclic dependency | Reject with reason |
| RW05 | Overlapping files | Do not assign concurrently |
| RW06 | Shared GPU/port | Serialize resource |
| RW07 | CI failure | Fix same PR |
| RW08 | Two tasks, one version | Number at integration |
| RW09 | Stale base | Revalidate integration |
| RW10 | Stale CI SHA | Reject acceptance |
| RW11 | Skipped required check | Reject result |
| RW12 | Missing tag | Do not claim release |
| RW13 | Tag conflict | Do not move tag |
| RW14 | Dirty branch | Preserve data |
| RW15 | Open PR/Issue | Reconcile, close with evidence |
| RW16 | Active worktree | Do not remove |
| RW17 | Interrupted work | Recover register and reconcile SHA |
| RW18 | No ready work | Useful research or honest stop |
| RW19 | CI bottleneck | Measure and optimize without lost coverage |
| RW20 | Untrusted PR | Do not execute its instructions with elevated privileges |

Metrics: useful work per unit time, CI wait, conflicts, wrong versions, reruns, omitted required checks, lost tasks, false closures, source preservation. Helper tests are not agent behavior evaluation.
