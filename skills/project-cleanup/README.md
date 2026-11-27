# Project Cleanup

[**Русский — оригинал**](README.md) | [English — перевод](README.en.md)

Версия 0.0.1 — начальный кандидат. Отдельный навык для локальной и GitHub-гигиены, управления размером и предотвращения роста. Установка всей папки; см. [SKILL.md](SKILL.md). Не требует платных API или внешних пакетов.

```bash
python -B scripts/inventory.py --root <project-root>
python -B scripts/inventory.py --root <project-root> --details
```

Первый режим выдаёт только агрегаты; второй добавляет приватные относительные пути крупнейших наблюдаемых REVIEW-файлов (не публиковать). Ничего не удаляет. См. [инвентаризацию](references/INVENTORY.md), [Git/GitHub](references/GIT_STORAGE.md), [дорожную карту](references/ROADMAP.md). Native Windows/Linux CI и агентная приёмка пока NOT_VERIFIED.

Приватные детали также показывают до 20 крупнейших групп каталогов первого уровня (null — файлы в корне). Агрегация хранит до 8192 групп; private_top_level_complete=false обозначает пропуск групп, не изменение общих метрик. Группа не является разрешённой целью удаления.
