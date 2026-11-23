# Подключение Microversion Release к мультиагентным системам

[**Русский — оригинал**](INTEGRATION.md) | [English — перевод](INTEGRATION.en.md)

## Единая переносимая основа

Структура навыка `SKILL.md + scripts/ + references/` соответствует соглашению Agent Skills. Нет обязательной зависимости от Codex, DeepSeek Harness, Claude Code, Hermes, MCP, отдельного сервера или сетевой авторизации. Для скриптов проверки нужен Python 3, для Git-тегов — установленный Git и соответствующие права.

В разных средах **различаются** папки загрузки навыков, условия обнаружения, доверие к проекту и способ принудительного выполнения. Наличие `SKILL.md` не означает автоматическое исполнение после каждого изменения.

## Быстрая безопасная установка

Из корня клонированной TESSERA (замените `<project-root>` на каталог целевого проекта):

```bash
python skills/microversion-release/scripts/install.py --platform codex --project-root <project-root>
python skills/microversion-release/scripts/install.py --platform codex --project-root <project-root> --apply
```

Без `--apply` программа **ничего не изменяет** и только показывает путь. С `--apply` копирует целый навык; существующий каталог не перезаписывается, секреты и чужие файлы не затрагиваются.

Варианты: `--platform codex|harness|claude|hermes|shared`. `shared` использует общий для Codex и Hermes проектный каталог `<project-root>/.agents/skills/`. Для нестандартного профиля или других систем задайте явно `--platform generic --target-root <skills-dir> --apply`. Пользовательские установки выполняйте только после проверки активного каталога соответствующей системы.

## Планируемый стандартный канал распространения

После проверки конкретной версии **официального GitHub CLI** главным способом установки/обновления навыка станет `gh skill`. До завершения испытаний существующий Python-установщик остаётся подтверждённым только как локальный механизм копирования. Для офлайн-режима и нестандартных профилей он будет сохранён как минимальный резерв.

TESSERA не требует установки сторонних менеджеров навыков. Подробные границы зависимостей: [документ TESSERA](../../../docs/DEPENDENCIES.md). Проверки `skills-ref` и NVIDIA SkillEvaluator Tier 1 относятся к будущему контуру качества, а не к runtime-навыку. Платные Tier 2/3 не применяются.

## Codex (OpenAI)

Проект: `<project-root>/.agents/skills/microversion-release/SKILL.md`. Пользовательский уровень: `<user-home>/.agents/skills/microversion-release/SKILL.md`. Codex находит навыки по описанию или через явный выбор в интерфейсе. Используйте его актуальные механизмы загрузки и, при необходимости, проектный `AGENTS.md` для обязанности применять навык. **Загрузка не гарантирует обязательного тегирования** без независимой проверки Git/CI.

Документация: https://developers.openai.com/codex/skills

## DeepSeek Harness

Проектный каталог: `<project-root>/.dsh/skills/microversion-release/`. Пользовательский — `<DSH_HOME>/skills/microversion-release/`, где `DSH_HOME` определяется реально работающим профилем. Убедитесь, что в конфигурации включены `dsh-skill`, `dsh-skill-filesystem` и потребитель `dsh-tool-skill`. Проверьте видимость навыка в каталоге сессии.

Для **обязательных** проверок перед остановкой агента требуется отдельный проверенный хук Harness, а не только SKILL.md. Не включайте новые плагины без аудита версии и прав.

Документация: https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md

## Claude Code (Anthropic)

Проект: `<project-root>/.claude/skills/microversion-release/SKILL.md`. Пользовательский каталог: `<user-home>/.claude/skills/microversion-release/SKILL.md`. Claude может применять навык автоматически по описанию; ручной вызов зависит от версии клиента. Для обязательного контроля добавьте проектные инструкции в `CLAUDE.md` и независимую проверку в CI или Git Hooks. Никаких специальных полей только для Claude в исходном YAML не требуется.

Документация: https://code.claude.com/docs/en/skills

## Hermes Agent (Nous Research)

Проектный каталог: `<project-root>/.hermes/skills/microversion-release/` **или** общий `<project-root>/.agents/skills/microversion-release/`. Пользовательский профиль по умолчанию использует `<user-home>/.hermes/skills/`, но альтернативные профили необходимо проверять отдельно. По требованиям Hermes проектные навыки **не загружаются из неизвестного репозитория без доверия**; решение о доверии принимайте после просмотра файлов, затем в проекте можно выполнить `hermes skills trust`.

TESSERA также подходит для штатного каталога Hermes (tap):

```bash
hermes skills tap add Sashido01/TESSERA
hermes skills search microversion-release
hermes skills install Sashido01/TESSERA/skills/microversion-release
```

Команды показаны на основании официального синтаксиса Hermes; установка и обнаружение в конкретном пользовательском Desktop/CLI пока **NOT_VERIFIED**. Проверяйте отчёт сканера безопасности и активный профиль.

Документация: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills

## Другие агенты и оркестраторы

Для среды, поддерживающей Agent Skills, используйте `--platform generic --target-root <skills-dir>`. Для платформ без поддержки стандарта нужна отдельная интеграция, читающая `SKILL.md`, предоставляющая модели документацию и вызывающая детерминированный скрипт проверки перед релизом.

Для нескольких агентов, работающих с одним репозиторием: единый источник версии, сериализация коммитов и релизов, повторная проверка HEAD, запрет перезаписи существующих тегов и совместный CI-контроль. Модель и Agent Skills сами по себе не являются системой распределённых блокировок.

## Приёмка интеграции

1. Проверить фактическую версию клиента и корневую папку навыков.
2. Установить весь каталог и убедиться, что навык доступен агенту.
3. Проверить вычисление `0.0.99 → 0.0.100` для незавершённой задачи.
4. В **изолированном тестовом Git-репозитории** выполнить релиз `0.1.0`: реальные проверки, содержательный коммит, аннотированный тег и `release_tag.py verify`.
5. Убедиться, что отсутствующий/неправильный тег даёт `BLOCKED / RELEASE_NOT_TAGGED`.
6. Отдельно проверить автоматическую активацию, если она требуется: наличие навыка не доказывает её.
7. Не объявлять все платформы проверенными только по одному успешному CI.

## Официальные источники

- https://agentskills.io/specification
- https://developers.openai.com/codex/skills
- https://code.claude.com/docs/en/skills
- https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md
- https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
