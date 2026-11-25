# Реестр технического долга TESSERA

[**Русский — оригинал**](TECHNICAL_DEBT.md) | [English — перевод](TECHNICAL_DEBT.en.md)

Снимок наблюдений 25.11.2026: main v0.0.66, SHA a550e0e638ca51a8a9b034773930da7ba5c25796, CI 45572387469 PASS и точный аннотированный тег подтверждены. Состояние веток/CI изменяется; перепроверять по API и локальному Git, а не считать этот снимок live. Закрывать записи только с фактом, SHA, проверкой и остаточными ограничениями. Активные рабочие ветки не равны заброшенным. Не удалять работу ради нулевого счётчика Issues/PR.

| ID | Приоритет | Долг и критерий закрытия | Статус на снимке |
|---|---|---|---|
| TD01 | P0 | PR #67 FULL_TIER1_SCANNER_VERSION:bandit: проверить tests-only runtime coverage реальным CI; не снижать пороги | CI_FAILED, исправление a2d4b25f04ecc277d646e673b8c09189fad20914 отправлено |
| TD02 | P0 | Независимый тег навыка: чтение его VERSION, проверка exact annotated commit, remote/report/preflight, совместимость legacy | IN_PROGRESS, t16-skill-tag-inspection |
| TD03 | P0 | Ruleset refs/tags/v* не защищает namespaced skill tags; согласовать расширение и проверить без разрушения опубликованных тегов | OPEN |
| TD04 | P0 | CI bottleneck: 488/943 с и 345/700 с история; разделить независимые jobs, required aggregate fail-closed, измерить wall-clock и runner-minutes | OPEN |
| TD05 | P0 | T12: Semgrep host isolation, advisory applicability (mcp, opentelemetry-api, wcmatch), Go reachability, TOCTOU/junction, output/resource bounds; конкретный риск закрывать доказательно | PARTIAL |
| TD06 | P0 | T03–T05/T13: установка, обнаружение, обязательное применение Microversion Release в реальных Codex/Harness; локальные ОС и мультиагентная работа | NOT_VERIFIED |
| TD07 | P1 | Синхронизация roadmap с T09/T10: pin/update и ZIP уже частично проверены; не путать локальные проверки с реальным клиентом | OPEN |
| TD08 | P1 | Project Audit уровень I: PR #67 и агентные E01–E20; отдельный Inventory Engine кандидат, интеграция и Windows-проверка | PARTIAL |
| TD09 | P1 | Repository Workflow: утверждённая методология, локальный планировщик, реальные evals, переносимость, bootstrap | PARTIAL |
| TD10 | P1 | Позднее назначение версии, DAG, изоляция ресурсов, обновление базы и повторная проверка без force-push; проверить параллельные ветки на реальном GitHub | PARTIAL |
| TD11 | P1 | T17: независимый выпуск, актуальная attestation конкретных артефактов, safe update/rollback; не выдавать Git tag за GitHub Release | OPEN |
| TD12 | P1 | Runner: локальные лимиты времени/вывода и потомков, классификация ошибок, отсутствие обычных успешных тестов блокирует PASS; Windows regression | PARTIAL |

## Гигиена при каждом цикле
Проверить open issues отдельно от PR, ветки и worktrees, активные задачи/зависимости, упавшие/отменённые/просроченные checks, missing tags, документацию, TODO/дубли, зависимости и риски. Для каждой находки сохранить источник/приоритет/критерий; не создавать дубли. Исправление → релевантная проверка → доказательство → закрытие исходной записи. Если требуется владелец, WAIT_OWNER и продолжение независимых задач. После squash не считать ветку ненужной только по ancestry; проверь принятый diff/PR и локальные данные. Удаление лишь разрешённой слитой ветки, без force. Долг не скрывать и не закрывать формально. Ссылки: [ROADMAP](ROADMAP.md), [параллельная работа](PARALLEL_WORKFLOW.md).
