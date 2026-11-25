# Repository Workflow changelog

[Русский — оригинал](CHANGELOG.md) | **English — translation**

## 0.0.2 — Clarify planner scope

The planner normalizes Unicode scopes with casefold + NFC, rejects reserved Windows device names and duplicate JSON keys, and checks dependency cycles in O(V+E). Added regressions for Unicode conflicts, reserved paths, long chains and cycles. Windows 11 / Python 3.14.3: 17/17 PASS. The planner remains advisory over a snapshot and does not atomically reserve resources; actual agent use is NOT_VERIFIED.

## 0.0.1 — Initial candidate

- LOCAL/GITHUB profiles, independent work planning, safe integration, debt review, CI performance and optional local planner. Actual agent trials and independent release remain open.
