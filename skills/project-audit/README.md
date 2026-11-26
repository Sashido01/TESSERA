# Project Audit

[**Русский — оригинал**](README.md) | [English — перевод](README.en.md)

Последняя подтверждённая независимая версия — 0.0.4; уровень II развивается. Навык глубокого аудита с упором на доказательства и ограничения, без автоматических исправлений. Начни с [SKILL.md](SKILL.md), затем изучи [направления](references/DIRECTIONS.md), [доказательства](references/EVIDENCE.md), [отчёт](references/REPORT.md), [приёмку](references/ACCEPTANCE.md) и [дорожную карту](references/ROADMAP.md).

Устанавливается вся папка навыка по правилам конкретной Agent Skills-системы. Активация и поведение в реальном агенте пока NOT_VERIFIED; независимый тег project-audit/v0.0.4 подтверждён; нет обязательных сторонних библиотек.

Опциональный помощник [Inventory Engine](references/INVENTORY.md) работает без сети и Git. Linux unit-тесты кандидата Inventory Engine 21/21; историческая Windows-ошибка v0.0.74 (#80) исправлена и принята в нативном CI v0.0.76; TOCTOU остаётся открытым. Не использовать метаданные вместо хеша содержимого.

Из доверенного checkout TESSERA: `python -B tools/run_skill_tests.py --skill project-audit` запускает только тесты Project Audit (из корня каталога). Для отдельного preflight с `--skill`: `python core/release_preflight.py --repo . --skill project-audit --version 0.0.4 --config release-checks-project-audit.json --plan`. `--execute` только с разрешением. Это не требует GitHub, не создаёт тег и не подтверждает поведение агента. Release Core принят в v0.0.70; CI v0.0.78 подтверждён; отдельный запуск preflight не считается доказанным только по общему CI.

Опциональный [Git Inspector](references/GIT_INSPECTOR.md): 13/13 локальных тестов Linux, счётчики статуса и refs без вывода имён и адресов remote. Только доверенный Git checkout. Не заменяет проверку целостности; для проекта без Git используй Inventory Engine и другие доступные доказательства.

Опциональный [Evidence Core](references/EVIDENCE_CORE.md): принимает только явно переданный JSON-реестр и проверяет формат, связи, область и привязку к объявленному снимку. Windows 11 / Python 3.14.3: 15/15 тестов. Не читает проект, не запускает проверки и не удостоверяет источники или факты; CI 45658775191 SUCCESS и точный независимый тег подтверждены; реальный агентный запуск NOT_VERIFIED.

Опциональный [DELTA planner](references/DELTA_PLAN.md) — кандидат, сравнивает два объявленных графа и планирует повторные проверки без переноса evidence. 14/14 изолированных Linux-тестов; полный CI и агентная приёмка открыты.
