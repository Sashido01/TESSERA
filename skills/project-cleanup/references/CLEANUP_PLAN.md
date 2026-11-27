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

## Дополнительная проверка Windows-семантики

RW05 native Windows regression в #98 выявила отказ при сравнении изменённого снимка; [CPython #157671](https://github.com/python/cpython/issues/157671) описывает несовместимость path stat/fstat ctime. PC02 превентивно разделяет cross-method identity (birthtime Windows/ctime POSIX плюс dev/ino/size/mtime/type/nlink) и same-method полную проверку до/после; ctime/attributes внутри метода не исключены. 3 новых regression methods, Linux 22/22 PASS (2.182 с), source d8701efc6cca9265cf117cf924e4120871389152, tests 6712f94de909adb08507796930a1f10a059196c5. Native Windows NOT_VERIFIED. В PowerShell 7.4+ прямой native stdout > file сохраняет byte stream; не объединять stderr и stdout, не пропускать через текстовый pipeline, проверять exit code и новые отдельные каталоги. См. [Microsoft about_Redirection](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_redirection?view=powershell-7).

## Усиление границ PC02 (27.11.2026)

Дополнительно отклоняются leading ASCII space, управляющие/format Unicode-символы и зарезервированные device stems с пробелами перед расширением; NFKC также выявляет COM¹/LPT¹. Бюджет совокупного UTF-8 размера уникальных prefix/key+display — 8 MiB (не оценка реального RSS). Два каталога снимков не должны вкладываться друг в друга. После чтения обоих повторно проверяются identity всех десяти файлов и двух каталогов; после проверки метаданных кандидата повторно проверяются его предки и отсутствие вложенного .git; после прохода сверяется root marker. Обнаруженные изменения дают BLOCKED или metadata_unverified, не разрешение удаления. Это снижает риск устойчивых подмен, но не делает операции атомарными и не доказывает отсутствие TOCTOU, bind mounts или алиасов. [Microsoft naming rules](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file), [Git ls-files](https://git-scm.com/docs/git-ls-files), [Python os](https://docs.python.org/3/library/os.html). Изолированная повторная проверка прежних 22/22 PASS, после изменения 27/27 Linux PASS (2.245 с); exact source 38128cd58959db5cc4d09c18a45b9b87806383fa, tests 2dc1e381216db6aa7959a84c324bf7e2088f0810. Native CI обязателен. Перед захватом отдельно проверяй exact Git top-level, отсутствие replacement refs и последовательное наблюдение HEAD. Git snapshots являются предоставленными доказательствами, не удостоверенными самим помощником.
