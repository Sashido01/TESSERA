# TESSERA 0.1.0 — критерии готовности первого продуктового выпуска

[**Русский — оригинал**](RELEASE_0_1_0.md) | [English — перевод](RELEASE_0_1_0.en.md)

Статус: утверждённый план подготовки (не релиз 0.1.0). 26.11.2026 владелец согласовал законченные базовые версии трёх навыков, обязательное исполнение в Codex/Harness, GitHub Immutable Release с аттестованным ZIP. Baseline v0.0.84: commit df8116f35fdfe2ccb7ee4a4316053455c407d3e9, main CI 45834594641 SUCCESS 6/6, точный аннотированный объект тега 7a1d8d334612fe6c8b60c63ecb4b73a75a763c08. Не назначать фиктивные микроверсии.

## Продуктовая граница

Три самостоятельных навыка Microversion Release, Project Audit и Repository Workflow. RU-first + EN, офлайн-помощники, проверяемые исходники и официальное распространение по точным тегам. Полноценный локальный Git без GitHub. Codex и DeepSeek Harness — целевая практическая приёмка. Не объявлять совместимость с Claude Code/Hermes без отдельного фактического испытания; не добавлять платные API, сторонние менеджеры и обязательный сервис. Расширенные графы, автоматический DELTA reuse, семантический уровень V, дополнительные платформы и оптимизации не входят в минимальную готовность этих трёх навыков без отдельного согласования владельца. Не считать незавершённую обязательную защиту будущей функцией.

## Release gates

| ID | Обязательный результат | Доказательство / состояние |
|---|---|---|
| G01 | Последовательный VERSION, changelog RU/EN, точные аннотированные теги | 0.0.86 подтверждён, 0.0.87 main CI и тег ожидают сверки; 0.1.0 NOT_VERIFIED |
| G02 | Все 6 main jobs на точном commit и attempt, полный каталог, native Windows/Linux | кандидат фиксированного CI profile; новый CI требуется |
| G03 | Безопасная установка каждого из трёх навыков по отдельному pin в чистый каталог, отказ дубликата | исторический single pin и локальный multi-skill PASS; актуальный remote multi-skill открыт |
| G04 | Безопасное обновление/откат отдельного навыка, сохранность остальных и локальных изменений | исторические fixture PASS; текущие три независимые refs и реальный профиль открыты |
| G05 | Codex и Harness: обнаружение, явное и автоматическое применение каждого навыка, P01–P08 + релевантные E/RW | текущий клиентский пилот NOT_VERIFIED; #81 открыта |
| G06 | Microversion Release: положительный и отрицательный release fixture, точный тег, отсутствие ложного COMPLETE при ошибке hook/CI | детерминированные тесты PASS; реальный least-privilege invocation и enforcement открыты |
| G07 | Project Audit: границы выбранного проекта, противоречивые evidence, неполная область, честный отчёт | исходники/тесты приняты; реальные E01–E20 открыты |
| G08 | Repository Workflow: LOCAL/GitHub, конфликтующие scopes, независимые задачи, безопасная гигиена, восстановление | planner принят; worktree candidate и реальные RW01–RW20 открыты |
| G09 | Безопасность: нет нерешённого блокирующего риска для заявленных операций; required checks неизменны; известные ограничения и неприменимость обоснованы | T12 PARTIAL; advisory/TOCTOU/ресурсные риски проверять по области, не обещать песочницу |
| G10 | Отдельный воспроизводимый ZIP из точного v0.1.0, SHA-256, manifest, проверенная Sigstore/SLSA attestation | v0.0.21 исторический PASS; v0.1.0 NOT_RUN |
| G11 | Закрытие #81 и подтверждение #78 по критериям, отсутствие незавершённых PR и CI для релиза; сохранённые/неиспользуемые ветки убраны после проверки | OPEN; локальные worktrees требуют владельца |
| G12 | Независимое свидетельство, инструкции, поддержанные/непроверенные среды; GitHub Immutable Release с проверенным ZIP | настройка ENABLED (owner PUT204/GET true); публикация и проверка NOT_RUN |

Все обязательные критерии для заявленного объёма должны быть доказаны. Любой NOT_VERIFIED в обязательной области блокирует заявление о готовности. Владелец может явно изменить продуктовую границу, но не присвоить PASS неисполненному критерию. Статусы не вычисляются как процент по количеству пунктов. Исторические результаты не переносятся на изменившиеся файлы, дерево навыка, окружение или политику.

## Последовательность

1. Принимать только реальные изменения; версия следующего компонента назначается при свободном интеграционном слоте. Политика [VERSIONING](VERSIONING.md) разрешает переход 0.0.99 → 0.1.0 при фактической готовности; незаконченная работа может продолжаться 0.0.100+. Не создавать пустых коммитов для заполнения номеров и не менять правила ради дедлайна.
2. Сначала исправить release-critical CI profile, TD04 и RW05, синхронизировать приёмку #78. Не ускорять за счёт исключения сканов. Далее реальный multi-skill pin/update/rollback, независимая проверка, минимальные адаптеры с позитивными/негативными испытаниями. Параллельно провести пилот.
3. Перед назначением 0.1.0 — согласовать точный scope, остановить необязательные изменения, завершить предрелизную приёмку с exact SHA. После merge сверить main CI, annotated tags и exact trees; любой сбой оставляет статус BLOCKED.
4. Запустить `build-attested-catalog.yml` **на v0.1.0**, не main. Скачать артефакт, проверить точные байты, воспроизводимость, signer workflow, source-ref и source digest официальным gh. Проверить report/certificate, которые не являются самостоятельной подписью. См. [Trusted Build](TRUSTED_BUILD.md).
5. Владелец утвердил GitHub Immutable Release с аттестованным ZIP: использовать уже существующий тег, подготовить черновик с проверенным ZIP и release notes RU/EN, проверить всё до публикации. Не создавать/перемещать тег повторно. Immutable Releases защищают assets и тег после публикации; это дополнение к Rulesets и проверке provenance, не замена. После публикации сверить метаданные и фактические байты. [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases), [verify release integrity](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/verify-release-integrity).

## Действия владельца (необходимые параллельные проверки)

- Из обычного доверенного терминала Windows, не sandbox агента: проверить чистоту выбранного checkout, текущий branch, worktrees, версии Git/Python/gh; синхронизировать только fast-forward после проверки. Не удалять переменные GIT_* и не ослаблять разрешения. Сверить 0.0.82 / 0.0.83 после подтверждения точного тега.
- Новый изолированный проект для каждого клиента; [AGENT_PILOT](AGENT_PILOT.md) с подтверждёнными pin. Записать фактические client versions, INSTALL, DISCOVERY, EXPLICIT_USE, AUTO_USE, ENFORCEMENT, UPDATE/ROLLBACK и exit codes. Проверка `python scripts/release_tag.py context` из установленного Microversion Release не запускает Git; при unsafe контексте остановить Git-операцию, вернуть только имена и status. Реальные release fixtures только по разрешению и без remote; не переносить рабочие данные.
- Проверить старые ветки после сверки сохранности: не удалять, если заняты worktree или есть уникальные изменения. Сначала project-audit-evidence-core (4/4 changed files совпали с main v0.0.82), затем repository-workflow-planner-hardening и agent-pilot-readiness после отдельной смысловой сверки. Не публиковать пути/причины lock. Удаление — только после повторного сравнения актуального SHA и разрешения.
- Включить Immutable Releases в Settings (решение владельца принято; состояние NOT_VERIFIED) и до публикации первого GitHub Release; выровнять allowed_merge_methods Ruleset до squash only, не менять required checks или tag protections. Не включать Restrict creations. При релизном теге запустить workflow_dispatch и независимую verification; действующий коннектор не предоставляет dispatch/delete ref/release publication. Это ручные действия, не текущий PASS.

## Новая исследовательская гипотеза

Harness capability seams разделяют skill provider, model invocation и shell/permission; явная загрузка skill может отличаться от автоматического вызова. Не судить по одному тексту ответа. Применить наблюдаемый критерий из [Harness skills subsystem](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md), [capability seams](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/capability-seams.md) и [OpenAI skill evals](https://developers.openai.com/blog/eval-skills): свежие изолированные сессии, явные/неявные триггеры, одинаковая задача без навыка, отрицательные проверки, минимальные разрешения. Не считать просмотр upstream доказательством интеграции TESSERA.

Сверка 26.11.2026: #78 CLOSED (completed) владельцем, последующий main CI и оба тега v0.0.83 подтверждены; #81 OPEN. Не переоткрывать без нового доказанного остатка.

## Утверждённая архитектура исполнения и публикации

T13/G06: независимый [Completion Gate и Guarded Run](../skills/microversion-release/references/ENFORCEMENT.md) кандидат 0.0.4. Локальные 26/26 PASS, native/client NOT_VERIFIED. В каждом клиенте подтвердить вызов Stop и реальный внешний контроль (позитив/негатив), не принимать один текст агента и не изменять разрешения. Harness bridge частично fail-open и не обеспечивает veto. Внешний controller не заменяет фактическую активацию; GUI не принимается автоматически. G02: фиксированный профиль CI принят в v0.0.84. G12: Immutable Release теперь обязательный, см. [публикация](IMMUTABLE_RELEASE.md). Ruleset Protect main уже проверен: allowed_merge_methods=[squash]. Иммутабельность ещё не подтверждена, #81 OPEN. TD04/RW05 ожидают интеграции.

## Фактическая предрелизная проверка владельцем — 26.11.2026

Источник: предоставленный владельцем отчёт Codex (OWNER_REPORTED, не независимо воспроизведённый удалённым CI). v0.0.84, main df8116f35fdfe2ccb7ee4a4316053455c407d3e9, чистый checkout, 94/94 tag refs совпали, 6 чистых worktrees. Git 2.52.0.windows.1, Python 3.14.3, gh 2.105.0, Codex CLI 0.166.0, Desktop runtime 26.1123.915.0. Harness CLI/установка не обнаружены — NOT_VERIFIED, не доказательство отсутствия. В обоих отдельных тестовых каталогах gh skill install/list подтвердил 3/3 точных pin (Microversion Release 0.0.3, Project Audit 0.0.5, Repository Workflow 0.0.2); G03 частично принят для размещения и pin, активация/обновление/rollback не приняты. GUI Codex не управлялся из-за недоступной геометрии, prompts не отправлялись. Unit suites с наследуемым контекстом: Microversion 42 (20 PASS, 3 FAIL, 19 ERROR); Audit 75 (61 PASS, 13 ERROR, 1 SKIP); Workflow 17/17 PASS. Причины отдельных ошибок NOT_DIAGNOSED; не переносить PASS чистого CI на клиент. next_version CLI .99→.100 и .99→0.1.0 PASS; release_tag context exit 1 GIT_CONTEXT_UNSAFE / Git NOT_EXECUTED. P02–P08, E/RW клиентские сценарии не приняты, #81 OPEN. Повторить сначала точечную диагностику ошибок и доступность доверенного запуска, затем полные клиентские испытания после опубликованных pin. Не удалять наследуемые настройки и не расширять права. Ветки с уникальными коммитами и занятые worktrees сохранять; удаление не подтверждено. Не публиковать локальные пути.

## Сверка 26.11.2026 — #92 принят, следующая защита кандидата

PR #92, exact head 5e770ebf66af9d2758b9df026229794e2932c15b, run 45852127083: все пять обязательных PR jobs PASS. Squash commit feaa3d211221ef0301edf45571f312d2637b0341; main run 45859420735 ещё требует проверки и двух точных annotated tags. SkillSpector 26/26 полных файлов Microversion Release, 100%; integrated Tier 1 execution PASS, policy verdict Microversion FAIL (11 HIGH, 24 MEDIUM, 0 CRITICAL), Audit FAIL (1 HIGH — aggregate risk gate, direct 55, 0 HIGH прямых), Workflow PASS (0 HIGH, direct risk 30). G09 OPEN: не считать execution PASS устранением находок, не подавлять findings. Владелец сообщил Node 24.18.0 / npm 12.0.2; npm manifest @deepseek-ai/dsh 0.2.2-rc.5 требует Node >=24.9.0. Harness фактически ещё не запущен. GET immutable-releases вернул enabled:false, enforced_by_owner:false — G12 BLOCKED до enable и повторной проверки. G06: кандидат Microversion 0.0.5 требует точный --expected-version; 4 новых тестовых метода. G07: Audit 0.0.6 защищает mutating fixture setup, аналогично Microversion; 2 regression methods в сумме. Новые изолированные fixtures передают только явный allowlist. Все новые тесты требуют CI, реальная приёмка #81 открыта. TD04/RW05 остаются отдельными кандидатами; не удалять occupied branches/worktrees.

## Сверка после #93

0.0.85 main CI 45859420735 SUCCESS 6/6; exact commit feaa3d211221ef0301edf45571f312d2637b0341, tag objects dc893d0ac9fc5291d53023f0dd5967a8e17d1222 (catalog) и 4cab74df967d2a6f8abd98737b67da84dd30fd4e (microversion-release/v0.0.4), оба direct target. #93 run 45860767387 SUCCESS 5/5, squash 0b207f09bb9fca7cf5525d6b35a1919e1d316515. G09 остаётся OPEN: direct coverage 100% всех трёх; Microversion 9 HIGH (было 11), Audit 1 direct HIGH (был aggregate gate), Workflow 0. Не менять severity или исключения. G12 owner setting ENABLED, publication NOT_RUN. Harness rc.5 запустил CLI help (owner-reported), реальная сессия и hook NOT_VERIFIED. TD04 интеграционный кандидат 0.0.87; Gitleaks live parity ещё требуется. #81 OPEN.

## Сверка после #94

0.0.86 main CI 45864624507 SUCCESS 6/6, commit 0b207f09bb9fca7cf5525d6b35a1919e1d316515; exact tag objects c270a15e48552fbb7dbed47f46126c33c30a6aef (v0.0.86), 853133f0dd4b54ef72e6dda0cccce9b956bdb58a (microversion-release/v0.0.5), f1ab06d7abf4f1a1147df4217708fde079ec9953 (project-audit/v0.0.6). #94 run 45865200170 SUCCESS 5/5, squash 75f27ca40d90aa46c387c5c81d38f3ff064200c2. TD04 host/container parity PASS (1551/1551 distinct blobs, 24116257 bytes, 0 findings; container 323.1s), main 0.0.87 ещё требует приёмки. Не переносить локальный benchmark read-only на весь CI. Владелец подтвердил exact rc.5 headless help: --json, session-id, permission-mode, approval-policy ask/never, add-dir. PROFILE_HELP_PASS, модель, фактическое исполнение, hook и #81 остаются NOT_VERIFIED/OPEN. G09: следующий кандидат экспортирует ограниченные координаты сообщённых HIGH/CRITICAL occurrences, без verdict changes. Microversion Release 0.0.6 требует впервые добавленную запись changelog, не просто присутствие heading. RW05 и реальная клиентская приёмка открыты.

## 27.11.2026 — v0.0.88 подтверждён, пилот владельца

Main CI 45874463052 SUCCESS 6/6; тег каталога 3be87bc90d9745aa2b074c9022cd4656e241010d и microversion-release/v0.0.6 49eb12134036b1c33e3e3a9198eea76cfde6d057 указывают на 015bed7f9eaf344b59e699a4b607c0e21b86f608. Все три независимых дерева совпадают с v0.0.88. G03/G04/G05/G06–G08 PARTIAL: положительные испытания Harness rc.1 владельца и наблюдаемая нативная загрузка (см. пилот); автоматический выбор, Stop-hook, полные E/RW матрицы и Codex открыты. Предупреждение записи metadata gh требует воспроизведения, не обхода. G09: 7+1 direct HIGH occurrences, нет CRITICAL finding; Tier 1 policy FAIL для двух навыков, не подавлять. G11 #81 OPEN. G10/G12 публикация NOT_RUN. Готовность v0.1.0 не заявлена.

## 27.11.2026 — владелец утвердил четвёртый навык

Project Cleanup 0.0.1 candidate — самостоятельный компонент гигиены хранения. Прежняя утверждённая матрица трёх навыков G01–G12 применима только к ним и не доказывает приёмку Project Cleanup. До выпуска каталога с ним подтвердить PC01–PC06 в заявленных границах, native Windows/Linux, точный pin дерева, отсутствие небезопасной очистки и явное клиентское применение. Не реализованную автоматизацию явно маркировать. Не ослаблять прежние три группы клиентской приёмки и не заявлять готовность четырёх навыков по этому кандидату. Начальный помощник не выполняет destructive operations.

## Актуальный контроль готовности 0.1.0 — 27.11.2026

Последний полностью принятый инженерный выпуск v0.0.91, main 85bd362067b5a2c8dc94ab0a550990281b80d1ee, CI 46006227100 6/6 PASS; annotated catalog tag be2a4605bee0772454c4690c9b3dcfe51e39b323 и repository-workflow/v0.0.3 ce833071628b1bc60d70b9806de9651d9dc6d4e5 → exact main. Четыре навыка: Microversion 0.0.6, Audit 0.0.6, Workflow 0.0.3, Cleanup 0.0.1. PC02 кандидат 0.0.2 (28/28 isolated Linux PASS). Оригинальная матрица выше — исторические критерии, не текущие статусы. Для продуктового релиза с четырьмя навыками добавляется PC01–PC06 без ослабления G01–G12.

| Группа | Текущая оценка | Условие закрытия |
| --- | --- | --- |
| G01/G02 | PASS для v0.0.91, 0.1.0 NOT_RUN | exact candidate/main/tags, полный CI |
| G03/G04 | PARTIAL | адресный pin/update/rollback в двух клиентах, сохранность локальных правок/остальных навыков, gh metadata warning |
| G05/G06 | BLOCKED по клиентским доказательствам | fresh Codex explicit/implicit, реальный разрешённый Git fixture без очистки GIT_*, Harness AUTO_USE и Stop/guard, owner-approved isolated hook only |
| G07/G08 | PARTIAL | реальные client E/RW scenarios, независимые задачи, actual occupancy, recovery |
| G09 | OPEN | 18 direct HIGH (7 Microversion + 1 Audit + 1 Workflow + 9 Cleanup), 0 CRITICAL occurrences в v0.0.91; raw policy FAIL всех четырёх, независимая оценка каждой причины, не подавлять |
| G10/G12 | NOT_RUN | на точном v0.1.0: dispatch, attested ZIP, independent gh verify, draft→immutable publication; owner setting ENABLED reported, повторно сверить перед выпуском |
| G11 | OPEN | #81, три старые ветки: сохранность/реальная occupancy, без destructive shortcuts |
| PC01–PC06 | PARTIAL | PC01 native CI, PC02 advisory 28/28 Linux pending native CI; PC03 execution/recovery, PC04 counters, PC05 budgets, PC06 client NOT_VERIFIED |

Не присваивать 0.1.0 до выполнения условий готовности. Не считать 0.0.99 дедлайном. Приоритет: PC02 native CI, проверяемое выполнение PC03 (только явно разрешённые disposable fixtures), G09 dispositions, точечная клиентская приёмка, Git/GitHub storage и профилактика, независимый release preflight. Проверка истории приближается к лимиту: PR #98 1642/2048 distinct blobs (406 reserve), контейнер 274.9 s, parity PASS, zero findings in scope. Изменять лимиты только после measured capacity и regression, не сокращать покрытие. Параллельная работа допустима, общая версия резервируется последовательно.

## 27.11.2026 — актуальная сверка 0.0.92 / TD17

Main 0.0.92 7ace18df60412f98cc84835a6ad81d4c36414683, CI 46019956070 6/6 PASS; annotated catalog tag 4545d85dfc5e9336423f72c3729eb748603d6d14 и project-cleanup/v0.0.2 96626f96dd73d40e72f813502e5412b0ad6ebfd2 → exact main. PC02 native CI Linux 49/49 PASS всего навыка, Windows 47 PASS + 2 FIFO SKIP, actual sparse/staged fixtures PASS; execution/recovery/client NOT_VERIFIED. G09: 20 HIGH (7+1+1+11), 0 CRITICAL occurrences, raw policies FAIL; новые Cleanup AR3 в отрицательной фразе и E2 в name-only fixture guard, exact underlying YR4 unresolved. TD17 кандидат 0.0.7: 4 focused isolated Linux probes PASS на exact release_tag.py, три новых regression methods, полный CI и Codex не приняты. #81 OPEN. Устранено расхождение pin-таблицы и PowerShell примера; guard проверяет четыре RU/EN mapping. История main 1651/2048 distinct blobs, 26511012 bytes, container parity PASS 457.05 s, 0 findings; отдельный TD04 batch кандидат 09c47faefc643f9deb1b2cb4b0d618f404376f13. 0.1.0 BLOCKED до реальных G01–G12 + PC01–PC06. Старые ветки и реальные worktrees не удалять без доказательств.

## 27.11.2026 — реальный one-link pilot и обязательный UP01

Владелец передал отчёты Codex и Harness, а также JSONL Harness. В обоих пользовательских профилях наблюдалось актуальное содержимое четырёх навыков на снимке каталога v0.0.92 (7ace18df60412f98cc84835a6ad81d4c36414683); GitHub независимо подтверждает деревья Microversion 0.0.6 12aebcae998b098a1e7d3c5f1fadd8bcd2b096e7, Audit 0.0.6 50d3f3dee94f1ceff9df343ef34689caf99ca184, Cleanup 0.0.2 cb41049a3ff565ae3f2fb7e5582837cc620c1477, Workflow 0.0.3 747474aff7e872c31285c1053f59eabd652fe9be. Установочные bytes/backup из отчёта владельца, не независимый доступ к профилю. Codex использовал адресный --unpin --all, а часть установок по main; сохранность локальных правок не доказана. Не считать gh metadata или up-to-date достаточным; реальный автоматический вызов Codex NOT_VERIFIED. Harness rc.1: журнал 687 records, 1 completed turn seq 11–685, 1661.002 s (27m41s), 41 steps, 43 top-level tool calls, 113 nested dispatches, 85 pwsh, 16 model retries (14 TIMEOUT, 2 TRANSPORT). Нативные skill loads seq 567/569/571/572 успешны, включая Cleanup; catalog suite 754=747 PASS+7 SKIP; per-skill tests и фактические bytes в отчёте. Режим session до turn изменён workspace-write→danger-full-access, поэтому least-privilege NOT_VERIFIED; не рекомендовать это как способ обновления. Один пользовательский scope может быть общим для двух клиентов; независимость двух установок NOT_VERIFIED. Данные raw session/локальные пути не публикуются.

UP01 — обязательный отдельный acceptance 0.1.0: из одного короткого запроса со ссылкой, без истории/полного unit suite, свежие клиенты с естественно разрешённым контекстом, точные pins, no-op повтор, отсутствующий навык, старый pin, локальная правка, одноимённый сторонний навык, отказ сети/permissions и восстановление. Цель: минимальный запрос и короткий отчёт, измерять elapsed, API calls, tool calls, retries, actual discovery, bytes и сохранность, не выдумывать фиксированный SLA. Предлагаемый CATALOG.json + UPDATE.md + read-only catalog_index.py: exact source 6531e6790398b8dbb7554206f98f08b0754b5f61, tests fcb5def96289ebfd2f45fefd7c20d2d7f7e87323, index 258e8b62e57628e20c239dfc7685907f49e46377. 10/10 isolated Linux tests PASS (0.006 s, mocked API и временный минимальный source tree); все три blob SHA совпали, отдельная сверка всех четырёх VERSION remote source PASS. Это не live API acceptance, не production updater. После публикации тега проверить реальный resolver через официальный gh и exact skill trees, затем staged per-skill updater и recovery в disposable native Windows/Linux, не использовать CI swap на рабочем профиле. G03/G04/G05 остаются PARTIAL; G06–G09, PC03–PC06, G10/G12 открыты.

## 27.11.2026 — UP01: адресные и массовые операции

Владелец явно потребовал установку/обновление одного, нескольких и всех навыков. Четыре режима: install + --skill, update + --skill (повторяемый), install + --all, update + --all. Install не заменяет существующее отличающееся дерево; update добавляет отсутствующие только в выбранном наборе, пропускает идентичные, заменяет устаревшие только после доказанной сохранности, downgrade отдельно согласуется. Невыбранные навыки не читаются резолвером (кроме общей схемы каталога), не изменяются и не удаляются. Unknown/duplicate/mixed/empty selection BLOCKED, отсутствие каталога без fallback. 15/15 exact Linux isolated mocked API tests 0.009 s; source blob 5d394edb79bc7fee76502cadfc93cd123e752068, tests 8c821cbb1fdf5250ed72787b91a1ddada9aaf47b. Native/live API, полный профильный updater, no-op/rollback с реальными клиентами и включение CATALOG/UPDATE/resolver в аттестованный ZIP открыты. UP01 не принят. 0.0.93 main exact SHA 168ccae683e92ed13fba141c6654201765cb2e3a, CI 46033970329 6/6 PASS, tags 43632297d99f515ade8251868a5255561b5d1db1 / b2659b8a68433eaa56d0edaaeda1de3d0faf72a5. Microversion 0.0.7 Windows 81/81, root Windows 749 PASS+7 SKIP; G09 20 HIGH/0 CRITICAL occurrences, raw FAIL всех четырёх, без подавлений. Main history 1629/2048 distinct blobs, 25838171 bytes, 434.49 s container parity PASS, zero findings in scope. TD04 отдельный кандидат остаётся; #81 OPEN. 0.1.0 BLOCKED до G01–G12, PC01–PC06 и UP01.

## 27.11.2026 — восстановление release gate после 0.0.94

PR #101 exact 23311503daf73bdee2430a14127a0167bcb60171 CI 46038347655 5/5 PASS; squash 346a28001263dffe09920f96821a2170de68a4be. Main CI 46042052275 Windows job 140651970098 FAIL: Project Cleanup test_git_marker_changed_during_plan, 49 executions = 46 PASS + 1 FAIL + 2 FIFO SKIP. 0.0.94 не принята; не создавать запоздалый тег. Стабильный подтверждённый baseline v0.0.93. UP01 код в main, но latest tagged index ещё отсутствует. Кандидат 0.0.95 / Cleanup 0.0.3: реальная подмена marker без clock assumption, отдельная инъекция mtime, исчезновение marker, zero inode/hardlink refusal, повторная ordinary root проверка. Никакого исключения Windows-теста или удаления проверок. TD04 пакетное чтение с exact source 4cfe6f756f79daa90082f288d63a3cfca1c36cde и tests 760ae6ce2b4eea1824964f23cec5c2923e1e81e5; прежние caps, digest, host/container parity. Linux/Windows/full history CI pending. UP02 profile-plan отдельно в branch, не опубликован. G09/#81/UP01/PC03–PC06 остаются открыты; 0.1.0 BLOCKED.

## Сверка 0.0.95 и кандидат UP02 0.0.96

main 0.0.95 b179d71f091083916a88067a895c85c6539bc480, CI 46053357417 6/6 PASS, annotated catalog and Cleanup tags 672f08ad6ae306f74410f4a6c62e813be89cb87f / c33bd2fe15aba1aeb35dadc80390820338720376, all four independent skill trees match. UP02: добавлены read-only profile_plan и skill_tree, 25/25 Linux по отчёту ветки; native/full CI ещё не подтверждён. См. [план профиля](PROFILE_UPDATE_PLAN.md). UP01/UP02 остаются PARTIAL: live resolver, gh metadata, журнал, безопасная замена и rollback, упаковка и клиентская приёмка открыты. #81/G09/PC03–PC06 и 0.1.0 остаются открытыми.

## Инструменты обновления в исходном ZIP (кандидат 0.0.97)

С 0.0.97 ZIP-контракт требует CATALOG.json, UPDATE RU/EN, профильную инструкцию RU/EN и три read-only инструмента UP01/UP02. Проверка отклоняет отсутствующие/лишние файлы и несогласованные версии каталога даже при пересчитанном манифесте. Старые ZIP проверяются по прежнему контракту. ZIP остаётся runtime subset: тесты навыков исключены, поэтому это не raw Git tree и не staging для skill_tree.py. Проверяющий код брать из независимо доверенного checkout; не выполнять код из непроверенного ZIP. Аттестация, live resolver, gh metadata, apply и rollback отдельно открыты.

## Проверка метаданных gh staging (кандидат 0.0.98)

0.0.97 main 4f0e5ec0175e42bf67afceef3360497d1261d140, CI 46062411446 SUCCESS, annotated tag object 726389b4f834b243413ab84ef36d9379bbd1684d.

UP02.02: read-only gh_stage связывает независимо предоставленный raw Git tree с установленным деревом и проверяет точный набор пяти github-* metadata, исходные поля frontmatter, body, bytes остальных файлов, modes и stage fingerprint. Ограниченный subset YAML (plain/simple quoted scalar и >- без сложных конструкций); неподдерживаемые формы BLOCKED. Реальная сериализация gh, lockfile, live refs, авторизация apply, атомарность и rollback NOT_VERIFIED. С 0.0.98 инструмент обязателен в ZIP; 0.0.97 остаётся совместимой. 10 новых fixture tests и package gate; native/full CI pending.

## Классификация восстановления без записи (0.0.99)

PR #105 CI 46065687896 PASS, squash b94fd6855f2a32179f6804cd8e562f7f5ca1f2f4; main CI/tag pending.

UP02.03: read-only классификатор восстановления одного навыка. Сопоставляет строго ограниченный journal с фактическими fingerprint profile/stage/backup, проверяет disjoint ordinary same-volume roots и повторно наблюдает identity. Различает NOT_STARTED, OLD_IN_BACKUP, NEW_PRESENT, NEW_PRESENT_OLD_RETAINED; неоднозначность и несовпадение фаз BLOCKED. 10 disposable fixture tests, включая прерывания между rename и записью фазы, local edit и отсутствие stage. Не создаёт journal, не выполняет rename/delete, не разрешает apply и не доказывает durability. Следующий этап — отдельный writer с no-clobber primitives и crash recovery, сначала в fixtures. Не включать диагностический кандидат в runtime ZIP до приёмки.

## Журнал фаз транзакции без перезаписи (0.0.100)

0.0.99 main 67ad5669abb80819b0183ed4cc9234b377f27802, CI 46118526414 SUCCESS, annotated tag object 4501f60a678567e4efdacdd78e4a52c9005a871b.

UP02.03: append-only журнал фаз одного навыка, отдельные канонические JSON-записи, строгая последовательность и неизменность полей, O_CREAT|O_EXCL, file flush/fsync и повторная сверка. Частичная запись и неизвестные файлы блокируют продолжение, существующие записи не перезаписываются. Девять fixture tests, включая collision и отказ fsync. Только библиотека для доверенного эксклюзивного каталога: durability родительского каталога, ACL/гонки, реальный crash, перемещение и rollback NOT_VERIFIED. В рабочий профиль не пишет; в runtime ZIP пока не включается.

## Перемещение навыков без перезаписи (0.0.101)

PR #107 прошёл CI 46119327281 и принят. Проверка main и тег ещё ожидаются.

Добавлена библиотека перемещения проверенного каталога без перезаписи: Windows rename и Linux renameat2(RENAME_NOREPLACE). Другие платформы и отсутствие поддержки блокируются; небезопасного fallback нет. Проверяются ожидаемый отпечаток, отдельные корни одного устройства, отсутствие цели, идентичность после перемещения. Девять тестов на временных каталогах. Это отдельная заготовка для доверенных эксклюзивных корней, не готовый установщик: ACL, гонки предков, сохранность после сбоя питания, интеграция журнала и rollback открыты. В рабочие профили не пишет в CI, в ZIP пока не входит.

## Проверка полного цикла обновления (0.0.102)

PR #108 прошёл CI 46120392984 и принят. Проверка main и тег ожидаются.

Журнал, перемещение и диагностика объединены в одном изолированном тестовом цикле. Установка и обновление проверяются на автоматически созданных временных каталогах, включая восемь сценариев имитации остановки между фазами. Старое дерево остаётся в backup, соседний навык не меняется. Шесть тестовых методов. Это не аварийное завершение процесса, не проверка отключения питания и не production updater. Нет произвольного пути профиля или автоматического rollback; ZIP не расширяется.

## Добавлены испытания аварийной остановки (0.0.103)

PR #109 прошёл CI 46122145983 и принят. Проверка main и тег ожидаются.

Добавлены испытания с принудительной остановкой отдельного процесса на восьми границах установки и обновления. Новый процесс считывает журнал и сверяет фактические каталоги. Проверяются сохранность резервной копии и соседнего навыка. Три тестовых метода; результаты CI ожидаются. Только временные данные, без автоматического восстановления и проверки отключения питания.

## Добавлен откат установленного обновления (0.0.104)

PR #110 прошёл CI 46124170657 и принят. Проверка main и тег ожидаются.

Добавлен откат уже установленного обновления: прежний навык возвращается в профиль, новый сохраняется в staging. Отдельный журнал отката не меняет исходный журнал. Повторный явный запуск продолжает согласованную фазу; несовпадение содержимого или журнала блокирует запись. Девять тестов на временных каталогах, включая два прерванных обратных перемещения. Это библиотека для доверенных эксклюзивных корней, не готовый установщик. Восстановление при отсутствии нового навыка, откат первой установки, реальное аварийное завершение отката и питание ещё открыты.

## Добавлена отмена незавершённых обновлений (0.0.105)

PR #111 прошёл CI 46128158068 и принят. Проверка main и тег ожидаются.

Добавлена отмена первой установки и незавершённого обновления без удаления файлов. Старая версия возвращается из резервной копии, новая остаётся в staging. Журнал отмены отделён от истории обновления. Девять тестов на временных каталогах; CI ожидается. Для уже установленного обновления используется отдельный откат. Рабочий CLI, защита от конкурентного доступа и устойчивость к потере питания остаются открытыми.

## Добавлено продолжение прерванных обновлений (0.0.106)

PR #112 прошёл CI 46133430573 и принят. Проверка main и тег ожидаются.

Объединены установка и обновление одного навыка с продолжением прерванной операции. Проверяются ожидаемые версии и отпечатки, журнал, резервная копия и результат. Отмена или откат блокируют повторное прямое применение той же операции. Десять тестов на временных каталогах, включая несовпадение содержимого и повреждённый обратный журнал. Это библиотека для доверенных эксклюзивных корней, не готовый установщик; авторизация, происхождение данных, защита от конкурентного доступа, пакетная операция, питание и рабочий CLI открыты. ZIP не изменён.
