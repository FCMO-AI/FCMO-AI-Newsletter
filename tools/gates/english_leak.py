from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

from .common import GateFailure, GateResult, fail, public_files, rel

CODE = "ENGLISH_LEAK"
ENGLISH_WORDS = {
    "a", "an", "and", "are", "as", "at", "because", "been", "but", "by", "can", "could",
    "for", "from", "has", "have", "how", "if", "in", "into", "is", "it", "its", "may",
    "new", "not", "of", "on", "or", "our", "should", "that", "the", "their", "this", "to",
    "was", "we", "were", "what", "when", "which", "while", "will", "with", "without", "you",
}
WORDS = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)?", re.UNICODE)
BLOCKS = {"h1", "h2", "h3", "h4", "li", "p", "figcaption", "blockquote"}
STRUCTURED_FIELDS = {"organizations", "models", "products", "source-domain"}


class VisibleBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0; self.structured = 0; self.structured_tags: list[str] = []; self.stack: list[list[str]] = []; self.blocks: list[str] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        values = {str(key).lower(): value or "" for key, value in attrs}
        if tag in {"script", "style", "template", "code", "pre"}: self.skip += 1
        if values.get("translate", "").lower() == "no" and values.get("data-field") in STRUCTURED_FIELDS:
            self.structured += 1
            self.structured_tags.append(tag)
        if not self.skip and tag in BLOCKS: self.stack.append([])

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"script", "style", "template", "code", "pre"}:
            self.skip = max(0, self.skip - 1); return
        if not self.skip and tag in BLOCKS and self.stack:
            text = " ".join(self.stack.pop()).strip()
            if text: self.blocks.append(text)
        if self.structured_tags and tag == self.structured_tags[-1]:
            self.structured_tags.pop()
            self.structured = max(0, self.structured - 1)

    def handle_startendtag(self, tag, attrs):
        return

    def handle_data(self, data):
        if not self.skip and not self.structured:
            for block in self.stack: block.append(data)


def looks_english(text: str) -> bool:
    text = re.sub(r"FCMO-[0-9A-F]{12}", "", text)
    words = [word.lower().replace("’", "'") for word in WORDS.findall(text)
             if len(word) > 1 and not (word.isascii() and word.isupper())]
    if len(words) < 4:
        return False
    hits = sum(word in ENGLISH_WORDS for word in words)
    # Three function words and a material fraction avoids flagging product names.
    return (hits >= 2 and hits / len(words) >= 0.40) or (hits >= 3 and hits / len(words) >= 0.18)


def locale_of(route: str, text: str) -> str | None:
    if route.startswith("es/") or re.search(r'<html\b[^>]*\blang=["\']es(?:-419)?["\']', text, re.I):
        return "es-419"
    if route.startswith("zh/") or re.search(r'<html\b[^>]*\blang=["\']zh(?:-Hans)?["\']', text, re.I):
        return "zh-Hans"
    return None


def check(root: Path) -> GateResult:
    pages = public_files(root, {".html"}); problems = []
    for path in pages:
        text = path.read_text(encoding="utf-8", errors="replace")
        locale = locale_of(rel(root, path), text)
        if not locale: continue
        parser = VisibleBlocks(); parser.feed(text)
        for block in parser.blocks:
            if looks_english(block):
                problems.append(f"{rel(root, path)} [{locale}]: English prose {block[:100]!r}")
                break
    fail(CODE, problems)
    return GateResult(CODE, len(pages))


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    try: result = check(args.root)
    except GateFailure as exc: raise SystemExit(f"{exc.code} FAIL: {'; '.join(exc.problems)}") from exc
    print(f"{result.code} PASS ({result.checked} pages)"); return 0


if __name__ == "__main__": raise SystemExit(main())
