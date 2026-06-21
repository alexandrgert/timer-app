from __future__ import annotations

from ..bitrix import entity_url
from ..controller import AppController


def bitrix_entity_url(controller: AppController, link: dict | None) -> str | None:
    config = controller.bitrix_portal_config()
    return entity_url(
        controller.bitrix_webhook(),
        link,
        projects_entity_type_id=config.projects_entity_type_id,
    )
