# Project Cleanup roadmap

[Русский — оригинал](ROADMAP.md) | **English — translation**

| ID | Result | Acceptance |
| --- | --- | --- |
| PC01 | Metadata inventory | Synthetic checks, actual Windows/Linux, root bounds, reparse/mount/errors/limits |
| PC02 | Cleanup plan | Git index/ignored intersection, reproducibility evidence, source/data protection, exact targets, no false authorization |
| PC03 | Execution | Isolated positive/negative fixtures, recheck, policy refusal, recovery, comparable metrics |
| PC04 | Git/GitHub | Separate history, worktrees, artifacts, caches, releases counters; evidence preservation |
| PC05 | Prevention | Agreed retention/budgets, growth checks, timing and rebuild cost |
| PC06 | Clients | Codex/Harness discovery, explicit/auto-use, actual fixture execution, scope containment |

PC01 — native CI PASS (0.0.1), actual platform and client boundaries still require acceptance. PC02 — PARTIAL, [advisory](CLEANUP_PLAN.en.md) 28/28 Linux PASS; native CI, reproducibility and execution unproved. PC03–PC05 documented workflow, automated execution NOT_IMPLEMENTED. PC06 NOT_VERIFIED. No reclaimed-space claim without measurement. Default policy deletes no data; project chooses budgets/retention. Optional tools are not mandatory.
