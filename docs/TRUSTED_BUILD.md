# T09.08 — доверенная сборка каталога и GitHub attestation

[**Русский — оригинал**](TRUSTED_BUILD.md) | [English — перевод](TRUSTED_BUILD.en.md)

## Что действительно распространяем

TESSERA — публичный каталог Agent Skills, **не исполняемое приложение**. В T09.08 появился настоящий исходный дистрибутив: `TESSERA-catalog-vX.Y.Z.zip` со всеми пригодными для использования файлами навыков, `LICENSE`, `README` и `VERSION`, а также детерминированным `MANIFEST.json`. Это версия **каталога**; она не заменяет независимую версию каждого навыка, которую предусматривает T16.

`tools/build_catalog_package.py` использует только Python stdlib. ZIP создаётся с фиксированными метаданными, упорядоченными путями и неизменным набором файлов. В манифесте указываются SHA-256 и размер каждого включённого файла, точный commit SHA и версия каталога. Файлы тестов, кэши, локальные каталоги и временные данные в пакет не входят. Исходные symlink, подозрительные пути и неполный набор обязательных файлов блокируются.

Для TESSERA **появился настоящий продуктовый сборочный артефакт**, поэтому `release-checks.json` теперь содержит обязательный шаг сборки. Два прежних набора тестов остаются обязательными.

## Два отдельных этапа

1. **PR/CI**: выполняются тесты, проверка безопасной конфигурации и воспроизводимая сборка ZIP, но **без attestation, OIDC и публикации GitHub Release**. Отказ CI блокирует слияние.
2. **После слияния и создания аннотированного тега**: отдельный `.github/workflows/build-attested-catalog.yml` запускается **только вручную по выбранному тегу** (`workflow_dispatch`). Он проверяет совпадение тега и `VERSION`, аннотированный объект и принадлежность коммита истории `main`, повторяет обязательные тесты, собирает ZIP, создаёт GitHub/Sigstore attestation и сохраняет пакет в GitHub Actions Artifacts.

Все Actions закреплены полными SHA. Право `contents: write` в подписывающем workflow **отсутствует**. Только его job получает ограниченные `id-token: write`, `attestations: write`, `contents: read`. Сборка из Pull Request никогда не получает права подписи; нет токена PAT и платного API.

## Обновлённые закреплённые Actions

Оба workflow используют `actions/checkout` v7.0.1 и `actions/setup-python` v7.1.0 с зафиксированными SHA; только signing workflow использует `actions/attest` v4.2.2 и `actions/upload-artifact` v7.0.2. Все манифесты используют Node.js 24. Точные SHA перечислены в [GITHUB_SECURITY](GITHUB_SECURITY.md) и контролируются `tools/check_actions_runtime.py`. Миграция рантайма не создаёт attestation: подписывающий workflow по-прежнему требуется запустить на аннотированном теге.

## Почему запуск ручной

Существующий `validate.yml` после успешного push в `main` создаёт тег с помощью стандартного `GITHUB_TOKEN`. По правилам GitHub такой push **не вызывает второй workflow по событию push**. Автоматическое создание подписи внутри job для `main` также привязало бы источник attestation к `refs/heads/main`, а не к требуемому `refs/tags/vX.Y.Z`.

Поэтому безопасная цепочка — подтверждённый тег, затем отдельно запущенный `workflow_dispatch` **на этом теге**. Возможную автоматизацию перехода после проверки завершённого CI надо прорабатывать в следующем этапе, без секретного PAT и без нарушения Rulesets.

## Безопасная версия CLI для проверки

Для скачивания Actions Artifact и последующего подтверждения его происхождения требуется `gh 2.102.0+`; старые версии имели ошибки сравнения `--signer-workflow`, `--source-ref` и безопасной записи скачанных файлов. Проверка `core/release_provenance.py` теперь отказывает при старой или нераспознанной версии CLI. Проверьте `gh --version` **перед** ручной командой получения архива; скрипт проверки ZIP остаётся отдельной офлайн-проверкой целостности. См. [RELEASE_PROVENANCE](RELEASE_PROVENANCE.md).

## Команды

После полного завершения `main` CI и проверки тега:

```bash
# Сборка локально для проверки (не подписывает и не публикует).
python tools/build_catalog_package.py --repo . --output-dir dist --check-reproducible

# Запуск реального signing workflow по подтверждённому тегу.
gh workflow run build-attested-catalog.yml --ref v0.0.14 -R Sashido01/TESSERA

# После появления завершённого run: получить пакет из GitHub Actions Artifacts.
gh run download <build-run-id> -R Sashido01/TESSERA -n tessera-catalog-v0.0.14

# Независимо проверить подписанное происхождение извлечённого ZIP.
gh attestation verify TESSERA-catalog-v0.0.14.zip \
  --repo Sashido01/TESSERA \
  --source-ref refs/tags/v0.0.14 \
  --source-digest <full-release-commit-sha> \
  --signer-workflow Sashido01/TESSERA/.github/workflows/build-attested-catalog.yml \
  --deny-self-hosted-runners
```

Команды с `v0.0.14` являются инструкцией для этой версии **после выпуска тега**, а не утверждением о фактически выполненном workflow. Не запускай signing по ветке или чужому тегу. Перед проверкой подставь действительные ID запуска и SHA. Для следующей версии обнови номер.

## Важные различия

- **GitHub Actions Artifact** — сохранённый файл завершённого workflow с ограниченным сроком хранения, **не GitHub Release asset**.
- **GitHub attestation** — криптографическое утверждение, относящееся к байтам файла и конкретному signing workflow, **не подпись итогового JSON-свидетельства TESSERA**.
- **Подписанный исходный ZIP каталога** — реальный распространяемый материал Agent Skills, **не доказательство работоспособности программ, которые используют навыки**.
- Существующий `core/release_provenance.py` T09.07 требует именно опубликованный GitHub Release asset. Новый Actions Artifact нельзя автоматически выдавать за такой asset. Сквозную связку двух способов распространения нужно реализовать отдельно.

## Приёмка и ограничения

Модульные тесты проверяют детерминизм пакета, манифест, байтовые SHA-256, ссылки, запрет лишних файлов, отказ при неверном теге/грязной рабочей копии и статические ограничения signing workflow. CI проверяет сборку реально на GitHub.

Пока signing workflow не запущен по реальному аннотированному тегу и нет его успешно завершённого отчёта с attestation, **`SIGNED_ARTIFACT=NOT_VERIFIED`**. Никакой GitHub Release этим этапом не создаётся. Следующие задачи: живой signing/verify, отдельное решение о публикации настоящего GitHub Release, интеграция attestations в Release Core и координация конкурирующих релизов.

Официальные руководства: [GitHub artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations), [`gh workflow run`](https://cli.github.com/manual/gh_workflow_run), [`gh attestation verify`](https://cli.github.com/manual/gh_attestation_verify).
