from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

from .common import GateResult, fail, public_files, rel

CODE = "INTERNAL_ID"
PUBLIC_ID = re.compile(r"\bFCMO-[0-9A-F]{12}\b")
HIDDEN = {"script", "style", "template"}
TITLE_META = {"description", "og:title", "og:description", "twitter:title", "twitter:description"}


class ReaderText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.title = 0
        self.visible: list[str] = []
        self.titles: list[str] = []
        self.meta: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        values = {str(key).lower(): value or "" for key, value in attrs}
        if tag in HIDDEN:
            self.hidden += 1
        if tag == "title":
            self.title += 1
        if tag == "meta":
            key = (values.get("property") or values.get("name") or "").lower()
            if key in TITLE_META:
                self.meta.append((key, values.get("content", "")))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in HIDDEN:
            self.hidden = max(0, self.hidden - 1)
        if tag == "title":
            self.title = max(0, self.title - 1)

    def handle_data(self, data: str) -> None:
        if self.hidden:
            return
        if self.title:
            self.titles.append(data)
        else:
            self.visible.append(data)


def check(root: Path) -> GateResult:
    pages = public_files(root, {".html"})
    problems: list[str] = []
    for path in pages:
        parser = ReaderText()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        for surface, value in (
            ("visible text", " ".join(parser.visible)),
            ("title", " ".join(parser.titles)),
            *((f"meta {key}", value) for key, value in parser.meta),
        ):
            match = PUBLIC_ID.search(value)
            if match:
                problems.append(f"{rel(root, path)}: {surface} exposes {match.group(0)}")
    fail(CODE, problems)
    return GateResult(CODE, len(pages))


def main(argv=None) -> int:
    import argparse
    from .common import GateFailure
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    try: result = check(args.root)
    except GateFailure as exc: raise SystemExit(f"{exc.code} FAIL: {'; '.join(exc.problems)}") from exc
    print(f"{result.code} PASS ({result.checked} pages)"); return 0


if __name__ == "__main__": raise SystemExit(main())
