from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from .common import GateFailure, GateResult, fail, public_files, rel

CODE = "REMOTE_SCRIPT"


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.dependencies: list[str] = []

    def handle_starttag(self, tag, attrs):
        data = {str(k).lower(): (v or "") for k, v in attrs}
        url = ""
        if tag.lower() == "script":
            url = data.get("src", "")
        elif tag.lower() == "link":
            kinds = {part.lower() for part in data.get("rel", "").split()}
            if kinds & {"stylesheet", "modulepreload"} or ("preload" in kinds and data.get("as") in {"script", "style"}):
                url = data.get("href", "")
        if url.startswith(("http://", "https://", "//")):
            self.dependencies.append(url)


def check(root: Path) -> GateResult:
    problems = []
    files = public_files(root, {".html"})
    for path in files:
        parser = Parser(); parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        if parser.dependencies:
            problems.append(f"{rel(root, path)}: {parser.dependencies}")
    fail(CODE, problems)
    return GateResult(CODE, len(files))


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    try: result = check(args.root)
    except GateFailure as exc: raise SystemExit(f"{exc.code} FAIL: {'; '.join(exc.problems)}") from exc
    print(f"{result.code} PASS ({result.checked} pages)"); return 0


if __name__ == "__main__": raise SystemExit(main())
