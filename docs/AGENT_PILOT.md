# Пилот TESSERA в Codex и DeepSeek Harness

[**Русский — оригинал**](AGENT_PILOT.md) | [English — перевод](AGENT_PILOT.en.md)

**Статус:** базовое явное применение трёх навыков Harness наблюдалось (см. доказательства ниже); Codex, AUTO_USE и обязательное исполнение NOT_VERIFIED. Project Cleanup — новый отдельный пилот. Приоритет владельца 25.11.2026: начать пилот до окончания всей дорожной карты. T03–T05/T13, TD06/TD13–TD15. Пилот не равен независимому выпуску или обязательному исполнению.

## Быстрый старт: не аудит репозитория

Ниже четыре подтверждённых pin; Microversion Release 0.0.7 — кандидат, использовать 0.0.6 до подтверждения точного тега. Отдельная приёмка PC01–PC06.

Проверенный снимок каталога: `v0.0.92`, commit `7ace18df60412f98cc84835a6ad81d4c36414683`, main CI 46019956070 SUCCESS (6/6). Четыре независимых аннотированных pin. GitHub Release не требуется для установки по тегу; отсутствие releases/latest не означает отсутствие навыков.

| Навык | Pin | Commit | Дерево навыка |
| --- | --- | --- | --- |
| microversion-release | `refs/tags/microversion-release/v0.0.6` | `015bed7f9eaf344b59e699a4b607c0e21b86f608` | `12aebcae998b098a1e7d3c5f1fadd8bcd2b096e7` |
| project-audit | `refs/tags/project-audit/v0.0.6` | `0b207f09bb9fca7cf5525d6b35a1919e1d316515` | `50d3f3dee94f1ceff9df343ef34689caf99ca184` |
| repository-workflow | `refs/tags/repository-workflow/v0.0.3` | `85bd362067b5a2c8dc94ab0a550990281b80d1ee` | `747474aff7e872c31285c1053f59eabd652fe9be` |
| project-cleanup | `refs/tags/project-cleanup/v0.0.2` | `7ace18df60412f98cc84835a6ad81d4c36414683` | `cb41049a3ff565ae3f2fb7e5582837cc620c1477` |

1. Сначала проверить только четыре целевые установленные папки в активном профиле и версии. Если они совпадают с проверенными деревьями (с учётом метаданных установки gh), не переустанавливать.
2. Если установка нужна, использовать новый пустой проект и четыре точных pin ниже; при недоступности API допустим проверенный локальный checkout точного тега и штатная установка --from-local в пустой каталог. Локальная копия не является remote pin. Не исследовать всю историю, не использовать latest/main, --all, --unpin или --force для пользовательского профиля.
3. Открыть новый сеанс после установки и отдельно вызвать каждый навык: Codex через $имя (например, $microversion-release), Harness через штатный /name или skill tool. Проверить P01–P05 отдельными короткими запросами. Для P06 новый сеанс без названия; правильный ответ сам по себе не подтверждает загрузку. Отрицательный контроль — нерелевантная задача без ожидаемого вызова.
4. Ограничить сетевые повторы двумя попытками на операцию; при отказе зафиксировать BLOCKED и продолжить независимые локальные read-only проверки. Не изменять разрешения и не чистить производственное окружение. P07/P08 и Stop-hook — отдельные испытания с разрешением, не условие начала P01–P06.

**Отдельная короткая PC01/PC06-проверка:** при необходимости установить только Project Cleanup в новый пустой проект по точному pin: `gh skill install Sashido01/TESSERA skills/project-cleanup --pin refs/tags/project-cleanup/v0.0.2 --dir <empty-project>/.agents/skills` (для Harness при необходимости `.dsh/skills`). Затем явно вызвать `$project-cleanup`/`/project-cleanup` на синтетической fixture с build/cache, данными и ссылкой; выполнить только metadata inventory и проверить scope/сумму/отсутствие удаления. Без аудита всего репозитория, массовых обновлений и реальной очистки. Отдельный fresh implicit trial; верный ответ не доказывает вызов.

## Входные условия

- Только новый одноразовый локальный проект, без remote, рабочих данных, секретов, глобальных hooks и изменения настоящих проектов. Не выдавать агенту дополнительные полномочия. Не запускать сканеры безопасности в клиентском профиле.
- Использовать только текущую таблицу pin выше; прежние снимки ниже — исторические доказательства, не инструкция установки.
- gh 2.105.0: владелец подтвердил remote multi-skill install и явную загрузку в Harness; предупреждение записи metadata требует отдельной проверки. Не применять --force, --all, unpinned update или сторонние менеджеры.
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
foreach ($skill in @('microversion-release','project-audit','repository-workflow','project-cleanup')) {
    if (Test-Path -LiteralPath (Join-Path $dest $skill)) { throw 'Skill already exists' }
    $pin = switch ($skill) {
        'microversion-release' { 'refs/tags/microversion-release/v0.0.6' }
        'project-audit' { 'refs/tags/project-audit/v0.0.6' }
        'repository-workflow' { 'refs/tags/repository-workflow/v0.0.3' }
        'project-cleanup' { 'refs/tags/project-cleanup/v0.0.2' }
    }
    gh skill install Sashido01/TESSERA "skills/$skill" --pin $pin --dir $dest
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
| P01 | Открыть новый проект, показать список навыков | Все четыре доступны именно из проектного root; зафиксировать путь/версию, не только gh skill list |
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

## Исторические снимки (не текущая приёмка)

Следующие записи отражают прежние состояния и не являются инструкцией для текущего релиза.

## Фактическая частичная приёмка Codex — 25.11.2026

Источник: отчёт владельца о собственном сеансе, не результат CI. Пользовательский профиль, Windows, Python 3.14, официальный gh, три каталога закреплены на `refs/tags/v0.0.74` → `ddab826e5a17641e0f475ecc63193f412065e28e`. Отчёт подтверждает gh skill list, pinned=true и совпадение Git tree; сырые логи и точные версии клиента/модели/gh не получены. GitHub API независимо подтверждает tag и исходные деревья:

| Навык | Дерево | Тесты / результат владельца |
| --- | --- | --- |
| Microversion Release 0.0.2 | `78d4645561a0b294e93b4a85b67e7cf51a339fd3` | 38/38 PASS после локальной очистки унаследованных GIT_CONFIG_* в процессе тестов |
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

### Следующий снимок — 25.11.2026

TD02/T16 BLOCKED ([#83](https://github.com/Sashido01/TESSERA/issues/83)): owner-reported Rule Suites 5360899907, 5359993044, 5359256574, 5359221161, все fail при создании refs/tags/microversion-release/v0.0.1 (before_sha — 40 нулей). Детализация последнего rule suite требует доступа владельца (connector 403). Правила 27932769 не изменены; не повторять push до установления конкретного rule. TD18 #82: Windows CI 45626552407 full catalog 713 = 705 PASS + 1 FAIL + 4 ERROR + 3 SKIP, skill suites 39/39 + 43/44 (FIFO skip) + 13/13. Исправлены четыре Linux secure-open сценария Bandit/Gitleaks и canonical fixture root reference-skills в 45eaeed021eb4fc36c805d2260aa2d0071f1abdd; новый CI 45627814264 ещё не завершён. TD14 #77: в том же catalog_checks 139248180713 PE3/E2 отсутствуют, risk 53 против 72, 9 MEDIUM + 1 LOW, standalone 0 индивидуальных HIGH; интегрированный policy FAIL из-за aggregate >50. Порог не менять, оставшиеся находки разобрать. Ни одно из этих доказательств не заменяет принятие в main, независимые теги и повторную агентную приёмку.

### Подтверждённая причина TD02 и полный Windows PASS — 25.11.2026

Owner-reported rule-suite 5360899907: `workflow_updates` FAIL (GitHub App не имеет разрешения workflows для исторической `.github/workflows/validate.yml`); secret_scanning и ruleset 27932769 update/non_fast_forward/deletion PASS. Не ослаблять ruleset. Разовое восстановление четырёх исторических тегов владельцем через изолированный свежий clone на exact main 115f79daae5886606261cb59c4d5ab2fd045f173, plan-only `tools/publish_skill_tags.py`, проверка 4 исторических пар (catalog v0.0.66/67/69/71) и явная sequential publication. Не хранить credential в CI или коде. Новые теги должны быть аннотированы, отсутствующие refs только создавать, существующие не перемещать; затем сверить remote и повторить упавший main tag job. #83 OPEN до фактического доказательства.

TD18 #82: 45627814264 Windows job 139252599141 exact 45eaeed021eb4fc36c805d2260aa2d0071f1abdd SUCCESS: catalog 715 = 708 PASS + 7 платформенных SKIP; skills 96 = 95 PASS + 1 FIFO SKIP. Linux-only secure-open и Bash проверки не заявлены как Windows runtime. На момент фиксации полный Linux/combined gate ещё не завершён, main остаётся v0.0.75. Новый кандидат 892cdaca33bdeb9c679a674d672c700dbd2e11e6 дополнительно проверяет origin тестовых импортов Project Audit; повторный CI/сканер ещё не подтверждён. Installed v0.0.74 не обновлять до приёмки.

### Исторический статус кандидата — 25.11.2026

Исторический снимок ветки до принятия последовательных независимых тегов: PR #74 exact 892cdaca33bdeb9c679a674d672c700dbd2e11e6, CI 45628965053 SUCCESS всех обязательных групп. Windows catalog 715 = 708 PASS + 7 platform SKIP, skills 98 = 97 PASS + FIFO SKIP; всего 813 = 805 PASS + 8 SKIP. SkillSpector 2.13.7 risk: Microversion Release 30, Project Audit 38 (ранее 72→53; 7 MEDIUM + 1 LOW), Repository Workflow 14. FULL_TIER1 все policy verdict PASS; это advisory review, не certification. TD14/TD16/TD18: PR evidence PASS, принятие main и повторная агентная приёмка открыты на тот момент. TD02 #83: owner сообщил refresh GitHub CLI; публикация независимых тегов на тот момент ещё требовалась, сейчас три refs подтверждены в основном снимке `v0.0.80` выше. TD13 #76: 9db01ec3170a5a3c684fc82eb9d5bd54cd2c337a, отдельная ветка skillspector-provenance-preflight, static wheel verifier 9/9 synthetic Linux PASS; реальные release wheel bytes и подключение preinstall gate NOT_VERIFIED.

## Актуальный снимок на момент подготовки PR #88

v0.0.80: все восемь независимых тегов подтверждены; #76/#77/#80/#82/#83 закрыты. Установка точных новых pin, обнаружение, явный вызов, AUTO_USE, ENFORCEMENT, UPDATE, ROLLBACK в реальных клиентах требуют новой приёмки. #81 остаётся открытой; послепроверка 0.0.80 владельцем отклонена GIT_CONTEXT_UNSAFE. Не очищать производственный контекст молча и не переносить доказательства старого профиля на новый pin.

26.11.2026: pin Microversion Release обновлён до принятого 0.0.3; в P03 допустима диагностика `python scripts/release_tag.py context` из установленного навыка (только имена, без Git). Это не разрешение на Git. #81 открыта. Для парной оценки фиксировать одинаковые fixture, модель, разрешения, инструменты, бюджет и свежую сессию; отдельно измерять PASS критериев, вызов навыка, ложную активацию, нарушения и затраты. Сравнение с контролем без навыка обязательно; статистическая значимость не заявляется по одному прогону.

## Фактическая предрелизная проверка владельцем — 26.11.2026

Источник: предоставленный владельцем отчёт Codex (OWNER_REPORTED, не независимо воспроизведённый удалённым CI). v0.0.84, main df8116f35fdfe2ccb7ee4a4316053455c407d3e9, чистый checkout, 94/94 tag refs совпали, 6 чистых worktrees. Git 2.52.0.windows.1, Python 3.14.3, gh 2.105.0, Codex CLI 0.166.0, Desktop runtime 26.1123.915.0. Harness CLI/установка не обнаружены — NOT_VERIFIED, не доказательство отсутствия. В обоих отдельных тестовых каталогах gh skill install/list подтвердил 3/3 точных pin (Microversion Release 0.0.3, Project Audit 0.0.5, Repository Workflow 0.0.2); G03 частично принят для размещения и pin, активация/обновление/rollback не приняты. GUI Codex не управлялся из-за недоступной геометрии, prompts не отправлялись. Unit suites с наследуемым контекстом: Microversion 42 (20 PASS, 3 FAIL, 19 ERROR); Audit 75 (61 PASS, 13 ERROR, 1 SKIP); Workflow 17/17 PASS. Причины отдельных ошибок NOT_DIAGNOSED; не переносить PASS чистого CI на клиент. next_version CLI .99→.100 и .99→0.1.0 PASS; release_tag context exit 1 GIT_CONTEXT_UNSAFE / Git NOT_EXECUTED. P02–P08, E/RW клиентские сценарии не приняты, #81 OPEN. Повторить сначала точечную диагностику ошибок и доступность доверенного запуска, затем полные клиентские испытания после опубликованных pin. Не удалять наследуемые настройки и не расширять права. Ветки с уникальными коммитами и занятые worktrees сохранять; удаление не подтверждено. Не публиковать локальные пути.

## Подготовка закреплённого Harness 0.2.2-rc.5

Владелец сообщил npm 12.0.2, Node 24.18.0, npm view @deepseek-ai/dsh 0.2.2-rc.5 engines >=24.9.0 — совместимость по заявленному manifest PASS, запуск NOT_VERIFIED. В отдельной доверенной одноразовой среде сначала проверить npm metadata конкретной версии, dist.integrity и peerDependencies hooks-codex той же версии. Не устанавливать глобально и не запускать latest/alpha автоматически. [Исходники rc.5](https://github.com/deepseek-ai/deepseek-harness/tree/dsh-v0.2.2-rc.5), [safety](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.5/SAFETY.md), [headless](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.5/packages/bundle/headless/README.md). Профиль headless не использует сохранённый GUI login; подключение модели отдельно согласовать, не передавать секреты в prompt/argv или публичный отчёт. При пилоте записать exact host/bridge pin, runtime, наблюдаемый hook/invoked и hook/result, exit и final.reason.kind, отдельную проверку Git/test. Не считать tool_result completed доказательством выполнения shell. Guarded Run 0.0.5 candidate требует --expected-version. Не использовать пока не принят независимый тег. Не изменять реальные проекты и существующие профили.

## Подтверждение CLI и npm metadata — 26.11.2026

OWNER_REPORTED: npm 12.0.2 / Node 24.18.0, @deepseek-ai/dsh@0.2.2-rc.5 dist.integrity sha512-cNbp12tLYLUTXaVli7zwwMjzmmEVCD1PRldg4oKtXM4+lFYckcaliMS2PU/FoThB4iAN/fKOSID0nrtRZU4Gjw==; hooks-codex@0.2.2-rc.5 sha512-S8xLbJfTESwXVXTTh+Bav+FgU0MWU1rlBcGfKD6zLGxdYRYO+jo8JaRsH0y8JkEKYCkALr0rzX52yCYC9R3khA==; peer dsh-llm/agent/tools/session/hook-protocol/working-directory все rc.5, cordis ~4.1.0. npm exec exact rc.5 показал help — CLI_LAUNCH_PASS (не независимая проверка tarball или транзитивного lock), warning deprecated node-domexception 1.0.0. Следующий шаг отдельный тестовый профиль/машина, headless help, проверка model route и минимальная безопасная задача; установка bridge и реальная загрузка skill ещё NOT_VERIFIED. Не менять настоящие профили, не запускать из рабочего репозитория, не публиковать credentials или полные config dumps. Для актуального теста после main CI выбрать точные опубликованные независимые теги .5/.6/.2, сверить targets; .4 уже опубликован, но exact target Guarded Run в .5.

## Headless help подтверждён владельцем

26.11.2026: точный npm pin 0.2.2-rc.5 вывел справку dsh --profile headless --help. PROFILE_HELP_PASS; это не сессия модели. Следующий ограниченный пилот: новый одноразовый проект и отдельные DSH_HOME и DSH_AGENTS_HOME (оба нужны, см. [home-paths rc.5](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.5/packages/util/home-paths/README.md)); без глобальных навыков, дополнительных writable roots и full access. По [skill-filesystem rc.5](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.5/packages/skill/skill-filesystem/README.md) проектный .dsh/skills приоритет 100, shared .agents/skills приоритет 200. Использовать текущие опубликованные pins .5/.6/.2, после обновления повторить затронутые сценарии. Первый запуск модели — только P01/P02 discovery/explicit read-only calculation; не менять репозиторий. Проверить реальные NDJSON session, tool_call/tool_result загрузки навыка и CLI, final.reason.kind=completed, exit 0. Сырые события могут содержать prompts, tool args и приватные данные; сообщать только санитизированные факты. Отсутствие разрешённого model route или отказ песочницы — BLOCKED; не выдавать новые права. Не устанавливать bridge до подтверждения чистого запуска.

## Приёмка владельца 27.11.2026 — v0.0.88

OWNER_REPORTED: Harness 0.2.2-rc.1, 29 PASS / 1 FAIL / 4 NOT_VERIFIED. Все три дерева совпали с таблицей выше; наблюдались явные вызовы трёх навыков, отказ неизвестного имени и реальные headless P02/P04/P05. Предоставленный JSONL независимо подтверждает успешные native skill dispatch для всех трёх, но не все дочерние прогоны. Guarded Run positive и отрицательные fixtures, unit suites 78/78, 76 PASS + 1 FIFO SKIP, 17/17 — OWNER_REPORTED. AUTO_USE, GUI-live, Stop-hook NOT_VERIFIED; gh search недоступен. gh 2.105.0: предупреждение could not record install из-за отсутствующей переменной USERPROFILE (цепочка вызовов подтверждена исходниками; native reproduction открыт), файлы и frontmatter проверены владельцем. Не рекомендовать широкое --unpin --all; отдельный staging pin/rollback и проверка сохранности соседних навыков обязательны. Codex: сетевой timeout, установка/активация NOT_VERIFIED, #81 OPEN. Повторить узкие проверки локально; при unsafe Git контексте отказ обязателен, без удаления ограничений.

### Адресная установка и предупреждение Windows metadata

В точном gh v2.105.0 [install.go](https://github.com/cli/cli/blob/v2.105.0/pkg/cmd/skills/install/install.go) выбирает DiscoverSkillByPath для селектора с префиксом skills/. [discovery.go](https://github.com/cli/cli/blob/v2.105.0/internal/skills/discovery/discovery.go) разрешает одну папку через contents родительского каталога на разрешённом коммите вместо полного discovery репозитория. Исполняемый блок выше использует этот более узкий вариант. Реальная задержка remote install и клиентская приёмка NOT_VERIFIED; не заявлять устранение сетевых таймаутов.

[installer.go](https://github.com/cli/cli/blob/v2.105.0/internal/skills/installer/installer.go) той же версии добавляет warning при отказе RecordInstall после успешной записи файлов; [lockfile.go](https://github.com/cli/cli/blob/v2.105.0/internal/skills/lockfile/lockfile.go) получает путь lock через os.UserHomeDir. На Windows HOME/GH_CONFIG_DIR не устанавливают USERPROFILE. Диагностировать только факт наличия переменной (не значение) в доверенном одноразовом Windows-процессе; отдельно сверять запись lock и байты установки. Не подставлять чужой home, не менять песочницу, не считать lock успешным из-за exit 0. Не объявлять upstream bug без воспроизведения.

## 27.11.2026 — реальный one-link pilot и обязательный UP01

Владелец передал отчёты Codex и Harness, а также JSONL Harness. В обоих пользовательских профилях наблюдалось актуальное содержимое четырёх навыков на снимке каталога v0.0.92 (7ace18df60412f98cc84835a6ad81d4c36414683); GitHub независимо подтверждает деревья Microversion 0.0.6 12aebcae998b098a1e7d3c5f1fadd8bcd2b096e7, Audit 0.0.6 50d3f3dee94f1ceff9df343ef34689caf99ca184, Cleanup 0.0.2 cb41049a3ff565ae3f2fb7e5582837cc620c1477, Workflow 0.0.3 747474aff7e872c31285c1053f59eabd652fe9be. Установочные bytes/backup из отчёта владельца, не независимый доступ к профилю. Codex использовал адресный --unpin --all, а часть установок по main; сохранность локальных правок не доказана. Не считать gh metadata или up-to-date достаточным; реальный автоматический вызов Codex NOT_VERIFIED. Harness rc.1: журнал 687 records, 1 completed turn seq 11–685, 1661.002 s (27m41s), 41 steps, 43 top-level tool calls, 113 nested dispatches, 85 pwsh, 16 model retries (14 TIMEOUT, 2 TRANSPORT). Нативные skill loads seq 567/569/571/572 успешны, включая Cleanup; catalog suite 754=747 PASS+7 SKIP; per-skill tests и фактические bytes в отчёте. Режим session до turn изменён workspace-write→danger-full-access, поэтому least-privilege NOT_VERIFIED; не рекомендовать это как способ обновления. Один пользовательский scope может быть общим для двух клиентов; независимость двух установок NOT_VERIFIED. Данные raw session/локальные пути не публикуются.

UP01 — обязательный отдельный acceptance 0.1.0: из одного короткого запроса со ссылкой, без истории/полного unit suite, свежие клиенты с естественно разрешённым контекстом, точные pins, no-op повтор, отсутствующий навык, старый pin, локальная правка, одноимённый сторонний навык, отказ сети/permissions и восстановление. Цель: минимальный запрос и короткий отчёт, измерять elapsed, API calls, tool calls, retries, actual discovery, bytes и сохранность, не выдумывать фиксированный SLA. Предлагаемый CATALOG.json + UPDATE.md + read-only catalog_index.py: exact source 6531e6790398b8dbb7554206f98f08b0754b5f61, tests fcb5def96289ebfd2f45fefd7c20d2d7f7e87323, index 258e8b62e57628e20c239dfc7685907f49e46377. 10/10 isolated Linux tests PASS (0.006 s, mocked API и временный минимальный source tree); все три blob SHA совпали, отдельная сверка всех четырёх VERSION remote source PASS. Это не live API acceptance, не production updater. После публикации тега проверить реальный resolver через официальный gh и exact skill trees, затем staged per-skill updater и recovery в disposable native Windows/Linux, не использовать CI swap на рабочем профиле. G03/G04/G05 остаются PARTIAL; G06–G09, PC03–PC06, G10/G12 открыты.
