"""Tests of the harness tools: fake clock, static server, Ghost mock and browser scripts.

Browser runs need an external Playwright install: set NODE_PATH to its
node_modules (and add axe-core's node_modules, or set AXE_CORE_PATH, for the axe
check). Without them those tests skip; everything else runs anywhere.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from harness import clock as clock_mod
from harness.clock import FakeClock, now_from
from harness.mock_ghost import (
    FAKE_ADMIN_KEY,
    MockGhost,
    sign_admin_token,
    unreachable_url,
    verify_admin_token,
)
from harness.serve import start_server

HARNESS = Path(__file__).resolve().parent
BROWSER = HARNESS / "browser"
NODE = shutil.which("node")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch(url: str, method: str = "GET", body=None, headers=None, timeout: float = 5.0):
    """(status, headers, body bytes) without following redirects."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as err:
        return err.code, err.headers, err.read()


def fetch_json(url, method="GET", body=None, token=None, timeout=5.0):
    headers = {"Authorization": f"Ghost {token}"} if token else {}
    status, _, raw = fetch(url, method, body, headers, timeout)
    return status, (json.loads(raw) if raw else None)


class ClockTests(unittest.TestCase):
    def test_fake_clock(self):
        clock = FakeClock()
        self.assertEqual(clock.iso(), "2026-09-26T20:00:00Z")
        self.assertEqual(clock.ago(hours=31), "2026-09-25T13:00:00Z")
        self.assertEqual(clock.ahead(minutes=15), "2026-09-26T20:15:00Z")
        clock.advance(hours=9)
        self.assertEqual(clock.iso(), "2026-09-27T05:00:00Z")
        self.assertEqual(clock.cdmx_date(), "2026-09-26")
        self.assertEqual(clock.argv(), ["--now", "2026-09-27T05:00:00Z"])
        self.assertEqual(clock.env({})["FCMO_NOW"], "2026-09-27T05:00:00Z")
        self.assertEqual(clock.set("2026-10-01").iso(), "2026-10-01T00:00:00Z")

    def test_now_precedence(self):
        env = {"FCMO_NOW": "2026-09-20T00:00:00Z"}
        self.assertEqual(now_from("2026-09-21T00:00:00Z", env).isoformat(), "2026-09-21T00:00:00+00:00")
        self.assertEqual(now_from(None, env).isoformat(), "2026-09-20T00:00:00+00:00")
        real = now_from(None, {})
        self.assertLess(abs((datetime.now(timezone.utc) - real).total_seconds()), 5)

    def test_patch(self):
        class Target:
            @staticmethod
            def utc_now():
                return "real"

        clock = FakeClock("2026-09-26T07:30:00Z")
        with clock.patch(Target, "utc_now", as_string=True):
            self.assertEqual(Target.utc_now(), "2026-09-26T07:30:00Z")
        self.assertEqual(Target.utc_now(), "real")
        with clock.patch(Target):
            self.assertEqual(Target.utc_now(), clock.now())

    def test_cdmx_has_no_dst(self):
        self.assertEqual(clock_mod.to_cdmx("2026-07-01T12:00:00Z").utcoffset().total_seconds(), -6 * 3600)
        self.assertEqual(clock_mod.to_cdmx("2026-12-01T12:00:00Z").utcoffset().total_seconds(), -6 * 3600)


class ServeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name) / "site"
        (root / "es").mkdir(parents=True)
        (root / "index.html").write_text("<!doctype html><title>home</title>", encoding="utf-8")
        (root / "es" / "index.html").write_text("<!doctype html><title>es</title>", encoding="utf-8")
        (root / "about.html").write_text("<!doctype html><title>about</title>", encoding="utf-8")
        (root / "404.html").write_text("<!doctype html><title>not found</title>", encoding="utf-8")
        (root / "data.json").write_text("{}", encoding="utf-8")
        (root / "feed.xml").write_text("<rss/>", encoding="utf-8")
        (Path(cls.tmp.name) / "secret.txt").write_text("outside", encoding="utf-8")
        cls.root = root
        cls.server = start_server(root, "/FCMO-AI-Newsletter/")

    @classmethod
    def tearDownClass(cls):
        cls.server.close()
        cls.tmp.cleanup()

    def test_pages_rules(self):
        base = self.server.url
        origin = base[: -len("/FCMO-AI-Newsletter/")]
        cases = [
            (base, 200, "text/html"),
            (base + "es/", 200, "text/html"),
            (base + "about", 200, "text/html"),
            (base + "about.html", 200, "text/html"),
            (base + "data.json", 200, "application/json"),
            (base + "feed.xml", 200, "application/xml"),
            (base + "missing/", 404, "text/html"),
            (origin + "/elsewhere/", 404, "text/html"),
        ]
        for url, status, ctype in cases:
            with self.subTest(url=url):
                code, headers, _ = fetch(url)
                self.assertEqual(code, status)
                self.assertTrue(headers["Content-Type"].startswith(ctype), headers["Content-Type"])
        code, _, body = fetch(base + "missing/")
        self.assertIn(b"not found", body)

    def test_redirects(self):
        base = self.server.url
        origin = base[: -len("/FCMO-AI-Newsletter/")]
        for url, location in ((base + "es", "/FCMO-AI-Newsletter/es/"),
                              (origin + "/FCMO-AI-Newsletter", "/FCMO-AI-Newsletter/"),
                              (origin + "/", "/FCMO-AI-Newsletter/")):
            with self.subTest(url=url):
                code, headers, _ = fetch(url)
                self.assertEqual(code, 301)
                self.assertEqual(headers["Location"], location)

    def test_traversal_and_methods(self):
        base = self.server.url
        for path in ("../secret.txt", "%2e%2e/secret.txt", "es/../../secret.txt"):
            with self.subTest(path=path):
                self.assertEqual(fetch(base + path)[0], 404)
        self.assertEqual(fetch(base, method="POST", body={})[0], 405)
        code, headers, body = fetch(base, method="HEAD")
        self.assertEqual((code, body), (200, b""))

    def test_cli_acceptance(self):
        proc = subprocess.Popen(
            [sys.executable, str(HARNESS / "serve.py"), "--root", str(self.root), "--base", "/FCMO-AI-Newsletter/", "--port", "0"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            line = proc.stdout.readline().strip()
            self.assertRegex(line, r"^SERVING http://127\.0\.0\.1:\d+/FCMO-AI-Newsletter/$")
            self.assertEqual(fetch(line.split()[1])[0], 200)
        finally:
            proc.terminate()
            proc.wait(timeout=10)
            proc.stdout.close()
            proc.stderr.close()

    def test_cli_rejects_missing_root(self):
        result = subprocess.run([sys.executable, str(HARNESS / "serve.py"), "--root", "/nonexistent-dir", "--port", "0"],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 2)


class GhostAuthTests(unittest.TestCase):
    def test_token_rules(self):
        now = time.time()
        self.assertIsNone(verify_admin_token(sign_admin_token(), FAKE_ADMIN_KEY, now))
        self.assertEqual(verify_admin_token(sign_admin_token(ttl=301), FAKE_ADMIN_KEY, now), "token lifetime above 5 minutes")
        self.assertEqual(verify_admin_token(sign_admin_token(iat=int(now) - 600), FAKE_ADMIN_KEY, now), "token expired")
        self.assertEqual(verify_admin_token(sign_admin_token(aud="/v3/admin/"), FAKE_ADMIN_KEY, now), "bad aud")
        other = "000000000000000000000fa9:" + "0f" * 32
        self.assertEqual(verify_admin_token(sign_admin_token(other), FAKE_ADMIN_KEY, now), "unknown kid")
        forged = FAKE_ADMIN_KEY.split(":")[0] + ":" + "1f" * 32
        self.assertEqual(verify_admin_token(sign_admin_token(forged), FAKE_ADMIN_KEY, now), "bad signature")
        self.assertEqual(verify_admin_token("nope", FAKE_ADMIN_KEY, now), "malformed token")


class GhostApiTests(unittest.TestCase):
    def setUp(self):
        self.ghost = MockGhost().start()
        self.addCleanup(self.ghost.close)
        self.token = self.ghost.admin_token()

    def admin(self, method, rest, body=None, token="default", timeout=5.0):
        tok = self.token if token == "default" else token
        return fetch_json(self.ghost.admin_url + rest, method, body, tok, timeout)

    def content(self, rest, timeout=5.0):
        sep = "&" if "?" in rest else "?"
        return fetch_json(f"{self.ghost.content_url}{rest}{sep}key={self.ghost.content_key}", timeout=timeout)

    def test_auth_required(self):
        status, body = self.admin("GET", "posts/", token=None)
        self.assertEqual((status, body["errors"][0]["type"]), (401, "UnauthorizedError"))
        self.assertEqual(self.admin("GET", "posts/", token="a.b.c")[0], 401)
        self.assertEqual(self.admin("GET", "site/", token=None)[0], 200)
        self.assertEqual(fetch_json(self.ghost.content_url + "posts/")[0], 401)
        self.assertEqual(fetch_json(self.ghost.content_url + "posts/?key=wrong")[0], 401)
        self.assertEqual(self.ghost.count(status=401), 4)

    def test_newsletters(self):
        status, body = self.admin("GET", "newsletters/")
        self.assertEqual(status, 200)
        self.assertEqual([n["slug"] for n in body["newsletters"]], ["cartas", "diario", "semanal", "alertas"])
        status, body = self.admin("GET", "newsletters/?filter=slug:diario")
        self.assertEqual([n["slug"] for n in body["newsletters"]], ["diario"])

    def test_content_rail(self):
        self.ghost.seed_cartas(4)
        self.ghost.seed_post("Borrador", tags=("cartas",), status="draft")
        self.ghost.seed_post("Otra etiqueta", tags=("avisos",))
        status, body = self.content("posts/?filter=tag:cartas&limit=3&include=tags,authors")
        self.assertEqual(status, 200)
        self.assertEqual([p["title"] for p in body["posts"]], ["Carta de prueba 4", "Carta de prueba 3", "Carta de prueba 2"])
        self.assertEqual(body["meta"]["pagination"]["total"], 4)
        self.assertIn("tags", body["posts"][0])
        self.assertNotIn("status", body["posts"][0])
        self.assertEqual(self.content("settings/")[1]["settings"]["lang"], "es")
        slug = body["posts"][0]["slug"]
        self.assertEqual(self.content(f"posts/slug/{slug}/")[0], 200)

    def test_dispatch_flow(self):
        post = {"title": "Diario 2026-09-28", "slug": "diario-2026-09-28", "html": "<p>Hoy</p>", "email_only": True}
        status, body = self.admin("POST", "posts/?source=html", {"posts": [post]})
        self.assertEqual(status, 201)
        draft = body["posts"][0]
        self.assertEqual((draft["status"], draft["slug"], draft["html"]), ("draft", "diario-2026-09-28", "<p>Hoy</p>"))
        _, dup = self.admin("POST", "posts/?source=html", {"posts": [post]})
        self.assertEqual(dup["posts"][0]["slug"], "diario-2026-09-28-2")
        status, body = self.admin("GET", "posts/?filter=slug:diario-2026-09-28")
        self.assertEqual([p["id"] for p in body["posts"]], [draft["id"]])

        stale = {"posts": [{"updated_at": "2026-01-01T00:00:00.000Z", "status": "published"}]}
        status, body = self.admin("PUT", f"posts/{draft['id']}/?newsletter=diario", stale)
        self.assertEqual((status, body["errors"][0]["type"]), (409, "UpdateCollisionError"))
        self.assertEqual(self.ghost.emails, [])

        publish = {"posts": [{"updated_at": draft["updated_at"], "status": "published"}]}
        status, body = self.admin("PUT", f"posts/{draft['id']}/?newsletter=diario&email_segment=all", publish)
        self.assertEqual(status, 200)
        sent = body["posts"][0]
        self.assertEqual((sent["status"], sent["newsletter"]["slug"], sent["email"]["status"]), ("sent", "diario", "submitted"))
        self.assertNotEqual(sent["updated_at"], draft["updated_at"])
        self.assertEqual(len(self.ghost.emails), 1)

        again = {"posts": [{"updated_at": sent["updated_at"], "status": "published"}]}
        self.assertEqual(self.admin("PUT", f"posts/{draft['id']}/?newsletter=diario", again)[0], 200)
        self.assertEqual(len(self.ghost.emails), 1, "a post is emailed at most once")
        self.assertEqual(self.content("posts/?filter=slug:diario-2026-09-28")[1]["posts"], [])
        self.assertEqual(self.ghost.count("POST", "/ghost/api/admin/posts/"), 2)
        self.assertEqual(self.admin("DELETE", f"posts/{draft['id']}/")[0], 204)
        self.assertEqual(self.admin("GET", f"posts/{draft['id']}/")[0], 404)

    def test_unknown_newsletter(self):
        _, body = self.admin("POST", "posts/", {"posts": [{"title": "X"}]})
        post = body["posts"][0]
        status, body = self.admin("PUT", f"posts/{post['id']}/?newsletter=nope", {"posts": [{"updated_at": post["updated_at"], "status": "published"}]})
        self.assertEqual(status, 404)
        self.assertEqual(self.ghost.emails, [])

    def test_frozen_clock_still_changes_updated_at(self):
        ghost = MockGhost(now=FakeClock("2026-09-28T13:30:00Z")).start()
        self.addCleanup(ghost.close)
        token = ghost.admin_token()
        _, body = fetch_json(ghost.admin_url + "posts/", "POST", {"posts": [{"title": "X"}]}, token)
        post = body["posts"][0]
        _, body = fetch_json(ghost.admin_url + f"posts/{post['id']}/", "PUT",
                             {"posts": [{"updated_at": post["updated_at"], "title": "Y"}]}, token)
        self.assertEqual(post["updated_at"], "2026-09-28T13:30:00.000Z")
        self.assertEqual(body["posts"][0]["updated_at"], "2026-09-28T13:30:00.001Z")

    def test_fault_injection(self):
        self.ghost.fail(status=503, method="PUT", path="/ghost/api/admin/posts/", times=1)
        _, body = self.admin("POST", "posts/", {"posts": [{"title": "X"}]})
        post = body["posts"][0]
        put = {"posts": [{"updated_at": post["updated_at"], "title": "Y"}]}
        self.assertEqual(self.admin("PUT", f"posts/{post['id']}/", put)[0], 503)
        self.assertEqual(self.admin("PUT", f"posts/{post['id']}/", put)[0], 200)

        self.ghost.fail(mode="timeout", seconds=3, path="/ghost/api/content/")
        started = time.monotonic()
        with self.assertRaises((TimeoutError, OSError)):
            self.content("posts/", timeout=0.5)
        self.assertLess(time.monotonic() - started, 2.5)

        self.ghost.fail(mode="drop", path="/ghost/api/content/")
        with self.assertRaises((OSError, urllib.error.URLError, ConnectionError)):
            self.content("posts/")
        self.assertEqual(self.content("posts/")[0], 200)

        self.ghost.fail(mode="drop", times=None)
        for _ in range(2):
            with self.assertRaises((OSError, urllib.error.URLError, ConnectionError)):
                self.content("settings/")
        self.ghost.clear_faults()
        self.assertEqual(self.content("settings/")[0], 200)

    def test_unreachable_url(self):
        with self.assertRaises(urllib.error.URLError):
            urllib.request.urlopen(unreachable_url() + "/ghost/api/content/posts/", timeout=2)


def _node_path_has(module: str) -> bool:
    if not NODE:
        return False
    probe = subprocess.run([NODE, "-e", f"require.resolve({json.dumps(module)})"], capture_output=True,
                           env=os.environ.copy(), timeout=30)
    return probe.returncode == 0


class BrowserScriptTests(unittest.TestCase):
    SCRIPTS = ("_common.mjs", "first_screen.mjs", "overflow.mjs", "axe.mjs")

    def setUp(self):
        if not NODE:
            self.skipTest("node is not installed")

    def test_syntax(self):
        for name in self.SCRIPTS:
            with self.subTest(script=name):
                result = subprocess.run([NODE, "--check", str(BROWSER / name)], capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_playwright_is_exit_2(self):
        env = {k: v for k, v in os.environ.items() if k not in {"NODE_PATH", "PLAYWRIGHT_MODULE"}}
        env["PLAYWRIGHT_MODULE"] = "/nonexistent/playwright"
        for name in ("first_screen.mjs", "overflow.mjs"):
            with self.subTest(script=name):
                result = subprocess.run([NODE, str(BROWSER / name), "http://127.0.0.1:9/"], capture_output=True,
                                        text=True, env=env, cwd=tempfile.gettempdir(), timeout=60)
                self.assertEqual(result.returncode, 2)
                self.assertIn("BROWSER_UNAVAILABLE", result.stderr)

    def test_missing_axe_is_exit_2(self):
        env = {k: v for k, v in os.environ.items() if k != "AXE_CORE_PATH"}
        env["AXE_CORE_PATH"] = "/nonexistent/axe.min.js"
        result = subprocess.run([NODE, str(BROWSER / "axe.mjs"), "http://127.0.0.1:9/"], capture_output=True,
                                text=True, env=env, timeout=60)
        self.assertEqual(result.returncode, 2)
        self.assertIn("AXE_UNAVAILABLE", result.stderr)


class BrowserRunTests(unittest.TestCase):
    """Real browser runs; they need Playwright (and axe-core) reachable through NODE_PATH."""

    @classmethod
    def setUpClass(cls):
        if not _node_path_has("playwright"):
            raise unittest.SkipTest("playwright not reachable through NODE_PATH")
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        head = '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        (root / "index.html").write_text(
            f'<!doctype html><html lang="en"><head>{head}<title>Good</title></head><body><main>'
            '<article data-lead><h1>Lead headline</h1><p style="font-size:16px">Body text.</p></article>'
            '</main></body></html>', encoding="utf-8")
        (root / "bad.html").write_text(
            f'<!doctype html><html><head>{head}<title>Bad</title></head><body><div style="height:1200px">x</div>'
            '<main><h1>Late headline</h1><div style="width:2000px">wide</div>'
            '<p style="font-size:9px;color:#bbb">tiny</p><img src="missing.png"></main></body></html>', encoding="utf-8")
        cls.server = start_server(root, "/FCMO-AI-Newsletter/")

    @classmethod
    def tearDownClass(cls):
        cls.server.close()
        cls.tmp.cleanup()

    def run_script(self, name, *args):
        result = subprocess.run([NODE, str(BROWSER / name), *args], capture_output=True, text=True, timeout=300)
        self.assertNotEqual(result.returncode, 2, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_first_screen(self):
        code, report = self.run_script("first_screen.mjs", self.server.url, "--viewport", "390x844")
        self.assertEqual(code, 0, report)
        self.assertLessEqual(report["pages"][0]["lead"]["bottom"], 844)
        code, report = self.run_script("first_screen.mjs", self.server.url + "bad", "--viewport", "390x844")
        self.assertEqual(code, 1)
        self.assertFalse(report["pages"][0]["withinFirstScreen"])
        self.assertTrue(report["pages"][0]["failedRequests"])

    def test_overflow(self):
        self.assertEqual(self.run_script("overflow.mjs", self.server.url)[0], 0)
        code, report = self.run_script("overflow.mjs", self.server.url + "bad", "--viewport", "390x844")
        self.assertEqual(code, 1)
        self.assertGreater(report["pages"][0]["scrollWidth"], report["pages"][0]["clientWidth"])
        self.assertTrue(report["pages"][0]["offenders"])

    def test_axe_and_min_font(self):
        if not (os.environ.get("AXE_CORE_PATH") or _node_path_has("axe-core/axe.min.js")):
            self.skipTest("axe-core not reachable (AXE_CORE_PATH or NODE_PATH)")
        code, report = self.run_script("axe.mjs", self.server.url, "--viewport", "390x844", "--min-font", "12")
        self.assertEqual(code, 0, report)
        self.assertEqual(report["pages"][0]["blocking"], 0)
        code, report = self.run_script("axe.mjs", self.server.url + "bad", "--viewport", "390x844", "--min-font", "12")
        self.assertEqual(code, 1)
        page = report["pages"][0]
        self.assertGreater(page["blocking"], 0)
        self.assertEqual(page["minFontPx"], 9)


if __name__ == "__main__":
    unittest.main()
