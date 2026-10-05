"""Canonical route construction for the static newspaper."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath

# O-8 stays open. Both public product names come from one config value each.
_products = json.loads((Path(__file__).resolve().parents[2] / "community/config/subscriptions.json").read_text(encoding="utf-8"))["products"]
PRODUCT_NAMES = {"newsletter": _products["letter"]["name"], "technical": _products["paper"]["name"]}
TECHNICAL_FRONT = "diario/"


@dataclass(frozen=True)
class Route:
    path: str
    kind: str
    locale: str | None = None
    story_id: str | None = None


def normalize_base(base: str) -> str:
    return "/" + base.strip("/") + "/" if base.strip("/") else "/"


def prefix(locale: dict) -> str:
    return locale.get("path_prefix", "").strip("/")


def join(*parts: str) -> str:
    clean = [part.strip("/") for part in parts if part and part.strip("/")]
    return "/".join(clean) + ("/" if clean else "")


def story_path(locale: dict, story: dict) -> str:
    year, month, day = story["url_date"].split("-")
    return join(prefix(locale), year, month, day, story["slug"])


def edition_path(locale: dict, date: str) -> str:
    return join(prefix(locale), "edition", date)


def beat_path(locale: dict, beat: str) -> str:
    return join(prefix(locale), "beat", beat)


def topic_path(locale: dict, topic: str) -> str:
    return join(prefix(locale), "topic", topic)


def org_path(locale: dict, organization: str) -> str:
    return join(prefix(locale), "org", organization)


def output_path(root: Path, route: str) -> Path:
    pure = PurePosixPath(route.strip("/"))
    if ".." in pure.parts:
        raise ValueError(f"unsafe route: {route}")
    return root.joinpath(*pure.parts, "index.html") if pure.parts else root / "index.html"


def href(base: str, route: str) -> str:
    return normalize_base(base) + route.lstrip("/")


def absolute(base_url: str, route: str) -> str:
    return base_url.rstrip("/") + "/" + route.lstrip("/")
