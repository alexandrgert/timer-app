#!/usr/bin/env python3
"""Merge upstream MainWindow UI methods into timerapp_ag/main_window.py."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "timer-app/win_timer_app/main_window.py"
TARGET = ROOT / "src/timerapp_ag/main_window.py"

METHODS = [
    "_build_ui",
    "_build_sidebar",
    "_set_page",
    "_build_tasks_page",
    "_build_timer_panel",
    "_build_focus_page",
    "_apply_styles",
    "refresh_ui",
    "_empty_hint",
    "_set_timer_running",
    "_refresh_active_panel",
    "_refresh_focus_panel",
    "_set_focus_done",
]

CHECK_ICON = '''
_CHECK_ICON_PATH: str | None = None


def _check_icon_path() -> str:
    """Draw a white checkmark PNG once (for the QCheckBox checked indicator)."""
    global _CHECK_ICON_PATH
    if _CHECK_ICON_PATH:
        return _CHECK_ICON_PATH
    import os
    import tempfile

    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QColor, QPainter, QPen, QPixmap

    path = os.path.join(tempfile.gettempdir(), "tasktimer_check.png")
    scale = 4
    pixmap = QPixmap(16 * scale, 16 * scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(scale, scale)
    pen = QPen(QColor("#FFFFFF"))
    pen.setWidthF(2.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.drawPolyline([QPointF(4, 8.4), QPointF(7, 11.2), QPointF(12, 5)])
    painter.end()
    pixmap.save(path, "PNG")
    _CHECK_ICON_PATH = path
    return path


'''

MENU_BAR_QSS = """
            /* ── Menu bar (link B24) ──────────────────────── */
            QMenuBar {
                background: #F2F3F7; color: #252835; padding: 4px 10px; spacing: 4px;
            }
            QMenuBar::item {
                background: transparent; padding: 6px 12px; border-radius: 8px;
            }
            QMenuBar::item:selected { background: rgba(37, 40, 53, 0.08); }
            QMenu {
                background: #FFFFFF; border: 1px solid rgba(37, 40, 53, 0.12);
                border-radius: 10px; padding: 4px;
            }
            QMenu::item { padding: 8px 24px 8px 12px; border-radius: 6px; }
            QMenu::item:selected { background: rgba(37, 40, 53, 0.08); }
"""


def already_migrated(source: str) -> bool:
    return "    def _build_sidebar(self)" in source and "QStackedWidget" in source


def extract_method(source: str, name: str) -> str:
    pattern = rf"    def {re.escape(name)}\b.*?(?=\n    def |\nclass |\Z)"
    match = re.search(pattern, source, re.DOTALL)
    if not match:
        raise RuntimeError(f"Method {name} not found in upstream")
    return match.group(0).rstrip() + "\n"


def replace_or_insert_after(target: str, anchor: str, name: str, new_body: str) -> str:
    pattern = rf"    def {re.escape(name)}\b.*?(?=\n    def |\nclass |\Z)"
    if re.search(pattern, target, re.DOTALL):
        return re.sub(pattern, new_body.rstrip(), target, count=1, flags=re.DOTALL)
    anchor_pattern = rf"(    def {re.escape(anchor)}\b.*?(?=\n    def |\nclass |\Z))"
    match = re.search(anchor_pattern, target, re.DOTALL)
    if not match:
        raise RuntimeError(f"Anchor {anchor} not found for inserting {name}")
    insert_at = match.end()
    return target[:insert_at] + "\n" + new_body.rstrip() + target[insert_at:]


def normalize_string_literals(source: str) -> str:
    source = re.sub(
        r'setText\("([^"]*)\n([^"]*)"\)',
        lambda m: f'setText("{m.group(1)}\\n{m.group(2)}")',
        source,
    )
    return re.sub(
        r'QLabel\("([^"]*)\n([^"]*)"\)',
        lambda m: f'QLabel("{m.group(1)}\\n{m.group(2)}")',
        source,
    )


def merge_upstream(target: str, upstream: str) -> str:
    if "_check_icon_path" not in target:
        target = target.replace("\n_ICON_CACHE:", CHECK_ICON + "_ICON_CACHE:", 1)

    if "QStackedWidget" not in target:
        target = target.replace(
            "    QSpinBox,\n    QStyle,",
            "    QSpinBox,\n    QStackedWidget,\n    QStyle,",
            1,
        )

    target = target.replace(
        """        self._sans_family = "Segoe UI"
        self._mono_family = "Consolas"
        self._build_ui()
        self._build_menu_bar()
        self._build_tray()
        self._load_fonts()
        self._apply_styles()""",
        """        self._load_fonts()
        self._build_ui()
        self._build_menu_bar()
        self._build_tray()
        self._apply_styles()""",
        1,
    )

    prev = "_load_fonts"
    for name in METHODS:
        body = extract_method(upstream, name)
        if name == "_apply_styles":
            body = body.replace(
                '            /* ── Dialogs ──────────────────────────────────── */',
                MENU_BAR_QSS + '            /* ── Dialogs ──────────────────────────────────── */',
                1,
            )
        if name == "_empty_hint":
            body = body.replace(
                '        return "Пока нет задач."\n        self._refresh_focus_panel()',
                '        return "Пока нет задач."',
                1,
            )
        if name == "refresh_ui":
            body = body.replace(
                "        self._refresh_active_panel()\n",
                "        self._refresh_active_panel()\n        self._refresh_focus_panel()\n",
                1,
            )
        target = replace_or_insert_after(target, prev, name, body)
        prev = name

    target = normalize_string_literals(target)

    for obsolete in ("_build_settings_button", "_build_tasks_tab", "_build_focus_tab"):
        pattern = rf"    def {re.escape(obsolete)}\b.*?(?=\n    def |\nclass |\Z)"
        target = re.sub(pattern, "", target, count=1, flags=re.DOTALL)

    return target


def validate_python(source: str, path: Path) -> None:
    compile(source, str(path), "exec")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-apply upstream methods even if sidebar layout is already present",
    )
    args = parser.parse_args(argv)

    if not UPSTREAM.is_file():
        print(f"Upstream not found: {UPSTREAM}", file=sys.stderr)
        return 1

    upstream = UPSTREAM.read_text(encoding="utf-8")
    target = TARGET.read_text(encoding="utf-8")

    if already_migrated(target) and not args.force:
        print(
            f"Skip: {TARGET} already has upstream sidebar UI. "
            "Pass --force to re-apply.",
            file=sys.stderr,
        )
        return 0

    merged = merge_upstream(target, upstream)
    validate_python(merged, TARGET)
    TARGET.write_text(merged, encoding="utf-8")
    print(f"Updated {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
