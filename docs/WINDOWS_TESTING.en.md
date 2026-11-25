# Native Windows verification

[Русский — оригинал](WINDOWS_TESTING.md) | **English — translation**

## Required check for every PR and main

- `windows_skill_checks`: GitHub-hosted windows-latest, Python 3.14, exact checkout SHA, pinned Actions, no persisted credentials, contents: read, no bytecode; three skill suites through the shared runner. WSL does not substitute for Windows.
- The validate aggregate requires all four groups to succeed; skipped/failed/cancelled is not PASS. Linux Docker/security groups remain mandatory.
- Record OS, Python and Git version, SHA, exit code, passed/failed/skipped; disclose actual limitations. FIFO is N/A on Windows; missing symlink privileges do not test junctions. Linux simulation does not establish Windows COMPLETE.

## Extension matrix

| ID | Scope | Acceptance |
| --- | --- | --- |
| W01 | Inventory, nested NTFS directories, spaces and Unicode | Exact metadata, no false DEVICE_BOUNDARY |
| W02 | Junction/reparse point, symlink, different device | Do not traverse target, visible boundary; separate real second device trial |
| W03 | ACL, inaccessible directories, locked files, long paths | Explicit PARTIAL or rejection; no ACL changes or content reads |
| W04 | Git CLI, unborn/detached, dirty, refs, conflicting tags | Exact results, no writes in read-only mode; writes only to fixtures |
| W05 | Codex Git context (TD17), PowerShell/UTF-8 | Preserve security gate; distinguish clean fixture from actual session |
| W06 | Release Core, catalog, ZIP, pin/update/rollback | Separate proven portable Windows subset; no replacement of Linux full CI |
| W07 | Actual Windows Codex/Harness | Independent discovery/explicit use/auto-use/enforcement; exact pin |
| W08 | Python versions | 3.14 current mandatory runner; 3.13 and other supported versions separately after measurement |

W01–W08 are criteria, not results. Expand native runner incrementally, no weaker protections or unmeasured timeout increases. Repair failures in the same PR. Disposable local directories and Git fixtures without remotes; real data and profiles unchanged. No third-party scanners in the user profile; retain Linux security coverage.

## Re-integration

Retain current user pin v0.0.74. Trial the candidate in a disposable project at an exact reviewed SHA without replacing global skills. After acceptance and verified tag: stage the new pin, verify tree, test, document backup/rollback, and obtain separate permission for update. No --force/--all/--unpin in an existing profile. Use `python -B` for local retests. Do not publish private paths, variable values or tokens.
