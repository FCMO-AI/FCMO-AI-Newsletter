#!/usr/bin/env python3
"""Generate PRODUCTION_STATUS.md from a health-state.json (contracts/health-state.schema.json).

PRODUCTION_STATUS.md is a generated file. It states the production state that
the last health run measured, never a hand-written claim. An unreadable or
invalid health state produces the state ``UNKNOWN``: a document that cannot be
checked never defaults to a healthy word.

Usage:

    python3 tools/status_report.py --health HEALTH.json [--out PRODUCTION_STATUS.md]
            [--if-changed [--max-age-h 24]] [--check] [--source TEXT] [--repo OWNER/NAME]

* ``--if-changed`` rewrites the file only when the state digest (state, signal
  statuses and codes, open alerts) differs from the one embedded in the current
  file, or when the embedded snapshot is older than ``--max-age-h`` hours. This
  keeps hourly health runs from producing hourly commits.
* ``--check`` writes nothing and exits 1 when the file on disk is not the one
  this health state would generate.

First stdout line: ``WROTE|UNCHANGED|CURRENT|STALE <path> state=<STATE> digest=<16 hex>``.
Exit codes: 0 written or unchanged (the state itself may be red), 1 ``--check``
found a stale file, 2 usage error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "PRODUCTION_STATUS.md"
DEFAULT_REPO = "FCMO-AI/FCMO-AI-Newsletter"
SCHEMA = "fcmo-health-state-v1"
REQUIRED_SIGNALS = ("serving", "transport", "upstream", "editorial")
INFO_SIGNALS = ("translation", "community", "watchdog")
SIGNAL_STATUSES = {"GREEN", "RED", "UNKNOWN"}
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
EDITION_RE = re.compile(
    r"^(FRESH|QUIET|TRANSPORT_DOWN|DELAYED:(ARB_MAIN_RED|CHECKPOINT_STALE|STORY_SUPPLY|TRANSPORT_FAIL|SNAPSHOT_REFUSED))$"
)
DIGEST_RE = re.compile(r"<!-- status-digest: ([0-9a-f]{16}) checked_at: (\S+) -->")
STALE_AFTER_H = 48

MEANING = {
    "FRESH": "New stories reached the public newspaper within the freshness window, and every required signal is green.",
    "QUIET": "Upstream research is green and sealed but produced no new public story recently. This is a legitimate quiet period, not an outage; the site keeps serving the current edition.",
    "DELAYED": "The site is up and serving its last good edition, but no new edition has been published within the freshness window. The reason code names the cause; the edition stays delayed until that cause clears.",
    "TRANSPORT_DOWN": "The newswire bridge has not reported within its window, so the newsroom cannot tell whether upstream has news. The site keeps serving its last good edition.",
    "DEGRADED": "The edition is current, but at least one required health signal is red.",
    "DOWN": "The public site is not serving correctly: routes fail or the live release does not match the deployed one.",
    "UNKNOWN": "The health state could not be read or validated, so nothing about production is claimed. Treat production as unverified until a health run succeeds.",
}


class HealthError(ValueError):
    """The health state is missing or does not have the contract shape."""


def load_health(path: Path) -> dict[str, Any]:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise HealthError("HEALTH_STATE_MISSING") from exc
    except OSError as exc:
        raise HealthError("HEALTH_STATE_UNREADABLE") from exc
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HealthError("HEALTH_STATE_INVALID") from exc
    problems = health_problems(doc)
    if problems:
        raise HealthError("HEALTH_STATE_INVALID")
    return doc


def health_problems(doc: Any) -> list[str]:
    """Structural checks of the fields this tool relies on (the schema is the full contract)."""
    if not isinstance(doc, dict):
        return ["not an object"]
    out: list[str] = []
    if doc.get("schema") != SCHEMA:
        out.append("schema")
    if doc.get("overall") not in {"GREEN", "RED"}:
        out.append("overall")
    if not isinstance(doc.get("checked_at"), str) or not UTC_RE.match(doc["checked_at"]):
        out.append("checked_at")
    if not isinstance(doc.get("edition_state"), str) or not EDITION_RE.match(doc["edition_state"]):
        out.append("edition_state")
    signals = doc.get("signals")
    if not isinstance(signals, dict):
        return out + ["signals"]
    for name in REQUIRED_SIGNALS:
        sig = signals.get(name)
        if not isinstance(sig, dict) or sig.get("status") not in SIGNAL_STATUSES or not isinstance(sig.get("code"), str):
            out.append(f"signals.{name}")
    for name, sig in signals.items():
        if name not in REQUIRED_SIGNALS + INFO_SIGNALS:
            out.append(f"signals.{name} unknown")
        elif not isinstance(sig, dict) or sig.get("status") not in SIGNAL_STATUSES:
            out.append(f"signals.{name}")
    if not isinstance(doc.get("open_alerts"), list):
        out.append("open_alerts")
    if not out:
        red = any(signals[name]["status"] != "GREEN" for name in REQUIRED_SIGNALS)
        if red != (doc["overall"] == "RED"):
            out.append("overall inconsistent with required signals")
    return out


def classify(doc: dict[str, Any] | None) -> tuple[str, str | None]:
    """Return (state, reason) for the canonical operating state line."""
    if doc is None:
        return "UNKNOWN", None
    signals = doc["signals"]
    serving = signals["serving"]
    if serving["status"] != "GREEN":
        return "DOWN", serving["code"]
    edition = doc["edition_state"]
    if edition.startswith("DELAYED:"):
        return "DELAYED", edition.split(":", 1)[1]
    if edition == "TRANSPORT_DOWN":
        return "TRANSPORT_DOWN", signals["transport"]["code"]
    if doc["overall"] == "RED":
        red = [f"{name}:{signals[name]['code']}" for name in REQUIRED_SIGNALS if signals[name]["status"] != "GREEN"]
        return "DEGRADED", ",".join(red)
    return edition, None


def state_digest(doc: dict[str, Any] | None, state: str, reason: str | None) -> str:
    """Digest of what the state is, not of when it was measured (details carry hourly ages)."""
    material: dict[str, Any] = {"state": state, "reason": reason}
    if doc is not None:
        material.update(
            overall=doc["overall"],
            edition_state=doc["edition_state"],
            release_id=doc.get("release_id"),
            signals={
                name: [sig.get("status"), sig.get("code"), sig.get("since")]
                for name, sig in sorted(doc["signals"].items())
            },
            open_alerts=sorted(
                (a.get("key"), a.get("code"), a.get("since")) for a in doc.get("open_alerts", []) if isinstance(a, dict)
            ),
        )
    blob = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _cell(value: Any) -> str:
    text = "—" if value is None or value == "" else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def render(
    doc: dict[str, Any] | None,
    *,
    error: str | None = None,
    source: str | None = None,
    repo: str = DEFAULT_REPO,
    generated_at: str | None = None,
) -> tuple[str, str, str]:
    """Return (markdown, state, digest)."""
    state, reason = classify(doc)
    digest = state_digest(doc, state, reason)
    checked_at = doc["checked_at"] if doc else (generated_at or _utc_now())
    headline = f"`{state}`" + (f" — `{reason}`" if reason else "")
    lines = [
        "<!-- GENERATED by tools/status_report.py from health-state.json. Do not edit by hand. -->",
        f"<!-- status-digest: {digest} checked_at: {checked_at} -->",
        "# FCMO AI Newsletter — Production Status",
        "",
        f"**Canonical operating state:** {headline}",
        "",
        f"{MEANING[state]}",
        "",
        "This file is generated from the hourly health state and rewritten by the",
        "`operator-alerts` workflow when the state changes, and at least once a day while",
        f"health runs. If the snapshot below is more than {STALE_AFTER_H} hours old, this file is",
        "itself stale: treat the state as `UNKNOWN` and check the live status page and the",
        "latest runs of the health workflow.",
        "",
        "## Snapshot",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    if doc is None:
        lines += [
            f"| Generated at | {_cell(checked_at)} |",
            f"| Health state | unreadable (`{_cell(error or 'HEALTH_STATE_MISSING')}`) |",
        ]
    else:
        run_id = doc.get("run_id")
        if source:
            origin = source
        elif run_id:
            origin = f"[health run {run_id}](https://github.com/{repo}/actions/runs/{run_id})"
        else:
            origin = "health state without a run id"
        lines += [
            f"| Checked at (UTC) | {_cell(checked_at)} |",
            f"| Source | {_cell(origin)} |",
            f"| Overall health | `{doc['overall']}` |",
            f"| Edition state | `{doc['edition_state']}` |",
            f"| Serving release | {_cell(doc.get('release_id'))} |",
        ]
    lines.append("")
    if doc is not None:
        lines += [
            "## Signals",
            "",
            "Serving, transport, upstream and editorial are separate signals. Only the",
            "required ones decide the overall health; the others are informational.",
            "",
            "| Signal | Required | Status | Code | Since (UTC) | Detail |",
            "|---|---|---|---|---|---|",
        ]
        for name in REQUIRED_SIGNALS + INFO_SIGNALS:
            sig = doc["signals"].get(name)
            if not isinstance(sig, dict):
                continue
            required = "yes" if name in REQUIRED_SIGNALS else "no"
            lines.append(
                f"| {name} | {required} | `{_cell(sig.get('status'))}` | `{_cell(sig.get('code'))}` "
                f"| {_cell(sig.get('since'))} | {_cell(sig.get('detail'))} |"
            )
        lines += ["", "## Open alerts", ""]
        alerts = [a for a in doc.get("open_alerts", []) if isinstance(a, dict)]
        if alerts:
            lines += ["| Key | Code | Since (UTC) |", "|---|---|---|"]
            for alert in alerts:
                lines.append(f"| {_cell(alert.get('key'))} | `{_cell(alert.get('code'))}` | {_cell(alert.get('since'))} |")
        else:
            lines.append("None.")
        lines.append("")
    lines += [
        "## States",
        "",
        "| State | Meaning |",
        "|---|---|",
    ]
    for name in ("FRESH", "QUIET", "DELAYED", "TRANSPORT_DOWN", "DEGRADED", "DOWN", "UNKNOWN"):
        lines.append(f"| `{name}` | {MEANING[name]} |")
    lines += [
        "",
        "Operator alerts open one incident issue when overall health turns red, comment",
        "on it when the failing signals change, and close it when health is green again.",
        "Two consecutive failures of the bridge, refresh, Pages or email-dispatch",
        "workflows open their own issue, closed by the next success.",
        "",
    ]
    return "\n".join(lines), state, digest


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def embedded(path: Path) -> tuple[str | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None, None
    match = DIGEST_RE.search(text)
    return (match.group(1), match.group(2)) if match else (None, None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--health", required=True, type=Path, help="health-state.json")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--if-changed", action="store_true")
    parser.add_argument("--max-age-h", type=float, default=24.0)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--source", help="Override the snapshot source line (public-safe text).")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--now", help="ISO time used when the health state is unreadable (default: FCMO_NOW or clock).")
    args = parser.parse_args(argv)

    doc: dict[str, Any] | None
    error: str | None = None
    try:
        doc = load_health(args.health)
    except HealthError as exc:
        doc, error = None, str(exc)
        print(f"ALERT {error} health={args.health.name}", file=sys.stderr)

    now = args.now or os.environ.get("FCMO_NOW") or _utc_now()
    text, state, digest = render(doc, error=error, source=args.source, repo=args.repo, generated_at=now)
    out = args.out

    if args.check:
        current = out.read_text(encoding="utf-8") if out.is_file() else None
        if doc is None:  # the unreadable-state page carries its generation time; compare the state only
            same = embedded(out)[0] == digest
        else:
            same = current == text
        print(f"{'CURRENT' if same else 'STALE'} {out.name} state={state} digest={digest}")
        return 0 if same else 1

    if args.if_changed:
        old_digest, old_at = embedded(out)
        new_at = _parse_utc(doc["checked_at"]) if doc else _parse_utc(now)
        old_dt = _parse_utc(old_at) if old_at else None
        too_old = old_dt is None or new_at is None or (new_at - old_dt).total_seconds() > args.max_age_h * 3600
        if old_digest == digest and not too_old:
            print(f"UNCHANGED {out.name} state={state} digest={digest}")
            return 0

    out.write_text(text, encoding="utf-8")
    print(f"WROTE {out.name} state={state} digest={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
