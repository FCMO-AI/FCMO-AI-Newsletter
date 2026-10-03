from __future__ import annotations

import subprocess
from pathlib import Path

from .common import GateFailure, GateResult

ROOT = Path(__file__).resolve().parents[2]

# Construct the signatures in pieces so this guard does not match itself.
SIGNATURES = (
    (b"/srv/" + b"fcmo", "server path"),
    (b"/ho" + b"me/", "home path"),
    (b"/tmp/" + b"claude", "temporary Claude path"),
)


def check(_publication_root: Path | None = None) -> GateResult:
    return check_repo(ROOT)


def check_repo(repo_root: Path) -> GateResult:
    try:
        listed = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "-z"],
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GateFailure("NO_MACHINE_PATHS", [f"cannot list tracked files: {exc}"]) from exc

    violations: list[str] = []
    tracked = [item for item in listed.decode("utf-8", errors="replace").split("\0") if item]
    for relative in tracked:
        normalized = relative.replace("\\", "/")
        if normalized.startswith("tests/fixtures/"):
            continue
        path = repo_root / relative
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise GateFailure("NO_MACHINE_PATHS", [f"cannot read tracked file {relative}: {exc}"]) from exc
        for signature, label in SIGNATURES:
            if signature in content:
                violations.append(f"{relative}: contains forbidden {label}")

    if violations:
        raise GateFailure("NO_MACHINE_PATHS", violations)
    return GateResult("NO_MACHINE_PATHS", len(tracked))
