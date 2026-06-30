from __future__ import annotations

import os
import time

import pytest

from timerapp_ag.domain.formatting import format_task_datetime


@pytest.fixture
def europe_moscow_tz(monkeypatch: pytest.MonkeyPatch) -> None:
    """????????? TZ: format_task_datetime ?????????? ????? ? ????????? ????."""
    monkeypatch.setenv("TZ", "Europe/Moscow")
    if hasattr(time, "tzset"):
        time.tzset()


def test_format_task_datetime_from_iso(europe_moscow_tz: None) -> None:
    assert format_task_datetime("2026-06-28T20:31:00+03:00") == "28.06.2026 20:31"


def test_format_task_datetime_empty() -> None:
    dash = "\u2014"
    assert format_task_datetime(None) == dash
    assert format_task_datetime("") == dash
