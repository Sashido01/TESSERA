# Style for commits, tags, changelogs, and releases

[Русский — основной язык](STYLE.md) | **English — translation**

## Core principle

Write so that a person understands the result: clearly, specifically, without fabricated facts or exaggeration. Technical terms are useful when they clarify the actual change.

## Commits

**Good** (examples retained in Russian because that is the project's required commit language):

- «Исправлен повторный запуск приложения после обновления» — Fixed restarting the application after an update.
- «Добавлена проверка доступности локальной базы перед запуском» — Added a local database availability check before startup.
- «Уточнена инструкция восстановления после сбоя» — Clarified the recovery instructions.
- «Подготовлена версия 0.2.0 с проверенной сборкой для Windows» — Prepared version 0.2.0 with a verified Windows build.

**Poor**:

- “chore: bump to 0.1.24”
- “fix: misc stuff”
- «Выполнены работы в рамках текущего спринта» — “Sprint work has been performed.”
- «Обновлена документация и оптимизированы процессы» — “Documentation updated and processes optimized.”

Use a short, standalone subject line without a trailing period. For complex changes, add 2–5 sentences explaining the purpose, affected areas, and actual verification. Never claim tests that did not run.

## Tags

A Git tag name is machine-readable: `v0.1.24`. Multiple skills in one repository may use namespaced tags such as `microversion-release/v0.1.24`. The **annotation** describes the real change in Russian:

- «Версия 0.1.24 — исправлен повторный запуск приложения»
- «Релиз 0.2.0 — устойчивый запуск и восстановление после ошибок»

Create annotated tags on verified commits. Never move existing published tags.

## CHANGELOG

### 0.1.24 — Restart issue fixed

**What changed:** a specific result supported by the source code and checks.

**How it was verified:** the actual command, environment, and outcome. If no test ran, explicitly state “Not tested.”

**Limitations:** unverified platforms and scenarios. Do not claim that there are no limitations unless you know that is true.

## Releases

### Version 0.2.0 — More reliable startup

**What's new:** actual user-facing changes.

**Fixes:** specific defects and verified results.

**Verification:** commands, platforms, and test outcomes.

**Installation and updates:** provide instructions only if the package actually exists.

**Still unverified:** remaining unknown scenarios.

## Distinguish these states

- A version number does not prove quality.
- A Git tag is not a built application.
- A changelog entry is not a published GitHub Release.
- A build artifact exists only after it has actually been created and checked.

## Continuing past .99

A three-digit PATCH is a valid working microversion, not an error or failure. The commit at `0.0.100` must explain the actual work, not merely the transition past 99. After the verified completion of a task, a `0.1.0` release is possible. If the work is only complete at `0.0.107`, do not mark `0.0.100` as the final commit or release too early.
