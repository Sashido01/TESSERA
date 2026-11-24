# Microversion Release

[**Русский — оригинал**](README.md) | [English — перевод](README.en.md)

**Переносимый Agent Skill для Codex, DeepSeek Harness, Claude Code, Hermes и других совместимых агентов.** Помогает вести микроверсии, оформлять коммиты и подтверждать обязательные аннотированные теги релизов. TESSERA хранит [русский SKILL.md](SKILL.md) как единственную точку входа, английская версия доступна для чтения: [SKILL.en.md](references/SKILL.en.md).

## Микроверсии и релизы

- Новые проекты: старт `0.0.0`. Каждое самостоятельное проверенное изменение увеличивает PATCH.
- После `.99`, если задача не закончена, допускаются `.100`, `.101` и далее, без искусственного ограничения.
- После фактического завершения и обязательных проверок: `0.0.99 → 0.1.0`, `0.1.99 → 0.2.0`, `0.99.99 → 1.0.0`. Если работа закончилась на `0.0.107`, после неё возможен `0.1.0`.
- **Каждый релиз обязательно получает аннотированный тег Git, связанный с точным релизным коммитом.** Если тег отсутствует или неверен, статус `BLOCKED / RELEASE_NOT_TAGGED`, а не COMPLETE. Изменения и описания — на понятном русском языке.

## Интеграция с агентами

| Среда | Папка навыков внутри проекта |
| --- | --- |
| Codex | `<project-root>/.agents/skills/` |
| DeepSeek Harness | `<project-root>/.dsh/skills/` |
| Claude Code | `<project-root>/.claude/skills/` |
| Hermes | `<project-root>/.hermes/skills/` или `<project-root>/.agents/skills/` |
| Другая совместимая | Явно переданный `<skills-dir>` |

Пример установки из клонированной TESSERA:

```bash
python skills/microversion-release/scripts/install.py --platform codex --project-root <project-root>
python skills/microversion-release/scripts/install.py --platform codex --project-root <project-root> --apply
```

По умолчанию `DRY-RUN`, только вывод пути. Безопасная установка **не перезаписывает** существующие папки. Для пользовательских профилей и других агентов используйте `--platform generic --target-root <skills-dir> --apply`, предварительно проверив расположение.

Установщик отклоняет символические ссылки и перенаправленные компоненты стандартного проектного пути, а также ссылки и специальные файлы в исходном навыке. Явный `--target-root` разрешается в выбранный пользователем каталог; это не разрешение на следование ссылкам внутри навыка. Проверки рассчитаны на доверенную файловую систему без конкурентной подмены путей; защита от гонок TOCTOU и нативные тесты точек соединения (junction) в Windows пока NOT_VERIFIED.

Для Hermes есть также штатный путь установки через собственный каталог на GitHub:

```bash
hermes skills tap add Sashido01/TESSERA
hermes skills install Sashido01/TESSERA/skills/microversion-release
```

Необходимость `hermes skills trust` зависит от выбранного проектного пути. **Полная инструкция для всех платформ:** [INTEGRATION.md](references/INTEGRATION.md) / [English](references/INTEGRATION.en.md).

## Калькулятор и проверка тегов

Из каталога навыка:

```bash
python scripts/next_version.py 0.0.99 --mode work
python scripts/next_version.py 0.0.107 --mode release
python scripts/release_tag.py verify 0.1.0 --repo <project-root>
python scripts/release_tag.py create 0.1.0 --repo <project-root> --message "Релиз 0.1.0 — исправлен запуск приложения"
python -m unittest discover -s tests -v
```

`release_tag.py create` создаёт только локальный аннотированный тег **после проверок и получения разрешения на запись в Git**. Он не выполняет `git push`, не формирует сборку и не объявляет релиз успешным без остальных проверок. [Правила тегов](references/RELEASE_TAGS.md).

## Совместимость и ограничения

Переносимая структура и CLI проверяются в CI TESSERA. **Установка, автоматическая активация и принудительное исполнение в реальных клиентских профилях Codex, Harness, Claude и Hermes пока NOT_VERIFIED.** Один SKILL.md не заменяет проверенный хук, проверку Git, CI или блокировку для параллельных агентов. Существующие проекты и опубликованную историю нельзя менять задним числом.

## Лицензия

MIT. Полный текст лицензии поставляется вместе с навыком: [LICENSE.txt](LICENSE.txt).
