from __future__ import annotations

import base64
import hashlib
from html.parser import HTMLParser
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit

from tests.harness.mock_ghost import MockGhost, unreachable_url
from tools.paper import community


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "contracts" / "fixtures"
CONTENT_PATH = "/ghost/api/content/posts/"


def loopback_sockets_available() -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM):
            return True
    except OSError:
        return False


LOOPBACK_SOCKETS = loopback_sockets_available()
requires_loopback = unittest.skipUnless(LOOPBACK_SOCKETS, "sandbox blocks loopback sockets; verifier reruns outside")


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str | None]] = []
        self.scripts: list[dict[str, str | None]] = []
        self.inputs = 0
        self.forms = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "a":
            self.links.append(values)
        elif tag == "script":
            self.scripts.append(values)
        elif tag == "input":
            self.inputs += 1
        elif tag == "form":
            self.forms += 1


class BadResponse:
    def __init__(self, body: bytes, status: int = 200) -> None:
        self.body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return None

    def getcode(self) -> int:
        return self.status

    def read(self, _limit: int) -> bytes:
        return self.body


class CommunityAdapterTests(unittest.TestCase):
    def test_projection_and_sorting_without_a_socket(self):
        payload = b'''{"posts":[
          {"title":"Second","url":"https://community.example/second/","custom_excerpt":"Two","published_at":"2026-09-22T12:00:00.000Z","feature_image":"https://community.example/content/images/two.jpg","email":"private@example.com","members":["private"]},
          {"title":"First","url":"https://community.example/first/","custom_excerpt":null,"published_at":"2026-09-23T12:00:00.000Z","feature_image":"https://tracker.example/one.jpg"},
          {"title":"Third","url":"https://community.example/third/","custom_excerpt":"Three","published_at":"2026-09-21T12:00:00.000Z","feature_image":null},
          {"title":"Too old","url":"https://community.example/old/","custom_excerpt":"Old","published_at":"2026-09-20T12:00:00.000Z","feature_image":null}
        ]}'''
        with patch("tools.paper.community.urlopen", return_value=BadResponse(payload)) as opened:
            posts = community.fetch_cartas("https://community.example/ghost/api/content/", "fake-key")
        self.assertEqual([post["title"] for post in posts], ["First", "Second", "Third"])
        self.assertEqual(set(posts[0]), {"title", "url", "custom_excerpt", "published_at", "feature_image"})
        self.assertNotIn("email", posts[0])
        self.assertIsNone(posts[0]["feature_image"])
        request = opened.call_args.args[0]
        self.assertIn("filter=tag%3Acartas", request.full_url)
        self.assertIn("limit=3", request.full_url)
        self.assertNotIn("admin", request.full_url)
        self.assertEqual(opened.call_args.kwargs["timeout"], 5.0)

    def test_http_connection_and_timeout_failures_without_a_socket(self):
        failures = (
            HTTPError("https://community.example", 400, "bad request", {}, None),
            HTTPError("https://community.example", 503, "unavailable", {}, None),
            URLError("connection refused"),
            TimeoutError("timed out"),
        )
        for failure in failures:
            with self.subTest(failure=type(failure).__name__, detail=str(failure)):
                with patch("tools.paper.community.urlopen", side_effect=failure):
                    self.assertEqual(community.fetch_cartas("https://community.example/ghost/api/content/", "fake-key"), [])

    def test_missing_key_short_circuits_without_a_socket(self):
        with patch("tools.paper.community.urlopen") as opened:
            self.assertEqual(community.fetch_cartas("https://community.example/ghost/api/content/", None), [])
            self.assertEqual(community.fetch_cartas("https://community.example/ghost/api/content/", ""), [])
        opened.assert_not_called()

    @requires_loopback
    def test_content_api_returns_three_newest_allowlisted_fields_only(self):
        with MockGhost() as ghost:
            ghost.seed_cartas(4)
            posts = community.fetch_cartas(ghost.content_url, ghost.content_key)

            self.assertEqual([post["title"] for post in posts], ["Carta de prueba 4", "Carta de prueba 3", "Carta de prueba 2"])
            self.assertTrue(all(set(post) == {"title", "url", "custom_excerpt", "published_at", "feature_image"} for post in posts))
            self.assertEqual(ghost.count("GET", CONTENT_PATH), 1)
            self.assertEqual(ghost.count(path="/ghost/api/admin/"), 0)
            request = next(row for row in ghost.requests if row["path"] == CONTENT_PATH)
            self.assertEqual(request["query"]["filter"], "tag:cartas")
            self.assertEqual(request["query"]["limit"], "3")
            self.assertEqual(request["query"]["fields"], "title,url,custom_excerpt,published_at,feature_image")

    @requires_loopback
    def test_missing_key_is_normal_empty_result_without_request(self):
        with MockGhost() as ghost:
            ghost.seed_cartas(1)
            self.assertEqual(community.fetch_cartas(ghost.content_url, None), [])
            self.assertEqual(community.fetch_cartas(ghost.content_url, ""), [])
            self.assertEqual(ghost.count(), 0)

    @requires_loopback
    def test_4xx_and_5xx_are_normal_empty_results(self):
        with MockGhost() as ghost:
            ghost.seed_cartas(1)
            self.assertEqual(community.fetch_cartas(ghost.content_url, "wrong-key"), [])
            self.assertEqual(ghost.count("GET", CONTENT_PATH, 401), 1)
            for status in (404, 500, 503):
                with self.subTest(status=status):
                    ghost.fail(status=status, method="GET", path=CONTENT_PATH)
                    self.assertEqual(community.fetch_cartas(ghost.content_url, ghost.content_key), [])

    @requires_loopback
    def test_timeout_is_bounded_and_normal_empty_result(self):
        self.assertEqual(community.DEFAULT_TIMEOUT_SECONDS, 5.0)
        with MockGhost() as ghost:
            ghost.seed_cartas(1)
            ghost.fail(mode="timeout", seconds=0.4, method="GET", path=CONTENT_PATH)
            started = time.monotonic()
            self.assertEqual(community.fetch_cartas(ghost.content_url, ghost.content_key, timeout=0.05), [])
            self.assertLess(time.monotonic() - started, 0.3)

    def test_malformed_payloads_are_normal_empty_results(self):
        payloads = (
            b"not-json",
            b"[]",
            b'{}',
            b'{"posts": {}}',
            b'{"posts": [null]}',
            b'{"posts": [{"title": "Carta", "url": "javascript:alert(1)", "published_at": "bad"}]}',
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                with patch("tools.paper.community.urlopen", return_value=BadResponse(payload)):
                    self.assertEqual(community.fetch_cartas("https://community.example/ghost/api/content/", "fake-key"), [])

    @requires_loopback
    def test_connection_failure_is_normal_empty_result(self):
        self.assertEqual(community.fetch_cartas(unreachable_url() + "/ghost/api/content/", "fake-key", timeout=0.1), [])

    @requires_loopback
    def test_feature_images_are_same_origin_only(self):
        with MockGhost() as ghost:
            local = ghost.url + "/content/images/carta.jpg"
            ghost.seed_post("Local image", tags=("cartas",), feature_image=local)
            ghost.seed_post("Foreign image", tags=("cartas",), feature_image="https://tracker.example/member.png?email=reader@example.com")
            by_title = {post["title"]: post for post in community.fetch_cartas(ghost.content_url, ghost.content_key)}
            self.assertEqual(by_title["Local image"]["feature_image"], local)
            self.assertIsNone(by_title["Foreign image"]["feature_image"])


class CommunityBuildTests(unittest.TestCase):
    def build(self, env: dict[str, str] | None = None) -> tuple[tempfile.TemporaryDirectory, Path, subprocess.CompletedProcess[str]]:
        temp = tempfile.TemporaryDirectory(prefix="wpB2-")
        out = Path(temp.name) / "publish"
        # These are Ghost/portal fixtures, including explicit empty-rail cases.
        # Never inherit whichever human essays happen to be in the checkout
        # (in production this suite also runs on a Studio publication candidate).
        editorial = Path(temp.name) / "editorial"
        editorial.mkdir()
        clean_env = os.environ.copy()
        for name in ("GHOST_CONTENT_URL", "GHOST_CONTENT_API_KEY", "GHOST_PORTAL_URL"):
            clean_env.pop(name, None)
        clean_env.update(env or {})
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "paper" / "build.py"),
                "--stories", str(FIXTURES / "stories.v2.json"),
                "--status", str(FIXTURES / "newsroom-status.fresh.json"),
                "--editorial", str(editorial),
                "--out", str(out),
                "--base", "/FCMO-AI-Newsletter/",
            ],
            cwd=ROOT,
            env=clean_env,
            text=True,
            capture_output=True,
            check=False,
        )
        return temp, out, result

    def test_inactive_state_has_no_form_dead_action_or_empty_cartas_box(self):
        temp, out, result = self.build()
        self.addCleanup(temp.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = {
            "index.html": "Subscriptions are coming soon",
            "es/index.html": "Las suscripciones llegarán pronto",
            "zh/index.html": "订阅即将开放",
        }
        for rel, message in expected.items():
            with self.subTest(rel=rel):
                text = (out / rel).read_text(encoding="utf-8")
                parser = LinkParser()
                parser.feed(text)
                self.assertIn(message, text)
                self.assertEqual(parser.inputs, 0)
                self.assertEqual(parser.forms, 0)
                self.assertNotIn("data-ghost-portal", text)
                self.assertNotIn('data-slot="cartas"', text)
                hrefs = {link.get("href") for link in parser.links}
                prefix = "/FCMO-AI-Newsletter/" + ({"es/index.html": "es/", "zh/index.html": "zh/"}.get(rel, ""))
                self.assertIn(prefix + "feed.xml", hrefs)
                self.assertIn(prefix + "feed.atom", hrefs)

    def test_configured_spanish_state_keeps_a_valid_no_js_portal_link(self):
        portal = "https://comunidad.example/#/portal/signup"
        temp, out, result = self.build({"GHOST_PORTAL_URL": portal})
        self.addCleanup(temp.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        for rel in ("es/index.html", "es/suscribete/index.html"):
            text = (out / rel).read_text(encoding="utf-8")
            parser = LinkParser()
            parser.feed(text)
            portal_links = [link for link in parser.links if link.get("data-ghost-portal") == "signup"]
            self.assertEqual(len(portal_links), 1, rel)
            self.assertEqual(portal_links[0]["href"], portal)
            split = urlsplit(portal_links[0]["href"])
            self.assertEqual((split.scheme, split.netloc, split.fragment), ("https", "comunidad.example", "/portal/signup"))
            self.assertEqual(parser.forms, 0)
            self.assertEqual(parser.inputs, 0)
        for rel in ("index.html", "zh/index.html", "suscribete/index.html", "zh/suscribete/index.html"):
            self.assertNotIn(portal, (out / rel).read_text(encoding="utf-8"), rel)

    def test_progressive_enhancement_is_first_party_and_hash_pinned(self):
        temp, out, result = self.build({"GHOST_PORTAL_URL": "https://comunidad.example"})
        self.addCleanup(temp.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        parser = LinkParser()
        parser.feed((out / "es" / "index.html").read_text(encoding="utf-8"))
        scripts = [script for script in parser.scripts if script.get("src", "").endswith("assets/js/subscribe.js")]
        self.assertEqual(len(scripts), 1)
        expected = "sha384-" + base64.b64encode(hashlib.sha384((out / "assets" / "js" / "subscribe.js").read_bytes()).digest()).decode("ascii")
        self.assertEqual(scripts[0].get("integrity"), expected)
        self.assertTrue(scripts[0]["src"].startswith("/FCMO-AI-Newsletter/"))
        self.assertNotIn("http", (out / "assets" / "js" / "subscribe.js").read_text(encoding="utf-8"))

    @requires_loopback
    def test_cartas_rail_uses_content_api_and_builds_newest_first(self):
        with MockGhost() as ghost:
            ghost.seed_cartas(4)
            temp, out, result = self.build({
                "GHOST_CONTENT_URL": ghost.content_url,
                "GHOST_CONTENT_API_KEY": ghost.content_key,
            })
            self.addCleanup(temp.cleanup)
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (out / "es" / "index.html").read_text(encoding="utf-8")
            self.assertEqual(text.count("Resumen de la carta"), 3)
            positions = [text.index(f"Carta de prueba {number}") for number in (4, 3, 2)]
            self.assertEqual(positions, sorted(positions))
            self.assertIn('data-slot="cartas"', text)
            self.assertEqual(ghost.count("GET", CONTENT_PATH), 1)
            self.assertEqual(ghost.count(path="/ghost/api/admin/"), 0)

    @requires_loopback
    def test_failed_content_api_does_not_fail_build(self):
        with MockGhost() as ghost:
            ghost.fail(status=503, method="GET", path=CONTENT_PATH)
            temp, out, result = self.build({
                "GHOST_CONTENT_URL": ghost.content_url,
                "GHOST_CONTENT_API_KEY": ghost.content_key,
            })
            self.addCleanup(temp.cleanup)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('data-slot="cartas"', (out / "index.html").read_text(encoding="utf-8"))

    def test_keys_tokens_and_emails_never_reach_static_output(self):
        secret = "content-secret-that-must-not-leak"
        token = "portal-token-that-must-not-leak"
        email = "reader@example.com"
        temp, out, result = self.build({
            "GHOST_CONTENT_URL": "https://community.example/ghost/api/content/",
            "GHOST_CONTENT_API_KEY": secret,
            "GHOST_PORTAL_URL": f"https://community.example/?token={token}&email={email}#/portal/signup",
        })
        self.addCleanup(temp.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        static = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in out.rglob("*") if path.is_file())
        self.assertNotIn(secret, static)
        self.assertNotIn(token, static)
        self.assertNotIn(email, static)
        self.assertNotIn("community.example", static)


if __name__ == "__main__":
    unittest.main()
