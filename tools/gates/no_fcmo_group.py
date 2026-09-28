"""Reject the internal umbrella name on any public or reader-facing surface."""

from __future__ import annotations

from pathlib import Path
import re

from .common import GateFailure, GateResult, public_files, rel

ROOT = Path(__file__).resolve().parents[2]
PATTERN = re.compile(b"fcmo" + rb"\s+" + b"group", re.IGNORECASE)
SOURCE_ROOTS = (
    "tools/paper", "tools/agent", "tools/email_render.py", "community/config",
    "community/ghost-theme", "i18n/ui", "site", "site-src",
    "release-src", "scaffold", "CONTENT_LICENSE.md",
    "README.md", "ATTRIBUTION.md", "COPYRIGHT.md", "LEGAL_REQUIREMENTS.md",
    "DESIGN_V2.md", "legal", "docs",
)
SUFFIXES = {".html", ".hbs", ".in", ".json", ".js", ".md", ".py", ".txt", ".xml"}


def _find(paths: list[Path], root: Path) -> tuple[int, list[str]]:
    violations = []
    checked = 0
    for path in paths:
        if not path.is_file() or path.suffix.lower() not in SUFFIXES:
            continue
        checked += 1
        for number, line in enumerate(path.read_bytes().splitlines(), 1):
            if PATTERN.search(line):
                violations.append(f"{rel(root, path)}:{number}")
                if len(violations) >= 30:
                    return checked, violations
    return checked, violations


def check(publication_root: Path) -> GateResult:
    built = public_files(publication_root, SUFFIXES)
    source = []
    # Small synthetic trees exercise the shared gate runner. The source audit
    # belongs to a complete publication, identified by its agent index.
    if (publication_root / "agent.json").is_file():
        for relative in SOURCE_ROOTS:
            path = ROOT / relative
            if path.is_file():
                source.append(path)
            elif path.is_dir():
                source.extend(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    built_count, built_violations = _find(built, publication_root)
    source_count, source_violations = _find(sorted(source), ROOT)
    problems = [f"built: {item}" for item in built_violations] + [f"source: {item}" for item in source_violations]
    if problems:
        raise GateFailure("NO_FCMO_GROUP", problems)
    return GateResult("NO_FCMO_GROUP", built_count + source_count)
