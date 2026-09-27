"""Temporary landing adapter; subscription lane replaces this component."""

import json
import os
from pathlib import Path

from tools.paper import community


def subscribe_block(zone: str, locale: str) -> str:
    """Keep the existing honest subscription state on the new Group landing."""
    config = json.loads((Path(__file__).resolve().parents[3] / "config" / "site.json").read_text(encoding="utf-8"))
    language = next(item for item in config["locales"] if item["code"] == locale)
    block, script = community.render_subscribe(
        locale_code=locale, path_prefix=language["path_prefix"],
        base=config["base_path"], portal_url=os.environ.get("GHOST_PORTAL_URL"),
    )
    return f'<div data-zone="{zone}">{block}{script}</div>'
