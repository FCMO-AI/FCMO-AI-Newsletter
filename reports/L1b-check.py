"""Offline route and data-preservation proof for the L1b merge candidate."""
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PUBLICATION = ROOT / "publish"
BASELINE = "78197c4"
V4 = "a89c952"


def git_bytes(ref, path):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lang = None
        self.h1 = 0
        self.urls = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "html":
            self.lang = values.get("lang")
        if tag == "h1":
            self.h1 += 1
        self.urls.extend(values[key] for key in ("href", "src") if values.get(key))


routes = json.loads((PUBLICATION / "data/routes.json").read_text())
config = json.loads((ROOT / "config/site.json").read_text())
base = config["base_path"]
origin = urlsplit(config["base_url"])
links = 0
for route in routes:
    path = PUBLICATION / route["path"] / "index.html"
    assert path.is_file(), path
    page = Page()
    page.feed(path.read_text())
    assert page.lang == route["locale"], (path, page.lang)
    assert page.h1, (path, "missing h1")
    for url in page.urls:
        parsed = urlsplit(url)
        if (parsed.scheme or parsed.netloc) and parsed.netloc != origin.netloc:
            continue
        if not parsed.path.startswith(base):
            continue
        links += 1
        target = PUBLICATION / unquote(parsed.path[len(base):])
        assert target.is_file() or (target / "index.html").is_file(), (route["path"], url)

for day in ("2026-10-03", "2026-10-04"):
    for prefix, locale in (("", "en"), ("es/", "es-419"), ("zh/", "zh-Hans")):
        route = next(row for row in routes if row["path"] == f"{prefix}edition/{day}/")
        assert route["locale"] == locale
        assert (PUBLICATION / prefix / "edition" / f"{day}.md").is_file()
    stub = (PUBLICATION / "editions" / f"{day}.html").read_text()
    assert f"{base}edition/{day}/" in stub
    assert (PUBLICATION / "api/v1/editions" / f"{day}.json").is_file()

ledger = "ops/publication-desk/LEDGER.jsonl"
expected = Counter(git_bytes(V4, ledger).splitlines()) | Counter(git_bytes(BASELINE, ledger).splitlines())
assert Counter((ROOT / ledger).read_bytes().splitlines()) == expected
preserved = 0
for prefix in ("corpus/", "release-src/data/editions/"):
    files = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASELINE, "--", prefix], cwd=ROOT
    ).decode().splitlines()
    for file in files:
        assert (ROOT / file).read_bytes() == git_bytes(BASELINE, file), file
        preserved += 1
print(json.dumps({"routes": len(routes), "local_links": links, "errors": 0,
                  "new_locale_editions": 6, "ledger_lines": sum(expected.values()),
                  "main_data_files_preserved": preserved}, indent=2))
