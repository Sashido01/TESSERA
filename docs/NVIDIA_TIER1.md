# T12.01 — NVIDIA SkillEvaluator: ограниченная проверка Tier 1

[**Русский — оригинал**](NVIDIA_TIER1.md) | [English — перевод](NVIDIA_TIER1.en.md)

## Решение и границы

На 24.11.2026 проверен официальный [релиз v1.2.0](https://github.com/NVIDIA/SkillEvaluator/releases/tag/v1.2.0), исходный commit `5625c2534bf266f810aea489ffbe69da0bb2645e`, лицензия Apache-2.0. Выбран только базовый wheel, без extras. Его SHA-256 `cd367d655b567bb6015aa79b0229d1f268ad4fa0429619f896f5dccef8e6948a` взят из метаданных релиза. 19 транзитивных/прямых зависимостей Linux x86_64 CPython 3.13 закреплены по версиям и хешам wheel из [uv.lock указанного commit](https://github.com/NVIDIA/SkillEvaluator/blob/5625c2534bf266f810aea489ffbe69da0bb2645e/uv.lock). Отдельное venv, pip --require-hashes --only-binary=:all и pip check. Это не подтверждение криптографической подписи релиза NVIDIA и не полный аудит лицензий/уязвимостей зависимостей.

Официальная [документация Tier 1](https://docs.nvidia.com/skills/skillevaluator/tier1-reference) различает статический режим и LLM-этапы. Команда общего validate по умолчанию может включить другие уровни, поэтому запрещена. Разрешён исключительно узкий вызов `skillevaluator tier1 PATH --no-llm --checks schema,quality --min-score 70 -r json -o REPORT_DIR`. HOME и переменные окружения изолированы, ключи провайдеров и GitHub token не передаются; PIP_NO_INDEX и UV_OFFLINE включены при оценке. Это не OS-сетевая песочница; загрузка закреплённых wheel в CI требует сети. Не запускать содержимое навыков, LLM, Tier 2/3. Не устанавливать [all], [llm], [tier2], [tier3].

## Приёмка

`tools/check_nvidia_tier1.py` проверяет точную версию, копию каталога, завершённость двух проверок, JSON, отсутствие LLM, согласованность exit code и результата, оценку 0–100. Отдельный некорректный синтетический навык обязан провалить schema. Содержимое и локальные пути отчёта не публикуются: только идентификаторы проверок, уровни серьёзности и оценка. Исходные файлы не должны изменяться.

**Политика первого запуска — advisory:** технически корректный отчёт с FAIL качества/схемы не делает навык PASS. CI блокируется при невозможности запустить проверку, неполном/несогласованном отчёте или пропущенной негативной проверке. Реальные замечания подлежат разбору, а не автоматическому подавлению. Англоязычные эвристики качества необходимо отдельно оценить на русском оригинале.

**Результат T12.01 (24.11.2026): PASS выбранных проверок.** [CI 45358283596](https://github.com/Sashido01/TESSERA/actions/runs/45358283596) подтвердил `NVIDIA_TIER1_FOCUSED_EXECUTION_PASS`: официальный wheel и 19 зависимостей установлены по хешам, pip check PASS, schema PASSED, quality PASSED, оценка 75.0/100 при пороге 70, 18 замечаний (7 medium, 11 low), негативный пример PASS, LLM DISABLED. 393 теста каталога и 19 тестов навыка PASS. Первый CI 45358033088 отказал из-за несовпадения ожидаемого машинного имени валидатора с фактическим `QUALITY`; исправление проверено повторным CI. Замечания не подавлены. Полная безопасность и языковые ложные срабатывания ещё не оценены. T12.01 COMPLETE в пределах schema/quality. T12 целиком PARTIAL: security, PII, license, code-integrity, unicode, lint, dependency и harness-check ещё не проверены; полная Tier 1 оценка, совместимость клиентских агентов, ложные срабатывания, полный аудит затрат и лицензий зависимостей остаются NOT_VERIFIED. Никаких платных AI API. Затраты CI не тождественны нулевой цене.

Следующий изолированный этап: [T12.02.01 — статические проверки и профили](NVIDIA_STATIC_REVIEW.md).

## T12.03.13 — интегрированный статический запуск (кандидат)

Явно запрошены 11 групп и 13 строк валидаторов, включая dependency. Только закреплённые SkillEvaluator 1.2.0, SkillSpector 2.13.7, Bandit 1.9.4, Gitleaks 8.30.1; проверка версий и SHA бинарника Gitleaks, абсолютные override для SkillSpector/Bandit, частный PATH-адаптер Gitleaks с фиксированным контрактом detect и --redact=100, --max-archive-depth 0. Без LLM, сырых отчётов в CI, с временной копией и сверкой содержимого. Проверка отсутствия managed fallback ограничена известными каталогами; PIP_NO_INDEX/UV_OFFLINE не являются сетевой изоляцией. Semgrep NOT_RUN (не установлен), будущие dependency manifests блокируются до отдельного закреплённого контракта. Оценка политики отделена от выполнения; наличие всех строк не сертификация. Семь офлайн регрессий, живой CI обязателен; живой synthetic redaction control интегрированного адаптера и полный sandbox остаются открытыми.

## T12.03.13 — результат PR

[CI 45403712350](https://github.com/Sashido01/TESSERA/actions/runs/45403712350) PASS: 543+29 тестов, 13 строк, execution PASS, policy FAIL (Security Scan 1 HIGH, 19 MEDIUM), остальные 12 PASSED; SkillSpector 53/100, 0 подавлений. Semgrep NOT_RUN, certification NOT_VERIFIED. Слит в main; приёмка main и тега отдельно.

## T12.03.14 — живой контроль адаптера Gitleaks (кандидат)

Реальный закреплённый бинарник вызывается через тот же частный shim с точным контрактом upstream, в отдельном временном каталоге с синтетическим TOML-правилом. Чистый файл: exit 0, пустой JSON; искусственный нерабочий маркер: exit 10, одна находка ожидаемого правила и файла, Secret=REDACTED, маркер отсутствует в stdout и stderr. Сверяются байты fixture/config и состав каталога fixture. Пять офлайн регрессий. Не выводить маркер или сырой отчёт; обязательна живая приёмка CI. Это контроль shim с собственным правилом, не доказательство upstream allowlist/полноты детектора, не тест сетевой изоляции и не сертификация NVIDIA. T12 PARTIAL.

## T12.03.14 — результат PR

[CI 45405865725](https://github.com/Sashido01/TESSERA/actions/runs/45405865725) PASS: 548+29=577 тестов, clean/detection/stdout-stderr redaction/fixture entries PASS реального shim. Общий policy FAIL, 1 HIGH и 19 MEDIUM в Security Scan; Semgrep NOT_RUN. v0.0.45 main CI 45405654421 и аннотированный тег подтверждены; v0.0.46 принят в main, его собственная приёмка отдельно.

## T12.03.15 — происхождение агрегированной HIGH-находки (кандидат)

[Закреплённый upstream](https://github.com/NVIDIA/SkillEvaluator/blob/5625c2534bf266f810aea489ffbe69da0bb2645e/src/skillevaluator/validators/security.py#L5693-L5703) добавляет отдельную HIGH-находку с category SECURITY и check_name skillspector_risk_score, если effective_score > 50 и нет отдельных CRITICAL/HIGH. JSON reporter сохраняет структурированный check_name через Finding.to_dict(). Поэтому 1 HIGH интегрированного отчёта при 0 HIGH прямого SkillSpector и 53/100 согласуется с агрегированным gate, но точный идентификатор предыдущего интегрированного отчёта не опубликован. Новый агрегат high_attribution различает только точное сочетание category/check_name для HIGH в Security Scan; остальные HIGH считаются other_high. Никакие findings, severity, policy verdict, пороги и scanner execution не изменены. Не выводятся сообщения, пути или произвольные идентификаторы. Три регрессии; живой CI должен подтвердить реальные счётчики. T12 PARTIAL, Semgrep и сетевой sandbox открыты.

## T12.03.15 — результат PR

[CI 45418208676](https://github.com/Sashido01/TESSERA/actions/runs/45418208676) PASS: 551+29 тестов, aggregate_risk_gate=1, other_high=0, MEDIUM=19, policy FAIL. v0.0.46 main CI 45417975016 и аннотированный тег подтверждены; v0.0.47 принят в main, его приёмка отдельно.

## T12.03.16 — Semgrep в Tier 1 (кандидат)

Используем upstream lock NVIDIA 5625c2534bf266f810aea489ffbe69da0bb2645e, blob 11859086088d6720e5f4f303de0740a4830b065b (66 строк закреплённых пакетов, 915 SHA-256), отдельный venv, wheel-only, require-hashes, pip check, OSV и метаданные лицензий реального окружения. Semgrep 1.182.0, локальные шесть правил NVIDIA (blob 3ef2067b69ef50f09b39c933771f751bc227b3db), точная версия, явный override и REQUIRE_SEMGREP=1. Чистый и положительный Python fixture сканируются, но не исполняются; проверяются exit, отсутствие errors, scanned path, точный ID, сохранность. В отчёте Tier 1 обязательна точная версия Semgrep в Code Risk Analysis; отсутствие/неполнота блокируют выполнение. Пять регрессий. Метрики и version check отключены, registry/Pro/LLM не используются; это не OS-сетевой sandbox, не аудит нативного OCaml-бинарника и не сертификация. Upstream исключает tests/test при интегрированном анализе; независимые Bandit/Gitleaks/SkillSpector сохранены. Живой CI обязателен, T12 PARTIAL.

## T12.03.16 — результат PR

[CI 45419767513](https://github.com/Sashido01/TESSERA/actions/runs/45419767513) PASS: 556+29=585 тестов, Semgrep 1.182.0 EXECUTED, clean/detection/coverage/fixture PASS, Code Risk Analysis PASSED. 67 Python distributions, OSV 8 ID в 3 пакетах (mcp 1.29.0:5, opentelemetry-api 1.37.0:2, wcmatch 8.5.2:1), 3 UNKNOWN license metadata, native binaries NOT_SCANNED. Это отдельные открытые риски; policy FAIL 19 MEDIUM + aggregate HIGH без изменений. v0.0.47 main CI и аннотированный тег подтверждены; v0.0.48 принят в main, собственная приёмка отдельно.

## T12.03.17 — усиление Git helper навыка (кандидат)

По обзору 19 MEDIUM (PR 48, комментарий 7135272307): production AST4 соответствует реальному вызову Git; ограничение каждого вызова 60 с, абсолютный executable из абсолютных PATH entries, закрытый stdin, shell=False, фиксированные ошибки без сырых диагностик, post-capture лимит 1 048 576 символов. Шесть регрессий; риск memory/pipe, доверие к PATH/config, Windows и гонки остаются ограничениями. AST4 может сохраниться как ожидаемый subprocess; подавлений нет. CI обязателен, T12 PARTIAL.

## T12.03.17 — результат PR

[CI 45421559705](https://github.com/Sashido01/TESSERA/actions/runs/45421559705) PASS: 556+35=591 тест, все шесть новых регрессий. SkillSpector 53/100, 19 MEDIUM, 0 подавлений, coverage 100% проверяемых файлов, Code Risk Analysis PASSED; policy FAIL неизменён. v0.0.48 main CI 45421312225 и аннотированный тег подтверждены; v0.0.49 принят в main, собственная приёмка отдельно.

## T12.03.18 — статические импорты тестов (кандидат)

Три тестовых модуля заменяют загрузку importlib по фиксированному файлу на обычный import из scripts текущего доверенного checkout: отклоняется конфликтующий кеш sys.modules, каталог временно ставится первым в sys.path, после импорта восстанавливается, __file__ сверяется с ожидаемым исходником. Три проверки происхождения модуля, прежние сценарии не удалены. Это упрощение тестового кода, не sandbox; доверие к checkout и Python import hooks сохраняется. Не меняются сканеры, пороги, suppression, рабочий код навыка или полномочия. CI должен подтвердить отсутствие регрессий и фактическое число AST3; снижение балла заранее не обещается. T12 PARTIAL.

## T12.03.18 — результат PR

[CI 45423325658](https://github.com/Sashido01/TESSERA/actions/runs/45423325658) PASS: 556+38=594 теста, AST3 6→0, SkillSpector 53→36/100, MEDIUM 19→13, aggregate HIGH 1→0, 0 подавлений, coverage 100% проверяемых файлов. Интегрированная статическая policy PASS, не сертификация безопасности. v0.0.49 main CI 45423143946 и аннотированный тег подтверждены; v0.0.50 принят в main, собственная приёмка отдельно.

## T12.03.19 — ясность русской терминологии (кандидат)

22 редакционные замены в шести файлах навыка: обычные словосочетания вместо смешанных дефисных токенов. Предварительно проверено 17 файлов, независимый подсчёт ASCII Latin + Cyrillic/Greek в изменённых файлах 22→0. Пять русских документов и два текста исключений release_tag.py; английский перевод сохраняет прежний смысл, исполняемые команды, коды ошибок, политика доступа и алгоритмы не меняются. Это не полный аудит Unicode или подтверждение устранения AE4; живой CI обязателен. Не отключаются правила, не используются подавления. AST4 и LP3 остаются предметом проверки, T12 PARTIAL.

## T12.03.19 — результат PR

[CI 45425640926](https://github.com/Sashido01/TESSERA/actions/runs/45425640926) PASS, 556+38=594 теста, AE4 6→0, MEDIUM 13→7 (AST4 6, LP3 1), SkillSpector 36→22/100, 0 подавлений, integrated policy PASS. v0.0.50 main CI 45425408841 и аннотированный тег подтверждены; v0.0.51 принят в main, собственная приёмка отдельно.

## T12.03.20 — Linux namespace preflight (кандидат)

Обязательный synthetic control, отдельный от сканеров: положительное подключение родителя к IPv4 loopback listener, отрицательное внутри отдельного network namespace, разные inode net namespace, PID=1, точные soft/hard rlimits CPU 10 s, AS 1 GiB, FSIZE 16 MiB, NOFILE 256, CORE 0; закрытые stdin/унаследованные FD, минимальное окружение, вывод во временные файлы, timeout и уничтожение PID namespace (потомок создал отдельную сессию setsid, не записал marker). Прототип реально прошёл в отдельном Linux x86_64 контейнере UID=0, util-linux 2.41.5, не GitHub Runner. Пять offline регрессий. CI блокируется при неуспехе, без sudo/fallback. Лимиты тестовые, не профили сканеров; файловая изоляция, AF_UNIX, суммарный cgroup бюджет, реальные scanner workloads и Windows NOT_VERIFIED. Не sandbox, T12 PARTIAL. Semgrep 8 OSV IDs остаются открытыми.

Первый PR CI 45427345462: 561+38=599 тестов PASS, обязательный preflight FAIL на Ubuntu 26.04. Исходная причина не установлена (слишком общий код). В том же кандидате добавлены ограниченные числовые сведения о политике user/net/pid namespaces и фиксированные коды ошибок unshare/prlimit без публикации stderr, ещё одна offline регрессия (всего шесть). Запрет fallback, требования контроля и права runner не изменены. Повторный CI обязателен.

Второй PR CI 45427736161: 562+38=600 тестов PASS, NAMESPACE_UNSHARE_PERMISSION_DENIED; kernel/unprivileged_userns_clone=1, apparmor_restrict_unprivileged_userns=1, user/net/pid max=55883. AppArmor вероятная причина, точный audit denial не получен. Вместо изменения политики хоста выбран явный Docker synthetic preflight на одноразовом доверенном runner: образ Python 3.13.18 slim trixie linux/amd64 закреплён manifest SHA-256 48d884813cf44e927cf64c5529dd630dd3b18338c6dc727991eef9b71e934a20; источник https://hub.docker.com/layers/library/python/3.13.18-slim-trixie/images/sha256-48d884813cf44e927cf64c5529dd630dd3b18338c6dc727991eef9b71e934a20 . Образ имеет опубликованные advisory, не считается проверенным supply chain; пока только synthetic без репозитория, секретов и mount/socket. Nonroot, no caps, no-new-privileges, seccomp, network none, read-only root, tmpfs, cgroup memory/swap/CPU/PID. Проверка реальных значений в контейнере и host sentinel; cleanup обязателен. Четыре новых offline теста. Старый unshare сохранён как диагностический инструмент, не автоматический fallback. Docker daemon — доверенная root-equivalent граница хоста, не доступен внутри контейнера; не переносить на пользовательские машины без отдельной модели угроз. Принудительное исчерпание ресурсов, потомки по таймауту и реальный запуск сканеров NOT_VERIFIED. CI обязателен, T12 PARTIAL.

## T12.03.21 — контейнерный Gitleaks (кандидат)

T12.03.20: [CI 45428224320](https://github.com/Sashido01/TESSERA/actions/runs/45428224320) PASS, 566+38=604 теста, Docker synthetic preflight PASS. v0.0.52 принят в main, тег отдельно. Новый обязательный контроль сравнивает host и container для tracked UTF-8 stdin scope; идентичный snapshot fingerprint, TSG1 digest, точные количества файлов/байтов, findings по правилам, clean/negative/redaction controls. Один nonroot контейнер с закреплённым образом и SHA256 binary, только минимальные helper modules и binary в отдельном read-only bind, repo/.git/socket не монтируются, сеть отключена, 2 CPU/512 MiB/64 PID, log-driver none, 300s timeout и rm --force. Девять offline регрессий; конкретный новый код и реальный Docker workload требуют CI. Host scan сохраняется, history/path checks не изолированы, образ не сертифицирован, retained report limit не hard disk quota, cleanup timeout/daemon failures не доказаны. T12 PARTIAL.

## T12.03.21 — результат PR

[CI 45432568241](https://github.com/Sashido01/TESSERA/actions/runs/45432568241) PASS: 575+38=613 тестов; Docker Gitleaks 177 файлов, 1 404 601 байт, 0 находок, host parity/frame digest/redaction/source preservation PASS. Host history: 864 blobs, 10 663 788 байт, 0 находок. Integrated Tier 1 policy PASS; v0.0.52 main CI 45432307038 и аннотированный тег подтверждены. v0.0.53 принят в main, собственная приёмка отдельно.

## T12.03.22 — контейнерное сканирование истории (кандидат)

Повторно используемый транспорт Gitleaks, отдельная обязательная проверка достижимых UTF-8 blobs: host inventory, проверка Git blob OID SHA-1/SHA-256, fingerprint inventory, TSG1 batches <=256 объектов и <=16 MiB каждый, суммарный прежний предел 128 MiB/2048 blobs. Общий deadline 540s, каждое сканирование до 300s; точная сверка coverage/findings с host, synthetic previous-content и прежний реальный Git fixture на host. Не передаём .git/OID/path в контейнер; только bytes и категория other. Семь новых offline регрессий. CI обязателен; производительность и полный Docker workload NOT_VERIFIED, path-specific/integrated scans остаются на host. Git SHA-1 не доказательство криптографической стойкости к коллизиям. T12 PARTIAL.

## T12.03.22 — результат PR

[CI 45434506035](https://github.com/Sashido01/TESSERA/actions/runs/45434506035) PASS: 582+38=620 тестов; история Docker 878 blobs, 10 952 864 байта, 4 пакета, 316.56s, 0 находок; identity, digest, host parity, previous-content PASS. CI 795s при лимите 1200s. v0.0.53 main CI и тег подтверждены; v0.0.54 принят в main, тег отдельно.

## T12.03.23 — контейнерная проверка по путям (кандидат)

Отдельный TSP1 режим транспорта: 10 фиксированных категорий (2 области x 5 существующих правил), до 256 targets/16 MiB в пакете, общий лимит 4096 targets/192 MiB, deadline 180s. Пустой пакет допустим только TSP1 для запуска пяти контрольных fixtures. Реальные пути/OID/.git не передаются; фиксированные канонические имена, прежний scan_rule, строгие десять строк отчёта и snapshot parity с host, повторная проверка источника. Девять новых offline регрессий (8 + workflow guard). Старые проверки сохраняются; integrated Gitleaks остаётся host. Реальное выполнение и допустимость лимитов требуют CI. T12 PARTIAL.

## T12.03.23 — результат PR

[CI 45439256012](https://github.com/Sashido01/TESSERA/actions/runs/45439256012) PASS: 591+38=629 тестов, Docker current 181 файл/1 437 066 байт, history 893 blobs/11 251 084 байта/416.82s, path 4 current+37 history targets/5 fixtures/21.52s; 0 находок во всех областях, host parity PASS, Tier 1 policy PASS. v0.0.54 main CI и тег подтверждены; v0.0.55 принят в main, собственная приёмка отдельно. Рост времени history с 316.56 до 416.82s требует измерений и оптимизации CI без снижения coverage.

## T12.03.24 — лицензии Semgrep (кандидат)

Три точных upstream LICENSE полностью прочитаны; Git blob SHA-1 пересчитан и совпал; SHA-256 закреплён для сравнения с установленным wheel RECORD. face 26.0.1 BSD-3-Clause: commit 86ec4072580809cc3978f5d6bb40261eb60c3045, blob 50c51841a2efd87b46c053beeceff5617ad8cfa1, 1497 bytes (CRLF сохранены); peewee 3.19.0 MIT: commit 45c166bce4630a55729f513a4b11fb95af23df5b, blob c752ab3ead2e7be324e5cafb5e1d53135c16af13, 1058 bytes; protobuf 6.33.6 BSD-3-Clause с пояснением generated code: commit 6e1998413a5bca7c058b85999667893f167434bc, blob 19b305b00060a774a9180fb916c14b49edb2008f, 1732 bytes. Существующий проверяющий механизм, без подмены metadata или нормализации текста; два новых offline теста. Локальный DNS PyPI заблокирован; реальное соответствие wheel/RECORD ожидает CI, несовпадение остаётся открытым, юридическая совместимость NOT_VERIFIED. Восемь OSV IDs не устранены. T12 PARTIAL.
