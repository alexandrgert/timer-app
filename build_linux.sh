#!/usr/bin/env bash
# Сборка Linux amd64 (PyInstaller onedir + FHS).
# Локально по умолчанию — только .deb; полный набор форматов — CI / релиз (см. scripts/linux_ci_formats.env).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/linux_package_lib.sh
source "$SCRIPT_DIR/scripts/linux_package_lib.sh"
# shellcheck source=scripts/linux_extra_formats.sh
source "$SCRIPT_DIR/scripts/linux_extra_formats.sh"

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

if linux_pkg_format_enabled ebuild; then
  echo "==> Сборка Gentoo ebuild"
  linux_pkg_build_ebuild
fi

if linux_pkg_format_enabled pisi; then
  echo "==> Сборка PiSi (.pisi)"
  linux_pkg_build_pisi
fi

if linux_pkg_format_enabled pet; then
  echo "==> Сборка Puppy Linux (.pet)"
  linux_pkg_build_pet
fi

if linux_pkg_format_enabled pup; then
  echo "==> Сборка Puppy Linux (.pup)"
  linux_pkg_build_pup
fi

if linux_pkg_format_enabled lzm; then
  echo "==> Сборка Slax (.lzm)"
  linux_pkg_build_lzm
fi

if linux_pkg_format_enabled appimage; then
  echo "==> Сборка AppImage"
  linux_pkg_build_appimage
fi

if linux_pkg_format_enabled flatpak; then
  echo "==> Сборка Flatpak"
  linux_pkg_build_flatpak
fi

if linux_pkg_format_enabled snap; then
  echo "==> Сборка Snap"
  linux_pkg_build_snap
fi

echo "==> Linux-сборка завершена (FORMATS=${FORMATS:-deb})"
