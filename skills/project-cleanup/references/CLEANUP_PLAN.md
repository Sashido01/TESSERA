# План очистки по Git-снимкам

[**Русский — оригинал**](CLEANUP_PLAN.md) | [English — перевод](CLEANUP_PLAN.en.md)

PC02 — кандидат read-only advisory. Не удаляет, не вызывает Git, не изменяет index или окружение. Требует доверенного, явно выбранного Git-проекта и двух отдельных свежих бинарных снимков из одного и того же корня; подлинность/полнота и независимость получения снимков не проверяются самим помощником.

В доверенном Git-контексте без наследованного небезопасного GIT_* и без запуска неизвестных hooks собери два набора в новых приватных обычных каталогах **вне проекта**. Не сбрасывай ограничения среды. Для каждого набора сохранить точный stdout каждой успешной команды, проверить exit code, не смешивать stderr, не преобразовывать кодировку, NUL или переводы строк. При unborn HEAD, ошибке Git, изменении статуса или невозможности получить полную выдачу — BLOCKED, ничего не удалять. Не использовать текстовый pipeline PowerShell, преобразующий байты.

| Файл | Команда из корня проекта |
| --- | --- |
| head-ref.txt | git rev-parse --verify HEAD |
| head.z | git ls-tree -r -z HEAD |
| index.z | git ls-files --stage -z |
| ignored.z | git ls-files --others --ignored --exclude-standard -z |
| untracked.z | git ls-files --others --exclude-standard -z |

`python -B scripts/cleanup_plan.py --root <project> --first <capture-a> --second <capture-b> --scope build`

Повторять --scope только для явно утверждённых generated-only директорий (до 20, без пересечения). Не выбирать произвольные области для уменьшения счётчика. `--details` добавляет до 100 крупнейших REVIEW-файлов (не каталоги) с относительными именами, размером и mtime; при превышении лимита детали неполны. Отчёт и снимки остаются приватными. Без флага — только агрегаты.

HEAD и index защищают даже staged deletions, sparse/skip-worktree и gitlinks; обычный untracked также защищён, включая ancestor/descendant. При unmerged index, non-portable path, alias collision (casefold/NFKC), malformed records и несовместимом object format — BLOCKED. Не считать нормализацию точной эмуляцией Windows/macOS. Known protected/unknown, links/reparse, hardlinks, nested .git, другое устройство, пропавшие/необычные объекты не входят в REVIEW. Метаданные проверяются без открытия содержимого кандидатов. Подлинность снимков, владение проектом, воспроизводимость, актуальная занятость, права, path races и физическое освобождение не доказаны.

Exit 0 OBSERVED, 1 STALE/PARTIAL без списка при несовпадении/превышении, 2 BLOCKED. До 2 MiB на файл снимка, 50000 строк на список, 100000 префиксов, 64 компонента/1024 UTF-8 bytes на путь, 10000 обработанных ignored-строк и 30 секунд между операциями metadata (не общий timeout процесса). Для превышения лимита не экстраполировать, не делить Git-доказательство произвольно. Применяется только к обычным файлам в этих границах; нет поддержки голых и unborn repos, nonportable paths, полных больших монорепозиториев сверх лимита. Два одинаковых снимка и digest не являются атомарной блокировкой. План всегда deletion_authorized=false, reclaimable_bytes=null, capture_authenticity=NOT_VERIFIED. Перед любым действием нужна независимая актуальная проверка Git, владельца/процессов, воспроизводимости/восстановления, точных целей и разрешений. Не обходить отказ политики.

Изолированное доказательство: 19/19 Linux unit tests PASS, Python 3.13.5, Git 2.47.3, suite 2.309 s. Реальный одноразовый Git fixture: ignored-файл, оставшийся после staged deletion, защищён через HEAD, а второй ignored-файл попал только в REVIEW; файлы и снимки сохранились. Source blob bf5a6103ee079a06ec399e9ecaca4af530629cad; tests 403e4ff49097909fd76978efa406d6f2cefdbc21. Windows и полный CI NOT_VERIFIED.

Источники: [git ls-files](https://git-scm.com/docs/git-ls-files), [git sparse-checkout](https://git-scm.com/docs/git-sparse-checkout), [git check-ignore](https://git-scm.com/docs/git-check-ignore), [git update-index](https://git-scm.com/docs/git-update-index).
