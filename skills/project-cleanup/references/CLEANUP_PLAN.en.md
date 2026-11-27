# Git-aware cleanup plan

[Русский — оригинал](CLEANUP_PLAN.md) | **English — translation**

PC02 is a read-only advisory candidate. No deletion, Git invocation, index or environment mutation. Requires a trusted explicitly selected Git project and two separate fresh binary captures from the same root; the helper cannot authenticate completeness or independent acquisition.

In a trusted Git context without inherited unsafe GIT_* and without unknown hooks, collect two sets in new private ordinary directories **outside the project**. Do not strip environment restrictions. For each set preserve exact stdout of every successful command, verify exit code, keep stderr separate, do not transform encoding, NUL or line endings. On unborn HEAD, Git error, changed status or inability to capture complete output: BLOCKED, no deletion. Do not use a PowerShell text pipeline that transforms bytes.

| File | Command from project root |
| --- | --- |
| head-ref.txt | git rev-parse --verify HEAD |
| head.z | git ls-tree -r -z HEAD |
| index.z | git ls-files --stage -z |
| ignored.z | git ls-files --others --ignored --exclude-standard -z |
| untracked.z | git ls-files --others --exclude-standard -z |

`python -B scripts/cleanup_plan.py --root <project> --first <capture-a> --second <capture-b> --scope build`

Repeat --scope only for explicitly approved generated-only directories (up to 20, no overlap). Never select arbitrary areas to reduce a counter. `--details` adds up to 100 largest REVIEW files (not directories) with relative name, size and mtime; exceeding the limit makes details incomplete. Keep reports and captures private. Default output is aggregate-only.

HEAD and index protect staged deletions, sparse/skip-worktree entries and gitlinks; ordinary untracked paths also protect ancestors/descendants. Unmerged index, nonportable paths, alias collision (casefold/NFKC), malformed records and incompatible object format yield BLOCKED. Normalization is not an exact Windows/macOS emulation. Known protected/unknown, links/reparse, hardlinks, nested .git, other devices, missing/unusual entries are excluded from REVIEW. Candidate metadata is checked without opening candidate contents. Capture authenticity, ownership, reproducibility, current occupancy, authority, path races and physical space reclaimed remain unproved.

Exit 0 OBSERVED, 1 STALE/PARTIAL with no detail list on mismatch/budget, 2 BLOCKED. Up to 2 MiB per capture file, 50000 rows per list, 100000 prefixes, 64 components/1024 UTF-8 bytes per path, 10000 processed ignored rows and 30 seconds between metadata operations (not a total process timeout). Do not extrapolate or arbitrarily split Git evidence on overflow. Applies only to ordinary files within these bounds; no bare/unborn repos, nonportable paths, or complete large monorepos beyond limits. Identical captures and digest are not an atomic lock. Always deletion_authorized=false, reclaimable_bytes=null, capture_authenticity=NOT_VERIFIED. Before any action independently verify current Git state, owner/process occupancy, reproducibility/recovery, exact targets and authority. Never bypass policy refusal.

Isolated evidence: 19/19 Linux unit tests PASS, Python 3.13.5, Git 2.47.3, suite 2.309 s. Actual disposable Git fixture: ignored file left after staged deletion protected by HEAD, second ignored file only REVIEW; files and captures unchanged. Source blob bf5a6103ee079a06ec399e9ecaca4af530629cad; tests 403e4ff49097909fd76978efa406d6f2cefdbc21. Windows and full CI NOT_VERIFIED.

Sources: [git ls-files](https://git-scm.com/docs/git-ls-files), [git sparse-checkout](https://git-scm.com/docs/git-sparse-checkout), [git check-ignore](https://git-scm.com/docs/git-check-ignore), [git update-index](https://git-scm.com/docs/git-update-index).

## Additional Windows-semantics check

RW05 native Windows regression in #98 found refusal comparing a modified capture; [CPython #157671](https://github.com/python/cpython/issues/157671) documents incompatible path stat/fstat ctime. PC02 proactively separates cross-method identity (Windows birthtime/POSIX ctime plus dev/ino/size/mtime/type/nlink) and full same-method before/after checks; ctime/attributes within a method remain checked. Three new regression methods, Linux 22/22 PASS (2.182 s), source d8701efc6cca9265cf117cf924e4120871389152, tests 6712f94de909adb08507796930a1f10a059196c5. Native Windows NOT_VERIFIED. PowerShell 7.4+ direct native stdout > file preserves the byte stream; never merge stderr/stdout, use no text pipeline, verify exit code and fresh separate directories. See [Microsoft about_Redirection](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_redirection?view=powershell-7).

## PC02 boundary hardening (27 November 2026)

Also reject leading ASCII space, Unicode control/format characters, and reserved device stems with spaces before extensions; NFKC also detects COM¹/LPT¹. Combined UTF-8 budget for unique prefix key+display is 8 MiB (not actual RSS). Capture folders cannot be nested. After both reads, recheck all ten file and two folder identities; after candidate metadata, recheck ancestors and absence of nested .git; after the pass recheck the root marker. Observed changes give BLOCKED or metadata_unverified, never deletion authority. Reduces persistent-substitution risk, not atomic and does not prove absence of TOCTOU, bind mounts or aliases. [Microsoft naming rules](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file), [Git ls-files](https://git-scm.com/docs/git-ls-files), [Python os](https://docs.python.org/3/library/os.html). Isolated repeat of previous 22/22 PASS, updated 27/27 Linux PASS (2.245 s); exact source 38128cd58959db5cc4d09c18a45b9b87806383fa, tests 2dc1e381216db6aa7959a84c324bf7e2088f0810. Native CI required. Before capture, separately confirm exact Git top-level, absence of replacement refs and consistent HEAD observation. Git snapshots are supplied evidence, not authenticated by the helper.

Additional actual Git 2.47.3 sparse-index fixture: tracked build/keep.txt is physically absent after sparse-checkout but standard ls-files --stage -z expands it; compressed --sparse snapshot with mode 040000 is rejected. Separate ignored file remains REVIEW without deletion. 28/28 Linux PASS, 2.406 s; unchanged source SHA 38128cd58959db5cc4d09c18a45b9b87806383fa, tests de6eeded6e23814e1f8c405f519742b13fd1bd98. Do not use --sparse when collecting evidence. Native Windows unverified.

## Unstable Windows test correction, 27 November 2026

PR #101 CI 46038347655 5/5 PASS, but main v0.0.94 CI 46042052275 Windows job 140651970098: 49 skill executions, 46 PASS + 1 FAIL + 2 FIFO SKIP. FAIL test_git_marker_changed_during_plan: no PlanError after writing a child file under .git. Test assumption of immediate directory metadata change; exact NTFS/CPython cause unconfirmed. New actual test substitutes the marker itself (old object retained), separately injects mtime change without clock dependence. Runtime requires nonzero root and marker inode, same device, nlink=1 for regular .git file; rechecks ordinary root and marker, OSError/unusual marker on recheck blocks ROOT_CHANGED. Not a check of .git contents or guarantee of detecting internal changes, not TOCTOU-safe. Four new tests and corrected old one; renewed Windows/full CI required. No result authorizes deletion.

PR #102 initial run 46042915262: native skill tests failed with NameError: base was no longer bound at metadata(root, parts, base) after the marker refactor. Keep the original root stat object from root_marker and derive its identity from that same observation; no weakening of checks. Renewed full CI required; initial run not accepted.
