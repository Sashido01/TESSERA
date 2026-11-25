# Project Audit

[**Русский — оригинал**](README.md) | [English — перевод](README.en.md)

Кандидат независимой версии 0.0.3, уровень II развивается. Навык глубокого аудита с упором на доказательства и ограничения, без автоматических исправлений. Начни с [SKILL.md](SKILL.md), затем изучи [направления](references/DIRECTIONS.md), [доказательства](references/EVIDENCE.md), [отчёт](references/REPORT.md), [приёмку](references/ACCEPTANCE.md) и [дорожную карту](references/ROADMAP.md).

Устанавливается вся папка навыка по правилам конкретной Agent Skills-системы. Активация, поведение и независимый релиз пока NOT_VERIFIED; нет обязательных сторонних библиотек.

Опциональный помощник [Inventory Engine](references/INVENTORY.md) работает без сети и Git. Linux unit-тесты кандидата Inventory Engine 21/21; Windows v0.0.74 FAIL (#80), исправление ожидает нативной приёмки. Не использовать метаданные вместо хеша содержимого.

Из доверенного checkout TESSERA: `python -B tools/run_skill_tests.py --skill project-audit` запускает только тесты Project Audit (из корня каталога). Для отдельного preflight с `--skill`: `python core/release_preflight.py --repo . --skill project-audit --version 0.0.3 --config release-checks-project-audit.json --plan`. `--execute` только с разрешением. Это не требует GitHub, не создаёт тег и не подтверждает поведение агента. Release Core принят в v0.0.70; полный CI кандидата и запуск отдельного preflight с новой версией требуют подтверждения.

Опциональный [Git Inspector](references/GIT_INSPECTOR.md): 13/13 локальных тестов Linux, счётчики статуса и refs без вывода имён и адресов remote. Только доверенный Git checkout. Не заменяет проверку целостности; для проекта без Git используй Inventory Engine и другие доступные доказательства.
