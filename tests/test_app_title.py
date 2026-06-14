from __future__ import annotations

from pathlib import Path

from timerapp_ag.main import APP_TITLE_BASE, resolve_app_title


def test_resolve_app_title_without_version_file() -> None:
    assert resolve_app_title() == APP_TITLE_BASE


def test_resolve_app_title_reads_version_file(tmp_path: Path, monkeypatch) -> None:
    fake_exe = tmp_path / "TaskTimer"
    fake_exe.write_text("", encoding="utf-8")
    (tmp_path / "VERSION").write_text("0.2.0\n", encoding="utf-8")
    monkeypatch.setattr("timerapp_ag.main.sys.executable", str(fake_exe))

    assert resolve_app_title() == f"{APP_TITLE_BASE} 0.2.0"
