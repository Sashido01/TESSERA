# Нативная проверка Windows

[**Русский — оригинал**](WINDOWS_TESTING.md) | [English — перевод](WINDOWS_TESTING.en.md)

## Обязательная проверка каждого PR и main

- `windows_skill_checks`: GitHub-hosted windows-latest, Python 3.14, точный checkout SHA, закреплённые Actions, без сохранения credentials, права contents: read, без байткода; три skill suites через общий runner. Не использовать WSL вместо Windows.
- Агрегатор validate требует успеха четырёх групп; skip/failure/cancelled не равны PASS. Linux Docker/security группы сохраняются.
- Для каждой проверки записать версию ОС, Python и Git, SHA, exit code, passed/failed/skipped; реальные ограничения не скрывать. FIFO на Windows N/A; отсутствие symlink privilege не является проверкой junction. Не объявлять Windows COMPLETE по моделированию Linux.

## Матрица расширения

| ID | Область | Критерий |
| --- | --- | --- |
| W01 | Inventory, вложенные каталоги NTFS, пробелы и Unicode | Точные метаданные, отсутствует ложный DEVICE_BOUNDARY |
| W02 | Junction/reparse point, symlink, другое устройство | Не обходить цель, сохранить явную границу; реальное второе устройство отдельно |
| W03 | ACL, недоступные каталоги, locked files, long paths | Явный PARTIAL или отказ; не менять ACL, не читать содержимое |
| W04 | Git CLI, unborn/detached, dirty, refs, конфликт тегов | Точный результат, отсутствие записи при read-only; запись только fixture |
| W05 | Git context Codex (TD17), PowerShell/UTF-8 | Не снимать security gate; различать чистый fixture и реальную сессию |
| W06 | Release Core, каталог, ZIP, pin/update/rollback | Отдельный Windows набор с доказанной переносимостью; не заменять Linux full CI |
| W07 | Codex/Harness на реальной Windows | Discovery/explicit use/auto-use/enforcement независимо; точный pin |
| W08 | Версии Python | 3.14 — текущий обязательный runner; 3.13 и иные поддерживаемые версии отдельная проверка после измерения |

W01–W08 — критерии, не результаты. Расширять native runner поэтапно, не ослаблять защиту и не повышать таймауты без измерения. При обнаружении сбоя исправлять существующий PR. Временные локальные каталоги и Git fixtures без remote, настоящие данные и профили неизменны. Не запускать сторонние сканеры в пользовательском профиле; Linux security coverage сохраняется.

## Повторная интеграция

Текущий пользовательский pin v0.0.74 сохранять. Кандидат можно испытать в отдельном временном проекте из точного проверенного SHA без замены глобальных навыков. После принятия и подтверждения тега — staging нового pin, сверка tree, тесты, документированный backup/rollback и отдельное разрешение на обновление. Не использовать --force/--all/--unpin в существующем профиле. Для локального повторного запуска использовать `python -B`. Отчёт не должен содержать персональные пути, значения переменных или токены.
