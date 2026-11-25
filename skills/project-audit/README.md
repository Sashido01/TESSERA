# Project Audit

[**Русский — оригинал**](README.md) | [English — перевод](README.en.md)

Кандидат независимой версии 0.0.2, уровень II начат. Навык глубокого аудита с упором на доказательства и ограничения, без автоматических исправлений. Начни с [SKILL.md](SKILL.md), затем изучи [направления](references/DIRECTIONS.md), [доказательства](references/EVIDENCE.md), [отчёт](references/REPORT.md), [приёмку](references/ACCEPTANCE.md) и [дорожную карту](references/ROADMAP.md).

Устанавливается вся папка навыка по правилам конкретной Agent Skills-системы. Активация, поведение и независимый релиз пока NOT_VERIFIED; нет обязательных сторонних библиотек.

Опциональный помощник [Inventory Engine](references/INVENTORY.md) работает без сети и Git. Локальные Linux unit-тесты 17/17 для исходных файлов помощника; полный CI кандидата и Windows не подтверждены. Не использовать метаданные вместо хеша содержимого.

Из доверенного checkout TESSERA: `python -B tools/run_skill_tests.py --skill project-audit` запускает только тесты Project Audit (из корня каталога). Для отдельного preflight после принятия Release Core с `--skill`: `python core/release_preflight.py --repo . --skill project-audit --version 0.0.2 --config release-checks-project-audit.json --plan`. `--execute` только с разрешением. Это не требует GitHub, не создаёт тег и не подтверждает поведение агента. Конфигурация preflight кандидата зависит от PR #70; до его принятия не заявлять работоспособность команды.
