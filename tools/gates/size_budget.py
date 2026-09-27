from __future__ import annotations

from pathlib import Path

from .common import GateFailure, GateResult, fail, rel

CODE = "SIZE_BUDGET"
HOME_HTML_MAX = 102_400
HTML_MAX = 1_000_000
JS_TOTAL_MAX = 30_720


def check(root: Path) -> GateResult:
    problems = []
    for route in ("index.html", "es/index.html", "zh/index.html"):
        path = root / route
        if not path.is_file(): problems.append(f"{route}: missing homepage"); continue
        if path.stat().st_size > HOME_HTML_MAX:
            problems.append(f"{route}: {path.stat().st_size} bytes > {HOME_HTML_MAX}")
    pages = [path for path in root.rglob("*.html") if path.is_file()]
    for path in pages:
        if path.stat().st_size > HTML_MAX:
            problems.append(f"{rel(root, path)}: {path.stat().st_size} bytes > {HTML_MAX}")
    scripts = [path for path in root.rglob("*.js") if path.is_file()]
    js_total = sum(path.stat().st_size for path in scripts)
    if js_total > JS_TOTAL_MAX:
        problems.append(f"JavaScript total: {js_total} bytes > {JS_TOTAL_MAX}")
    fail(CODE, problems)
    return GateResult(CODE, len(pages) + len(scripts))


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    try: result = check(args.root)
    except GateFailure as exc: raise SystemExit(f"{exc.code} FAIL: {'; '.join(exc.problems)}") from exc
    print(f"{result.code} PASS ({result.checked} assets)"); return 0


if __name__ == "__main__": raise SystemExit(main())

