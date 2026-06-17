# Переоформление форка на GitHub

Цель: [alexandrgert/timer-app](https://github.com/alexandrgert/timer-app) должен быть **прямым форком** [useraitester-creator/win-timer-app-v1](https://github.com/useraitester-creator/win-timer-app-v1), а не lukoyanov-aa.

## Почему нельзя просто «сменить родителя»

GitHub не позволяет сменить parent у существующего форка. В одной **fork network** у пользователя может быть только один форк. Сейчас цепочка:

`useraitester-creator` → `lukoyanov-aa` → `alexandrgert` (старый parent в UI).

Чтобы parent в UI стал `useraitester-creator`, нужно **удалить** старый репозиторий и **создать новый форк** напрямую от useraitester.

## Что сохранится / что потеряется

| | После миграции |
|--|--|
| Локальный код и git-история | сохраняются (push в новый remote) |
| Releases v0.2.2–v0.4.2 | **нужно пересоздать** на новом репо (или оставить архив со старым именем) |
| Issues / PR | на старом репо — пропадут при удалении |
| URL `github.com/alexandrgert/timer-app` | снова заработает после нового форка |

## Шаги (один раз)

### 1. Авторизация gh с правом удаления

```bash
gh auth refresh -h github.com -s delete_repo
```

Подтвердите код в браузере.

### 2. Архив (опционально)

Если нужны старые Releases без пересборки — **не удаляйте** репо, а только переименуйте в `tasktimer-link-b24-archive` и создайте форк под другим именем. Для имени `timer-app` старый репо нужно удалить.

### 3. Удалить старый форк

```bash
gh repo delete alexandrgert/tasktimer-link-b24 --yes
# или, если имя ещё timer-app:
# gh repo delete alexandrgert/timer-app --yes
```

### 4. Создать форк от useraitester

```bash
gh repo fork useraitester-creator/win-timer-app-v1 --fork-name timer-app --remote=false
```

Проверка:

```bash
gh api repos/alexandrgert/timer-app --jq '{parent: .parent.full_name}'
# ожидается: "useraitester-creator/win-timer-app-v1"
```

### 5. Запушить свой код

```bash
git remote set-url origin https://github.com/alexandrgert/timer-app.git
git remote remove upstream 2>/dev/null || true
git remote add upstream https://github.com/useraitester-creator/win-timer-app-v1.git
git push -u origin main --force
git push origin --tags --force
```

`--force` нужен: ваш `main` — TaskTimer link B24 (`timerapp_ag/`), не копия upstream `win_timer_app/`.

### 6. Восстановить Releases (при необходимости)

```bash
# пример для последнего релиза, если артефакты есть в dist/
gh release create v0.4.2 dist/tasktimer-link-b24-0.4.2-* \
  --title "TaskTimer link B24 v0.4.2" \
  --notes-file docs/release-notes-v0.4.2.md
```

## Remotes после миграции

| Remote | URL |
|--------|-----|
| `origin` | `https://github.com/alexandrgert/timer-app.git` |
| `upstream` | `https://github.com/useraitester-creator/win-timer-app-v1.git` |

Папку `upstream/win-timer-app-v1/` в репозитории можно удалить — достаточно `git fetch upstream`.

## Синхронизация изменений upstream → fork

Не делайте `git merge upstream/main` вслепую (разные пути: `win_timer_app/` vs `src/timerapp_ag/`).

```bash
git fetch upstream
git log --oneline main..upstream/main   # что нового у upstream
# перенос по фичам в timerapp_ag, pytest
```
