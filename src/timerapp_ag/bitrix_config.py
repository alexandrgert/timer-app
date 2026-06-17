"""Bitrix24 portal-specific settings (SPA projects registry, filter fields).

Defaults match the original webmens portal (СПА 150 «Реестр проектов»).
Values are persisted in ``ui.bitrix.portal`` and can be auto-discovered from
the portal via ``discover_portal_config``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

# Original portal: smart-process «Реестр проектов» (entityTypeId 150).
DEFAULT_PROJECTS_ENTITY_TYPE_ID = 150
DEFAULT_PROJECTS_EXECUTOR_FIELDS = ("ufCrm16MainIspolnitel", "ufCrm16Supporters")
DEFAULT_PROJECTS_REGISTRY_TITLE = "Реестр проектов"

DEFAULT_WORKLOG_ENTITY_TYPE_ID = 1092
DEFAULT_WORKLOG_PARENT_FIELD = "parentId150"
DEFAULT_WORKLOG_HOURS_FIELD = "ufCrm88HoursWork"
DEFAULT_WORKLOG_COMMENT_FIELD = "ufCrm88CommentWork"
DEFAULT_WORKLOG_DATE_FIELD = "ufCrm88DateWork"

_EXECUTOR_KEYWORDS = ("главн", "исполнител", "main")
_SUPPORTER_KEYWORDS = ("помощник", "supporter", "соисполнител", "участник")
_WORKLOG_TITLE_KEYWORDS = ("журнал", "работ")
_HOURS_KEYWORDS = ("час", "hour")
_COMMENT_KEYWORDS = ("коммент", "comment", "назван", "описан")
_DATE_KEYWORDS = ("дата", "date")


@dataclass(frozen=True)
class BitrixPortalConfig:
    projects_entity_type_id: int = DEFAULT_PROJECTS_ENTITY_TYPE_ID
    projects_executor_fields: tuple[str, ...] = DEFAULT_PROJECTS_EXECUTOR_FIELDS
    projects_registry_title: str = DEFAULT_PROJECTS_REGISTRY_TITLE
    worklog_entity_type_id: int = DEFAULT_WORKLOG_ENTITY_TYPE_ID
    worklog_parent_field: str = DEFAULT_WORKLOG_PARENT_FIELD
    worklog_hours_field: str = DEFAULT_WORKLOG_HOURS_FIELD
    worklog_comment_field: str = DEFAULT_WORKLOG_COMMENT_FIELD
    worklog_date_field: str = DEFAULT_WORKLOG_DATE_FIELD

    def to_dict(self) -> dict[str, Any]:
        return {
            "projects_entity_type_id": self.projects_entity_type_id,
            "projects_executor_fields": list(self.projects_executor_fields),
            "projects_registry_title": self.projects_registry_title,
            "worklog_entity_type_id": self.worklog_entity_type_id,
            "worklog_parent_field": self.worklog_parent_field,
            "worklog_hours_field": self.worklog_hours_field,
            "worklog_comment_field": self.worklog_comment_field,
            "worklog_date_field": self.worklog_date_field,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> BitrixPortalConfig:
        if not isinstance(data, dict):
            return cls()
        raw_fields = data.get("projects_executor_fields")
        fields: tuple[str, ...]
        if isinstance(raw_fields, list) and raw_fields:
            fields = tuple(str(item) for item in raw_fields if item)
        else:
            fields = DEFAULT_PROJECTS_EXECUTOR_FIELDS
        try:
            entity_type_id = int(data.get("projects_entity_type_id", DEFAULT_PROJECTS_ENTITY_TYPE_ID))
        except (TypeError, ValueError):
            entity_type_id = DEFAULT_PROJECTS_ENTITY_TYPE_ID
        title = str(data.get("projects_registry_title") or DEFAULT_PROJECTS_REGISTRY_TITLE).strip()
        try:
            worklog_entity_type_id = int(
                data.get("worklog_entity_type_id", DEFAULT_WORKLOG_ENTITY_TYPE_ID)
            )
        except (TypeError, ValueError):
            worklog_entity_type_id = DEFAULT_WORKLOG_ENTITY_TYPE_ID
        worklog_parent_field = str(
            data.get("worklog_parent_field") or DEFAULT_WORKLOG_PARENT_FIELD
        ).strip() or DEFAULT_WORKLOG_PARENT_FIELD
        worklog_hours_field = str(
            data.get("worklog_hours_field") or DEFAULT_WORKLOG_HOURS_FIELD
        ).strip() or DEFAULT_WORKLOG_HOURS_FIELD
        worklog_comment_field = str(
            data.get("worklog_comment_field") or DEFAULT_WORKLOG_COMMENT_FIELD
        ).strip() or DEFAULT_WORKLOG_COMMENT_FIELD
        worklog_date_field = str(
            data.get("worklog_date_field") or DEFAULT_WORKLOG_DATE_FIELD
        ).strip() or DEFAULT_WORKLOG_DATE_FIELD
        return cls(
            projects_entity_type_id=entity_type_id,
            projects_executor_fields=fields,
            projects_registry_title=title or DEFAULT_PROJECTS_REGISTRY_TITLE,
            worklog_entity_type_id=worklog_entity_type_id,
            worklog_parent_field=worklog_parent_field,
            worklog_hours_field=worklog_hours_field,
            worklog_comment_field=worklog_comment_field,
            worklog_date_field=worklog_date_field,
        )


def merge_portal_config(stored: dict[str, Any] | None) -> BitrixPortalConfig:
    """Return stored portal config merged over defaults."""
    return BitrixPortalConfig.from_dict(stored)


def _title_matches(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = (text or "").lower()
    return any(keyword in lowered for keyword in keywords)


def _pick_spa_type(types: list[dict], preferred_title: str) -> dict | None:
    if not types:
        return None
    preferred = (preferred_title or "").strip().lower()
    if preferred:
        for item in types:
            title = str(item.get("title", "")).strip().lower()
            if title == preferred:
                return item
        for item in types:
            title = str(item.get("title", "")).strip().lower()
            if preferred in title or title in preferred:
                return item
    for item in types:
        title = str(item.get("title", "")).strip().lower()
        if "реестр" in title and "проект" in title:
            return item
    for item in types:
        title = str(item.get("title", "")).strip().lower()
        if "проект" in title:
            return item
    return None


def _field_entries(fields_payload: dict | list) -> list[tuple[str, str]]:
    """Return ``(code, title)`` pairs from ``crm.item.fields`` response."""
    if isinstance(fields_payload, list):
        items = fields_payload
    elif isinstance(fields_payload, dict):
        items = fields_payload.get("fields", fields_payload)
        if isinstance(items, dict):
            return [
                (str(code), str(meta.get("title", meta.get("formLabel", ""))))
                for code, meta in items.items()
                if isinstance(meta, dict)
            ]
        if not isinstance(items, list):
            return []
    else:
        return []
    pairs: list[tuple[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        code = str(item.get("upperName") or item.get("name") or item.get("code") or "")
        title = str(item.get("title") or item.get("formLabel") or "")
        if code:
            pairs.append((code, title))
    return pairs


def _match_executor_fields(pairs: list[tuple[str, str]]) -> list[str]:
    executors = [code for code, title in pairs if _title_matches(title, _EXECUTOR_KEYWORDS)]
    supporters = [code for code, title in pairs if _title_matches(title, _SUPPORTER_KEYWORDS)]
    matched = executors + [code for code in supporters if code not in executors]
    return matched or list(DEFAULT_PROJECTS_EXECUTOR_FIELDS)


def _pick_worklog_type(types: list[dict], preferred_entity_type_id: int) -> dict | None:
    if not types:
        return None
    for item in types:
        try:
            if int(item.get("entityTypeId") or 0) == preferred_entity_type_id:
                return item
        except (TypeError, ValueError):
            continue
    for item in types:
        title = str(item.get("title", "")).lower()
        if all(keyword in title for keyword in _WORKLOG_TITLE_KEYWORDS):
            return item
    return None


def _first_field_code(
    pairs: list[tuple[str, str]],
    keywords: tuple[str, ...],
    *,
    fallback: str,
    code_prefix: str | None = None,
) -> str:
    if code_prefix:
        for code, _title in pairs:
            if code == code_prefix:
                return code
    for code, title in pairs:
        if _title_matches(title, keywords):
            return code
    return fallback


def _match_worklog_fields(
    pairs: list[tuple[str, str]],
    projects_entity_type_id: int,
) -> tuple[str, str, str, str]:
    parent_field = _first_field_code(
        pairs,
        ("проект", "project"),
        fallback=f"parentId{projects_entity_type_id}",
        code_prefix=f"parentId{projects_entity_type_id}",
    )
    hours_field = _first_field_code(
        pairs,
        _HOURS_KEYWORDS,
        fallback=DEFAULT_WORKLOG_HOURS_FIELD,
    )
    comment_field = _first_field_code(
        pairs,
        _COMMENT_KEYWORDS,
        fallback=DEFAULT_WORKLOG_COMMENT_FIELD,
    )
    date_field = _first_field_code(
        pairs,
        _DATE_KEYWORDS,
        fallback=DEFAULT_WORKLOG_DATE_FIELD,
    )
    return parent_field, hours_field, comment_field, date_field


def discover_worklog_config(
    *,
    list_types: Callable[[], list[dict]],
    list_fields: Callable[[int], dict | list],
    projects_entity_type_id: int,
    preferred_worklog_entity_type_id: int = DEFAULT_WORKLOG_ENTITY_TYPE_ID,
) -> tuple[int, str, str, str, str]:
    """Detect worklog SPA entity type and field codes from the portal."""
    worklog = _pick_worklog_type(list_types(), preferred_worklog_entity_type_id)
    if worklog is None:
        return (
            preferred_worklog_entity_type_id,
            f"parentId{projects_entity_type_id}",
            DEFAULT_WORKLOG_HOURS_FIELD,
            DEFAULT_WORKLOG_COMMENT_FIELD,
            DEFAULT_WORKLOG_DATE_FIELD,
        )
    entity_type_id = int(worklog.get("entityTypeId") or preferred_worklog_entity_type_id)
    fields_payload = list_fields(entity_type_id)
    parent_field, hours_field, comment_field, date_field = _match_worklog_fields(
        _field_entries(fields_payload),
        projects_entity_type_id,
    )
    return entity_type_id, parent_field, hours_field, comment_field, date_field


def discover_portal_config(
    *,
    list_types: Callable[[], list[dict]],
    list_fields: Callable[[int], dict | list],
    preferred_registry_title: str = DEFAULT_PROJECTS_REGISTRY_TITLE,
) -> BitrixPortalConfig:
    """Detect SPA projects registry, worklog fields, and user-filter fields from the portal."""
    types = list_types()
    spa = _pick_spa_type(types, preferred_registry_title)
    if spa is None:
        return BitrixPortalConfig(projects_registry_title=preferred_registry_title)
    entity_type_id = int(spa.get("entityTypeId") or DEFAULT_PROJECTS_ENTITY_TYPE_ID)
    title = str(spa.get("title") or preferred_registry_title).strip()
    fields_payload = list_fields(entity_type_id)
    executor_fields = tuple(_match_executor_fields(_field_entries(fields_payload)))
    (
        worklog_entity_type_id,
        worklog_parent_field,
        worklog_hours_field,
        worklog_comment_field,
        worklog_date_field,
    ) = discover_worklog_config(
        list_types=lambda: types,
        list_fields=list_fields,
        projects_entity_type_id=entity_type_id,
    )
    return BitrixPortalConfig(
        projects_entity_type_id=entity_type_id,
        projects_executor_fields=executor_fields,
        projects_registry_title=title,
        worklog_entity_type_id=worklog_entity_type_id,
        worklog_parent_field=worklog_parent_field,
        worklog_hours_field=worklog_hours_field,
        worklog_comment_field=worklog_comment_field,
        worklog_date_field=worklog_date_field,
    )
