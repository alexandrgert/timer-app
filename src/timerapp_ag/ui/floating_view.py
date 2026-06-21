from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from ..controller import format_duration
from ..models import Task, TaskStatus


@dataclass(frozen=True)
class FloatingView:
    title: str
    time_text: str
    running: bool
    is_focus: bool


def resolve_floating_task(
    *,
    active: Task | None,
    tracked_task_id: str | None,
    find_task: Callable[[str], Task],
    panel_task: Task | None = None,
) -> tuple[Task | None, str | None]:
    """Running/paused task for mini-widget and tray tooltip (active → tracked → panel)."""
    if active is not None:
        return active, active.id
    if tracked_task_id is not None:
        try:
            task = find_task(tracked_task_id)
        except KeyError:
            task = None
        else:
            if task.status == TaskStatus.COMPLETED:
                pass
            elif task.status in (TaskStatus.RUNNING, TaskStatus.PAUSED):
                return task, tracked_task_id
    if panel_task is not None and panel_task.status in (TaskStatus.RUNNING, TaskStatus.PAUSED):
        return panel_task, panel_task.id
    return None, None


def resolve_floating_view(
    *,
    focus_remaining_seconds: int,
    focus_session_task_id: str | None,
    find_task: Callable[[str], Task],
    floating_task: Task | None,
    now: datetime | None = None,
) -> FloatingView | None:
    """Mini-widget content: focus countdown takes priority over task timer."""
    if focus_remaining_seconds > 0:
        title = "Режим концентрации"
        if focus_session_task_id:
            try:
                title = find_task(focus_session_task_id).title
            except KeyError:
                pass
        return FloatingView(
            title=title,
            time_text=format_duration(focus_remaining_seconds),
            running=True,
            is_focus=True,
        )
    if floating_task is None:
        return None
    now = now or datetime.now()
    running = (
        floating_task.status == TaskStatus.RUNNING
        and floating_task.active_session() is not None
    )
    return FloatingView(
        title=floating_task.title,
        time_text=format_duration(floating_task.total_seconds(now)),
        running=running,
        is_focus=False,
    )
