#!/usr/bin/env python3
"""Final consistency pass over generated editorial-discovery HTML.

The discovery builder is intentionally independent of the Story builder. This pass
binds their route contracts, writes path-accurate canonical URLs, folds every durable
HTML route into the sitemap, rejects remote executable dependencies, then refreshes
the candidate build manifest and re-runs final-release validation when operating on
an assembled publish tree.
"""
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

BASE_URL = "https://fcmo-ai.github.io/FCMO-AI-Newsletter"
CANONICAL = re.compile(r'<link rel="canonical" href="[^"]*">', re.I)
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


class _RemoteExecParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.dependencies: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key.lower(): (value or "") for key, value in attrs}
        tag = tag.lower()
        if tag == "script":
            src = data.get("src", "")
            if src.startswith(("http://", "https://", "//")):
                self.dependencies.append(src)
        elif tag == "link":
            rel = {token.lower() for token in data.get("rel", "").split()}
            href = data.get("href", "")
            if "stylesheet" in rel and href.startswith(("http://", "https://", "//")):
                self.dependencies.append(href)


def remote_exec_dependencies(text: str) -> list[str]:
    parser = _RemoteExecParser()
    parser.feed(text)
    return parser.dependencies


def augment_sitemap(root: Path) -> None:
    sitemap = root / "sitemap.xml"
    if sitemap.is_file():
        tree = ElementTree.parse(sitemap)
        node = tree.getroot()
    else:
        ElementTree.register_namespace("", NS)
        node = ElementTree.Element(f"{{{NS}}}urlset")
        tree = ElementTree.ElementTree(node)
    existing = {
        child.findtext(f"{{{NS}}}loc")
        for child in node.findall(f"{{{NS}}}url")
    }
    for path in sorted(root.rglob("*.html")):
        rel = path.relative_to(root).as_posix()
        if rel == "404.html":
            continue
        url = BASE_URL + ("/" if rel == "index.html" else f"/{rel}")
        if url in existing:
            continue
        entry = ElementTree.SubElement(node, f"{{{NS}}}url")
        ElementTree.SubElement(entry, f"{{{NS}}}loc").text = url
        existing.add(url)
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)


def refresh_candidate_manifest(root: Path) -> None:
    """Make the manifest describe the post-overlay, post-frontend candidate."""
    try:
        from tools import apply_final_release
    except ImportError:
        import apply_final_release  # type: ignore
    manifest_path = apply_final_release.MANIFEST
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Footnote: apply_final_release writes its manifest before this presentation
    # layer exists. Rewriting it here prevents a green deployment from carrying
    # a stale inventory/hash map after topic/org/detail surfaces are generated.
    apply_final_release.write_build_manifest(root, manifest["release"])
    apply_final_release.validate(root, manifest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--refresh-manifest", action="store_true")
    args = parser.parse_args(argv)
    root = args.site
    targets = [
        root / name for name in (
            "archive.html", "search.html", "topics.html", "organizations.html",
            "corrections.html", "feeds.html", "methodology.html", "editorial-policy.html",
            "automation.html", "accessibility.html", "status.html", "404.html",
        )
    ]
    targets += sorted((root / "topics").glob("*.html"))
    targets += sorted((root / "organizations").glob("*.html"))
    targets += [root / "news" / "index.html"]

    errors: list[str] = []
    touched = 0
    for path in targets:
        if not path.is_file():
            errors.append(f"missing generated frontend: {path.relative_to(root)}")
            continue
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        # Footnote: the Story builder's stable route is `news/en/FCMO-*.html`.
        # Repairing this before publication also protects no-JS readers/crawlers.
        text = text.replace("/news/en/STORY-", "/news/en/FCMO-")
        canonical = f'{BASE_URL}/{rel}'
        replacement = f'<link rel="canonical" href="{canonical}">'
        if CANONICAL.search(text):
            text = CANONICAL.sub(replacement, text, count=1)
        else:
            text = text.replace("</head>", replacement + "</head>", 1)
        dependencies = remote_exec_dependencies(text)
        if dependencies:
            errors.append(f"{rel}: remote executable/style dependency detected: {dependencies}")
        path.write_text(text, encoding="utf-8")
        touched += 1

    if errors:
        raise SystemExit("editorial frontend finalization FAILED:\n" + "\n".join(f"- {x}" for x in errors))
    augment_sitemap(root)
    if args.refresh_manifest:
        refresh_candidate_manifest(root)
    print(f"editorial frontend finalization OK; pages={touched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
