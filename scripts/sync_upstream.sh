#!/usr/bin/env bash
# Fetch upstream useraitester-creator/win-timer-app-v1 and refresh local snapshot.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UPSTREAM_URL="${UPSTREAM_URL:-https://github.com/useraitester-creator/win-timer-app-v1.git}"
SNAPSHOT="${ROOT}/upstream/win-timer-app-v1"

git -C "${ROOT}" fetch upstream main 2>/dev/null || git -C "${ROOT}" remote add upstream "${UPSTREAM_URL}" 2>/dev/null || true
git -C "${ROOT}" fetch upstream main

echo "Upstream commits not in main:"
git -C "${ROOT}" log --oneline main..upstream/main || true

rm -rf "${SNAPSHOT}"
git clone --depth 1 "${UPSTREAM_URL}" "${SNAPSHOT}"
rm -rf "${SNAPSHOT}/.git"

echo "Snapshot updated at ${SNAPSHOT}"
echo "Port changes into src/timerapp_ag/ by feature (do not blind-merge)."
