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
