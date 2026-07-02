#!/usr/bin/env bash
# Сборка .deb для TaskTimer link B24 (Linux amd64). Обёртка над build_linux.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export FORMATS="${FORMATS:-deb}"
exec "$SCRIPT_DIR/build_linux.sh"
