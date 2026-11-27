# Project Cleanup

[Русский — оригинал](README.md) | **English — translation**

Version 0.0.1 — initial candidate. A standalone skill for local and GitHub hygiene, storage measurement and growth prevention. Install the entire directory; see [SKILL](references/SKILL.en.md). No paid APIs or external packages required.

```bash
python -B scripts/inventory.py --root <project-root>
python -B scripts/inventory.py --root <project-root> --details
```

The first mode outputs aggregates only; the second adds private relative paths of the largest observed REVIEW files (do not publish). No deletion. See [inventory](references/INVENTORY.en.md), [Git/GitHub](references/GIT_STORAGE.en.md), [roadmap](references/ROADMAP.en.md). Native Windows/Linux CI and agent acceptance are NOT_VERIFIED.
