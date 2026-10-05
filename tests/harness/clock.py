"""Fake clock and time helpers for newsroom tests.

Convention for every time-dependent tool (normative, see contracts/README.md):

* a ``--now ISO8601`` flag overrides the clock;
* otherwise the ``FCMO_NOW`` environment variable does;
* otherwise the real UTC clock is used.

``FakeClock`` produces those values for subprocess tests and can also stand in
for an in-process ``now()`` callable::

    clock = FakeClock()                 # 2026-09-26T20:00:00Z, the fixture reference time
    clock.advance(hours=31)
    subprocess.run([... , *clock.argv()], env=clock.env())
    with clock.patch(module, "utc_now"):  # module.utc_now() now returns the fake time
        ...
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterator, Mapping

UTC = timezone.utc
CANONICAL_NOW = "2026-09-26T20:00:00Z"
ENV_VAR = "FCMO_NOW"
CDMX_NAME = "America/Mexico_City"

try:  # Mexico City has had no DST since 2022, so UTC-6 is an exact fallback.
    from zoneinfo import ZoneInfo

    CDMX: Any = ZoneInfo(CDMX_NAME)
except Exception:  # pragma: no cover - only without tzdata
    CDMX = timezone(timedelta(hours=-6), "CST")


def parse_utc(value: str | datetime | date) -> datetime:
    """Parse an ISO 8601 value (``Z``, offsets, fractions or a bare date) into aware UTC."""
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime(value.year, value.month, value.day)
    else:
        raw = str(value).strip()
        if not raw:
            raise ValueError("empty timestamp")
        if len(raw) == 10:
            raw += "T00:00:00"
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def format_utc(value: str | datetime) -> str:
    """Contract timestamp form: ``YYYY-MM-DDTHH:MM:SSZ`` (fraction truncated)."""
    return parse_utc(value).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_cdmx(value: str | datetime) -> datetime:
    return parse_utc(value).astimezone(CDMX)


def cdmx_date(value: str | datetime) -> str:
    """America/Mexico_City calendar date (edition date, URL date)."""
    return to_cdmx(value).date().isoformat()


def hours_between(earlier: str | datetime, later: str | datetime) -> float:
    return (parse_utc(later) - parse_utc(earlier)).total_seconds() / 3600.0


def now_from(flag: str | None = None, env: Mapping[str, str] | None = None) -> datetime:
    """Reference implementation of the --now / FCMO_NOW convention."""
    env = os.environ if env is None else env
    if flag:
        return parse_utc(flag)
    if env.get(ENV_VAR):
        return parse_utc(env[ENV_VAR])
    return datetime.now(UTC)


class FakeClock:
    """A settable, advanceable UTC clock."""

    def __init__(self, start: str | datetime = CANONICAL_NOW) -> None:
        self._now = parse_utc(start)

    def __call__(self) -> datetime:
        return self._now

    def __repr__(self) -> str:
        return f"FakeClock({self.iso()!r})"

    def now(self) -> datetime:
        return self._now

    def iso(self) -> str:
        return format_utc(self._now)

    def set(self, value: str | datetime) -> "FakeClock":
        self._now = parse_utc(value)
        return self

    def advance(self, **delta: float) -> "FakeClock":
        """Move forward (or back with negative values); accepts timedelta keywords."""
        self._now += timedelta(**delta)
        return self

    def ago(self, **delta: float) -> str:
        """Contract timestamp ``delta`` before now, e.g. ``clock.ago(hours=31)``."""
        return format_utc(self._now - timedelta(**delta))

    def ahead(self, **delta: float) -> str:
        return format_utc(self._now + timedelta(**delta))

    def cdmx_date(self) -> str:
        return cdmx_date(self._now)

    def argv(self) -> list[str]:
        return ["--now", self.iso()]

    def env(self, base: Mapping[str, str] | None = None) -> dict[str, str]:
        merged = dict(os.environ if base is None else base)
        merged[ENV_VAR] = self.iso()
        return merged

    @contextmanager
    def patch(self, target: Any, name: str = "utc_now", *, as_string: bool = False) -> Iterator["FakeClock"]:
        """Temporarily replace ``target.name`` with a callable returning the fake time."""
        original = getattr(target, name)
        setattr(target, name, (lambda *a, **k: self.iso()) if as_string else (lambda *a, **k: self._now))
        try:
            yield self
        finally:
            setattr(target, name, original)
