# Скорость и доказательства CI

[**Русский — оригинал**](CI.md) | [English — перевод](CI.en.md)

Скорость — критерий качества процесса. Измеряй время ожидания runner, время до первого полезного результата, полный критический путь, p50/p95, повторные запуски и расход runner-minutes. Не смешивай длительность отдельных jobs с wall-clock.

1. Используй существующие локальные штатные проверки до отправки кода. FAST — формат, метаданные, затронутые тесты; FULL — все обязательные проверки. Не называй FAST полной приёмкой.
2. При GitHub Actions сначала измерь job/step timings; выдели тяжёлые независимые проверки в параллельные jobs. Сохрани read-only права, pinned Actions, одинаковый SHA, проверенные входы и изоляцию. Итоговый required check запускается всегда и требует успеха каждой обязательной стадии; skipped/cancelled/failure — отказ. Не пропускай целый required workflow по paths.
3. Используй штатные matrix, needs, concurrency, dependency caching и reusable workflows, только если они упрощают процесс. Отменяй исключительно устаревшую необязательную проверку того же кандидата; не отменяй выпуск и приёмку уникального принятого SHA. Очередь CI не заменяет интеграционную очередь.
4. Определяй затронутые тесты по изменениям и доказанным зависимостям; неизвестные зависимости требуют FULL. Кешируй только проверяемые данные с привязкой к версиям, хешам конфигурации и исходникам; не доверяй PR-кешу для привилегированного выпуска. Историю секретов не сокращай без проверки эквивалентного охвата.
5. Успешные PR-проверки связывай с точным HEAD и актуальной базой; проверяй фактический итог интеграции и тег отдельно. Ошибку исправляй в той же ветке. Не отключай проверки ради ускорения.

Источники: [GitHub required checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks?apiVersion=2022-11-28), [concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency), [dependency caching](https://docs.github.com/en/actions/concepts/workflows-and-actions/dependency-caching), [reusable workflows](https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations).
