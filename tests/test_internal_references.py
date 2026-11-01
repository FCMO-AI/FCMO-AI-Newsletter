import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

from tools import build_newsroom_surfaces as newsroom
from tools.paper.build import PaperBuilder
from tools.paper.i18n import load_catalogs


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "FCMO-44B66AB54A44"
PUBLIC_REFERENCE_ID = "FCMO-EB438DED40B1"
PRIVATE_REFERENCE_ID = "FCMO-AAAAAAAAAAAA"


class VisibleLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.links = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "template"}:
            self.hidden += 1
        if tag == "a":
            self.links.append(dict(attrs))

    def handle_endtag(self, tag):
        if tag in {"script", "style", "template"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.text.append(data)


def corpus_fixture():
    for line in (ROOT / "corpus/data/developments.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("id") == SOURCE_ID:
            return row
    raise AssertionError(f"real corpus fixture {SOURCE_ID} is missing")


def brief_fixture():
    path = ROOT / "release-src/data/briefs" / f"{PUBLIC_REFERENCE_ID}.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    return value["brief"]


class InternalReferenceTests(unittest.TestCase):
    def render(self, locale, source, references):
        links = {key: f"https://example.test/news/{key}/{SOURCE_ID}.html"
                 for key in newsroom.LOCALES}
        story = {"story_type": "BRIEF", "published_at": "2026-11-01T00:00:00Z",
                 "event_at": "2026-11-01T00:00:00Z", "media": {}}
        return newsroom.article_html(locale, source, story, links, references=references)

    def test_real_corpus_reference_is_linked_and_unknown_id_is_localized(self):
        source = corpus_fixture()
        public_brief = brief_fixture()
        references = {PUBLIC_REFERENCE_ID: public_brief}
        for locale in ("en", "es-419", "zh-Hans"):
            with self.subTest(locale=locale):
                page = self.render(locale, source, references)
                parsed = VisibleLinks()
                parsed.feed(page)
                visible = " ".join(parsed.text)
                self.assertNotIn(PUBLIC_REFERENCE_ID, visible)
                self.assertIn(public_brief["title"], visible)
                slug = newsroom.LOCALES[locale]["slug"]
                self.assertTrue(any(link.get("href", "").endswith(
                    f"/news/{slug}/{PUBLIC_REFERENCE_ID}.html") for link in parsed.links))

                private_source = json.loads(json.dumps(source))
                private_source["technical"]["strongest_baseline"] = (
                    f"Another related report, {PRIVATE_REFERENCE_ID}."
                )
                private_page = self.render(locale, private_source, references)
                private_parsed = VisibleLinks()
                private_parsed.feed(private_page)
                private_visible = " ".join(private_parsed.text)
                self.assertNotIn(PRIVATE_REFERENCE_ID, private_visible)
                expected = {
                    "en": "a related FCMO AI note",
                    "es-419": "una nota relacionada de FCMO AI",
                    "zh-Hans": "FCMO AI 的一篇相关报道",
                }[locale]
                self.assertIn(expected, private_visible)

                paper = PaperBuilder.__new__(PaperBuilder)
                paper.base = "/FCMO-AI-Newsletter/"
                paper.catalogs = load_catalogs(ROOT)
                paper.public_references = {
                    PUBLIC_REFERENCE_ID: {
                        "research_id": PUBLIC_REFERENCE_ID,
                        "headline": public_brief["title"],
                        "title": public_brief["title"],
                        "slug": "related-public-note",
                        "url_date": "2026-10-27",
                    }
                }
                locale_config = {"code": locale, "path_prefix": {"en": "", "es-419": "es/", "zh-Hans": "zh/"}[locale]}
                rendered = paper._prose(source["technical"]["strongest_baseline"], locale_config)
                self.assertIn(public_brief["title"], rendered)
                self.assertIn("<a href=", rendered)
                self.assertNotIn(PUBLIC_REFERENCE_ID + "</", rendered)
                self.assertIn(expected, paper._prose(
                    f"An unpublished note, {PRIVATE_REFERENCE_ID}.", locale_config
                ))


if __name__ == "__main__":
    unittest.main()
