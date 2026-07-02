#!/usr/bin/env bash
# Общая логика Linux-сборки: PyInstaller onedir + FHS-дерево для .deb / .rpm / .tar.*
set -euo pipefail

linux_pkg_init_env() {
  local script_dir="${1:?}"
  LINUX_PKG_PROJECT_DIR="$script_dir"
  LINUX_PKG_PACKAGING_DIR="$LINUX_PKG_PROJECT_DIR/packaging/linux"
  LINUX_PKG_PACKAGE_NAME="${PACKAGE_NAME:-tasktimer-link-b24}"
  LINUX_PKG_TARGET_ARCH=amd64
  LINUX_PKG_MAINTAINER="${PACKAGE_MAINTAINER:-alexandrgert <alexandrgert@gmail.com>}"
  LINUX_PKG_VENV="${VENV:-$LINUX_PKG_PROJECT_DIR/.venv}"
  LINUX_PKG_PYTHON="${PYTHON:-$LINUX_PKG_VENV/bin/python}"
  LINUX_PKG_INSTALL_PREFIX="${INSTALL_PREFIX:-/opt/tasktimer-link-b24}"
  LINUX_PKG_BIN_NAME="${BIN_NAME:-tasktimer-link-b24}"
  LINUX_PKG_BUMP="${BUMP:-patch}"
  LINUX_PKG_DIST_DIR="$LINUX_PKG_PROJECT_DIR/dist"
  LINUX_PKG_OFFLINE="${OFFLINE:-0}"
  LINUX_PKG_ALLOW_NO_BUMP="${ALLOW_NO_BUMP:-0}"
  LINUX_PKG_PACKAGE_TITLE="${PACKAGE_TITLE:-TaskTimer link B24}"
}

linux_pkg_require_amd64_host() {
  case "$(uname -m)" in
    x86_64) ;;
    *)
      echo "Ошибка: Linux-сборка поддерживается только на x86_64 (amd64)." >&2
      exit 1
      ;;
  esac
}

linux_pkg_check_arch() {
  if [[ -n "${ARCH:-}" && "${ARCH}" != "amd64" ]]; then
    echo "Неподдерживаемая ARCH=${ARCH}. Допустимо только amd64." >&2
    exit 1
  fi
}

linux_pkg_resolve_version() {
  if [[ ! -x "$LINUX_PKG_PYTHON" ]]; then
    echo "Не найден Python в venv: $LINUX_PKG_PYTHON" >&2
    exit 1
  fi

  if [[ -z "${VERSION:-}" ]]; then
    if [[ "${NO_BUMP:-0}" == "1" && "$LINUX_PKG_ALLOW_NO_BUMP" != "1" ]]; then
      echo "NO_BUMP=1 игнорируется: для сборок версия всегда поднимается минимум на patch." >&2
      echo "Если нужно явно отключить bump, используйте ALLOW_NO_BUMP=1 NO_BUMP=1." >&2
    fi
    if [[ "${NO_BUMP:-0}" != "1" || "$LINUX_PKG_ALLOW_NO_BUMP" != "1" ]]; then
      echo "==> Semver bump (${LINUX_PKG_BUMP}) в pyproject.toml"
      "$LINUX_PKG_PYTHON" "$LINUX_PKG_PROJECT_DIR/scripts/bump_version.py" "$LINUX_PKG_BUMP" >/dev/null
    fi
  fi

  LINUX_PKG_VERSION="${VERSION:-$(
    "$LINUX_PKG_PYTHON" -c "import tomllib; print(tomllib.load(open('$LINUX_PKG_PROJECT_DIR/pyproject.toml','rb'))['project']['version'])"
  )}"
  echo "==> Версия пакета: ${LINUX_PKG_VERSION}"
}

linux_pkg_install_build_deps() {
  if [[ "$LINUX_PKG_OFFLINE" == "1" ]]; then
    echo "==> OFFLINE=1: пропускаю установку зависимостей сборки"
    return 0
  fi
  echo "==> Установка зависимостей сборки"
  "$LINUX_PKG_PYTHON" -m pip install -q -e "$LINUX_PKG_PROJECT_DIR" -r "$LINUX_PKG_PROJECT_DIR/requirements-build.txt"
}

linux_pkg_run_pyinstaller() {
  echo "==> PyInstaller (TaskTimer-linux.spec)"
  cd "$LINUX_PKG_PROJECT_DIR"
  "$LINUX_PKG_PYTHON" -m PyInstaller --noconfirm --clean TaskTimer-linux.spec

  if [[ ! -x "$LINUX_PKG_DIST_DIR/TaskTimer/TaskTimer" ]]; then
    echo "Не найден бинарник: $LINUX_PKG_DIST_DIR/TaskTimer/TaskTimer" >&2
    exit 1
  fi
}

linux_pkg_create_fhs_staging() {
  local opt_rel="${LINUX_PKG_INSTALL_PREFIX#/}"
  LINUX_PKG_STAGING="$(mktemp -d)"
  local install_dir="$LINUX_PKG_STAGING/$opt_rel"

  mkdir -p "$install_dir"
  cp -a "$LINUX_PKG_DIST_DIR/TaskTimer/." "$install_dir/"
  echo "$LINUX_PKG_VERSION" > "$install_dir/VERSION"

  mkdir -p "$LINUX_PKG_STAGING/usr/bin"
  cat > "$LINUX_PKG_STAGING/usr/bin/$LINUX_PKG_BIN_NAME" <<EOF
#!/bin/sh
exec ${LINUX_PKG_INSTALL_PREFIX}/TaskTimer "\$@"
EOF
  chmod 755 "$LINUX_PKG_STAGING/usr/bin/$LINUX_PKG_BIN_NAME"

  mkdir -p "$LINUX_PKG_STAGING/usr/share/applications"
  cat > "$LINUX_PKG_STAGING/usr/share/applications/tasktimer-link-b24.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=${LINUX_PKG_PACKAGE_TITLE}
Name[ru]=${LINUX_PKG_PACKAGE_TITLE}
Comment=Desktop task timer with Bitrix24 integration
Comment[ru]=Таймер задач с интеграцией Битрикс24
Exec=${LINUX_PKG_BIN_NAME}
Icon=tasktimer-link-b24
Terminal=false
Categories=Office;Utility;
StartupWMClass=tasktimer-link-b24
EOF

  mkdir -p "$LINUX_PKG_STAGING/usr/share/icons/hicolor/scalable/apps"
  cp "$LINUX_PKG_PACKAGING_DIR/tasktimer.svg" \
    "$LINUX_PKG_STAGING/usr/share/icons/hicolor/scalable/apps/tasktimer-link-b24.svg"
}

linux_pkg_cleanup_staging() {
  if [[ -n "${LINUX_PKG_STAGING:-}" && -d "$LINUX_PKG_STAGING" ]]; then
    rm -rf "$LINUX_PKG_STAGING"
    LINUX_PKG_STAGING=""
  fi
}

linux_pkg_installed_size_kb() {
  local opt_rel="${LINUX_PKG_INSTALL_PREFIX#/}"
  du -sk "$LINUX_PKG_STAGING/$opt_rel" "$LINUX_PKG_STAGING/usr" 2>/dev/null | awk '{s += $1} END {print s}'
}

linux_pkg_write_install_txt() {
  local dest="$1"
  cat > "$dest/INSTALL.txt" <<EOF
TaskTimer link B24 ${LINUX_PKG_VERSION} — Linux amd64

Установка из архива (tar.xz или .tgz) в систему:

  sudo tar -xJf tasktimer-link-b24-${LINUX_PKG_VERSION}-linux-amd64.tar.xz -C /
  # или
  sudo tar -xzf tasktimer-link-b24-${LINUX_PKG_VERSION}-linux-amd64.tgz -C /

Запуск: ${LINUX_PKG_BIN_NAME}

Для Fedora / RHEL / openSUSE предпочтительнее пакет .rpm.
Для Debian / Ubuntu / Mint — пакет .deb.
EOF
}

linux_pkg_build_deb() {
  if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "Установите dpkg-deb: sudo apt install dpkg" >&2
    return 1
  fi

  local deb_file="${LINUX_PKG_PACKAGE_NAME}-${LINUX_PKG_VERSION}-${LINUX_PKG_TARGET_ARCH}.deb"
  local deb_out="${LINUX_PKG_DIST_DIR}/${deb_file}"
  local opt_rel="${LINUX_PKG_INSTALL_PREFIX#/}"
  local installed_size_kb
  local deb_root
  deb_root="$(mktemp -d)"

  cp -a "$LINUX_PKG_STAGING/." "$deb_root/"
  installed_size_kb="$(du -sk "$deb_root/$opt_rel" "$deb_root/usr" 2>/dev/null | awk '{s += $1} END {print s}')"

  mkdir -p "$deb_root/DEBIAN"
  cat > "$deb_root/DEBIAN/control" <<EOF
Package: ${LINUX_PKG_PACKAGE_NAME}
Version: ${LINUX_PKG_VERSION}
Section: utils
Priority: optional
Architecture: ${LINUX_PKG_TARGET_ARCH}
Installed-Size: ${installed_size_kb}
Maintainer: ${LINUX_PKG_MAINTAINER}
Conflicts: tasktimer
Replaces: tasktimer
Depends: libc6 (>= 2.31), libglib2.0-0, libx11-6, libxcb1, libxkbcommon0, libdbus-1-3, libfontconfig1, libfreetype6, libgl1, libegl1, libxext6, libxrender1, libxi6, libxrandr2, libxss1, libxcursor1, libxinerama1, libtiff5 | libtiff6
Description: ${LINUX_PKG_PACKAGE_TITLE}
 Desktop task timer: daily plan, focus mode, Bitrix24 tasks and smart-process projects.
EOF

  cat > "$deb_root/DEBIAN/preinst" <<EOF
#!/bin/sh
set -e
PKG_NAME="${LINUX_PKG_PACKAGE_NAME}"
NEW_VERSION="${LINUX_PKG_VERSION}"
is_installed() { dpkg-query -W -f='\${Status}' "\$PKG_NAME" 2>/dev/null | grep -q "install ok installed"; }
installed_version() { dpkg-query -W -f='\${Version}' "\$PKG_NAME" 2>/dev/null; }
reject_downgrade() {
  old_version="\$1"
  if [ -z "\$old_version" ]; then return 0; fi
  if dpkg --compare-versions "\$NEW_VERSION" lt "\$old_version"; then
    echo "Ошибка: уже установлена более новая версия \$PKG_NAME (\$old_version)." >&2
    exit 1
  fi
}
case "\$1" in
  install) is_installed && reject_downgrade "\$(installed_version)" ;;
  upgrade) reject_downgrade "\$2" ;;
esac
exit 0
EOF
  chmod 755 "$deb_root/DEBIAN/preinst"

  cat > "$deb_root/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q /usr/share/applications 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q /usr/share/icons/hicolor 2>/dev/null || true
fi
exit 0
EOF
  chmod 755 "$deb_root/DEBIAN/postinst"

  cat > "$deb_root/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
  if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications 2>/dev/null || true
  fi
  if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor 2>/dev/null || true
  fi
fi
exit 0
EOF
  chmod 755 "$deb_root/DEBIAN/postrm"

  mkdir -p "$LINUX_PKG_DIST_DIR"
  rm -f "$deb_out"
  dpkg-deb --build --root-owner-group "$deb_root" "$deb_out"
  rm -rf "$deb_root"

  echo "Готово: $deb_out"
  ls -lh "$deb_out"
  dpkg-deb -I "$deb_out" | grep -E '^( Package| Version| Architecture| Installed-Size| Maintainer):'
}

linux_pkg_build_rpm() {
  if ! command -v rpmbuild >/dev/null 2>&1; then
    echo "Установите rpmbuild: sudo apt install rpm" >&2
    return 1
  fi

  local rpm_top
  rpm_top="$(mktemp -d)"
  local rpm_out="${LINUX_PKG_DIST_DIR}/${LINUX_PKG_PACKAGE_NAME}-${LINUX_PKG_VERSION}-${LINUX_PKG_TARGET_ARCH}.rpm"

  mkdir -p "$rpm_top"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
  cp "$LINUX_PKG_PACKAGING_DIR/tasktimer-link-b24.spec" "$rpm_top/SPECS/${LINUX_PKG_PACKAGE_NAME}.spec"

  rpmbuild -bb \
    --define "_topdir $rpm_top" \
    --define "package_version $LINUX_PKG_VERSION" \
    --define "staging_dir $LINUX_PKG_STAGING" \
    --define "package_title $LINUX_PKG_PACKAGE_TITLE" \
    --define "debug_package %{nil}" \
    --define "_build_id_links none" \
    "$rpm_top/SPECS/${LINUX_PKG_PACKAGE_NAME}.spec"

  local built_rpm
  built_rpm="$(find "$rpm_top/RPMS" -name '*.rpm' -print -quit)"
  if [[ -z "$built_rpm" ]]; then
    echo "RPM не создан в $rpm_top/RPMS" >&2
    rm -rf "$rpm_top"
    return 1
  fi

  mkdir -p "$LINUX_PKG_DIST_DIR"
  rm -f "$rpm_out"
  cp "$built_rpm" "$rpm_out"
  rm -rf "$rpm_top"

  echo "Готово: $rpm_out"
  ls -lh "$rpm_out"
}

linux_pkg_build_tarballs() {
  local bundle_name="${LINUX_PKG_PACKAGE_NAME}-${LINUX_PKG_VERSION}-linux-amd64"
  local bundle_root
  bundle_root="$(mktemp -d)"
  local bundle_dir="$bundle_root/$bundle_name"

  mkdir -p "$bundle_dir"
  cp -a "$LINUX_PKG_STAGING/." "$bundle_dir/"
  linux_pkg_write_install_txt "$bundle_dir"

  mkdir -p "$LINUX_PKG_DIST_DIR"
  local tar_xz_out="${LINUX_PKG_DIST_DIR}/${bundle_name}.tar.xz"
  local tgz_out="${LINUX_PKG_DIST_DIR}/${bundle_name}.tgz"

  rm -f "$tar_xz_out" "$tgz_out"
  tar -cJf "$tar_xz_out" -C "$bundle_root" "$bundle_name"
  tar -czf "$tgz_out" -C "$bundle_root" "$bundle_name"
  rm -rf "$bundle_root"

  echo "Готово: $tar_xz_out"
  ls -lh "$tar_xz_out"
  echo "Готово: $tgz_out"
  ls -lh "$tgz_out"
}

linux_pkg_format_enabled() {
  local format="$1"
  local formats="${FORMATS:-deb}"
  local item
  IFS=',' read -ra _linux_pkg_format_list <<< "$formats"
  for item in "${_linux_pkg_format_list[@]}"; do
    item="${item// /}"
    if [[ "$item" == "$format" ]]; then
      return 0
    fi
  done
  return 1
}
