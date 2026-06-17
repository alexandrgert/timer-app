"""Durable journal for Bitrix time transfers (crash-safe before UI callback)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .storage import Storage


@dataclass(frozen=True)
class TransferJournalEntry:
    task_id: str
    session_ids: tuple[str, ...]
    record_id: str


def journal_path(storage: Storage) -> Path:
    return storage.path.parent / "bitrix_transfer_journal.json"


def _read_entries(path: Path) -> list[TransferJournalEntry]:
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, list):
        return []
    entries: list[TransferJournalEntry] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        task_id = str(item.get("task_id") or "")
        record_id = str(item.get("record_id") or "")
        raw_ids = item.get("session_ids")
        if not task_id or not record_id or not isinstance(raw_ids, list):
            continue
        session_ids = tuple(str(value) for value in raw_ids if value)
        if session_ids:
            entries.append(TransferJournalEntry(task_id, session_ids, record_id))
    return entries


def _write_entries(path: Path, entries: list[TransferJournalEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "task_id": entry.task_id,
            "session_ids": list(entry.session_ids),
            "record_id": entry.record_id,
        }
        for entry in entries
    ]
    temp_path = path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp_path, path)


def record_transfer_result(
    storage: Storage,
    task_id: str,
    session_ids: list[str],
    record_id: str,
) -> None:
    """Persist a successful transfer before the UI thread marks sessions."""
    path = journal_path(storage)
    entries = _read_entries(path)
    entries.append(
        TransferJournalEntry(task_id, tuple(session_ids), str(record_id)),
    )
    _write_entries(path, entries)


def remove_transfer_result(
    storage: Storage,
    task_id: str,
    session_ids: list[str],
    record_id: str,
) -> None:
    """Drop a journal entry after the UI has applied it."""
    path = journal_path(storage)
    session_set = set(session_ids)
    remaining = [
        entry
        for entry in _read_entries(path)
        if not (
            entry.task_id == task_id
            and entry.record_id == str(record_id)
            and set(entry.session_ids) == session_set
        )
    ]
    if remaining:
        _write_entries(path, remaining)
    elif path.is_file():
        path.unlink(missing_ok=True)


def apply_transfer_journal(
    storage: Storage,
    mark_transferred: Callable[[str, list[str], str], None],
) -> int:
    """Apply any journal entries left from an interrupted transfer. Returns count."""
    path = journal_path(storage)
    entries = _read_entries(path)
    if not entries:
        return 0
    for entry in entries:
        mark_transferred(entry.task_id, list(entry.session_ids), entry.record_id)
    if path.is_file():
        path.unlink(missing_ok=True)
    return len(entries)
