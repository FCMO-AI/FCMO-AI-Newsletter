#!/usr/bin/env python3
"""In-process mock of the Ghost Admin and Content APIs for offline tests.

One mock serves every package that talks to Ghost: the email dispatcher (Admin
API: posts, newsletters, publish-and-send), the community rail (Content API:
posts by tag, settings) and the Ghost setup checks. It keeps state in memory,
records every request and can inject failures.

    from tests.harness.mock_ghost import MockGhost
    with MockGhost() as ghost:                  # 127.0.0.1, free port
        ghost.seed_cartas(3)
        env = {"GHOST_URL": ghost.url, "GHOST_ADMIN_API_KEY": ghost.admin_key,
               "GHOST_CONTENT_API_KEY": ghost.content_key}
        ...
        assert ghost.count("POST", "/ghost/api/admin/posts/") == 0
        ghost.fail(status=503, method="PUT", path="/ghost/api/admin/posts/", times=1)
        ghost.fail(mode="timeout", seconds=6)   # the client must give up first
        ghost.fail(mode="drop")                 # connection closed with no response

Behaviour copied from Ghost 5/6 (what clients depend on):

* Admin auth is ``Authorization: Ghost <jwt>``: HS256, header ``kid`` = key id,
  secret = hex-decoded key secret, ``aud`` = ``/admin/``, ``exp`` at most 5
  minutes after ``iat``. Missing or bad tokens answer 401.
* ``POST /posts/`` takes ``{"posts": [..]}`` (``?source=html`` for html bodies)
  and makes slugs unique the Ghost way (``slug``, ``slug-2``, ...).
* ``PUT /posts/{id}/`` must echo the current ``updated_at`` or gets 409
  ``UpdateCollisionError``. Moving a post to ``published`` with
  ``?newsletter=<slug>`` sends it once to that newsletter (recorded in
  ``emails``); an ``email_only`` post then has status ``sent`` and never
  appears in the Content API.
* The Content API needs ``?key=`` and returns only published web posts,
  newest first, with ``filter`` (``tag:``, ``slug:``, ``+`` for AND) and
  ``limit``.

The keys are obviously fake and must never be replaced by real ones in tests.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import hmac
import itertools
import json
import re
import socket
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import parse_qs, urlsplit

HOST = "127.0.0.1"
FAKE_ADMIN_KEY_ID = "000000000000000000000fa1"
FAKE_ADMIN_SECRET = "0f" * 32
FAKE_ADMIN_KEY = f"{FAKE_ADMIN_KEY_ID}:{FAKE_ADMIN_SECRET}"
FAKE_CONTENT_KEY = "00000000000000000000000fa2"
ADMIN_PREFIX = "/ghost/api/admin/"
CONTENT_PREFIX = "/ghost/api/content/"
MAX_TOKEN_TTL_S = 300
DEFAULT_NEWSLETTERS = (
    ("cartas", "Cartas"),
    ("diario", "Diario"),
    ("semanal", "Semanal"),
    ("alertas", "Alertas"),
)


# ---------------------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------------------
def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign_admin_token(admin_key: str = FAKE_ADMIN_KEY, iat: int | None = None, ttl: int = MAX_TOKEN_TTL_S,
                     aud: str = "/admin/") -> str:
    """Build an Admin API JWT the way Ghost's own SDK does (for tests of the mock)."""
    key_id, secret = admin_key.split(":", 1)
    issued = int(time.time()) if iat is None else int(iat)
    header = {"alg": "HS256", "typ": "JWT", "kid": key_id}
    payload = {"iat": issued, "exp": issued + ttl, "aud": aud}
    signing_input = ".".join(
        _b64url(json.dumps(part, separators=(",", ":")).encode()) for part in (header, payload)
    )
    signature = hmac.new(bytes.fromhex(secret), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


def verify_admin_token(token: str, admin_key: str, now: float | None = None) -> str | None:
    """Return None when the token is acceptable, else a short reason."""
    key_id, secret = admin_key.split(":", 1)
    parts = token.split(".")
    if len(parts) != 3:
        return "malformed token"
    try:
        header = json.loads(_b64url_decode(parts[0]))
        payload = json.loads(_b64url_decode(parts[1]))
        signature = _b64url_decode(parts[2])
    except (ValueError, json.JSONDecodeError):
        return "malformed token"
    if header.get("alg") != "HS256":
        return "unsupported alg"
    if header.get("kid") != key_id:
        return "unknown kid"
    expected = hmac.new(bytes.fromhex(secret), f"{parts[0]}.{parts[1]}".encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        return "bad signature"
    if payload.get("aud") != "/admin/":
        return "bad aud"
    iat, exp = payload.get("iat"), payload.get("exp")
    if not isinstance(iat, (int, float)) or not isinstance(exp, (int, float)):
        return "missing iat/exp"
    if exp - iat > MAX_TOKEN_TTL_S:
        return "token lifetime above 5 minutes"
    current = time.time() if now is None else now
    if exp <= current:
        return "token expired"
    if iat > current + 60:
        return "token issued in the future"
    return None


def unreachable_url() -> str:
    """A base URL on 127.0.0.1 where nothing listens (connection refused)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        port = sock.getsockname()[1]
    return f"http://{HOST}:{port}"


def ghost_time(dt: datetime) -> str:
    """Ghost's timestamp form: 2026-09-26T20:00:00.000Z."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:185] or "untitled"


def _object_id(counter: Callable[[], int]) -> str:
    return f"{counter():024x}"


@dataclass
class Fault:
    method: str = "*"
    path: str = ""
    status: int = 500
    mode: str = "status"  # status | timeout | drop
    seconds: float = 6.0
    times: int | None = 1  # None = until cleared

    def matches(self, method: str, path: str) -> bool:
        return (self.method in {"*", method}) and path.startswith(self.path)


class GhostError(Exception):
    def __init__(self, status: int, kind: str, message: str) -> None:
        super().__init__(message)
        self.status, self.kind, self.message = status, kind, message


# ---------------------------------------------------------------------------------------
# NQL filter subset
# ---------------------------------------------------------------------------------------
def _filter_values(raw: str) -> tuple[bool, list[str]]:
    negate = raw.startswith("-")
    raw = raw[1:] if negate else raw
    if raw.startswith("[") and raw.endswith("]"):
        values = [v.strip().strip("'\"") for v in raw[1:-1].split(",") if v.strip()]
    else:
        values = [raw.strip("'\"")]
    return negate, values


def post_matches(post: dict[str, Any], expression: str | None) -> bool:
    """Evaluate the Ghost filter subset used by FCMO tools: ``key:value`` joined by ``+``."""
    if not expression:
        return True
    for clause in expression.split("+"):
        if ":" not in clause:
            raise GhostError(400, "BadRequestError", f"Error parsing filter: {clause}")
        key, raw = clause.split(":", 1)
        negate, values = _filter_values(raw)
        key = key.strip()
        if key in {"tag", "tags", "tags.slug"}:
            have = {t["slug"] for t in post.get("tags", [])}
            hit = bool(have & set(values))
        elif key in {"slug", "id", "status", "visibility", "uuid"}:
            hit = str(post.get(key)) in values
        elif key == "email_only":
            hit = str(bool(post.get("email_only"))).lower() in {v.lower() for v in values}
        elif key == "newsletter":
            hit = bool(post.get("newsletter")) and post["newsletter"]["slug"] in values
        else:
            raise GhostError(400, "BadRequestError", f"Unsupported filter key in mock: {key}")
        if hit == negate:
            return False
    return True


# ---------------------------------------------------------------------------------------
# The mock
# ---------------------------------------------------------------------------------------
class MockGhost:
    """A running mock Ghost site; use as a context manager or call start()/close()."""

    def __init__(
        self,
        admin_key: str = FAKE_ADMIN_KEY,
        content_key: str = FAKE_CONTENT_KEY,
        newsletters: tuple[tuple[str, str], ...] = DEFAULT_NEWSLETTERS,
        now: Callable[[], datetime] | None = None,
        token_time: Callable[[], float] | None = None,
        port: int = 0,
    ) -> None:
        self.admin_key = admin_key
        self.content_key = content_key
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._token_time = token_time or time.time
        self._ids = itertools.count(1).__next__
        self._lock = threading.RLock()
        self._closing = threading.Event()
        self.port = port
        self.posts: dict[str, dict[str, Any]] = {}
        self.requests: list[dict[str, Any]] = []
        self.emails: list[dict[str, Any]] = []
        self.faults: list[Fault] = []
        self.newsletters = [
            {"id": _object_id(self._ids), "uuid": str(uuid.uuid4()), "name": name, "slug": slug,
             "status": "active", "visibility": "members", "subscribe_on_signup": slug == "cartas",
             "sender_email": None, "sort_order": order}
            for order, (slug, name) in enumerate(newsletters)
        ]
        self.site = {"title": "FCMO Comunidad (mock)", "description": "Mock Ghost site for tests", "locale": "es",
                     "version": "6.0"}
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    # -- lifecycle ------------------------------------------------------------------
    def start(self) -> "MockGhost":
        mock = self

        class Handler(_Handler):
            ghost = mock

        self._httpd = ThreadingHTTPServer((HOST, self.port), Handler)
        self._httpd.daemon_threads = True
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, name="mock-ghost", daemon=True)
        self._thread.start()
        return self

    def close(self) -> None:
        self._closing.set()
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self._thread:
            self._thread.join(timeout=5)

    def __enter__(self) -> "MockGhost":
        return self.start() if self._httpd is None else self

    def __exit__(self, *exc) -> None:
        self.close()

    @property
    def url(self) -> str:
        return f"http://{HOST}:{self.port}"

    @property
    def admin_url(self) -> str:
        return self.url + ADMIN_PREFIX

    @property
    def content_url(self) -> str:
        return self.url + CONTENT_PREFIX

    def admin_token(self, **kw: Any) -> str:
        return sign_admin_token(self.admin_key, **kw)

    # -- faults and log -------------------------------------------------------------
    def fail(self, status: int = 500, method: str = "*", path: str = "", times: int | None = 1,
             mode: str = "status", seconds: float = 6.0) -> Fault:
        if mode not in {"status", "timeout", "drop"}:
            raise ValueError("mode must be status, timeout or drop")
        fault = Fault(method=method.upper(), path=path, status=status, mode=mode, seconds=seconds, times=times)
        with self._lock:
            self.faults.append(fault)
        return fault

    def clear_faults(self) -> None:
        with self._lock:
            self.faults.clear()

    def _take_fault(self, method: str, path: str) -> Fault | None:
        with self._lock:
            for fault in self.faults:
                if fault.matches(method, path):
                    if fault.times is not None:
                        fault.times -= 1
                        if fault.times <= 0:
                            self.faults.remove(fault)
                    return fault
        return None

    def count(self, method: str | None = None, path: str | None = None, status: int | None = None) -> int:
        """Number of logged requests matching method, path prefix and status."""
        with self._lock:
            return sum(
                1 for r in self.requests
                if (method is None or r["method"] == method.upper())
                and (path is None or r["path"].startswith(path))
                and (status is None or r["status"] == status)
            )

    def reset_log(self) -> None:
        with self._lock:
            self.requests.clear()
            self.emails.clear()

    # -- seeding --------------------------------------------------------------------
    def seed_post(self, title: str, *, tags: tuple[str, ...] | list[str] = (), status: str = "published",
                  html: str | None = None, slug: str | None = None, email_only: bool = False,
                  published_at: datetime | None = None, custom_excerpt: str | None = None,
                  feature_image: str | None = None, authors: tuple[str, ...] = ("Autor de prueba",)) -> dict[str, Any]:
        with self._lock:
            post = self._new_post({"title": title, "html": html or f"<p>{title}</p>", "slug": slug, "status": status,
                                   "email_only": email_only, "custom_excerpt": custom_excerpt,
                                   "feature_image": feature_image, "tags": list(tags),
                                   "authors": [{"name": a} for a in authors]})
            if published_at is not None:
                post["published_at"] = ghost_time(published_at)
            return copy.deepcopy(post)

    def seed_cartas(self, n: int = 3, start: datetime | None = None) -> list[dict[str, Any]]:
        """Seed ``n`` published human letters tagged ``cartas`` (newest last)."""
        base = start or datetime(2026, 9, 20, 15, 0, tzinfo=timezone.utc)
        return [
            self.seed_post(f"Carta de prueba {i + 1}", tags=("cartas",), custom_excerpt=f"Resumen de la carta {i + 1}.",
                           published_at=base + timedelta(days=i))
            for i in range(n)
        ]

    # -- domain logic ---------------------------------------------------------------
    def _unique_slug(self, wanted: str, exclude_id: str | None = None) -> str:
        taken = {p["slug"] for p in self.posts.values() if p["id"] != exclude_id}
        if wanted not in taken:
            return wanted
        for n in itertools.count(2):
            candidate = f"{wanted}-{n}"
            if candidate not in taken:
                return candidate
        raise AssertionError("unreachable")

    def _tag(self, value: Any) -> dict[str, Any]:
        name = value.get("name") or value.get("slug") if isinstance(value, dict) else str(value)
        tag_slug = value.get("slug") if isinstance(value, dict) and value.get("slug") else slugify(str(name))
        return {"id": hashlib.sha1(tag_slug.encode()).hexdigest()[:24], "name": name, "slug": tag_slug}

    def _author(self, value: Any) -> dict[str, Any]:
        name = value.get("name", "Autor de prueba") if isinstance(value, dict) else str(value)
        return {"id": hashlib.sha1(name.encode()).hexdigest()[:24], "name": name, "slug": slugify(name)}

    def _new_post(self, fields: dict[str, Any]) -> dict[str, Any]:
        now = ghost_time(self._now())
        title = fields.get("title") or "(Untitled)"
        post_id = _object_id(self._ids)
        status = fields.get("status") or "draft"
        if status not in {"draft", "published", "scheduled"}:
            raise GhostError(422, "ValidationError", f"Validation error, cannot save post. status '{status}'")
        post = {
            "id": post_id, "uuid": str(uuid.uuid4()), "title": title,
            "slug": self._unique_slug(slugify(fields.get("slug") or title)),
            "html": fields.get("html"), "lexical": fields.get("lexical"), "status": status,
            "visibility": fields.get("visibility", "public"), "email_only": bool(fields.get("email_only")),
            "custom_excerpt": fields.get("custom_excerpt"), "feature_image": fields.get("feature_image"),
            "created_at": now, "updated_at": now,
            "published_at": fields.get("published_at") or (now if status == "published" else None),
            "tags": [self._tag(t) for t in fields.get("tags", [])],
            "authors": [self._author(a) for a in fields.get("authors", [{"name": "Autor de prueba"}])],
            "newsletter": None, "email": None, "email_segment": "all",
        }
        post["excerpt"] = post["custom_excerpt"] or re.sub(r"<[^>]+>", "", post["html"] or "")[:300]
        post["primary_author"] = post["authors"][0] if post["authors"] else None
        post["primary_tag"] = post["tags"][0] if post["tags"] else None
        post["url"] = f"{self.url}/{post['slug']}/"
        self.posts[post_id] = post
        return post

    def _publish_email(self, post: dict[str, Any], newsletter_slug: str, segment: str) -> None:
        newsletter = next((n for n in self.newsletters if n["slug"] == newsletter_slug), None)
        if newsletter is None or newsletter["status"] != "active":
            raise GhostError(404, "NotFoundError", f"Newsletter '{newsletter_slug}' not found.")
        at = ghost_time(self._now())
        post["newsletter"] = {"id": newsletter["id"], "slug": newsletter["slug"], "name": newsletter["name"]}
        post["email_segment"] = segment
        post["email"] = {"id": _object_id(self._ids), "status": "submitted", "recipient_filter": segment,
                         "subject": post["title"], "submitted_at": at}
        self.emails.append({"post_id": post["id"], "slug": post["slug"], "newsletter": newsletter_slug,
                            "segment": segment, "email_only": post["email_only"], "at": at})
        if post["email_only"]:
            post["status"] = "sent"

    def _update_post(self, post_id: str, fields: dict[str, Any], query: dict[str, str]) -> dict[str, Any]:
        post = self.posts.get(post_id)
        if post is None:
            raise GhostError(404, "NotFoundError", "Post not found.")
        if "updated_at" not in fields:
            raise GhostError(422, "ValidationError", "Validation error, cannot edit post. updated_at is required.")
        if fields["updated_at"] != post["updated_at"]:
            raise GhostError(409, "UpdateCollisionError", "Saving failed! Someone else is editing this post.")
        before = post["status"]
        for key in ("title", "html", "lexical", "custom_excerpt", "feature_image", "visibility", "email_only",
                    "published_at"):
            if key in fields:
                post[key] = fields[key]
        if "slug" in fields:
            post["slug"] = self._unique_slug(slugify(fields["slug"]), exclude_id=post_id)
        if "tags" in fields:
            post["tags"] = [self._tag(t) for t in fields["tags"]]
            post["primary_tag"] = post["tags"][0] if post["tags"] else None
        status = fields.get("status", before)
        if status not in {"draft", "published", "scheduled", "sent"}:
            raise GhostError(422, "ValidationError", f"Validation error, cannot edit post. status '{status}'")
        post["status"] = status
        if status == "published" and before in {"draft", "scheduled"}:
            post["published_at"] = post.get("published_at") or ghost_time(self._now())
            if query.get("newsletter"):
                self._publish_email(post, query["newsletter"], query.get("email_segment", "all"))
        elif query.get("newsletter") and status != "published":
            raise GhostError(400, "BadRequestError", "The newsletter parameter needs a transition to published.")
        stamp = self._now()
        previous = datetime.strptime(fields["updated_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        if stamp <= previous:  # frozen or slow test clocks: every edit still gets a new updated_at
            stamp = previous + timedelta(milliseconds=1)
        post["updated_at"] = ghost_time(stamp)
        return post


# ---------------------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------------------
def _page(items: list[dict[str, Any]], query: dict[str, str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    limit_raw = query.get("limit", "15")
    total = len(items)
    if limit_raw == "all":
        limit, page = max(total, 1), 1
    else:
        try:
            limit = max(1, int(limit_raw))
            page = max(1, int(query.get("page", "1")))
        except ValueError as exc:
            raise GhostError(400, "BadRequestError", "Invalid limit or page") from exc
    pages = max(1, -(-total // limit))
    chunk = items[(page - 1) * limit: page * limit]
    meta = {"pagination": {"page": page, "limit": limit if limit_raw != "all" else "all", "pages": pages,
                           "total": total, "next": page + 1 if page < pages else None,
                           "prev": page - 1 if page > 1 else None}}
    return chunk, meta


def _project(post: dict[str, Any], query: dict[str, str], content: bool) -> dict[str, Any]:
    out = copy.deepcopy(post)
    include = set(filter(None, query.get("include", "").split(",")))
    if content:
        for key in ("lexical", "newsletter", "email", "email_segment", "email_only", "status"):
            out.pop(key, None)
        if "tags" not in include:
            out.pop("tags", None)
            out.pop("primary_tag", None)
        if "authors" not in include:
            out.pop("authors", None)
            out.pop("primary_author", None)
    fields = [f for f in query.get("fields", "").split(",") if f]
    if fields:
        out = {k: v for k, v in out.items() if k in fields}
    return out


class _Handler(BaseHTTPRequestHandler):
    ghost: MockGhost
    protocol_version = "HTTP/1.1"
    server_version = "mock-ghost/1"

    def log_message(self, fmt: str, *args: Any) -> None:  # silence the stdlib logger
        pass

    def _reply(self, status: int, payload: Any | None) -> None:
        body = b"" if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body and self.command != "HEAD":
            self.wfile.write(body)

    def _error(self, err: GhostError) -> tuple[int, Any]:
        return err.status, {"errors": [{"message": err.message, "type": err.kind, "context": None}]}

    def _body(self) -> Any:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GhostError(400, "BadRequestError", "Request body is not valid JSON") from exc

    def _handle(self) -> None:
        ghost = self.ghost
        parts = urlsplit(self.path)
        path = parts.path if parts.path.endswith("/") else parts.path + "/"
        query = {k: v[0] for k, v in parse_qs(parts.query).items()}
        entry: dict[str, Any] = {"method": self.command, "path": path, "query": query, "api": None, "auth": None,
                                 "status": None, "body": None, "fault": None}
        with ghost._lock:
            ghost.requests.append(entry)
        try:
            entry["body"] = self._body()
        except GhostError as err:
            entry["status"], payload = self._error(err)
            self._reply(entry["status"], payload)
            return
        fault = ghost._take_fault(self.command, path)
        if fault is not None:
            entry["fault"] = fault.mode
            if fault.mode == "drop":
                entry["status"] = 0
                self.close_connection = True
                try:
                    self.connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                return
            if fault.mode == "timeout":
                ghost._closing.wait(fault.seconds)
            else:
                entry["status"] = fault.status
                self._reply(fault.status, {"errors": [{"message": "Injected failure", "type": "InternalServerError",
                                                       "context": f"mock fault {fault.status}"}]})
                return
        try:
            with ghost._lock:
                status, payload = self._route(path, query, entry)
        except GhostError as err:
            status, payload = self._error(err)
        entry["status"] = status
        try:
            self._reply(status, payload)
        except OSError:  # the client gave up (timeouts)
            pass

    def _route(self, path: str, query: dict[str, str], entry: dict[str, Any]) -> tuple[int, Any]:
        ghost = self.ghost
        if path.startswith(ADMIN_PREFIX):
            entry["api"] = "admin"
            rest = path[len(ADMIN_PREFIX):]
            if rest == "site/" and self.command == "GET":
                return 200, {"site": {**ghost.site, "url": ghost.url + "/"}}
            header = self.headers.get("Authorization", "")
            if not header.startswith("Ghost "):
                entry["auth"] = "missing"
                raise GhostError(401, "UnauthorizedError", 'Authorization header format is "Authorization: Ghost [token]"')
            problem = verify_admin_token(header[len("Ghost "):].strip(), ghost.admin_key, ghost._token_time())
            entry["auth"] = "invalid" if problem else "ok"
            if problem:
                raise GhostError(401, "UnauthorizedError", f"Invalid token: {problem}")
            return self._admin(rest, query, entry["body"])
        if path.startswith(CONTENT_PREFIX):
            entry["api"] = "content"
            if query.get("key") != ghost.content_key:
                entry["auth"] = "invalid" if query.get("key") else "missing"
                raise GhostError(401, "UnauthorizedError", "Unknown Content API Key")
            entry["auth"] = "ok"
            return self._content(path[len(CONTENT_PREFIX):], query)
        raise GhostError(404, "NotFoundError", "Resource not found")

    def _admin(self, rest: str, query: dict[str, str], body: Any) -> tuple[int, Any]:
        ghost, method = self.ghost, self.command
        if rest == "newsletters/" and method == "GET":
            items = [n for n in ghost.newsletters if post_matches_newsletter(n, query.get("filter"))]
            chunk, meta = _page(items, query)
            return 200, {"newsletters": copy.deepcopy(chunk), "meta": meta}
        if rest == "posts/" and method == "GET":
            items = sorted((p for p in ghost.posts.values() if post_matches(p, query.get("filter"))),
                           key=lambda p: (p["published_at"] or p["updated_at"]), reverse=True)
            chunk, meta = _page(items, query)
            return 200, {"posts": [_project(p, query, content=False) for p in chunk], "meta": meta}
        if rest == "posts/" and method == "POST":
            posts = body.get("posts") if isinstance(body, dict) else None
            if not isinstance(posts, list) or len(posts) != 1 or not isinstance(posts[0], dict):
                raise GhostError(422, "ValidationError", "Validation error, cannot save post. No root key ('posts') provided.")
            fields = dict(posts[0])
            if query.get("source") != "html" and fields.get("html") and not fields.get("lexical"):
                fields["html"] = None  # Ghost ignores html unless ?source=html
            post = ghost._new_post(fields)
            if post["status"] == "published" and query.get("newsletter"):
                ghost._publish_email(post, query["newsletter"], query.get("email_segment", "all"))
            return 201, {"posts": [_project(post, query, content=False)]}
        match = re.fullmatch(r"posts/slug/([^/]+)/", rest)
        if match and method == "GET":
            post = next((p for p in ghost.posts.values() if p["slug"] == match.group(1)), None)
            if post is None:
                raise GhostError(404, "NotFoundError", "Post not found.")
            return 200, {"posts": [_project(post, query, content=False)]}
        match = re.fullmatch(r"posts/([0-9a-f]{24})/", rest)
        if match:
            post_id = match.group(1)
            if method == "GET":
                if post_id not in ghost.posts:
                    raise GhostError(404, "NotFoundError", "Post not found.")
                return 200, {"posts": [_project(ghost.posts[post_id], query, content=False)]}
            if method == "PUT":
                posts = body.get("posts") if isinstance(body, dict) else None
                if not isinstance(posts, list) or len(posts) != 1 or not isinstance(posts[0], dict):
                    raise GhostError(422, "ValidationError", "Validation error, cannot edit post. No root key ('posts') provided.")
                fields = dict(posts[0])
                if query.get("source") != "html" and "html" in fields and "lexical" not in fields:
                    fields.pop("html")
                post = ghost._update_post(post_id, fields, query)
                return 200, {"posts": [_project(post, query, content=False)]}
            if method == "DELETE":
                if ghost.posts.pop(post_id, None) is None:
                    raise GhostError(404, "NotFoundError", "Post not found.")
                return 204, None
        raise GhostError(404, "NotFoundError", "Resource not found")

    def _content(self, rest: str, query: dict[str, str]) -> tuple[int, Any]:
        ghost = self.ghost
        if self.command != "GET":
            raise GhostError(405, "MethodNotAllowedError", "The Content API is read-only")
        web = [p for p in ghost.posts.values() if p["status"] == "published" and not p["email_only"]]
        if rest == "posts/":
            items = sorted((p for p in web if post_matches(p, query.get("filter"))),
                           key=lambda p: p["published_at"], reverse=True)
            chunk, meta = _page(items, query)
            return 200, {"posts": [_project(p, query, content=True) for p in chunk], "meta": meta}
        match = re.fullmatch(r"posts/slug/([^/]+)/", rest)
        if match:
            post = next((p for p in web if p["slug"] == match.group(1)), None)
            if post is None:
                raise GhostError(404, "NotFoundError", "Post not found.")
            return 200, {"posts": [_project(post, query, content=True)]}
        if rest == "settings/":
            return 200, {"settings": {"title": ghost.site["title"], "description": ghost.site["description"],
                                      "lang": ghost.site["locale"], "url": ghost.url + "/", "timezone": "America/Mexico_City"}}
        raise GhostError(404, "NotFoundError", "Resource not found")

    do_GET = do_POST = do_PUT = do_DELETE = _handle  # noqa: N815


def post_matches_newsletter(newsletter: dict[str, Any], expression: str | None) -> bool:
    if not expression:
        return True
    for clause in expression.split("+"):
        key, _, raw = clause.partition(":")
        negate, values = _filter_values(raw)
        if (str(newsletter.get(key.strip())) in values) == negate:
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the mock Ghost Admin + Content API")
    parser.add_argument("--port", type=int, default=0, help="port on 127.0.0.1 (0 = any free port)")
    parser.add_argument("--seed-cartas", type=int, default=3, help="published posts tagged cartas to seed")
    args = parser.parse_args(argv)
    ghost = MockGhost(port=args.port).start()
    ghost.seed_cartas(args.seed_cartas)
    print(f"MOCK_GHOST {ghost.url} admin_key={ghost.admin_key} content_key={ghost.content_key}", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        ghost.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
