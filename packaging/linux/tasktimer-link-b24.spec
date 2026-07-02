Name:           tasktimer-link-b24
Version:        %{package_version}
Release:        1%{?dist}
Summary:        %{package_title}
License:        Proprietary
URL:            https://github.com/alexandrgert/timer-app
BuildArch:      x86_64
AutoReqProv:    no
Requires:       glibc >= 2.31
Requires:       libglib-2.0.so.0
Requires:       libX11.so.6
Requires:       libxcb.so.1
Requires:       libxkbcommon.so.0
Requires:       libdbus-1.so.3
Requires:       libfontconfig.so.1
Requires:       libfreetype.so.6
Requires:       libGL.so.1
Requires:       libEGL.so.1
Conflicts:      tasktimer
Obsoletes:      tasktimer

%description
Desktop task timer: daily plan, focus mode, Bitrix24 tasks and smart-process projects.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
cp -a %{staging_dir}/. %{buildroot}/

%pre
if rpm -q tasktimer-link-b24 >/dev/null 2>&1; then
  OLD_VERSION="$(rpm -q --qf '%%{VERSION}' tasktimer-link-b24)"
  NEW_VERSION="%{package_version}"
  if [ -n "$OLD_VERSION" ] && [ "$(printf '%s\n' "$OLD_VERSION" "$NEW_VERSION" | sort -V | head -n1)" = "$NEW_VERSION" ] && [ "$OLD_VERSION" != "$NEW_VERSION" ]; then
    echo "Ошибка: уже установлена более новая версия tasktimer-link-b24 ($OLD_VERSION)." >&2
    exit 1
  fi
fi

%post
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q /usr/share/applications 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q /usr/share/icons/hicolor 2>/dev/null || true
fi

%postun
if [ "$1" -eq 0 ]; then
  if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications 2>/dev/null || true
  fi
  if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor 2>/dev/null || true
  fi
fi

%files
/opt/tasktimer-link-b24
/usr/bin/tasktimer-link-b24
/usr/share/applications/tasktimer-link-b24.desktop
/usr/share/icons/hicolor/scalable/apps/tasktimer-link-b24.svg
