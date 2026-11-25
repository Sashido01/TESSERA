# Repository Workflow

[Русский — оригинал](README.md) | **English — translation**

Independent candidate 0.0.2. Organizes fast, continuous, verifiable development cycles, including local projects without GitHub. Install the entire folder in the selected Agent Skills host. Start with [SKILL.md](SKILL.md) or the [translation](references/SKILL.en.md); [process](references/WORKFLOW.en.md), [tasks](references/TASKS.en.md), [CI](references/CI.en.md), [technical debt](references/DEBT.en.md), [acceptance](references/ACCEPTANCE.en.md), [roadmap](references/ROADMAP.en.md).

The Python standard-library helper is optional. No paid APIs, external database, orchestration service or GitHub required. Actual agent activation and full CI remain NOT_VERIFIED.

Catalog 0.0.1 accepted in v0.0.69; candidate 0.0.2 has 17/17 local tests. From the trusted TESSERA root: `python -B tools/run_skill_tests.py --skill repository-workflow`; independent plan `python core/release_preflight.py --repo . --skill repository-workflow --version 0.0.2 --config release-checks-repository-workflow.json --plan`. Use `--execute` only with authorization. Full candidate CI and real agent activation remain unverified.
