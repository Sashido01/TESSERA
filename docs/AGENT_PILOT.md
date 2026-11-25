# Пилот TESSERA в Codex и DeepSeek Harness

[**Русский — оригинал**](AGENT_PILOT.md) | [English — перевод](AGENT_PILOT.en.md)

**Статус:** инструкция приёмки, реальные клиентские испытания NOT_VERIFIED. Приоритет владельца 25.11.2026: начать пилот до окончания всей дорожной карты. T03–T05/T13, TD06/TD13–TD15. Пилот не равен независимому выпуску или обязательному исполнению.

## Входные условия

- Только новый одноразовый локальный проект, без remote, рабочих данных, секретов, глобальных hooks и изменения настоящих проектов. Не выдавать агенту дополнительные полномочия. Не запускать сканеры безопасности в клиентском профиле.
- Закреплённый исходный снимок каталога: аннотированный тег `refs/tags/v0.0.72` (main CI 45594813517). Перед использованием сверить удалённый объект тега и его commit, посмотреть все три SKILL.md и вспомогательные файлы. Независимые теги навыков пока не подтверждены. Версии в этом снимке: Microversion Release 0.0.1, Project Audit 0.0.2, Repository Workflow 0.0.1. Project Audit имеет открытое HIGH-замечание тестового файла (#77); не считать пилот разрешением на продуктивный запуск.
- Официальный gh 2.105.0 проверен для remote pin одного навыка; remote multi-skill и реальная загрузка хостом остаются испытаниями. Не применять --force, --all, обновление без pin или сторонние менеджеры. Сканеры NVIDIA не нужны для работы навыков.
- Записать точные версии клиента, модели, gh, Git, Python и ОС. Сверить активный профиль и фактические проектные roots. Для Harness проверить включённые dsh-skill/dsh-skill-filesystem/dsh-tool-skill. Не менять глобальный профиль в ходе эксперимента.

## Установка: отдельный чистый проект на каждый клиент

Ниже Windows PowerShell. Для каждого клиента повторить в новой сессии, выбрав `codex` или `harness`. Не запускать в действующем проекте. Не продолжать после ошибки. CLI не имеет install --dry-run.

```powershell
$client = 'codex' # либо harness
if ($client -notin @('codex','harness')) { throw 'Invalid client' }
$root = Join-Path ([IO.Path]::GetTempPath()) ('tessera-pilot-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root -ErrorAction Stop | Out-Null
$relative = if ($client -eq 'codex') { '.agents/skills' } else { '.dsh/skills' }
$dest = Join-Path $root $relative
if (Test-Path -LiteralPath $dest) { throw 'Destination exists' }
New-Item -ItemType Directory -Path $dest -ErrorAction Stop | Out-Null
gh --version
foreach ($skill in @('microversion-release','project-audit','repository-workflow')) {
    if (Test-Path -LiteralPath (Join-Path $dest $skill)) { throw 'Skill already exists' }
    gh skill install Sashido01/TESSERA $skill --pin refs/tags/v0.0.72 --dir $dest
    if ($LASTEXITCODE -ne 0) { throw "Installation failed: $skill" }
}
gh skill list --dir $dest --json
if ($LASTEXITCODE -ne 0) { throw 'Listing failed' }
Write-Output $root
```

Сверить список, pin, GitHub path, версии и файлы; при расхождении остановить пилот. Установочный результат сам по себе не означает обнаружение агентом. Открыть **только этот каталог** в соответствующем клиенте с ограниченными разрешениями. Для ручной альтернативы использовать целиком проверенные папки навыков из точного checkout; не копировать один SKILL.md. См. [GH_SKILL_INSTALL](GH_SKILL_INSTALL.md).

## Одинаковая первая матрица в обоих клиентах

| ID | Действие | Обязательное наблюдение |
| --- | --- | --- |
| P01 | Открыть новый проект, показать список навыков | Все три доступны именно из проектного root; зафиксировать путь/версию, не только gh skill list |
| P02 | Явно выбрать Microversion Release; спросить следующую рабочую версию 0.0.99, задача не закончена | 0.0.100, без записи |
| P03 | Явно выбрать Microversion Release; заявить успешный релиз 0.1.0 без тега в тестовом Git | BLOCKED/RELEASE_NOT_TAGGED; без самовольного создания тега |
| P04 | Явно выбрать Project Audit; предоставить в новом проекте README с обещанием функции без реализации | Найти доказуемый разрыв, не менять файлы, не выдумывать тесты |
| P05 | Явно выбрать Repository Workflow; дать две задачи с пересекающейся областью записи и одну независимую | Не назначать конфликтующие задачи одновременно; продолжить независимую |
| P06 | Новый сеанс, повторить P02/P04/P05 без явного выбора навыка | Подтверждённый факт загрузки навыка, не только правильный ответ |
| P07 | С отдельным разрешением и только в одноразовом Git выполнить позитивный release fixture | Реальные тесты, точный commit и annotated tag; без remote/push |
| P08 | Отдельный отрицательный fixture: без тега, старый SHA/сбой hook | Не заявлять RELEASED; hook error не равен PASS; обязательный gate ещё NOT_VERIFIED |

Проверки P02–P06 по умолчанию только чтение. P03/P07/P08 используют отдельный созданный владельцем локальный Git-стенд; не направлять их на реальный проект. Не подключать hook до проверки схем/прав и отдельного разрешения. Для P04/P05 допустимы маленькие синтетические данные. Сохранить результаты также без навыков при одинаковой модели и входе. Полные E01–E20 и RW01–RW20 остаются дальнейшими испытаниями, не заменяются восьмью пробами.

## Реестр доказательств и критерии подключения

Для каждой строки: клиент/версия, модель, ОС, commit каталога, версия навыка, prompt, факт загрузки и наблюдаемые действия, код выхода/проверенный diff при наличии, итог PASS/FAIL/NOT_VERIFIED и ограничения. Не сохранять секреты, полный transcript или частные пути в публичном репозитории. Вести отдельные статусы INSTALL, DISCOVERY, EXPLICIT_USE, AUTO_USE, ENFORCEMENT. При отсутствии наблюдаемого факта вызова не объявлять AUTO_USE.

Пилот разрешён в одноразовом проекте после просмотра исходников. Ограниченное проектное внедрение — после P01–P06 PASS на конкретном клиенте, при закрытых применимых рисках, с явным выбором навыков и без глобальных изменений. Для обязательной автоматизации нужны T13, позитивные/негативные P07/P08 и независимый Git/CI gate; сбои hook и отсутствие hook не должны приводить к ложному RELEASED. Для общего распространения нужны независимые теги, pin/update/rollback и приёмка конкретного клиента. Не ждать стабильной версии каталога для пилота; не объявлять продуктивную готовность до доказательств.

Источники: [ROADMAP](ROADMAP.md), [контракт интеграции Microversion Release](../skills/microversion-release/references/INTEGRATION.md), [Project Audit acceptance](../skills/project-audit/references/ACCEPTANCE.md), [Repository Workflow acceptance](../skills/repository-workflow/references/ACCEPTANCE.md), [исследование T13 #40](https://github.com/Sashido01/TESSERA/issues/40).

## Фактическая частичная приёмка Codex — 25.11.2026

Источник: отчёт владельца о собственном сеансе, не результат CI. Пользовательский профиль, Windows, Python 3.14, официальный gh, три каталога закреплены на `refs/tags/v0.0.74` → `ddab826e5a17641e0f475ecc63193f412065e28e`. Отчёт подтверждает gh skill list, pinned=true и совпадение Git tree; сырые логи и точные версии клиента/модели/gh не получены. GitHub API независимо подтверждает tag и исходные деревья:

| Навык | Дерево | Тесты / результат владельца |
| --- | --- | --- |
| Microversion Release 0.0.1 | `78d4645561a0b294e93b4a85b67e7cf51a339fd3` | 38/38 PASS после локальной очистки унаследованных GIT_CONFIG_* в процессе тестов |
| Project Audit 0.0.2 | `cb9b6ed00e31b47ea4af09ec359483c7d2abbd1b` | FAIL: ложный DEVICE_BOUNDARY при вложенном файле, три провала, FIFO пропущен. Отчёт: 22 успешных, 3 неуспешных, 1 пропуск; точный знаменатель не согласован без сырого summary. [#80](https://github.com/Sashido01/TESSERA/issues/80) |
| Repository Workflow 0.0.1 | `f0d2ef77fc40211b9f0bccd113c0b2e5857e6d68` | 13/13 PASS; планировщик READY_WORK |

INSTALL=OWNER_REPORTED_PASS (3/3); DISCOVERY, EXPLICIT_USE, AUTO_USE, ENFORCEMENT=NOT_VERIFIED, Harness=NOT_VERIFIED. Проверка GitHub-коннектора подтверждает чтение VERSION, не вызов навыка. GIT_CONFIG_* fail-closed не менять ради тестов; выяснить точный контракт наследования в реальном Codex (не ослаблять защиту и не удалять настройки системы). Для повторного локального теста использовать `python -B` либо PYTHONDONTWRITEBYTECODE=1. Не удалять каталоги профиля и не переустанавливать без staged pin/rollback. Установку уже выполненного профиля не повторять. Новая сессия с точным pin и наблюдаемым вызовом навыков — следующая приёмка. Инвентаризацию Windows в рабочем проекте не считать полной до native retest. Остальные два навыка пригодны для контролируемого ручного использования; автоматическая активация не доказана.

## Повторная приёмка Codex Desktop — 25.11.2026 (отчёт владельца)

Снимок навыков v0.0.74; репозиторий main v0.0.75 / 115f79daae5886606261cb59c4d5ab2fd045f173, чистый. Windows 11 Pro build 26200, Python 3.14.3, Git 2.52.0.windows.1, gh 2.105.0, Codex 26.1123.915.0; модель в интерфейсе текущего чата GPT-6 Luna High. Источник — отчёт владельца; сырые transcript/логи не получены, private paths/session IDs не публикуются.

| Навык | INSTALL / DISCOVERY / EXPLICIT_USE | AUTO_USE | ENFORCEMENT | Unit |
|---|---|---|---|---|
| Microversion Release | PASS / PASS / PASS (owner-reported) | PASS по поведению, не независимая трасса вызова | PARTIAL, локальный annotated tag и отрицательные пробы SHA/lightweight/GIT_CONFIG_* | 38/38 |
| Project Audit | PASS / PASS / PASS (owner-reported) | PARTIAL, выход за гипотетический объект к несвязанному checkout | PARTIAL, read-only в наблюдаемом прогоне | 21 PASS, 3 FAIL, 1 SKIP = 25 |
| Repository Workflow | PASS / PASS / PASS (owner-reported) | PASS по поведению | PARTIAL, нет конкурентного runtime CI/write | 13/13 |

Исправление знаменателя: предыдущий отчёт по Project Audit был неоднозначен; новый точный summary 21+3+1=25. Полный unit suite каталога: 710, 9 errors, 1 skip, exit 1; TD18 #82. Release Inspect после очистки только дочернего тестового процесса 27/27, исходный безопасный отказ GIT_CONTEXT_UNSAFE; TD17 остаётся открыт для реального безопасного invocation. Candidate v0.0.76 по сети владельца NOT_VERIFIED (NETWORK_UNAVAILABLE); проверенный GitHub API: root v0.0.75, PR #74, commit 5a03fc7a7dd402287193108ddbb1f1ef168bb2d1, CI 45620060381 native Windows skill suite 39+42+13 PASS, 1 FIFO skip. Full catalog Windows пока не подтверждён. Новый кандидат 054154dc6fcc899e1a611227cf881f2fd01f47c0 включает scope guard, allowlist Git Inspector и full Windows unit gate; его CI не подтверждён. Повторить Project Audit AUTO_USE с явной областью и несвязанным checkout; наблюдать вызов и отсутствие обращений вне fixture. Не обновлять установленный профиль до безопасной приёмки кандидата; update/rollback и Harness открыты.
