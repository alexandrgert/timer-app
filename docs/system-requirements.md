# Системные требования TaskTimer link B24

Минимальные требования для **установленных** сборок (не для разработки из исходников).

Текущая версия продукта: **0.5.31** (см. [`pyproject.toml`](../pyproject.toml)).

---

## Сводная таблица

| Платформа | Артефакт | ОС | Процессор | ОЗУ | Диск | Сеть |
|-----------|----------|-----|-----------|-----|------|------|
| **Linux** | `.deb`, `.rpm`, `.tar.xz`, `.tgz` amd64 | Debian 11+, Ubuntu 20.04+, Fedora 38+, RHEL 9+, openSUSE и др. с **glibc ≥ 2.31** | x86_64 (64-bit) | 512 МБ | ~200 МБ | для Битрикс24 / WebDAV |
| **Windows** | `.exe` win64 | Windows **10** (64-bit) или **11** | x86_64 (AMD64) | 512 МБ | ~150 МБ | для Битрикс24 / WebDAV |
| **macOS** | `.app` в `.zip` | **macOS 11** Big Sur и новее | Apple Silicon (**arm64**) в релизе; Intel — отдельная сборка | 512 МБ | ~200 МБ | для Битрикс24 / WebDAV |

**Не поддерживается:** 32-bit Linux/Windows, Flatpak/AppImage.

---

## Linux (amd64)

Поддерживаемые форматы: **`.deb`**, **`.rpm`**, **`.tar.xz`**, **`.tgz`**.

### Минимум для работы

| Параметр | Требование |
|----------|------------|
| Архитектура | **amd64** (x86_64) |
| Ядро / libc | glibc **≥ 2.31** (типично Ubuntu 20.04+, Debian 11+) |
| Графика | X11 или Wayland, рабочий стол с системным треем |
| ОЗУ | 512 МБ свободной (рекомендуется 1 ГБ+) |
| Диск | ~200 МБ под программу; данные — отдельно в `~/.local/share/timerapp/` |

Пакеты `.deb` / `.rpm` тянут зависимости автоматически; для `.tar.xz` / `.tgz` нужны те же системные библиотеки (OpenGL/EGL, X11, fontconfig, DBus, libtiff).

### Установка

| Формат | Команда |
|--------|---------|
| `.deb` | `sudo dpkg -i tasktimer-link-b24-*-amd64.deb && sudo apt-get install -f` |
| `.rpm` | `sudo dnf install ./tasktimer-link-b24-*-amd64.rpm` или `sudo rpm -Uvh …rpm` |
| `.tar.xz` / `.tgz` | `sudo tar -xJf …tar.xz -C /` или `sudo tar -xzf …tgz -C /` |

### WebDAV (Linux)

- Периодическая проверка сервера работает **в фоне** (в том числе при свёрнутом окне в трей).
- Минимальный интервал проверки — **1 минута** (настраивается в UI).

### Сборка (разработчик)

- ОС: Linux **x86_64**
- `dpkg-deb`, `rpmbuild` (`rpm`), Python 3.10+, venv, `requirements-build.txt`
- Команда: `./build_linux.sh` → все форматы в `dist/`

---

## Windows (`.exe` win64)

### Минимум для работы

| Параметр | Требование |
|----------|------------|
| ОС | **Windows 10** или **11**, только **64-bit** |
| Процессор | x64 (AMD64); ARM Windows **не** поддерживается |
| ОЗУ | 512 МБ (рекомендуется 1 ГБ+) |
| Диск | ~150 МБ под `TaskTimer.exe`; данные в `%LOCALAPPDATA%\timerapp\` |
| Прочее | Python ставить **не нужно** (всё внутри exe) |

Первый запуск exe может занять чуть больше времени (распаковка PyInstaller).

### WebDAV (Windows)

- Периодическая проверка работает при свёрнутом окне в трей.
- Минимальный интервал — **1 минута**.

### Сборка (разработчик)

- ОС: **Windows 10/11** x64
- Python 3.10+, PowerShell, venv, `requirements-build.txt`
- Команда: `.\build_exe.ps1` → `dist\tasktimer-link-b24-<версия>-win64.exe`

---

## macOS (`.app`)

### Минимум для работы

| Параметр | Требование |
|----------|------------|
| ОС | **macOS 11** Big Sur и новее |
| Процессор | Apple Silicon (**arm64**) — [релиз v0.5.31](https://github.com/alexandrgert/timer-app/releases/tag/v0.5.31); Intel (x86_64) — отдельная сборка `./build_macos.sh` на Mac |
| ОЗУ | 512 МБ (рекомендуется 1 ГБ+) |
| Диск | ~200 МБ; данные в `~/Library/Application Support/timerapp/` |

Сборка **не подписана** Apple Developer ID — при первом запуске macOS может потребовать
«Открыть в любом случае» в настройках безопасности (Системные настройки → Конфиденциальность и безопасность).

### WebDAV (macOS)

- Периодическая проверка при работе приложения в фоне (трей).
- Минимальный интервал — **1 минута**.

### Сборка (разработчик)

- ОС: **macOS** (только на Darwin)
- Python 3.10+, venv, `requirements-build.txt`
- Команда: `./build_macos.sh` → `dist/tasktimer-link-b24-<версия>-macos-<arch>.zip`

---

## Общие требования (все desktop-платформы)

| Функция | Требование |
|---------|------------|
| **WebDAV** | HTTPS-доступ к серверу (Nextcloud, Яндекс.Диск, корпоративное облако и т.п.); один общий файл `data.json` |
| **Битрикс24** | Доступ в интернет, входящий вебхук с правами task, crm, user |
| **Один экземпляр** | Второй запуск активирует уже открытое окно |
| **Данные** | ~1–50 МБ на типичную базу задач (зависит от истории) |
| **Секреты** | Пароль WebDAV и вебхук Б24 **не** попадают в облако — только локально на каждом компьютере |

---

## Скачивание сборок

Готовые артефакты — [GitHub Releases](https://github.com/alexandrgert/timer-app/releases).

| Файл | Платформа |
|------|-----------|
| `tasktimer-link-b24-*-amd64.deb` | Linux (Debian/Ubuntu) |
| `tasktimer-link-b24-*-amd64.rpm` | Linux (Fedora/RHEL/openSUSE) |
| `tasktimer-link-b24-*-linux-amd64.tar.xz` / `*.tgz` | Linux (универсальный архив) |
| `tasktimer-link-b24-*-win64.exe` | Windows |
| `tasktimer-link-b24-*-macos-arm64.zip` / `*-macos-x86_64.zip` | macOS |

**Текущий релиз:** [v0.5.31](https://github.com/alexandrgert/timer-app/releases/tag/v0.5.31) — Linux, Windows, macOS (arm64).

CI (`.github/workflows/ci.yml`) при push в `main` собирает **Linux** (`.deb`, `.rpm`, `.tar.xz`, `.tgz`), **Windows .exe** и **macOS .zip**.

---

## См. также

- [ИНСТРУКЦИЯ.md](../ИНСТРУКЦИЯ.md) — для пользователей
- [architecture-cross-platform.md](architecture-cross-platform.md) — архитектура
- [release-notes-v0.5.31.md](release-notes-v0.5.31.md) — что нового в релизе
