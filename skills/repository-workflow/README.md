# Repository Workflow

[**Русский — оригинал**](README.md) | [English — перевод](README.en.md)

Независимый кандидат 0.0.2. Навык организации быстрых, непрерывных и проверяемых циклов разработки, включая локальные проекты без GitHub. Устанавливай всю папку в выбранную Agent Skills-систему. Начни с [SKILL.md](SKILL.md); [процесс](references/WORKFLOW.md), [задачи](references/TASKS.md), [CI](references/CI.md), [технический долг](references/DEBT.md), [приёмка](references/ACCEPTANCE.md), [дорожная карта](references/ROADMAP.md).

Помощник на стандартной библиотеке Python опционален. Не требует платных API, внешней БД, сервиса-оркестратора или GitHub. 0.0.1 принят в каталоге v0.0.69. Для кандидата 0.0.2 — 17/17 локальных тестов, полный CI и реальная активация NOT_VERIFIED.

Из доверенного корня TESSERA: `python -B tools/run_skill_tests.py --skill repository-workflow`; независимый план `python core/release_preflight.py --repo . --skill repository-workflow --version 0.0.2 --config release-checks-repository-workflow.json --plan`. Выполнять `--execute` только с разрешением. Эти команды ещё требуют CI на новом кандидате.
