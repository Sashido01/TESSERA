# Project Audit

[Русский — оригинал](README.md) | **English — translation**

Independent version 0.0.4 candidate, level II in progress. Deep project audit emphasizing evidence and limitations, without automated fixes. Start with [SKILL.md](SKILL.md) or its [English translation](references/SKILL.en.md), then read [directions](references/DIRECTIONS.en.md), [evidence](references/EVIDENCE.en.md), [report](references/REPORT.en.md), [acceptance](references/ACCEPTANCE.en.md) and [roadmap](references/ROADMAP.en.md).

Install the entire skill directory according to your Agent Skills host. Activation, behavior and independent release remain NOT_VERIFIED; no mandatory third-party libraries.

Optional [Inventory Engine](references/INVENTORY.en.md) works without network or Git. Linux candidate Inventory Engine unit tests 21/21; Windows v0.0.74 FAIL (#80), fix awaits native acceptance. Do not substitute metadata for a content hash.

From a trusted TESSERA checkout root: `python -B tools/run_skill_tests.py --skill project-audit` runs only Project Audit tests. For independent preflight with `--skill`: `python core/release_preflight.py --repo . --skill project-audit --version 0.0.4 --config release-checks-project-audit.json --plan`. Use `--execute` only with authorization. No GitHub required; this creates no tag and does not prove agent behavior. Release Core was accepted in v0.0.70; full candidate CI and the separate preflight for the new version still require verification.

Optional [Git Inspector](references/GIT_INSPECTOR.en.md): 13/13 local Linux tests, status and ref counts without emitting names or remote URLs. Trusted Git checkout only. Not an integrity check; for a non-Git project use Inventory Engine and other available evidence.

Optional [Evidence Core](references/EVIDENCE_CORE.en.md): accepts only an explicitly supplied JSON register and checks its format, links, scope and binding to the declared snapshot. Windows 11 / Python 3.14.3: 15/15 tests. It does not read projects, run checks, or authenticate sources or facts; integrated CI and actual agent use remain pending.
