# T09.03 — удалённый Git-тег и доказательный отчёт

[**Русский — оригинал**](RELEASE_REPORT.md) | [English — перевод](RELEASE_REPORT.en.md)

## Назначение

Release Core теперь содержит три независимых компонента:

- [T09.01](RELEASE_CORE.md): `core/release_inspect.py` проверяет локальный аннотированный тег, версию в указанном коммите и его SHA.
- [T09.02](RELEASE_PREFLIGHT.md): `core/release_preflight.py` проверяет VERSION, CHANGELOG и план сборки/тестов; запуск команд только с явным разрешением.
- **T09.03**: `core/release_remote.py` сравнивает SHA самого аннотированного тега на remote с локальным объектом; `core/release_report.py` формирует JSON или Markdown-отчёт из фактических проверок.

Эти инструменты независимы от Codex, Harness, Claude Code и Hermes. Наличие Git-тега **не** подтверждает публикацию приложения.

## Проверки и команды

```bash
# Только локальный Git и предварительный план; не использует сеть и не запускает тесты
python core/release_report.py --repo . --version 0.0.9

# Явная проверка тега на заранее доверенном Git remote
python core/release_report.py --repo . --version 0.0.9 --verify-remote --remote origin

# Отчёт для человека, без сетевых запросов
python core/release_report.py --repo . --version 0.0.9 --format markdown

# Только для доверенного проекта: запуск команд release-checks.json по явному разрешению
python core/release_report.py --repo . --version 0.0.9 --execute-checks

# Старый релиз: проверка тега по историческому полному SHA, без повторного запуска тестов
python core/release_report.py --repo . --version 0.0.8 --commit <full-commit-sha> --verify-remote
```

Все пути `<...>` заменяются фактическими значениями локальной среды и **не публикуются** в документации. Команды требуют локального Git-репозитория. Сетевой запрос выполняется **только** с `--verify-remote`. Команды сборки и тестов выполняются **только** с `--execute-checks` и должны быть заранее проверены владельцем проекта. Оба флага могут применяться вместе, но для недоверенного Pull Request `--execute-checks` не используется.

## Что доказывает проверка remote

Инструмент запрашивает точный `refs/tags/<version>` у именованного remote через `git ls-remote --refs --tags`. Для аннотированного тега сравнивается **SHA самого объекта tag**, а не только SHA коммита, на который он указывает. Отдельно уже проверены версия в коммите и целевой commit SHA локального тега.

- `PASS` означает, что Git remote в момент запроса сообщил **тот же объект аннотированного тега**.
- `REMOTE_TAG_MISSING` — указанный ref отсутствует.
- `REMOTE_TAG_OBJECT_MISMATCH` — тот же ref указывает на другой объект тега, даже если commit SHA совпадает.
- `REMOTE_QUERY_FAILED` / `REMOTE_QUERY_TIMEOUT` — невозможно проверить remote, не следует приравнивать к отсутствующему тегу.
- `LOCAL_TAG_INVALID` — локальная проверка не прошла, запрос remote не выполняется.

Проверяется выбранный **доверенный remote**, который может быть GitHub или другой Git-сервер. Инструмент не доказывает идентичность сервера вне имеющихся настроек транспорта/доверия, не создаёт GitHub Release и не подтверждает наличие установочного пакета.

## Контракт отчёта

JSON содержит `local_tag_status`, `preflight_status`, `checks_status`, `remote_tag_status`, `stage`, `evidence_status`, `release_readiness`, `problems` и конкретный commit SHA.

- `evidence_status=PASS` — **все запрошенные** проверки прошли; непросмотренные проверки сохраняют `NOT_CHECKED` или `NOT_RUN`.
- `evidence_status=BLOCKED` — обнаружена хотя бы одна ошибка в запрошенных проверках.
- `release_readiness=NOT_VERIFIED` — всегда в T09.03, даже когда локальные тесты и удалённый тег подтверждены.
- `remote_publication=TAG_REF_VERIFIED` — проверен только удалённый Git ref, а не приложение.
- `github_release=NOT_CHECKED` — GitHub Release не проверялся.
- Для исторического коммита `preflight_status=NOT_CHECKED_HISTORICAL`. Повторный запуск тестов старого релиза в текущем HEAD запрещён.

Команда завершается кодом 0 при `evidence_status=PASS`, кодом 1 при BLOCKED. Это **не** код подтверждения готовности приложения к выпуску.

## Проверка завершённого GitHub Actions — T09.04

См. [Release CI](RELEASE_CI.md). После полного завершения workflow можно добавить явные параметры `--verify-ci --github-repo owner/repository --run-id 123456789`. Будут проверены SHA коммита, имя репозитория, событие push в main, правильный workflow и обе обязательные jobs. В отчёт добавляются `ci_status` и реквизиты проверенного run. **Без `--verify-ci` API не вызывается.** Даже `CI_VERIFIED` и `CI_AND_REMOTE_TAG_VERIFIED` не означают готовый или опубликованный продукт: `release_readiness=NOT_VERIFIED`.

## Отдельная проверка публикации — T09.05

См. [Release Publication](RELEASE_PUBLICATION.md). Флаг `--verify-publication` требует доверенный `--github-repo`, проверяет соответствие Git remote и запрашивает **опубликованный** GitHub Release. `--format certificate` выдаёт неподписанное свидетельство с воспроизводимым SHA-256 его полей. Полный статус `SOURCE_RELEASE_PUBLISHED` возможен только при подтверждённых удалённом теге, завершённом CI и опубликованных metadata Release. Даже тогда `release_readiness=NOT_VERIFIED` для исполняемого приложения.

## Действительные байты файлов — T09.06

Раздел [RELEASE_ASSETS](RELEASE_ASSETS.md) добавляет явную `--verify-assets` при уже подтверждённом `--verify-publication`. В отчёт включены `publication_asset_content_verification`, `verified_assets` и `artifact_provenance=NOT_VERIFIED`; в свидетельстве `SOURCE_ASSETS_BYTES_VERIFIED` возможен только при подтверждённых CI, удалённом теге, опубликованном Release и реально скачанных совпадающих байтах. Контрольная сумма самого свидетельства не является его подписью.

## Аттестация происхождения артефакта — T09.07

Подробнее в [RELEASE_PROVENANCE](RELEASE_PROVENANCE.md). Новый `--verify-provenance` требует `--verify-publication`, реальный локальный `--artifact-file` и доверенный `--signer-workflow`. Модуль сначала проверяет байты файла по метаданным GitHub Release, затем вызывает официальный `gh attestation verify` с exact source commit SHA, `refs/tags/<version>` и конкретной signing identity. Вывод не содержит локального пути. Поле `provenance_status=PASS` подтверждает только проверенную подпись и заявленное происхождение, а не готовность приложения.

## Безопасность и приёмка

- Git fetch/push, создание или обновление тегов не выполняются.
- Для запроса remote используется заданный Git remote, с отключением интерактивных запросов и ограничением времени; `protocol.ext` запрещён.
- Ответ Git проверяется по полному имени ref и формату SHA. Ошибки транспорта не считаются отсутствием тега; секреты и stderr не включаются в отчёт.
- В CI TESSERA новый отчёт выполняется **после** подтверждения аннотированного тега в отдельном GitHub Actions job. До слияния PR его не требуют, поскольку тег версии ещё не существует.
- Тесты с удалёнными репозиториями используют исключительно временный локальный bare Git и не затрагивают историю TESSERA.

**Ограничения:** T09 в целом остаётся PARTIAL. Не реализованы независимое доказательство внешних CI-проверок, безопасная сериализация нескольких агентов, подписи артефактов и финальный контроллер `RELEASED`. Проверка конфигурации сборок в T09.02 не доказывает смысловую достаточность этих сборок.
