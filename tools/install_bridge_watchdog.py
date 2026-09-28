#!/usr/bin/env python3
"""Install the independent bridge watchdog as a user systemd timer on a host.

This is an operator command, never invoked from publication CI. It requires an
existing token file and a persistent checkout. No token is copied into units.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def units(repo: Path, token_file: Path, state_file: Path) -> tuple[str, str]:
    for path in (repo, token_file, state_file):
        if "\n" in str(path) or " " in str(path):
            raise ValueError("watchdog paths cannot contain spaces or newlines")
    service = f"""[Unit]
Description=FCMO bridge watchdog outside GitHub Actions

[Service]
Type=oneshot
WorkingDirectory={repo}
ExecStart=/usr/bin/env python3 {repo}/tools/bridge_watchdog.py --token-file {token_file} --state {state_file}
"""
    timer = """[Unit]
Description=Check FCMO newswire bridge every hour

[Timer]
OnCalendar=hourly
Persistent=true
RandomizedDelaySec=300
Unit=fcmo-bridge-watchdog.service

[Install]
WantedBy=timers.target
"""
    return service, timer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    token_file = args.token_file.expanduser().resolve()
    if not (repo / "tools/bridge_watchdog.py").is_file():
        raise SystemExit("watchdog script missing from checkout")
    if not token_file.is_file() or token_file.stat().st_mode & 0o077:
        raise SystemExit("token file must exist and be readable only by its owner (chmod 600)")
    unit_dir = Path.home() / ".config/systemd/user"
    state_file = Path.home() / ".local/state/fcmo/bridge-watchdog.json"
    service, timer = units(repo, token_file, state_file)
    unit_dir.mkdir(parents=True, exist_ok=True)
    (unit_dir / "fcmo-bridge-watchdog.service").write_text(service, encoding="utf-8")
    (unit_dir / "fcmo-bridge-watchdog.timer").write_text(timer, encoding="utf-8")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", "fcmo-bridge-watchdog.timer"], check=True)
    print("WATCHDOG TIMER INSTALLED; dispatch still requires a stale bridge and a valid token")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
