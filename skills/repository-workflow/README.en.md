# Repository Workflow

[Русский — оригинал](README.md) | **English — translation**

Skill version 0.0.3. Organizes fast, continuous, verifiable development cycles, including local projects without GitHub. Install the entire folder in the selected Agent Skills host. Start with [SKILL.md](SKILL.md) or the [translation](references/SKILL.en.md); [process](references/WORKFLOW.en.md), [tasks](references/TASKS.en.md), [CI](references/CI.en.md), [technical debt](references/DEBT.en.md), [acceptance](references/ACCEPTANCE.en.md), [roadmap](references/ROADMAP.en.md).

The optional Python planner operates only on an explicitly supplied snapshot. Windows 11 / Python 3.14.3: 17/17 tests. It does not establish evidence truth or block writes; actual agent evaluation remains NOT_VERIFIED. No paid APIs, external database or orchestration service is required.

From a trusted TESSERA checkout: `python core/release_preflight.py --repo . --skill repository-workflow --version 0.0.3 --config release-checks-repository-workflow.json --plan`. Planning runs no commands and creates no tag.

Optional [Worktree Inventory](references/WORKTREE_INVENTORY.en.md) candidate compares two supplied binary captures, invokes no Git and deletes no branches. 21/21 isolated Linux tests (Git 2.47.3), including an actual disposable Git fixture. Full CI and Windows for the new module are open.
