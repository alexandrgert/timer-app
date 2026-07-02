#!/usr/bin/env bash
# Дополнительные Linux-форматы для CI / GitHub Releases (не для локальной сборки по умолчанию).
set -euo pipefail

linux_pkg_create_appdir() {
  local appdir
  appdir="$(mktemp -d)/TaskTimerLinkB24.AppDir"
  cp -a "$LINUX_PKG_STAGING/." "$appdir/"

  cp "$appdir/usr/share/applications/tasktimer-link-b24.desktop" "$appdir/tasktimer-link-b24.desktop"
  sed -i 's/^Exec=.*/Exec=AppRun/' "$appdir/tasktimer-link-b24.desktop"
  cp "$appdir/usr/share/icons/hicolor/scalable/apps/tasktimer-link-b24.svg" "$appdir/tasktimer-link-b24.svg"

  cat > "$appdir/AppRun" <<'EOF'
#!/bin/sh
APPDIR="$(dirname "$(readlink -f "$0")")"
export LD_LIBRARY_PATH="${APPDIR}/opt/tasktimer-link-b24:${APPDIR}/opt/tasktimer-link-b24/_internal:${LD_LIBRARY_PATH:-}"
exec "${APPDIR}/opt/tasktimer-link-b24/TaskTimer" "$@"
EOF
  chmod 755 "$appdir/AppRun"
  printf '%s\n' "$appdir"
}

linux_pkg_ensure_appimagetool() {
  if [[ -n "${APPIMAGETOOL:-}" && -x "${APPIMAGETOOL}" ]]; then
    printf '%s\n' "$APPIMAGETOOL"
    return 0
  fi

  local cache_dir="${LINUX_PKG_PROJECT_DIR}/.cache"
  local tool="${cache_dir}/appimagetool-x86_64.AppImage"
  if [[ ! -f "$tool" ]]; then
    mkdir -p "$cache_dir"
    curl -fsSL \
      "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" \
      -o "$tool"
    chmod +x "$tool"
  fi
  printf '%s\n' "$tool"
}

linux_pkg_build_ebuild() {
  local ebuild_out="${LINUX_PKG_DIST_DIR}/${LINUX_PKG_PACKAGE_NAME}-${LINUX_PKG_VERSION}.ebuild"
  mkdir -p "$LINUX_PKG_DIST_DIR"
  rm -f "$ebuild_out"
  cat > "$ebuild_out" <<EOF
# Copyright 1999-$(date +%Y) Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8

DESCRIPTION="${LINUX_PKG_PACKAGE_TITLE} — desktop task timer with Bitrix24 integration"
HOMEPAGE="https://github.com/alexandrgert/timer-app"
SRC_URI="https://github.com/alexandrgert/timer-app/releases/download/v\${PV}/${LINUX_PKG_PACKAGE_NAME}-\${PV}-linux-amd64.tar.xz"

S="\${WORKDIR}/${LINUX_PKG_PACKAGE_NAME}-\${PV}-linux-amd64"

LICENSE="all-rights-reserved"
SLOT=0
KEYWORDS="~amd64"

RDEPEND="
	>=sys-libs/glibc-2.31
	dev-libs/glib
	x11-libs/libX11
	x11-libs/libxcb
	x11-libs/libxkbcommon
	sys-apps/dbus
	media-libs/mesa
	media-libs/fontconfig
	media-libs/freetype
	media-libs/libglvnd
	tiff? ( media-libs/tiff )
"

src_install() {
	cp -a opt usr "\${D}" || die
}
EOF
  echo "Готово: $ebuild_out"
  ls -lh "$ebuild_out"
}

linux_pkg_build_pisi() {
  local work_dir pisi_out files_archive
  work_dir="$(mktemp -d)"
  pisi_out="${LINUX_PKG_DIST_DIR}/${LINUX_PKG_PACKAGE_NAME}-${LINUX_PKG_VERSION}-x86_64.pisi"
  files_archive="$work_dir/files.tar.lzma"

  ( cd "$LINUX_PKG_STAGING" && tar cf - . | lzma -9 >"$files_archive" )

  cat > "$work_dir/pspec.xml" <<EOF
<PISI>
  <Source>
    <Name>${LINUX_PKG_PACKAGE_NAME}</Name>
    <Homepage>https://github.com/alexandrgert/timer-app</Homepage>
    <Packager>
      <Name>alexandrgert</Name>
      <Email>alexandrgert@gmail.com</Email>
    </Packager>
    <Summary>${LINUX_PKG_PACKAGE_TITLE}</Summary>
    <Description>Desktop task timer with Bitrix24 integration and WebDAV sync.</Description>
    <License>Proprietary</License>
    <IsA>app:gui</IsA>
    <Archive sha1sum="0000000000000000000000000000000000000000" type="binary">files.tar.lzma</Archive>
    <BuildDependencies/>
    <RuntimeDependencies>
      <Dependency>libX11</Dependency>
      <Dependency>libxcb</Dependency>
      <Dependency>libxkbcommon</Dependency>
      <Dependency>dbus-glib</Dependency>
      <Dependency>mesa</Dependency>
      <Dependency>fontconfig</Dependency>
      <Dependency>freetype</Dependency>
    </RuntimeDependencies>
  </Source>
  <Package>
    <Name>${LINUX_PKG_PACKAGE_NAME}</Name>
    <Summary>${LINUX_PKG_PACKAGE_TITLE}</Summary>
    <Description>Desktop task timer with Bitrix24 integration and WebDAV sync.</Description>
    <Files>
      <Path fileType="executable">/usr/bin/${LINUX_PKG_BIN_NAME}</Path>
      <Path fileType="executable">/opt/tasktimer-link-b24/TaskTimer</Path>
      <Path fileType="data">/opt/tasktimer-link-b24</Path>
      <Path fileType="data">/usr/share/applications/tasktimer-link-b24.desktop</Path>
      <Path fileType="data">/usr/share/icons/hicolor/scalable/apps/tasktimer-link-b24.svg</Path>
    </Files>
  </Package>
  <History>
    <Update release="${LINUX_PKG_VERSION}">
      <Date>$(date +%Y-%m-%d)</Date>
      <Version>${LINUX_PKG_VERSION}</Version>
      <Comment>Release ${LINUX_PKG_VERSION}</Comment>
    </Update>
  </History>
</PISI>
EOF

  mkdir -p "$LINUX_PKG_DIST_DIR"
  rm -f "$pisi_out"
  ( cd "$work_dir" && tar cf - pspec.xml files.tar.lzma | lzma -9 >"$pisi_out" )
  rm -rf "$work_dir"

  echo "Готово: $pisi_out"
  ls -lh "$pisi_out"
}

linux_pkg_build_pet() {
  local pet_root pet_out
  pet_root="$(mktemp -d)/pet"
  mkdir -p "$pet_root"
  cp -a "$LINUX_PKG_STAGING/." "$pet_root/"

  cat > "$pet_root/pet.spec" <<EOF
pkgname='${LINUX_PKG_PACKAGE_NAME}'
package_version='${LINUX_PKG_VERSION}'
provider='alexandrgert'
category='Office'
description='${LINUX_PKG_PACKAGE_TITLE}'
EOF

  mkdir -p "$LINUX_PKG_DIST_DIR"
  pet_out="${LINUX_PKG_DIST_DIR}/${LINUX_PKG_PACKAGE_NAME}-${LINUX_PKG_VERSION}-amd64.pet"
  rm -f "$pet_out"
  tar -czf "$pet_out" -C "$pet_root" .
  rm -rf "$(dirname "$pet_root")"

  echo "Готово: $pet_out"
  ls -lh "$pet_out"
}

linux_pkg_build_pup() {
  local pup_root pup_out
  pup_root="$(mktemp -d)/pup"
  mkdir -p "$pup_root"
  cp -a "$LINUX_PKG_STAGING/." "$pup_root/"

  cat > "$pup_root/pup.spec" <<EOF
name=${LINUX_PKG_PACKAGE_NAME}
version=${LINUX_PKG_VERSION}
description=${LINUX_PKG_PACKAGE_TITLE}
author=alexandrgert
EOF

  mkdir -p "$LINUX_PKG_DIST_DIR"
  pup_out="${LINUX_PKG_DIST_DIR}/${LINUX_PKG_PACKAGE_NAME}-${LINUX_PKG_VERSION}-amd64.pup"
  rm -f "$pup_out"
  tar -czf "$pup_out" -C "$pup_root" .
  rm -rf "$(dirname "$pup_root")"

  echo "Готово: $pup_out"
  ls -lh "$pup_out"
}

linux_pkg_build_lzm() {
  local module_dir lzm_out
  module_dir="$(mktemp -d)/module"
  mkdir -p "$module_dir"
  cp -a "$LINUX_PKG_STAGING/." "$module_dir/"

  mkdir -p "$LINUX_PKG_DIST_DIR"
  lzm_out="${LINUX_PKG_DIST_DIR}/${LINUX_PKG_PACKAGE_NAME}-${LINUX_PKG_VERSION}-amd64.lzm"
  rm -f "$lzm_out"
  ( cd "$module_dir" && tar cf - . | lzma -9 >"$lzm_out" )
  rm -rf "$module_dir"

  echo "Готово: $lzm_out"
  ls -lh "$lzm_out"
}

linux_pkg_build_appimage() {
  if ! command -v lzma >/dev/null 2>&1; then
    echo "Для AppImage нужен lzma (xz-utils)." >&2
    return 1
  fi

  local appdir appimagetool out
  appdir="$(linux_pkg_create_appdir)"
  appimagetool="$(linux_pkg_ensure_appimagetool)"
  out="${LINUX_PKG_DIST_DIR}/${LINUX_PKG_PACKAGE_NAME}-${LINUX_PKG_VERSION}-amd64.AppImage"
  mkdir -p "$LINUX_PKG_DIST_DIR"
  rm -f "$out"

  export ARCH=x86_64
  export VERSION="${LINUX_PKG_VERSION}"
  APPIMAGE_EXTRACT_AND_RUN=1 "$appimagetool" "$appdir" "$out"

  echo "Готово: $out"
  ls -lh "$out"
}

linux_pkg_build_flatpak() {
  if ! command -v flatpak-builder >/dev/null 2>&1; then
    echo "Установите flatpak-builder." >&2
    return 1
  fi

  local user_flag=""
  if flatpak info org.freedesktop.Platform//23.08 >/dev/null 2>&1; then
    user_flag=""
  elif flatpak info --user org.freedesktop.Platform//23.08 >/dev/null 2>&1; then
    user_flag="--user"
  else
    echo "Flatpak runtime org.freedesktop.Platform//23.08 не установлен." >&2
    return 1
  fi

  local build_root manifest_dir repo out
  build_root="$(mktemp -d)"
  manifest_dir="$LINUX_PKG_PROJECT_DIR/packaging/flatpak"
  repo="$build_root/repo"
  out="${LINUX_PKG_DIST_DIR}/${LINUX_PKG_PACKAGE_NAME}-${LINUX_PKG_VERSION}-amd64.flatpak"

  cp -a "$LINUX_PKG_STAGING" "$build_root/staging"
  cp "$manifest_dir/com.timerapp.LinkB24.yml" "$build_root/manifest.yml"

  # shellcheck disable=SC2086
  flatpak-builder --force-clean $user_flag --repo="$repo" "$build_root/build" "$build_root/manifest.yml"
  # shellcheck disable=SC2086
  flatpak build-bundle $user_flag "$repo" "$out" com.timerapp.LinkB24

  rm -rf "$build_root"
  echo "Готово: $out"
  ls -lh "$out"
}

linux_pkg_build_snap() {
  if ! command -v snapcraft >/dev/null 2>&1; then
    echo "Установите snapcraft." >&2
    return 1
  fi

  local snap_dir snap_build out
  snap_dir="$LINUX_PKG_PROJECT_DIR/packaging/snap"
  snap_build="$(mktemp -d)"
  out="${LINUX_PKG_DIST_DIR}/${LINUX_PKG_PACKAGE_NAME}_${LINUX_PKG_VERSION}_amd64.snap"

  cp -a "$LINUX_PKG_STAGING/." "$snap_build/root/"
  sed "s/@VERSION@/${LINUX_PKG_VERSION}/g" "$snap_dir/snapcraft.yaml" >"$snap_build/snapcraft.yaml"

  mkdir -p "$LINUX_PKG_DIST_DIR"
  rm -f "$out"
  export SNAPCRAFT_BUILD_ENVIRONMENT=host
  ( cd "$snap_build" && snapcraft pack --destructive-mode --output "$out" )
  rm -rf "$snap_build"

  echo "Готово: $out"
  ls -lh "$out"
}
