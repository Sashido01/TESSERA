# Project Cleanup

[Русский — оригинал](README.md) | **English — translation**

Version 0.0.1 — initial candidate. A standalone skill for local and GitHub hygiene, storage measurement and growth prevention. Install the entire directory; see [SKILL](references/SKILL.en.md). No paid APIs or external packages required.

```bash
python -B scripts/inventory.py --root <project-root>
python -B scripts/inventory.py --root <project-root> --details
```

The first mode outputs aggregates only; the second adds private relative paths of the largest observed REVIEW files (do not publish). No deletion. See [inventory](references/INVENTORY.en.md), [Git/GitHub](references/GIT_STORAGE.en.md), [roadmap](references/ROADMAP.en.md). Native Windows/Linux CI and agent acceptance are NOT_VERIFIED.

Private details also report up to 20 largest top-level directory groups (null denotes root files). Aggregation keeps at most 8192 groups; private_top_level_complete=false marks omitted groups, not a change to the aggregate inventory. A directory group is not an approved deletion target.

Isolated Linux evidence: 18/18 tests PASS; source and test Git blobs matched exactly. Synthetic fixture: 10000 files × 128 bytes = 1280000 logical bytes, three inventory passes 104/114/103 ms, median 104 ms. Not a Windows or actual project benchmark; native CI and client tests pending.
