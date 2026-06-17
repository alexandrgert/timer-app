from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication, QStackedWidget

from timerapp_ag.controller import AppController
from timerapp_ag.domain import queries
from timerapp_ag.domain.formatting import format_hm
from timerapp_ag.main_window import MainWindow, TaskRow
from timerapp_ag.models import Task

@pytest.fixture
def main_window(
    qapp: QApplication, controller: AppController, monkeypatch: pytest.MonkeyPatch
) -> MainWindow:
    monkeypatch.setattr("timerapp_ag.main_window.QTimer.singleShot", lambda *args, **kwargs: None)
    window = MainWindow(controller, qapp)
    yield window
    window.close()


def test_main_window_has_sidebar_and_stacked_pages(main_window: MainWindow) -> None:
    assert isinstance(main_window.pages, QStackedWidget)
    assert main_window.pages.count() == 2
    assert len(main_window._nav_buttons) == 2
    assert set(main_window._view_buttons) == {"plan", "in_progress", "all"}


def test_main_window_timer_panel_widgets_exist(main_window: MainWindow) -> None:
    assert main_window.timer_digits is not None
    assert main_window.timer_today_value is not None
    assert main_window.timer_total_value is not None
    assert main_window.stop_active_button is not None
    assert main_window.complete_active_button is not None


def test_show_startup_notices_uses_tray_without_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _StubTray:
        def isVisible(self) -> bool:
            return True

    class _StubController:
        webdav_startup_notice = "WebDAV: синхронизировано"

    window = MainWindow.__new__(MainWindow)
    window.controller = _StubController()  # type: ignore[assignment]
    window.tray_available = True
    window.tray = _StubTray()  # type: ignore[assignment]
    shown: list[int] = []
    dialogs: list[int] = []
    window._show_tray_message = lambda *args, **kwargs: shown.append(1)  # type: ignore[method-assign]
    monkeypatch.setattr(
        "timerapp_ag.main_window.QMessageBox.information",
        lambda *args, **kwargs: dialogs.append(1),
    )
    monkeypatch.setattr("timerapp_ag.main_window.clear_webdav_pending_notice", lambda: None)

    MainWindow._show_startup_notices(window)

    assert shown == [1]
    assert dialogs == []
    assert window.controller.webdav_startup_notice is None


def test_timer_panel_task_prefers_running_over_paused(controller: AppController) -> None:
    first = controller.create_task("First", start_now=True)
    controller.stop_task(first.id)
    second = controller.create_task("Second", start_now=True)

    assert queries.timer_panel_task(controller.state) is not None
    assert queries.timer_panel_task(controller.state).id == second.id

    controller.stop_task(second.id)
    panel = queries.timer_panel_task(controller.state)
    assert panel is not None
    assert panel.id == second.id


def test_timer_panel_shows_paused_task(
    main_window: MainWindow, controller: AppController
) -> None:
    task = controller.create_task("Paused work", start_now=True)
    controller.stop_task(task.id)
    main_window.refresh_ui()

    assert controller.timer_panel_task() is not None
    assert main_window.active_task_name.text() == "Paused work"
    assert main_window.stop_active_button.text() == "Продолжить"
    assert main_window.stop_active_button.isEnabled()
    assert not main_window.timer_panel.property("running")


def test_task_row_update_times_refreshes_labels(
    qapp: QApplication, controller: AppController, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = controller.create_task("Tick", start_now=True)
    row = TaskRow(controller, task)
    seconds = iter([100, 160])
    monkeypatch.setattr(controller, "today_seconds", lambda _task, _day=None: next(seconds))
    total = iter([500, 560])
    monkeypatch.setattr(
        Task,
        "total_seconds",
        lambda self, now=None: next(total),
    )

    row.update_times(controller, task)
    assert row._today_value.text() == format_hm(100)
    assert row._total_value.text() == format_hm(500)

    row.update_times(controller, task)
    assert row._today_value.text() == format_hm(160)
    assert row._total_value.text() == format_hm(560)


def test_update_task_row_times_called_from_tick(
    main_window: MainWindow, controller: AppController, monkeypatch: pytest.MonkeyPatch
) -> None:
    controller.create_task("Live", start_now=True)
    main_window.refresh_ui()
    calls: list[int] = []
    monkeypatch.setattr(
        main_window,
        "_update_task_row_times",
        lambda: calls.append(1),
    )
    main_window._tick()
    assert calls == [1]


def test_floating_close_hides_widget_until_tray_show(
    main_window: MainWindow, controller: AppController
) -> None:
    task = controller.create_task("Tray task", start_now=True)
    main_window._track_floating_task(task.id)
    main_window._show_floating()
    assert main_window.floating.isVisible()

    main_window._floating_close()
    assert not main_window.floating.isVisible()
    assert main_window._floating_user_dismissed

    main_window._show_floating()
    assert not main_window.floating.isVisible()

    main_window._show_floating_from_tray()
    assert main_window.floating.isVisible()
    assert not main_window._floating_user_dismissed
