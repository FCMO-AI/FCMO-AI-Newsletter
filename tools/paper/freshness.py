"""How fresh the FCMO AI corpus is, measured against the newsroom's last check.

Pure and deterministic: the reference is the status file's ``status_updated_at``,
never the wall clock, so the same corpus and status always yield the same signal.
"""

from __future__ import annotations

import datetime

from .front_order import FRESH_WINDOW, _instant, fresh_instant, front_order

STALE_AFTER = datetime.timedelta(days=7)
_HOUR = datetime.timedelta(hours=1)
_DAY = datetime.timedelta(days=1)
_ZERO = datetime.timedelta(0)


def _utc(value: datetime.datetime | None) -> str | None:
    return value.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if value else None


def corpus_freshness(live: list[dict], checked_at: object) -> dict:
    """Date the newest live story, its lag behind ``checked_at`` and the lead's age.

    ``state`` is ``current`` within ``FRESH_WINDOW``, ``lagging`` within
    ``STALE_AFTER``, ``stale`` beyond it, and ``unknown`` whenever either end of
    the lag cannot be dated: an unmeasured corpus is never reported as current.
    """
    checked = _instant(checked_at)
    dated = [instant for instant in map(fresh_instant, live) if instant is not None]
    newest = max(dated) if dated else None
    lag = max(checked - newest, _ZERO) if checked and newest else None
    if lag is None:
        state = "unknown"
    elif lag <= FRESH_WINDOW:
        state = "current"
    elif lag <= STALE_AFTER:
        state = "lagging"
    else:
        state = "stale"
    lead = front_order(live)[0] if live else None
    lead_at = fresh_instant(lead) if lead else None
    return {
        "state": state,
        "checked_at": _utc(checked),
        "newest_at": _utc(newest),
        "lag_hours": lag // _HOUR if lag is not None else None,
        "lag_days": lag // _DAY if lag is not None else None,
        "lead_id": str(lead["id"]) if lead and lead.get("id") is not None else None,
        "lead_at": _utc(lead_at),
        "lead_gap_days": max(newest - lead_at, _ZERO) // _DAY if newest and lead_at else None,
    }
