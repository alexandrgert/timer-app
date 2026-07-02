# Архитектура TaskTimer link B24

Документ описывает модель для **Windows, macOS, Linux** (Python + PySide6, WebDAV sync, локальные секреты).

## Принцип

**Один контракт данных, десктопные оболочки.**

| Слой | Содержимое | Реализация |
|------|------------|------------|
| **Domain** | модели, merge, таймер, план, напоминания | `src/timerapp_ag/domain/` |
| **Application** | orchestration, save/load, sync hooks | `controller.py` |
| **Adapters** | файлы, WebDAV, Bitrix REST | `storage.py`, `webdav_*`, `bitrix.py` |
| **Shell** | UI, tray, single-instance | `main_window.py`, `main.py` |
| **Platform** | пути, OS-интеграции | `platform_paths.py` |

## Пути данных

Модуль `platform_paths.py` — единая точка для путей:

| Назначение | Linux | macOS | Windows |
|------------|-------|-------|---------|
| Данные | `~/.local/share/timerapp/TaskTimer link B24/data.json` | `~/Library/Application Support/timerapp/...` | `%LOCALAPPDATA%\timerapp\...` |
| Секреты | `~/.config/tasktimer/` | `~/Library/Application Support/TaskTimer/` | `%APPDATA%\TaskTimer\` |
| `.env` | `~/.config/tasktimer/.env` | то же | `%APPDATA%\TaskTimer\.env` |

Файлы секретов (не синхронизируются):

- `bitrix.json` — webhook Битрикс24
- `webdav.json` — учётные данные WebDAV

## Синхронизация

- **Синхронизируется:** `data.json` (задачи, сессии, `ui` без секретов)
- **Транспорт:** WebDAV (PUT/GET), merge по `task.id`
- **Конфликт задач:** учёт `status`, `completed_at`, union сессий по `session.id`

Контракт формата: [`data-schema.md`](data-schema.md), JSON Schema: [`schemas/data.schema.json`](schemas/data.schema.json).

Алгоритм WebDAV: [`webdav-sync.md`](webdav-sync.md).

## Desktop (Win / macOS / Linux)

| Платформа | Сборка | Артефакт |
|-----------|--------|----------|
| **Windows** | `build_exe.ps1` | `tasktimer-link-b24-<ver>-win64.exe` |
| **Linux** | `build_deb.sh` | `.deb` **amd64** |
| **macOS** | `build_macos.sh` | `TaskTimer link B24.app` в `.zip` |

**Linux:** единственный формат дистрибуции — **Debian-пакет amd64**. Flatpak и AppImage **не используются**.

CI: `.github/workflows/ci.yml` — jobs `build-deb`, `build-exe`, `build-macos`.

## Структура пакетов

```
src/timerapp_ag/
  domain/           # без I/O и без Qt
  platform_paths.py
  controller.py     # application layer
  storage.py        # persistence
  main_window.py    # Qt shell
```

## Что не делать

- Flatpak / AppImage для Linux (только `.deb` amd64)
- Хранение webhook в `data.json`
- Разные schema на платформах
