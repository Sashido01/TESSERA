# Project Audit

[Русский — оригинал](README.md) | **English — translation**

Independent version 0.0.3 candidate, level II in progress. Deep project audit emphasizing evidence and limitations, without automated fixes. Start with [SKILL.md](SKILL.md) or its [English translation](references/SKILL.en.md), then read [directions](references/DIRECTIONS.en.md), [evidence](references/EVIDENCE.en.md), [report](references/REPORT.en.md), [acceptance](references/ACCEPTANCE.en.md) and [roadmap](references/ROADMAP.en.md).

Install the entire skill directory according to your Agent Skills host. Activation, behavior and independent release remain NOT_VERIFIED; no mandatory third-party libraries.

Optional [Inventory Engine](references/INVENTORY.en.md) works without network or Git. Local Linux unit tests 17/17 for original helper files; full candidate CI and Windows unverified. Do not substitute metadata for a content hash.

From a trusted TESSERA checkout root: `python -B tools/run_skill_tests.py --skill project-audit` runs only Project Audit tests. For independent preflight with `--skill`: `python core/release_preflight.py --repo . --skill project-audit --version 0.0.3 --config release-checks-project-audit.json --plan`. Use `--execute` only with authorization. No GitHub required; this creates no tag and does not prove agent behavior. Release Core was accepted in v0.0.70; full candidate CI and the separate preflight for the new version still require verification.

Optional [Git Inspector](references/GIT_INSPECTOR.en.md): 13/13 local Linux tests, status and ref counts without emitting names or remote URLs. Trusted Git checkout only. Not an integrity check; for a non-Git project use Inventory Engine and other available evidence.
