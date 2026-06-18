# TaskTimer link B24 — версия 0.4.5

## Что нового

### Интерфейс и UX

- **Tooltip в трее** — при сворачивании окна снова показываются названия активных и приостановленных задач (а не только название приложения).
- Учитывается **последняя задача на панели таймера**, даже если плавающий виджет не открывали.
- После скрытия плавающего виджета (✕) подсказка в трее обновляется сразу.

---

## Сборки в релизе

| Платформа | Файл |
|-----------|------|
| Linux amd64 | `tasktimer-link-b24-0.4.5-amd64.deb` |
| Windows x64 | `tasktimer-link-b24-0.4.5-win64.exe` |
| macOS | `tasktimer-link-b24-0.4.5-macos-<arch>.zip` |
| Android 10+ | `tasktimer-link-b24-0.4.5-android.apk` |

Минимальные требования: [system-requirements.md](system-requirements.md).

---

## Как обновиться

### Linux

```bash
wget https://github.com/alexandrgert/timer-app/releases/download/v0.4.5/tasktimer-link-b24-0.4.5-amd64.deb
sudo dpkg -i tasktimer-link-b24-0.4.5-amd64.deb
sudo apt-get install -f
```

### Windows / macOS / Android

Скачайте нужный файл на [странице релиза v0.4.5](https://github.com/alexandrgert/timer-app/releases/tag/v0.4.5).

Данные (`data.json`) и настройки в `~/.config/tasktimer/` сохраняются при обновлении.
