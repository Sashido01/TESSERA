# Repository Workflow

[**Русский — оригинал**](README.md) | [English — перевод](README.en.md)

Версия навыка 0.0.2. Организует быстрые, непрерывные и проверяемые циклы разработки, включая локальные проекты без GitHub. Устанавливай всю папку в выбранную Agent Skills-систему. Начни с [SKILL.md](SKILL.md); [процесс](references/WORKFLOW.md), [задачи](references/TASKS.md), [CI](references/CI.md), [технический долг](references/DEBT.md), [приёмка](references/ACCEPTANCE.md), [дорожная карта](references/ROADMAP.md).

Опциональный Python планировщик работает только с явно предоставленным снимком. Windows 11 / Python 3.14.3: 17/17 тестов. Планировщик не проверяет истинность доказательств и не блокирует запись; реальные агентные оценки остаются NOT_VERIFIED. Навык не требует платных API, внешней БД или сервиса-оркестратора.

Из доверенного checkout TESSERA: `python core/release_preflight.py --repo . --skill repository-workflow --version 0.0.2 --config release-checks-repository-workflow.json --plan`. План ничего не исполняет и не создаёт тег.
