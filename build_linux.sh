#!/usr/bin/env bash
# Сборка Linux amd64 (PyInstaller onedir + FHS).
# Локально по умолчанию — только .deb; все форматы: FORMATS=deb,rpm,tar.xz,tgz (CI / релиз).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/linux_package_lib.sh
source "$SCRIPT_DIR/scripts/linux_package_lib.sh"

linux_pkg_init_env "$SCRIPT_DIR"
linux_pkg_check_arch
linux_pkg_require_amd64_host
linux_pkg_resolve_version
linux_pkg_install_build_deps
linux_pkg_run_pyinstaller
linux_pkg_create_fhs_staging

trap linux_pkg_cleanup_staging EXIT

if linux_pkg_format_enabled deb; then
  echo "==> Сборка .deb"
  linux_pkg_build_deb
fi

if linux_pkg_format_enabled rpm; then
  echo "==> Сборка .rpm"
  linux_pkg_build_rpm
fi

if linux_pkg_format_enabled tar.xz || linux_pkg_format_enabled tgz; then
  echo "==> Сборка .tar.xz / .tgz"
  linux_pkg_build_tarballs
fi

echo "==> Linux-сборка завершена (FORMATS=${FORMATS:-deb})"
