# Repository Workflow changelog

[Русский — оригинал](CHANGELOG.md) | **English — translation**

## 0.0.3 — Reconcile worktree captures before debt closure

- Optional read-only Worktree Inventory: two binary captures, bounded parse, ref and SHA format, branch/head/detached counts, distinct file identities. STALE on mismatch, never authorizes deletion, authenticity/current occupancy NOT_VERIFIED.
- 21/21 isolated Linux tests PASS, actual Git fixture, unsafe Git context refused before mutation. Full CI/Windows and actual agents require acceptance.

- Windows regression: separate path/fstat ctime semantics, retain same-method identity checks, add three tests; 24/24 Linux PASS, renewed Windows CI required.

## 0.0.2 — Clarify planner scope

The planner normalizes Unicode scopes with casefold + NFC, rejects reserved Windows device names and duplicate JSON keys, and checks dependency cycles in O(V+E). Added regressions for Unicode conflicts, reserved paths, long chains and cycles. Windows 11 / Python 3.14.3: 17/17 PASS. The planner remains advisory over a snapshot and does not atomically reserve resources; actual agent use is NOT_VERIFIED.

## 0.0.1 — Initial candidate

- LOCAL/GITHUB profiles, independent work planning, safe integration, debt review, CI performance and optional local planner. Actual agent trials and independent release remain open.
