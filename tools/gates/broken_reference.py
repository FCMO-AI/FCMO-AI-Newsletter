from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urljoin, urlsplit

from .common import GateResult, fail, public_files, rel

CODE = "BROKEN_REFERENCE"
URL_ATTRS = {"src", "href", "poster"}


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.values: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = {str(key).lower(): value or "" for key, value in attrs}
        for name in URL_ATTRS:
            if values.get(name):
                self.values.append((name, values[name]))
        if values.get("srcset"):
            for candidate in values["srcset"].split(","):
                url = candidate.strip().split()[0] if candidate.strip() else ""
                if url:
                    self.values.append(("srcset", url))
        if tag.lower() == "meta" and values.get("property", "").lower() == "og:image" and values.get("content"):
            self.values.append(("og:image", values["content"]))


def _site_identity(root: Path) -> tuple[str, str]:
    index = root / "index.html"
    if not index.is_file():
        return "", "/"
    parser = References(); parser.feed(index.read_text(encoding="utf-8", errors="replace"))
    for name, value in parser.values:
        if name != "href":
            continue
        parsed = urlsplit(value)
        if parsed.scheme in {"http", "https"} and parsed.netloc and parsed.path.endswith("/"):
            return f"{parsed.scheme}://{parsed.netloc}", parsed.path
    return "", "/"


def _candidate_path(root: Path, page: Path, raw: str, origin: str, base: str) -> Path | None:
    value = raw.strip()
    if not value or value.startswith(("#", "data:", "mailto:", "tel:", "javascript:")):
        return None
    parsed = urlsplit(value)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc and (not origin or f"{parsed.scheme}://{parsed.netloc}" != origin):
        return None
    if not parsed.netloc and not value.startswith("/"):
        page_url = origin + base + rel(root, page)
        parsed = urlsplit(urljoin(page_url, value))
    path = unquote(parsed.path)
    if base != "/":
        if not path.startswith(base):
            return None
        path = path[len(base):]
    else:
        path = path.lstrip("/")
    pure = PurePosixPath(path)
    if ".." in pure.parts:
        return root / "__unsafe_reference__"
    target = root.joinpath(*pure.parts)
    if path.endswith("/") or not pure.suffix:
        target /= "index.html"
    return target


def check(root: Path) -> GateResult:
    pages = public_files(root, {".html"})
    origin, base = _site_identity(root)
    problems: list[str] = []
    checked = 0
    for page in pages:
        parser = References(); parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        for attribute, value in parser.values:
            target = _candidate_path(root, page, value, origin, base)
            if target is None:
                continue
            checked += 1
            if not target.is_file():
                problems.append(f"{rel(root, page)}: {attribute}={value!r} does not resolve inside candidate")
    fail(CODE, problems)
    return GateResult(CODE, checked)


def main(argv=None) -> int:
    import argparse
    from .common import GateFailure
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    try: result = check(args.root)
    except GateFailure as exc: raise SystemExit(f"{exc.code} FAIL: {'; '.join(exc.problems)}") from exc
    print(f"{result.code} PASS ({result.checked} local references)"); return 0


if __name__ == "__main__": raise SystemExit(main())
