from __future__ import annotations

import re
from pathlib import Path

from .common import GateFailure, GateResult, fail, public_files, rel

CODE = "BINDING_COMPLETE"
PATTERNS = (
    re.compile(r'\bdata-(?:bind(?:ing)?|field|value)=["\']\s*[—–-]\s*["\']', re.I),
    re.compile(r"(?:EVIDENCE|EVIDENCIA|证据)\s*[—–-](?:\s|<)", re.I),
    re.compile(r"[—–-]\s*/\s*10\b"),
    re.compile(r"\{\{\s*[A-Za-z_][^{}]*\}\}"),
    re.compile(r"\$\{\s*[A-Za-z_][^{}]*\}"),
    re.compile(r"__(?:PLACEHOLDER|TODO|TBD)__", re.I),
)


def check(root: Path) -> GateResult:
    problems: list[str] = []
    files = public_files(root, {".html", ".json", ".jsonl", ".xml"})
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() == ".html":
            text = re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>", "", text, flags=re.I | re.S)
        for pattern in PATTERNS:
            match = pattern.search(text)
            if match:
                problems.append(f"{rel(root, path)}: unresolved binding {match.group(0)[:80]!r}")
                break
    fail(CODE, problems)
    return GateResult(CODE, len(files))


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    try: result = check(args.root)
    except GateFailure as exc: raise SystemExit(f"{exc.code} FAIL: {'; '.join(exc.problems)}") from exc
    print(f"{result.code} PASS ({result.checked} files)"); return 0


if __name__ == "__main__": raise SystemExit(main())
