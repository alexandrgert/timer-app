#!/usr/bin/env bash
# Переоформление форка: прямой parent useraitester-creator/win-timer-app-v1.
# Требует: gh auth с scope delete_repo (см. docs/fork-migration.md).
set -euo pipefail

OLD_REPO="${OLD_REPO:-alexandrgert/tasktimer-link-b24}"
UPSTREAM="useraitester-creator/win-timer-app-v1"
NEW_NAME="timer-app"

echo "==> Проверка gh и scope delete_repo"
if ! gh auth status -h github.com &>/dev/null; then
  echo "Выполните: gh auth login" >&2
  exit 1
fi

echo "==> Удаление старого форка: ${OLD_REPO}"
gh repo delete "${OLD_REPO}" --yes

echo "==> Создание форка ${UPSTREAM} как ${NEW_NAME}"
gh repo fork "${UPSTREAM}" --fork-name "${NEW_NAME}" --remote=false

PARENT=$(gh api "repos/alexandrgert/${NEW_NAME}" --jq '.parent.full_name')
echo "Parent: ${PARENT}"
if [[ "${PARENT}" != "${UPSTREAM}" ]]; then
  echo "Ошибка: parent не ${UPSTREAM}" >&2
  exit 1
fi

echo "==> Настройка remotes и push"
git remote set-url origin "https://github.com/alexandrgert/${NEW_NAME}.git"
git remote remove upstream 2>/dev/null || true
git remote add upstream "https://github.com/${UPSTREAM}.git"
git push -u origin main --force
git push origin --tags --force

echo "Готово. Проверьте: https://github.com/alexandrgert/${NEW_NAME}"
