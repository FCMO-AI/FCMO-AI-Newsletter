#!/usr/bin/env python3
"""Static file server that behaves like GitHub Pages under a project base path.

    python3 tests/harness/serve.py --root site --base /FCMO-AI-Newsletter/ --port 8765

Behaviour (the parts the site and its tests depend on):

* only paths under ``--base`` are served; ``/`` redirects to the base;
* a directory without a trailing slash answers 301 to the slashed URL;
* a directory serves its ``index.html``; ``/a/b`` falls back to ``/a/b.html``;
* anything else answers 404 with ``<root>/404.html`` as the body when present;
* ``..`` and symlinks that leave the root are refused;
* GET and HEAD only; binds 127.0.0.1.

The first stdout line is ``SERVING http://127.0.0.1:<port><base>`` (flushed), so
callers can use ``--port 0`` and read the chosen port. Tests can also call
``start_server()`` and get a running server back.
"""
from __future__ import annotations

import argparse
import mimetypes
import posixpath
import sys
import threading
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

HOST = "127.0.0.1"
TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".xml": "application/xml; charset=utf-8",
    ".rss": "application/rss+xml; charset=utf-8",
    ".atom": "application/atom+xml; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".avif": "image/avif",
    ".gif": "image/gif",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".webmanifest": "application/manifest+json",
    ".jsonl": "application/x-ndjson; charset=utf-8",
}


def normalize_base(base: str) -> str:
    base = "/" + base.strip("/")
    return "/" if base == "/" else base + "/"


def content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TYPES:
        return TYPES[suffix]
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


class PagesHandler(BaseHTTPRequestHandler):
    server_version = "fcmo-pages-harness/1"
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, root: Path, base: str, quiet: bool, **kwargs) -> None:
        self.root = root
        self.base = base
        self.quiet = quiet
        super().__init__(*args, **kwargs)

    # -- plumbing -------------------------------------------------------------------
    def log_message(self, fmt: str, *args) -> None:  # noqa: D401 - stdlib signature
        if not self.quiet:
            sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def _send(self, status: int, body: bytes, ctype: str, extra: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _redirect(self, location: str) -> None:
        self._send(HTTPStatus.MOVED_PERMANENTLY, b"", "text/plain; charset=utf-8", {"Location": location})

    def _not_found(self) -> None:
        page = self.root / "404.html"
        if page.is_file():
            self._send(HTTPStatus.NOT_FOUND, page.read_bytes(), TYPES[".html"])
        else:
            self._send(HTTPStatus.NOT_FOUND, b"404 Not Found\n", TYPES[".txt"])

    def _inside_root(self, candidate: Path) -> bool:
        try:
            candidate.resolve().relative_to(self.root)
            return True
        except (OSError, ValueError):
            return False

    # -- routing --------------------------------------------------------------------
    def resolve(self, url_path: str) -> tuple[str, Path | str | None]:
        """Return ("file", path), ("redirect", location) or ("missing", None)."""
        if url_path + "/" == self.base:
            return "redirect", self.base
        if not url_path.startswith(self.base):
            return ("redirect", self.base) if url_path == "/" else ("missing", None)
        rel = url_path[len(self.base):]
        parts = [p for p in rel.split("/") if p]
        if any(p in {".", ".."} or "\\" in p or "\x00" in p for p in parts):
            return "missing", None
        target = self.root.joinpath(*parts) if parts else self.root
        if not self._inside_root(target):
            return "missing", None
        if target.is_dir():
            if not url_path.endswith("/"):
                return "redirect", quote(url_path) + "/"
            index = target / "index.html"
            return ("file", index) if index.is_file() and self._inside_root(index) else ("missing", None)
        if target.is_file():
            return "file", target
        if parts and not url_path.endswith("/"):
            html = target.with_name(target.name + ".html")
            if html.is_file() and self._inside_root(html):
                return "file", html
        return "missing", None

    def do_GET(self) -> None:  # noqa: N802 - stdlib name
        raw_path = urlsplit(self.path).path
        url_path = posixpath.normpath(unquote(raw_path)) if raw_path not in {"", "/"} else "/"
        if raw_path.endswith("/") and url_path != "/":
            url_path += "/"
        if ".." in unquote(raw_path).split("/"):
            self._not_found()
            return
        kind, value = self.resolve(url_path)
        if kind == "redirect":
            query = urlsplit(self.path).query
            self._redirect(str(value) + (f"?{query}" if query else ""))
        elif kind == "file":
            path = Path(str(value))
            try:
                body = path.read_bytes()
            except OSError:
                self._not_found()
                return
            self._send(HTTPStatus.OK, body, content_type(path))
        else:
            self._not_found()

    def do_HEAD(self) -> None:  # noqa: N802 - stdlib name
        self.do_GET()

    def _method_not_allowed(self) -> None:
        self._send(HTTPStatus.METHOD_NOT_ALLOWED, b"405 Method Not Allowed\n", TYPES[".txt"], {"Allow": "GET, HEAD"})

    do_POST = do_PUT = do_DELETE = do_PATCH = _method_not_allowed  # noqa: N815


class RunningServer:
    """A server started on a background thread; use as a context manager."""

    def __init__(self, httpd: ThreadingHTTPServer, base: str) -> None:
        self.httpd = httpd
        self.base = base
        self.port = httpd.server_address[1]
        self.url = f"http://{HOST}:{self.port}{base}"
        self.thread = threading.Thread(target=httpd.serve_forever, name="pages-harness", daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)

    def __enter__(self) -> "RunningServer":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def make_server(root: str | Path, base: str = "/", port: int = 0, quiet: bool = True) -> ThreadingHTTPServer:
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise FileNotFoundError(f"--root is not a directory: {root}")
    handler = partial(PagesHandler, root=root_path, base=normalize_base(base), quiet=quiet)
    httpd = ThreadingHTTPServer((HOST, port), handler)
    httpd.daemon_threads = True
    return httpd


def start_server(root: str | Path, base: str = "/", port: int = 0, quiet: bool = True) -> RunningServer:
    """Start a background server; ``port=0`` picks a free port (see ``.url``)."""
    return RunningServer(make_server(root, base, port, quiet), normalize_base(base))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GitHub Pages-like static server for tests")
    parser.add_argument("--root", required=True, help="directory to serve (the built site)")
    parser.add_argument("--base", default="/", help="project base path, e.g. /FCMO-AI-Newsletter/")
    parser.add_argument("--port", type=int, default=8765, help="port on 127.0.0.1 (0 = any free port)")
    parser.add_argument("--verbose", action="store_true", help="log requests to stderr")
    args = parser.parse_args(argv)
    try:
        httpd = make_server(args.root, args.base, args.port, quiet=not args.verbose)
    except (FileNotFoundError, OSError) as exc:
        print(f"serve.py: {exc}", file=sys.stderr)
        return 2
    print(f"SERVING http://{HOST}:{httpd.server_address[1]}{normalize_base(args.base)}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
