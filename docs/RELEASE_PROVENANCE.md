# T09.07 — проверка происхождения артефакта по подписанной GitHub attestation

[**Русский — оригинал**](RELEASE_PROVENANCE.md) | [English — перевод](RELEASE_PROVENANCE.en.md)

## Назначение

TESSERA использует **официальный GitHub CLI** и механизм **GitHub artifact attestations (Sigstore / SLSA provenance)**, а не разрабатывает собственную криптографию. Модуль `core/release_provenance.py` проверяет криптографическое утверждение о происхождении конкретного файла и связывает его с исходным коммитом, Git-тегом, репозиторием и разрешённым подписывающим workflow.

Проверка доступна только по явной команде, когда проект реально опубликовал GitHub Release с прикреплённым файлом **и создал для этого файла attestation**. Наличие тега, успешных тестов или просто метаданных digest недостаточно. В TESSERA на момент разработки T09.07 GitHub Releases отсутствуют; никакой реально подписанный артефакт проекта пока не подтверждён.

## Модель доверия и что именно подтверждается

Проверка выполняется двумя независимыми стадиями:

1. Открывается **локальный файл**, который пользователь получил из конкретного GitHub Release. Его имя, размер и вычисленный SHA-256 сверяются с подтверждёнными метаданными именно этого release asset. Для файла установлен предел 64 МиБ по умолчанию, максимально 512 МиБ; данные читаются потоково. Файлы с symlink, отличающимся именем, размером или digest блокируются.
2. Запускается `gh attestation verify` над **этим же файлом**, с указанием точного `--repo`, `--source-digest` (полного SHA исходного коммита), `--source-ref refs/tags/<version>`, `--signer-workflow` и предиката `https://slsa.dev/provenance/v1`. Запрещены attestations от self-hosted runners (`--deny-self-hosted-runners`). CLI сам проверяет сертификат и криптографическую подпись посредством доверенных механизмов GitHub/Sigstore. TESSERA дополнительно сверяет SHA-256 предмета подписанного заявления с файлом.

**Доверие ограничено указанным workflow:** имя задаётся полным путём `owner/repository/.github/workflows/build.yml` и должно принадлежать тому же репозиторию. Нельзя принимать любую успешную CI job или произвольный подписывающий workflow. Для реализации реального подписывания впоследствии потребуется отдельный процесс сборки по Git-тегу, не доступный для изменения из непроверенного Pull Request.

**Ограничение доверия:** даже подтверждённая attestation доказывает, что соответствующее утверждение подписано через указанную GitHub Actions identity. Она не доказывает автоматически безопасность программы, полную воспроизводимость сборки или истинность всех описательных полей `predicate` — на них может влиять сам workflow.

## Использование

Необходимы установленный официальный `gh` с командой `gh attestation verify` и доступ к публичной GitHub attestation. Запуск выполняется в доверенной пользовательской среде; TESSERA не устанавливает CLI автоматически и не хранит токены.

```bash
# По умолчанию: без сети и без исполнения проверки attestations
python core/release_report.py --repo . --version 0.0.13

# После публикации реального Release, загрузки его файла и подготовки доверенного workflow:
python core/release_report.py --repo . --version 0.0.13 \
  --verify-publication --verify-provenance \
  --github-repo owner/repository \
  --artifact-file <local-asset-file> \
  --signer-workflow owner/repository/.github/workflows/build.yml \
  --format certificate
```

Пример — **синтаксический**, не свидетельство наличия такого `build.yml` или подписанного файла в TESSERA. Имя конкретного файла должно совпадать с прикреплённым GitHub Release asset. Чтобы дополнительно подтвердить удалённый Git-тег и завершённый CI, используются отдельные флаги `--verify-remote --verify-ci --run-id <completed-run-id>`.

## Отказы и отсутствие ложного успеха

- `PROVENANCE_REQUIRES_PUBLICATION_VERIFICATION` — недопустимо проверять происхождение релизного файла без установленной публикации.
- `PROVENANCE_REQUIRES_FILE_AND_SIGNER` — не указан конкретный файл или подписывающий workflow.
- `PROVENANCE_RELEASE_ASSET_MISSING` — нет ровно одного подходящего прикреплённого файла.
- `PROVENANCE_FILE_DIGEST_MISMATCH`, `PROVENANCE_FILE_SIZE_MISMATCH`, `PROVENANCE_FILE_MISMATCH` — содержимое или идентичность файла не совпадают с metadata.
- `PROVENANCE_VERIFIER_UNAVAILABLE`, `PROVENANCE_VERIFIER_TIMEOUT`, `PROVENANCE_SIGNATURE_VERIFICATION_FAILED`, `PROVENANCE_VERIFIER_OUTPUT_INVALID` — отсутствует официальный верификатор, произошла ошибка, подпись не подтвердилась или получены некорректные доказательства.
- `PROVENANCE_ARTIFACT_CHANGED_DURING_VERIFICATION` — файл изменился в ходе проверки.

Ошибки CLI, секреты, абсолютные пути локального файла и подробное содержимое подписанных заявлений **не включаются в итоговый отчёт**.

## Контракт результата и свидетельства

`core/release_report.py` добавляет `provenance_status`, `local_artifact_integrity`, `provenance_signer_workflow`, `provenance_source_commit`, `provenance_source_ref` и `provenance_verified_asset`, не раскрывая локальный путь.

`core/release_certificate.py` сохраняет `signed=false`: **само итоговое свидетельство не подписано**. Отдельное `attestation_signature_verified=true` относится только к проверенной GitHub attestation. Статус `SOURCE_ASSET_ATTESTATION_VERIFIED` возникает только при подтверждённых опубликованном GitHub Release, совпадающем remote-теге, успешном завершённом CI, локальном файле и подписи происхождения. И даже тогда `application_release_readiness=NOT_VERIFIED`.

Пока реальные подписанные файлы TESSERA отсутствуют, эксплуатационное подтверждение этого статуса не выполнялось: тесты имитируют ответы GitHub CLI, **не подделывая реальные сертификаты**.

## Что ещё нужно для полного T09

1. Спроектировать доверенный build workflow, создающий файл из зафиксированного Git-тега; закрепить actions по SHA и минимальные разрешения.
2. Добавить выпуск реальной GitHub artifact attestation только для реально созданного продукта; подписывающий workflow должен иметь `id-token: write`, `attestations: write`, `contents: read`.
3. Проверить живую цепочку «Git-тег → сборка → attestation → публикация asset → загрузка → независимое gh verify». Не создавать фиктивный релиз ради теста.
4. Завершить безопасное управление конкурирующими релизами и независимое подтверждение готовности приложения. T09 остаётся PARTIAL.

Документы: [GitHub artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations), [официальный gh attestation verify](https://cli.github.com/manual/gh_attestation_verify).
