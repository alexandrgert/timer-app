from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from timerapp_ag.bitrix import seconds_to_worklog_hours
from timerapp_ag.bitrix_config import BitrixPortalConfig, discover_worklog_config
from timerapp_ag.bitrix_transfer_journal import (
    apply_transfer_journal,
    journal_path,
    record_transfer_result,
    remove_transfer_result,
)
from timerapp_ag.controller import AppController
from timerapp_ag.domain import queries
from timerapp_ag.models import Session, Task, TaskStatus


def test_seconds_to_worklog_hours_never_zero_for_short_work() -> None:
    assert seconds_to_worklog_hours(10) == 0.01
    assert seconds_to_worklog_hours(3600) == 1.0
    assert seconds_to_worklog_hours(5400) == 1.5


def test_discover_worklog_config_matches_parent_and_custom_fields() -> None:
    types = [
        {"entityTypeId": 150, "title": "Реестр проектов"},
        {"entityTypeId": 1092, "title": "Журнал работ"},
    ]

    def list_fields(entity_type_id: int) -> dict:
        if entity_type_id == 1092:
            return {
                "fields": {
                    "parentId150": {"title": "Проект"},
                    "ufCrm99HoursWork": {"title": "Часы работы"},
                    "ufCrm99CommentWork": {"title": "Комментарий"},
                    "ufCrm99DateWork": {"title": "Дата работы"},
                }
            }
        return {"fields": {}}

    entity_type_id, parent, hours, comment, date = discover_worklog_config(
        list_types=lambda: types,
        list_fields=list_fields,
        projects_entity_type_id=150,
    )
    assert entity_type_id == 1092
    assert parent == "parentId150"
    assert hours == "ufCrm99HoursWork"
    assert comment == "ufCrm99CommentWork"
    assert date == "ufCrm99DateWork"


def test_add_project_time_uses_portal_config_fields() -> None:
    from timerapp_ag.bitrix import Bitrix24Client

    captured = {}

    def poster(url, method, payload):
        captured.update(method=method, payload=payload)
        return {"item": {"id": 42}}

    config = BitrixPortalConfig(
        worklog_entity_type_id=2001,
        worklog_parent_field="parentId177",
        worklog_hours_field="ufHours",
        worklog_comment_field="ufComment",
        worklog_date_field="ufDate",
    )
    client = Bitrix24Client(
        "https://acme.bitrix24.ru/rest/1/abc/",
        portal_config=config,
        post_func=poster,
    )
    record_id = client.add_project_time("99", "2026-06-11", 0.25, "Work", 3)
    assert record_id == "42"
    assert captured["payload"]["entityTypeId"] == 2001
    fields = captured["payload"]["fields"]
    assert fields["parentId177"] == 99
    assert fields["ufHours"] == 0.25
    assert fields["ufComment"] == "Work"
    assert fields["ufDate"] == "2026-06-11"


def test_transfer_journal_recovers_after_interrupt(storage) -> None:
    controller = AppController(storage)
    task = controller.create_task("T")
    controller.add_session(
        task.id,
        datetime(2026, 6, 11, 9, 0),
        datetime(2026, 6, 11, 10, 0),
    )
    task = controller.find_task(task.id)
    session_id = task.sessions[0].id
    record_transfer_result(storage, task.id, [session_id], "777")

    fresh = AppController(storage)
    marked = fresh.find_task(task.id).sessions[0]
    assert marked.bitrix_record_id == "777"
    assert not journal_path(storage).exists()


def test_finalize_sessions_transfer_clears_journal(storage) -> None:
    controller = AppController(storage)
    task = controller.create_task("T")
    controller.add_session(
        task.id,
        datetime(2026, 6, 11, 9, 0),
        datetime(2026, 6, 11, 10, 0),
    )
    session_id = controller.find_task(task.id).sessions[0].id
    record_transfer_result(storage, task.id, [session_id], "888")
    controller.mark_sessions_transferred(task.id, [session_id], "888")
    controller.finalize_sessions_transfer(task.id, [session_id], "888")
    assert not journal_path(storage).exists()


def test_timer_panel_task_uses_last_pause_not_earliest_start(controller: AppController) -> None:
    morning = controller.create_task("Morning")
    controller.start_task(morning.id)
    controller.stop_task(morning.id)

    afternoon = controller.create_task("Afternoon")
    controller.start_task(afternoon.id)
    controller.stop_task(afternoon.id)

    panel = queries.timer_panel_task(controller.state)
    assert panel is not None
    assert panel.id == afternoon.id


def test_timer_panel_task_long_morning_short_afternoon_pause(controller: AppController) -> None:
    """Regression: paused task with earlier start but later stop must win."""
    long_task = controller.create_task("Long")
    controller.start_task(long_task.id)
    controller.stop_task(long_task.id)
    long_task = controller.find_task(long_task.id)
    long_task.sessions[0] = Session(
        id=long_task.sessions[0].id,
        started_at=(datetime.now() - timedelta(hours=5)).isoformat(),
        ended_at=(datetime.now() - timedelta(hours=1)).isoformat(),
    )
    long_task.status = TaskStatus.PAUSED
    controller.save()

    short_task = controller.create_task("Short")
    controller.start_task(short_task.id)
    controller.stop_task(short_task.id)

    panel = queries.timer_panel_task(controller.state)
    assert panel is not None
    assert panel.id == short_task.id


def test_apply_transfer_journal_is_idempotent_when_already_marked(storage) -> None:
    controller = AppController(storage)
    task = controller.create_task("T")
    controller.add_session(
        task.id,
        datetime(2026, 6, 11, 9, 0),
        datetime(2026, 6, 11, 10, 0),
    )
    session_id = controller.find_task(task.id).sessions[0].id
    controller.mark_sessions_transferred(task.id, [session_id], "999")
    record_transfer_result(storage, task.id, [session_id], "999")
    applied = apply_transfer_journal(storage, controller.mark_sessions_transferred)
    assert applied == 1
    assert controller.find_task(task.id).sessions[0].bitrix_record_id == "999"
    remove_transfer_result(storage, task.id, [session_id], "999")
    assert not journal_path(storage).exists()
