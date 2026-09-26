"""WP-A6: the visual desk refuses site chrome and page-level licences, stores
image-level licensed pictures locally with a credit, and otherwise falls back to
a language-neutral FCMO explainer. Every test runs offline with a fake web."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for entry in (REPO, REPO / "tests"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from tools import visual_desk as vd  # noqa: E402
from harness.validate import Validator  # noqa: E402

EXPLAINERS = REPO / "site-src" / "assets" / "explainers"
MEDIA_JSON = REPO / "site" / "data" / "media.json"
ARXIV_LOGO = "https://arxiv.org/static/browse/0.3.4/images/arxiv-logo-fb.png"
NOW = "2026-09-26T20:00:00Z"


def png(width: int, height: int, seed: int = 0) -> bytes:
    """A real, decodable grey PNG of the given size."""
    row = b"\x00" + bytes([seed % 256]) * width
    raw = zlib.compress(row * height, 9)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", raw) + chunk(b"IEND", b"")


def jpeg_header(width: int, height: int) -> bytes:
    sof = b"\xff\xc0" + struct.pack(">HBHHB", 11, 8, height, width, 1) + b"\x01\x11\x00"
    return b"\xff\xd8\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x00" * 9 + sof + b"\xff\xd9"


class FakeWeb:
    """``Fetcher`` stand-in: url -> (content type, body); anything else is a 404."""

    allow_private = False

    def __init__(self, pages: dict[str, tuple[str, bytes | str]]) -> None:
        self.pages = pages
        self.calls: list[str] = []

    def get(self, url: str, *, max_bytes: int, html_only: bool = False) -> vd.Response:
        self.calls.append(url)
        if url not in self.pages:
            raise vd.FetchError("FETCH_FAILED:HTTP_404")
        content_type, body = self.pages[url]
        if html_only and "html" not in content_type:
            raise vd.FetchError("NOT_HTML")
        data = body.encode("utf-8") if isinstance(body, str) else body
        if len(data) > max_bytes:
            raise vd.FetchError("FETCH_FAILED:TOO_LARGE")
        return vd.Response(url, content_type, data)


def page(*, og: str = "", alt: str = "", licence_link: str = "", ld: object | None = None) -> str:
    head = ['<html><head><title>Story</title>']
    if og:
        head.append(f'<meta property="og:image" content="{og}"/>')
    if alt:
        head.append(f'<meta property="og:image:alt" content="{alt}"/>')
    if ld is not None:
        head.append(f'<script type="application/ld+json">{json.dumps(ld)}</script>')
    head.append("</head><body><article><p>Body</p>")
    if licence_link:
        head.append(f'<a href="{licence_link}" title="Rights to this article">licence</a>')
    head.append("</article></body></html>")
    return "".join(head)


def commons_api(name: str, **meta: str) -> str:
    extmetadata = {key: {"value": value} for key, value in meta.items()}
    info = {
        "url": f"https://upload.wikimedia.org/wikipedia/commons/a/ab/{name}",
        "thumburl": f"https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/{name}/1600px-{name}",
        "descriptionurl": f"https://commons.wikimedia.org/wiki/File:{name}",
        "width": 3200,
        "height": 1800,
        "mime": "image/png",
        "extmetadata": extmetadata,
    }
    return json.dumps({"query": {"pages": [{"title": f"File:{name}", "imageinfo": [info]}]}})


def commons_api_url(name: str) -> str:
    query = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": "1600",
        "titles": f"File:{name}",
    }
    import urllib.parse

    return f"{vd.COMMONS_API}?{urllib.parse.urlencode(query)}"


def record(story_id: str, sources: list[str], **extra: object) -> dict:
    row = {"id": story_id, "title": "A story", "primary_desk": "evaluation_science", "development_type": "paper", "source_urls": sources}
    row.update(extra)
    return row


def media_schema() -> dict:
    schema = json.loads((REPO / "contracts" / "stories.v2.schema.json").read_text(encoding="utf-8"))
    return schema["$defs"]["story"]["properties"]["media"]


class DeskCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.site = Path(self.tmp.name) / "site"
        self.site.mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def resolve(self, records: list[dict], web: FakeWeb | None, previous: dict | None = None) -> vd.Outcome:
        return vd.resolve_media(records, site=self.site, previous=previous or {}, fetcher=web, now=NOW)

    def reasons(self, row: dict) -> list[str]:
        return [item["reason"] for item in row.get("rejected_candidates", [])]


class ChromeAndPageLicence(DeskCase):
    def test_arxiv_logo_under_a_paper_licence_falls_back_to_explainer(self) -> None:
        src = "https://arxiv.org/abs/2609.13134"
        web = FakeWeb({src: ("text/html", page(og="/static/browse/0.3.4/images/arxiv-logo-fb.png", alt="arXiv logo",
                                                licence_link="http://creativecommons.org/licenses/by/4.0/")),
                       ARXIV_LOGO: ("image/png", png(1200, 700))})
        row = self.resolve([record("FCMO-7EBD0FA07C12", [src])], web).rows[0]
        self.assertEqual(row["mode"], "fcmo_explainer")
        self.assertIn("SITE_CHROME:LOGO_PATH", self.reasons(row))
        self.assertNotIn(ARXIV_LOGO, web.calls, "a logo is refused before any download")
        self.assertNotIn("arxiv-logo", json.dumps(row))
        self.assertEqual(row["credit"], "FCMO AI")
        self.assertFalse(row["evidence_image"])

    def test_page_licence_never_licenses_the_share_image(self) -> None:
        src = "https://example.org/2026/story"
        photo = "https://example.org/uploads/2026/09/turbine-hall.jpg"
        web = FakeWeb({src: ("text/html", page(og=photo, licence_link="https://creativecommons.org/licenses/by/4.0/")),
                       photo: ("image/png", png(1600, 900))})
        row = self.resolve([record("FCMO-000000000001", [src])], web).rows[0]
        self.assertEqual(row["mode"], "fcmo_explainer")
        self.assertEqual(self.reasons(row), ["LICENSE:PAGE_ONLY"])
        self.assertNotIn(photo, web.calls)

    def test_generated_share_cards_are_chrome(self) -> None:
        for url in (
            "https://cdn-thumbnails.huggingface.co/social-thumbnails/datasets/IFM/TxT360-v2.png",
            "https://opengraph.githubassets.com/abc/owner/repo",
            "https://repository-images.githubusercontent.com/1/2",
            "https://static.arxiv.org/icons/twitter/arxiv-logo-twitter-square.png",
        ):
            with self.subTest(url=url):
                self.assertEqual(vd.chrome_reason(url), "SITE_CHROME:GENERATED_CARD")

    def test_logo_like_paths_and_alt_text_are_chrome(self) -> None:
        for url in (
            "https://www.example.com/assets/img/logo.png",
            "https://www.example.com/favicon-512.png",
            "https://www.example.com/images/default-og.jpg",
            "https://www.example.com/static/twitter-card.png",
            "https://www.example.com/img/apple-touch-icon.png",
            "https://upload.wikimedia.org/wikipedia/commons/a/ab/Seal_of_the_NSA.svg",
        ):
            with self.subTest(url=url):
                self.assertEqual(vd.chrome_reason(url), "SITE_CHROME:LOGO_PATH")
        self.assertEqual(vd.chrome_reason("https://www.example.com/p/hero.jpg", "Company logo"), "SITE_CHROME:LOGO_ALT")
        self.assertIsNone(vd.chrome_reason("https://www.example.com/2026/09/datacenter-hall.jpg", "A data hall"))
        self.assertIsNone(vd.chrome_reason("https://upload.wikimedia.org/wikipedia/commons/a/ab/Silicon_wafer.jpg"))

    def test_one_image_on_two_pages_is_site_chrome(self) -> None:
        shared = "https://news.example.org/media/house-style.jpg"
        ld = {"@type": "ImageObject", "contentUrl": shared, "license": "https://creativecommons.org/licenses/by/4.0/",
              "creditText": "Example News"}
        web = FakeWeb({
            "https://news.example.org/a": ("text/html", page(ld=ld)),
            "https://news.example.org/b": ("text/html", page(ld=ld)),
            shared: ("image/png", png(1600, 900)),
        })
        rows = self.resolve([record("FCMO-000000000001", ["https://news.example.org/a"]),
                             record("FCMO-000000000002", ["https://news.example.org/b"])], web).rows
        for row in rows:
            self.assertEqual(row["mode"], "fcmo_explainer")
            self.assertIn("SITE_CHROME:REPEATED", self.reasons(row))

    def test_publisher_logo_in_json_ld_is_never_a_candidate(self) -> None:
        ld = {"@type": "NewsArticle", "publisher": {"@type": "Organization", "logo": {
            "@type": "ImageObject", "url": "https://news.example.org/p/mark.png",
            "license": "https://creativecommons.org/licenses/by/4.0/", "creditText": "Example"}}}
        parsed = vd.parse_page(vd.Response("https://news.example.org/a", "text/html", page(ld=ld).encode()))
        self.assertEqual(parsed.candidates, [])

    def test_non_public_hosts_and_schemes_are_refused(self) -> None:
        self.assertEqual(vd.url_refusal("http://127.0.0.1/x"), "URL:NON_PUBLIC_HOST")
        self.assertEqual(vd.url_refusal("http://10.1.2.3/x"), "URL:NON_PUBLIC_HOST")
        self.assertEqual(vd.url_refusal("http://localhost/x"), "URL:NON_PUBLIC_HOST")
        self.assertEqual(vd.url_refusal("file:///etc/passwd"), "URL:UNSUPPORTED")
        self.assertIsNone(vd.url_refusal("https://arxiv.org/abs/2609.13134"))
        row = self.resolve([record("FCMO-000000000001", ["http://169.254.169.254/latest"])], FakeWeb({})).rows[0]
        self.assertEqual(self.reasons(row), ["URL:NON_PUBLIC_HOST"])

    def test_non_html_sources_and_fetch_failures_fall_back(self) -> None:
        web = FakeWeb({"https://example.gov/report.pdf": ("application/pdf", b"%PDF-1.7")})
        row = self.resolve([record("FCMO-000000000001", ["https://example.gov/report.pdf", "https://gone.example/x"])], web).rows[0]
        self.assertEqual(row["mode"], "fcmo_explainer")
        self.assertEqual(self.reasons(row), ["NOT_HTML", "FETCH_FAILED:HTTP_404"])


COMMONS_NAME = "Data_center_hall_2026.png"


def commons_web(**meta: str) -> FakeWeb:
    """A Wikipedia article whose lead image is a Commons file with the given metadata."""
    name = COMMONS_NAME
    article = "https://en.wikipedia.org/wiki/Data_center"
    og = f"https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/{name}/1200px-{name}"
    thumb = f"https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/{name}/1600px-{name}"
    return FakeWeb({
        article: ("text/html", page(og=og, licence_link="https://creativecommons.org/licenses/by-sa/4.0/")),
        commons_api_url(name): ("application/json", commons_api(name, **meta)),
        thumb: ("image/png", png(1600, 900, seed=7)),
    })


class ImageLevelLicences(DeskCase):
    NAME = COMMONS_NAME

    def commons_web(self, **meta: str) -> FakeWeb:
        return commons_web(**meta)

    def test_commons_file_licence_is_stored_locally_with_credit(self) -> None:
        web = self.commons_web(LicenseUrl="https://creativecommons.org/licenses/by-sa/4.0", LicenseShortName="CC BY-SA 4.0",
                               Artist='<a href="//commons.wikimedia.org/wiki/User:Jane">Jane Doe</a>')
        outcome = self.resolve([record("FCMO-00000000000A", ["https://en.wikipedia.org/wiki/Data_center"])], web)
        row = outcome.rows[0]
        self.assertEqual(row["mode"], "licensed_source", row)
        self.assertEqual(row["rights_basis"], "COMMONS_FILE_METADATA")
        self.assertEqual(row["credit"], "Jane Doe / Wikimedia Commons")
        self.assertEqual(row["license"], "CC BY-SA 4.0")
        self.assertEqual(row["source_url"], f"https://commons.wikimedia.org/wiki/File:{self.NAME}")
        self.assertTrue(row["local_path"].startswith("media/FCMO-00000000000A-"))
        self.assertEqual((row["width"], row["height"]), (1600, 900))
        self.assertEqual(row["media"]["kind"], "licensed")
        self.assertEqual(Validator(media_schema()).errors(row["media"]), [])
        # Stored locally, never hotlinked; the receipt validates against the file.
        vd.store_blobs(self.site, outcome.blobs)
        stored = self.site / row["local_path"]
        self.assertEqual(hashlib.sha256(stored.read_bytes()).hexdigest(), row["sha256"])
        vd.validate_media_rows(outcome.rows, {"FCMO-00000000000A"}, self.site, EXPLAINERS)
        self.assertNotIn("upload.wikimedia.org", row["image_url"])

    def test_commons_non_permissive_restricted_or_uncredited_files_are_refused(self) -> None:
        cases = {
            "LICENSE:NOT_PERMISSIVE": dict(LicenseUrl="https://creativecommons.org/licenses/by-nc/4.0/", Artist="Jane"),
            "LICENSE:RESTRICTED": dict(LicenseUrl="https://creativecommons.org/licenses/by/4.0/", Artist="Jane", Restrictions="trademarked"),
            "LICENSE:NO_CREDIT": dict(LicenseUrl="https://creativecommons.org/licenses/by/4.0/"),
        }
        for code, meta in cases.items():
            with self.subTest(code=code):
                row = self.resolve([record("FCMO-00000000000A", ["https://en.wikipedia.org/wiki/Data_center"])],
                                   self.commons_web(**meta)).rows[0]
                self.assertEqual(row["mode"], "fcmo_explainer")
                self.assertEqual(self.reasons(row), [code])

    def test_json_ld_image_object_licence(self) -> None:
        src = "https://lab.example.org/blog/result"
        image = "https://lab.example.org/files/result-figure.png"
        ld = {"@context": "https://schema.org", "@type": "BlogPosting", "image": {
            "@type": "ImageObject", "contentUrl": image, "license": "https://creativecommons.org/licenses/by/4.0/",
            "creditText": "Example Lab", "acquireLicensePage": "https://lab.example.org/licensing"}}
        web = FakeWeb({src: ("text/html", page(ld=ld)), image: ("image/png", png(1920, 1080, seed=3))})
        row = self.resolve([record("FCMO-00000000000B", [src])], web).rows[0]
        self.assertEqual(row["mode"], "licensed_source")
        self.assertEqual(row["rights_basis"], "JSONLD_IMAGEOBJECT_LICENSE")
        self.assertEqual((row["credit"], row["license"]), ("Example Lab", "CC BY 4.0"))
        self.assertEqual(row["source_url"], "https://lab.example.org/licensing")
        self.assertEqual(row["source_page"], src)

    def test_json_ld_nc_nd_or_uncredited_image_is_refused(self) -> None:
        src = "https://lab.example.org/blog/result"
        image = "https://lab.example.org/files/result-figure.png"
        for licence, credit, code in (
            ("https://creativecommons.org/licenses/by-nc/4.0/", "Lab", "LICENSE:NOT_PERMISSIVE"),
            ("https://creativecommons.org/licenses/by-nd/4.0/", "Lab", "LICENSE:NOT_PERMISSIVE"),
            ("https://example.org/terms", "Lab", "LICENSE:NOT_PERMISSIVE"),
            ("https://creativecommons.org/licenses/by/4.0/", "", "LICENSE:NO_CREDIT"),
        ):
            with self.subTest(licence=licence, credit=credit):
                ld = {"@type": "ImageObject", "contentUrl": image, "license": licence, "creditText": credit}
                web = FakeWeb({src: ("text/html", page(ld=ld)), image: ("image/png", png(1920, 1080))})
                row = self.resolve([record("FCMO-00000000000B", [src])], web).rows[0]
                self.assertEqual(row["mode"], "fcmo_explainer")
                self.assertEqual(self.reasons(row), [code])

    def test_pixels_must_be_a_raster_landscape_hero(self) -> None:
        src = "https://lab.example.org/blog/result"
        image = "https://lab.example.org/files/result-figure.png"
        ld = {"@type": "ImageObject", "contentUrl": image, "license": "https://creativecommons.org/licenses/by/4.0/",
              "creditText": "Lab"}
        for body, code in (
            (png(256, 256), "SITE_CHROME:ICON_SIZE"),
            (png(1000, 1000), "SITE_CHROME:SQUARE_MARK"),
            (png(700, 420), "IMAGE:TOO_SMALL"),
            (png(900, 1600), "IMAGE:NOT_LANDSCAPE"),
            (png(3000, 600), "IMAGE:BANNER_SHAPE"),
            (b'<svg xmlns="http://www.w3.org/2000/svg"/>', "IMAGE:NOT_RASTER"),
        ):
            with self.subTest(code=code):
                web = FakeWeb({src: ("text/html", page(ld=ld)), image: ("image/png", body)})
                row = self.resolve([record("FCMO-00000000000B", [src])], web).rows[0]
                self.assertEqual(self.reasons(row), [code])

    def test_image_header_parsing(self) -> None:
        self.assertEqual(vd.image_info(png(1600, 900)), ("png", 1600, 900))
        self.assertEqual(vd.image_info(jpeg_header(1280, 720)), ("jpg", 1280, 720))
        webp = b"RIFF" + struct.pack("<I", 30) + b"WEBPVP8X" + struct.pack("<I", 10) + b"\x00" * 4 + (1199).to_bytes(3, "little") + (629).to_bytes(3, "little")
        self.assertEqual(vd.image_info(webp), ("webp", 1200, 630))
        self.assertIsNone(vd.image_info(b"GIF89a...."))


class CarryForward(DeskCase):
    def test_legacy_hotlinked_licensed_rows_are_not_grandfathered(self) -> None:
        old = {"id": "FCMO-179D8B7D7D2D", "mode": "licensed_source", "sourced": True, "rights_state": "PERMISSIVE_LICENSE",
               "image_url": ARXIV_LOGO, "source_page": "https://arxiv.org/abs/2609.06649",
               "license_url": "http://creativecommons.org/licenses/by/4.0/", "credit": "arxiv.org",
               "reuse_basis": "machine-verifiable permissive license on the source page"}
        row = self.resolve([record("FCMO-179D8B7D7D2D", ["https://arxiv.org/abs/2609.06649"])], None,
                           {"FCMO-179D8B7D7D2D": old}).rows[0]
        self.assertEqual(row["mode"], "fcmo_explainer")
        self.assertNotIn("arxiv-logo", json.dumps(row))

    def licensed_previous(self) -> dict:
        web = commons_web(LicenseUrl="https://creativecommons.org/licenses/by/4.0/", Artist="Jane")
        outcome = self.resolve([record("FCMO-00000000000A", ["https://en.wikipedia.org/wiki/Data_center"])], web)
        vd.store_blobs(self.site, outcome.blobs)
        return outcome.rows[0]

    def test_valid_licensed_row_survives_an_offline_run(self) -> None:
        previous = self.licensed_previous()
        self.assertEqual(previous["mode"], "licensed_source")
        row = self.resolve([record("FCMO-00000000000A", [])], None, {previous["id"]: previous}).rows[0]
        self.assertEqual(row["mode"], "licensed_source")
        self.assertEqual(row["sha256"], previous["sha256"])

    def test_tampered_local_file_is_not_carried_forward(self) -> None:
        previous = self.licensed_previous()
        (self.site / previous["local_path"]).write_bytes(png(1600, 900, seed=99))
        row = self.resolve([record("FCMO-00000000000A", [])], None, {previous["id"]: previous}).rows[0]
        self.assertEqual(row["mode"], "fcmo_explainer")

    def test_prune_removes_only_unreferenced_desk_files(self) -> None:
        media = self.site / "media"
        media.mkdir()
        (media / "FCMO-00000000000A-0123456789ab.png").write_bytes(b"x")
        (media / "README.txt").write_text("keep", encoding="utf-8")
        removed = vd.prune_media(self.site, [])
        self.assertEqual(removed, ["FCMO-00000000000A-0123456789ab.png"])
        self.assertTrue((media / "README.txt").exists())


class Validation(unittest.TestCase):
    def test_licensed_rows_need_local_media_credit_and_image_level_basis(self) -> None:
        bogus = {"id": "FCMO-00000000000C", "mode": "licensed_source", "sourced": True, "rights_state": "PERMISSIVE_LICENSE",
                 "image_url": ARXIV_LOGO, "license_url": "http://creativecommons.org/licenses/by/4.0/",
                 "reuse_basis": "page licence", "credit": "", "source_page": "https://arxiv.org/abs/1"}
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError) as caught:
            vd.validate_media_rows([bogus], {"FCMO-00000000000C"}, Path(tmp))
        message = str(caught.exception)
        for fragment in ("image-level licence", "lacks local_path", "lacks credit", "site chrome"):
            self.assertIn(fragment, message)

    def test_hotlinked_local_path_is_refused(self) -> None:
        row = {"id": "FCMO-00000000000C", "mode": "licensed_source", "sourced": True, "rights_state": "PERMISSIVE_LICENSE",
               "license_url": "https://creativecommons.org/licenses/by/4.0/", "rights_basis": "COMMONS_FILE_METADATA",
               "local_path": "https://upload.wikimedia.org/x.jpg", "credit": "Jane", "license": "CC BY 4.0",
               "source_url": "https://commons.wikimedia.org/wiki/File:X.jpg", "sha256": "0" * 64, "width": 1600, "height": 900}
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError, "under media/"):
            vd.validate_media_rows([row], {"FCMO-00000000000C"}, Path(tmp))

    def test_ids_must_match_exactly(self) -> None:
        row = vd.explainer_row("FCMO-00000000000D", "research", [])
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError, "missing=.*FCMO-00000000000E"):
            vd.validate_media_rows([row], {"FCMO-00000000000D", "FCMO-00000000000E"}, Path(tmp), EXPLAINERS)


class Explainers(unittest.TestCase):
    def test_committed_explainers_match_the_generator(self) -> None:
        self.assertEqual(vd.check_explainers(EXPLAINERS), [])
        self.assertEqual(len(list(EXPLAINERS.glob("*.svg"))), len(vd.BEATS) * vd.EXPLAINER_VARIANTS)

    def test_explainers_are_language_neutral_safe_and_small(self) -> None:
        for path in sorted(EXPLAINERS.glob("*.svg")):
            with self.subTest(file=path.name):
                svg = path.read_text(encoding="utf-8")
                self.assertLessEqual(len(svg.encode("utf-8")), vd.EXPLAINER_MAX_BYTES)
                self.assertIn('viewBox="0 0 1200 630"', svg)
                for banned in ("<text", "foreignObject", "<script", "href", "on" + "load", "—", "/10"):
                    self.assertNotIn(banned, svg)
                self.assertIsNone(re.search(r"https?://(?!www\.w3\.org/2000/svg)", svg))

    def test_contract_fixture_explainer_paths_exist(self) -> None:
        stories = json.loads((REPO / "contracts" / "fixtures" / "stories.v2.json").read_text(encoding="utf-8"))["stories"]
        for story in stories:
            media = story.get("media")
            if media and media["kind"] == "explainer":
                self.assertTrue((REPO / "site-src" / media["local_path"]).is_file(), media["local_path"])

    def test_explainer_rows_fit_the_stories_v2_media_contract(self) -> None:
        validator = Validator(media_schema())
        for beat in vd.BEATS:
            row = vd.explainer_row("FCMO-00000000000F", beat, [])
            self.assertEqual(validator.errors(row["media"]), [])
            self.assertTrue((REPO / "site-src" / row["local_path"]).is_file())
            self.assertEqual(set(row["alt"]), set(vd.LOCALES))
            self.assertIn("not source evidence", row["alt"]["en"])

    def test_variant_choice_is_deterministic(self) -> None:
        paths = {vd.explainer_for(f"FCMO-{n:012X}", "research") for n in range(40)}
        self.assertEqual(len(paths), vd.EXPLAINER_VARIANTS)
        self.assertEqual(vd.explainer_for("FCMO-7EBD0FA07C12", "research"), vd.explainer_for("FCMO-7EBD0FA07C12", "research"))


class Beats(unittest.TestCase):
    def test_beat_precedence(self) -> None:
        self.assertEqual(vd.resolve_beat({"beat": "society", "development_type": "paper"}), "society")
        self.assertEqual(vd.resolve_beat({"development_type": "policy_security", "primary_desk": "labs_industry"}), "policy")
        self.assertEqual(vd.resolve_beat({"development_type": "industry_transaction"}), "business")
        self.assertEqual(vd.resolve_beat({"development_type": "model_or_system_release"}), "technology")
        self.assertEqual(vd.resolve_beat({"development_type": "paper"}), "research")
        self.assertEqual(vd.resolve_beat({}), "technology")


class CorpusCommand(unittest.TestCase):
    def run_main(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = vd.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_dry_run_prints_rows_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp) / "site"
            code, out, err = self.run_main(["--corpus", str(REPO / "contracts" / "fixtures" / "corpus-43"), "--site", str(site),
                                            "--explainers", str(EXPLAINERS), "--dry-run", "--offline"])
            self.assertEqual(code, 0)
            rows = json.loads(out)
            self.assertEqual(len(rows), 43)
            self.assertIn("DRY-RUN licensed=0 explainer=43 total=43 rights=PASS", err)
            self.assertFalse(site.exists())

    def test_write_mode_covers_corpus_and_carried_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus"
            (corpus / "data").mkdir(parents=True)
            source = (REPO / "contracts" / "fixtures" / "corpus-43" / "data" / "developments.jsonl").read_text(encoding="utf-8")
            (corpus / "data" / "developments.jsonl").write_text(source, encoding="utf-8")
            carried = (REPO / "contracts" / "fixtures" / "corpus-carried.example.jsonl").read_text(encoding="utf-8")
            (corpus / "carried.jsonl").write_text(carried, encoding="utf-8")
            site = Path(tmp) / "site"
            code, out, _ = self.run_main(["--corpus", str(corpus), "--site", str(site), "--explainers", str(EXPLAINERS),
                                          "--offline", "--now", NOW])
            self.assertEqual(code, 0)
            self.assertIn("visual desk OK licensed=0 explainer=44 total=44", out)
            rows = json.loads((site / "data" / "media.json").read_text(encoding="utf-8"))
            self.assertIn("FCMO-FDBE3D996243", {row["id"] for row in rows})

    def test_committed_media_json_is_rights_clean(self) -> None:
        # Rights and shape only: the refresh pipeline, not this test, keeps the id
        # set in step with a corpus that changes every day.
        rows = json.loads(MEDIA_JSON.read_text(encoding="utf-8"))
        vd.validate_media_rows(rows, {row["id"] for row in rows}, REPO / "site", EXPLAINERS)
        self.assertNotIn("arxiv-logo", MEDIA_JSON.read_text(encoding="utf-8"))
        validator = Validator(media_schema())
        for row in rows:
            self.assertEqual(validator.errors(row["media"]), [], row["id"])
            if row["mode"] == "licensed_source":
                self.assertTrue(row["local_path"].startswith("media/"))
                self.assertTrue(row["credit"].strip())

    def test_legacy_mode_explainer_has_no_empty_score_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            release = Path(tmp) / "release-src"
            (release / "data" / "briefs").mkdir(parents=True)
            brief = {"id": "FCMO-000000000010", "title": "Untitled score", "source_urls": []}
            (release / "data" / "briefs" / "FCMO-000000000010.json").write_text(json.dumps({"brief": brief}), encoding="utf-8")
            site = Path(tmp) / "site"
            code, out, _ = self.run_main(["--release-src", str(release), "--site", str(site), "--offline"])
            self.assertEqual(code, 0)
            svg = (site / "assets" / "story-media" / "FCMO-000000000010.svg").read_text(encoding="utf-8")
            self.assertNotIn("—/10", svg)
            self.assertNotIn("EVIDENCE —", svg)
            self.assertIn("not source evidence", svg)


if __name__ == "__main__":
    unittest.main()
