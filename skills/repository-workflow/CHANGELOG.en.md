# Repository Workflow changelog

[Русский — оригинал](CHANGELOG.md) | **English — translation**

## 0.0.2 — Portable planner validation

- Unicode casefold + NFC, reject Windows device names and surrogates, reject duplicate JSON keys; linear DAG traversal instead of repeated layer scans. 17/17 local tests (13 prior + 4 new). Independent local preflight plan. Full CI and Windows open.

## 0.0.1 — Initial candidate

- LOCAL/GITHUB profiles, independent work planning, safe integration, debt review, CI performance and optional local planner. Actual agent trials and independent release remain open.
