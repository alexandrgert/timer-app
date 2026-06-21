from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QEasingCurve, Qt, QPropertyAnimation, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..controller import AppController, format_day_label, format_hm
from ..models import Task, TaskStatus
from .bitrix_links import bitrix_entity_url
from .icons import draw_stopwatch, draw_trash, line_icon
from .text_layout import (
    TASK_ROW_ACTIONS_OVERLAY_RESERVE,
    TASK_ROW_DESC_HORIZONTAL_INSET,
    TASK_ROW_NAME_MIN_WIDTH,
    TASK_ROW_PINNED_FOOTER_V_PAD,
    break_long_unbroken_runs,
    fit_wrapped_label_height,
)

_STATUS_PROP = {
    TaskStatus.RUNNING: "running",
    TaskStatus.PAUSED: "paused",
    TaskStatus.COMPLETED: "done",
    TaskStatus.OPEN: "todo",
}


class TaskRow(QFrame):
    """Compact task row with expandable description on click."""

    start_requested = Signal(str)
    stop_requested = Signal(str)
    complete_requested = Signal(str)
    resume_requested = Signal(str)
    history_requested = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    plan_toggle_requested = Signal(str)
    row_selected = Signal(str)
    row_deselected = Signal(str)

    def __init__(
        self, controller: AppController, task: Task, reference_date: str | None = None
    ) -> None:
        super().__init__()
        self.setObjectName("taskRow")
        self._task_id = task.id
        self._title = task.title
        self._description = task.description.strip()
        self._pinned = False
        self._is_running = task.status == TaskStatus.RUNNING
        status = _STATUS_PROP.get(task.status, "todo")
        self.setProperty("status", status)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setObjectName("taskRowHeader")
        header.setFixedHeight(48)
        self._header = header
        layout = QHBoxLayout(header)
        self._header_layout = layout
        layout.setContentsMargins(13, 0, 12, 0)
        layout.setSpacing(10)

        dot = QFrame()
        dot.setObjectName("taskDot")
        dot.setProperty("status", status)
        dot.setFixedSize(8, 8)
        layout.addWidget(dot)

        self._name_label = QLabel(task.title)
        self._name_label.setObjectName("taskName")
        self._name_label.setToolTip(task.title)
        self._name_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)
        layout.addWidget(self._name_label, 1)

        reference = reference_date or controller.today_str()
        is_today = reference == controller.today_str()
        self._times_box = QWidget()
        times = QHBoxLayout(self._times_box)
        times.setContentsMargins(0, 0, 0, 0)
        times.setSpacing(4)
        today_label = QLabel("сег." if is_today else format_day_label(reference))
        today_label.setObjectName("rowTimeLbl")
        times.addWidget(today_label)
        today_value = QLabel(format_hm(controller.today_seconds(task, reference)))
        today_value.setObjectName("rowTimeVal")
        today_value.setProperty("live", self._is_running)
        self._today_value = today_value
        times.addWidget(today_value)
        sep = QLabel("·")
        sep.setObjectName("rowTimeSep")
        times.addWidget(sep)
        total_label = QLabel("всего")
        total_label.setObjectName("rowTimeLbl")
        times.addWidget(total_label)
        total_value = QLabel(format_hm(task.total_seconds(datetime.now())))
        total_value.setObjectName("rowTimeVal")
        self._total_value = total_value
        times.addWidget(total_value)
        layout.addWidget(self._times_box)

        self._actions = QWidget()
        self._actions.setObjectName("rowActions")
        actions = QHBoxLayout(self._actions)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(4)

        fade = QFrame()
        fade.setObjectName("rowActionsFade")
        fade.setFixedWidth(26)
        self._actions_fade = fade
        actions.addWidget(fade)
        actions.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        is_done = task.status == TaskStatus.COMPLETED

        edit_button = QPushButton("Изменить")
        edit_button.setObjectName("linkAction")
        edit_button.setToolTip("Изменить название и описание")
        edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_button.clicked.connect(lambda: self.edit_requested.emit(task.id))
        actions.addWidget(edit_button)

        if not is_done:
            history_button = QPushButton()
            history_button.setObjectName("iconAction")
            history_button.setFixedSize(26, 26)
            history_button.setIcon(line_icon("stopwatch", draw_stopwatch))
            history_button.setToolTip("История сессий")
            history_button.setCursor(Qt.CursorShape.PointingHandCursor)
            history_button.clicked.connect(lambda: self.history_requested.emit(task.id))
            actions.addWidget(history_button)

            portal_url = bitrix_entity_url(controller, task.bitrix)
            if portal_url:
                open_button = QPushButton("Открыть в Б24")
                open_button.setObjectName("linkAction")
                open_button.setToolTip("Открыть сущность в Битрикс24")
                open_button.setCursor(Qt.CursorShape.PointingHandCursor)
                open_button.clicked.connect(
                    lambda checked=False, url=portal_url: QDesktopServices.openUrl(QUrl(url))
                )
                actions.addWidget(open_button)

            complete_button = QPushButton("Завершить")
            complete_button.setObjectName("linkAction")
            complete_button.setCursor(Qt.CursorShape.PointingHandCursor)
            complete_button.clicked.connect(lambda: self.complete_requested.emit(task.id))
            actions.addWidget(complete_button)

        in_plan = controller.in_today_plan(task)
        plan_button = QPushButton("Из плана" if in_plan else "В план")
        plan_button.setObjectName("linkAction")
        plan_button.setCursor(Qt.CursorShape.PointingHandCursor)
        plan_button.clicked.connect(lambda: self.plan_toggle_requested.emit(task.id))
        actions.addWidget(plan_button)

        delete_button = QPushButton()
        delete_button.setObjectName("iconActionDanger")
        delete_button.setFixedSize(26, 26)
        delete_button.setIcon(line_icon("trash", draw_trash))
        delete_button.setToolTip("Удалить задачу")
        delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_button.clicked.connect(lambda: self.delete_requested.emit(task.id))
        actions.addWidget(delete_button)

        if is_done:
            resume_button = QPushButton("Возобновить")
            resume_button.setObjectName("rowResume")
            resume_button.setFixedHeight(26)
            resume_button.setCursor(Qt.CursorShape.PointingHandCursor)
            resume_button.clicked.connect(lambda: self.resume_requested.emit(task.id))
            actions.addWidget(resume_button)
        elif self._is_running:
            stop_button = QPushButton("Стоп")
            stop_button.setObjectName("rowStop")
            stop_button.setFixedHeight(26)
            stop_button.setCursor(Qt.CursorShape.PointingHandCursor)
            stop_button.clicked.connect(lambda: self.stop_requested.emit(task.id))
            actions.addWidget(stop_button)
        else:
            start_button = QPushButton("Старт")
            start_button.setObjectName("rowStart")
            start_button.setFixedHeight(26)
            start_button.setCursor(Qt.CursorShape.PointingHandCursor)
            start_button.clicked.connect(lambda: self.start_requested.emit(task.id))
            actions.addWidget(start_button)

        layout.addWidget(self._actions)
        root.addWidget(header)

        self._pinned_footer = QWidget()
        self._pinned_footer.setObjectName("taskRowPinnedFooter")
        self._pinned_footer_layout = QHBoxLayout(self._pinned_footer)
        self._pinned_footer_layout.setContentsMargins(
            31,
            TASK_ROW_PINNED_FOOTER_V_PAD,
            12,
            TASK_ROW_PINNED_FOOTER_V_PAD,
        )
        self._pinned_footer_layout.setSpacing(4)
        root.addWidget(self._pinned_footer)
        self._pinned_footer.hide()

        self._desc_wrap = QWidget()
        self._desc_wrap.setObjectName("taskRowDescWrap")
        desc_layout = QHBoxLayout(self._desc_wrap)
        desc_layout.setContentsMargins(31, 0, 12, 10)
        desc_layout.setSpacing(0)
        self._desc_label = QLabel()
        self._desc_label.setObjectName("taskRowDesc")
        self._desc_label.setWordWrap(True)
        self._desc_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        self._desc_label.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Minimum,
        )
        desc_layout.addWidget(self._desc_label, 1)
        root.addWidget(self._desc_wrap)
        self._desc_wrap.hide()

        self.setFixedHeight(48)

        self._fade_effect = QGraphicsOpacityEffect(self._actions)
        self._fade_effect.setOpacity(1.0 if self._is_running else 0.0)
        self._actions.setGraphicsEffect(self._fade_effect)
        self._actions.setEnabled(self._is_running)
        self._fade_anim = QPropertyAnimation(self._fade_effect, b"opacity", self)
        self._fade_anim.setDuration(150)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._fade_anim.finished.connect(self._on_fade_finished)

        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

    def _content_max_width(self) -> int:
        ancestor = self.parentWidget()
        while ancestor is not None:
            if ancestor.objectName() == "taskListBg":
                return max(ancestor.width() - 40, 200)
            ancestor = ancestor.parentWidget()
        return max(self.width(), 200)

    def _apply_row_width_constraint(self) -> None:
        max_width = self._content_max_width()
        if max_width > 0:
            self.setMaximumWidth(max_width)

    def refresh_layout(self) -> None:
        self._apply_row_width_constraint()
        self._fit_header_layout()
        self._fit_description_layout()
        if self._pinned:
            self._update_pinned_row_height()

    def _title_area_width(self) -> int:
        margins = 25
        dot_block = 18
        times_block = self._times_box.sizeHint().width() + 10
        actions_block = (
            0
            if self._pinned
            else TASK_ROW_ACTIONS_OVERLAY_RESERVE
        )
        return max(
            self._content_max_width() - margins - dot_block - times_block - actions_block,
            TASK_ROW_NAME_MIN_WIDTH,
        )

    def _reset_name_label_constraints(self) -> None:
        self._name_label.setMinimumHeight(0)
        self._name_label.setMaximumHeight(16777215)
        self._name_label.setMinimumWidth(0)
        self._name_label.setMaximumWidth(16777215)

    def _fit_header_layout(self) -> None:
        if self._pinned:
            self._name_label.setWordWrap(True)
            available = self._title_area_width()
            display_text = break_long_unbroken_runs(self._title)
            fit_wrapped_label_height(self._name_label, display_text, width=available)
            self._header.setFixedHeight(max(48, self._name_label.height() + 8))
            return

        self._reset_name_label_constraints()
        self._name_label.setWordWrap(False)
        self._name_label.setMinimumWidth(TASK_ROW_NAME_MIN_WIDTH)
        self._header.setFixedHeight(48)
        width = self._title_area_width()
        if width > 0:
            metrics = self._name_label.fontMetrics()
            elided = metrics.elidedText(self._title, Qt.TextElideMode.ElideRight, width)
            self._name_label.setText(elided)

    def _description_area_width(self) -> int:
        return max(self._content_max_width() - TASK_ROW_DESC_HORIZONTAL_INSET, 120)

    def _relayout_actions_for_pinned(self, pinned: bool) -> None:
        if pinned:
            if self._actions.parentWidget() is self._header:
                self._header_layout.removeWidget(self._actions)
                self._pinned_footer_layout.addWidget(
                    self._actions,
                    1,
                    Qt.AlignmentFlag.AlignVCenter,
                )
            self._actions_fade.hide()
            self._pinned_footer.show()
            self._fade_anim.stop()
            self._fade_effect.setOpacity(1.0)
            self._actions.setEnabled(True)
            return

        self._actions_fade.show()
        if self._actions.parentWidget() is self._pinned_footer:
            self._pinned_footer_layout.removeWidget(self._actions)
            self._header_layout.addWidget(self._actions)
        self._pinned_footer.hide()
        if self._is_running:
            self._fade_effect.setOpacity(1.0)
            self._actions.setEnabled(True)
        else:
            self._fade_effect.setOpacity(0.0)
            self._actions.setEnabled(False)

    def _fit_description_layout(self) -> None:
        if not self._pinned or self._desc_wrap.isHidden():
            return
        available = self._description_area_width()
        self._desc_wrap.setFixedWidth(self._content_max_width())
        if self._description:
            display_text = break_long_unbroken_runs(self._description)
            fit_wrapped_label_height(self._desc_label, display_text, width=available)
        else:
            self._desc_label.setFixedWidth(available)
            self._desc_label.setMaximumWidth(available)
            self._desc_label.setFixedHeight(
                self._desc_label.fontMetrics().lineSpacing()
            )

    def _update_pinned_row_height(self) -> None:
        if not self._pinned:
            self.setFixedHeight(48)
            return
        footer_height = (
            self._pinned_footer.sizeHint().height()
            if self._pinned_footer.isVisible()
            else 0
        )
        self.setFixedHeight(
            self._header.height() + self._desc_wrap.sizeHint().height() + footer_height
        )

    def set_pinned(self, pinned: bool) -> None:
        self._pinned = pinned
        self._sync_description_visible()

    def _sync_description_visible(self) -> None:
        show = self._pinned
        self._relayout_actions_for_pinned(show)
        if show:
            if self._description:
                self._desc_label.setText(break_long_unbroken_runs(self._description))
                self._desc_label.setProperty("empty", False)
            else:
                self._desc_label.setText("Описание не заполнено")
                self._desc_label.setProperty("empty", True)
            self._desc_label.style().unpolish(self._desc_label)
            self._desc_label.style().polish(self._desc_label)
            self._desc_wrap.show()
            self.setMinimumHeight(48)
            self.setMaximumHeight(16777215)
            self.refresh_layout()
        else:
            self._desc_wrap.hide()
            self._fit_header_layout()
            self.setFixedHeight(48)

    def _is_interactive_target(self, pos) -> bool:
        target = self.childAt(pos)
        while target is not None and target is not self:
            if isinstance(target, QPushButton):
                return True
            if target is self._actions:
                return True
            target = target.parentWidget()
        return False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and not self._is_interactive_target(event.position().toPoint())
        ):
            if self._pinned:
                self.row_deselected.emit(self._task_id)
                self.set_pinned(False)
            else:
                self.row_selected.emit(self._task_id)
                self.set_pinned(True)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and not self._is_interactive_target(event.position().toPoint())
        ):
            self.edit_requested.emit(self._task_id)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def update_times(
        self, controller: AppController, task: Task, reference_date: str | None = None
    ) -> None:
        """Refresh displayed durations without rebuilding the row."""
        reference = reference_date or controller.today_str()
        now = datetime.now()
        is_running = task.status == TaskStatus.RUNNING
        if is_running != self._is_running:
            self._is_running = is_running
            self._today_value.setProperty("live", is_running)
            self._today_value.style().unpolish(self._today_value)
            self._today_value.style().polish(self._today_value)
        self._today_value.setText(format_hm(controller.today_seconds(task, reference)))
        self._total_value.setText(format_hm(task.total_seconds(now)))

    def _animate_actions(self, target: float) -> None:
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self._fade_effect.opacity())
        self._fade_anim.setEndValue(target)
        self._fade_anim.start()

    def _on_fade_finished(self) -> None:
        if self._fade_effect.opacity() <= 0.01:
            self._actions.setEnabled(False)

    def enterEvent(self, event) -> None:
        if not self._pinned:
            self._actions.setEnabled(True)
            self._animate_actions(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if not self._pinned and not self._is_running:
            self._animate_actions(0.0)
        super().leaveEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.refresh_layout()
