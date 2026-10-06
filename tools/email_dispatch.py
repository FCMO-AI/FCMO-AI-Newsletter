#!/usr/bin/env python3
"""Dispatch the verified, fresh FCMO AI Newsletter through a configured provider adapter.

The legacy Ghost implementation remains available for compatibility. Kit and
Listmonk are exercised through offline fixtures; delivery runs only on invocation.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, time as clock_time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from tools.email_render import RenderedEmail, render_daily_email, select_stories
except ModuleNotFoundError:  # direct invocation from tools/
    from email_render import RenderedEmail, render_daily_email, select_stories


CDMX = ZoneInfo("America/Mexico_City")
UTC = timezone.utc
EMAIL_TIME = clock_time(7, 30)
USER_AGENT = "FCMO-Newsletter-Email-Dispatcher/1.0"


class GhostAPIError(RuntimeError):
    def __init__(self, status: int, message: str, body: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.body = body


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def admin_jwt(api_key: str, now: int | None = None) -> str:
    try:
        key_id, secret = api_key.split(":", 1)
        secret_bytes = bytes.fromhex(secret)
    except (ValueError, TypeError) as exc:
        raise ValueError("GHOST_ADMIN_API_KEY must be key_id:hex_secret") from exc
    issued = int(time.time()) if now is None else int(now)
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT", "kid": key_id}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"iat": issued, "exp": issued + 300, "aud": "/admin/"}, separators=(",", ":")).encode())
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = hmac.new(secret_bytes, signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64(signature)}"


def parse_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=parsed.tzinfo or UTC).astimezone(UTC)


def _json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _verification_passed(path: Path) -> bool:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return False
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError:
        return raw.lstrip().startswith("SERVING OK")
    if not isinstance(doc, dict):
        return False
    return (doc.get("status") == "GREEN" and doc.get("code") == "OK") or doc.get("passed") is True


def _recent_stories(doc: Any, *, now: datetime) -> list[dict[str, Any]]:
    values = doc.get("stories") if isinstance(doc, dict) else doc
    if not isinstance(values, list):
        raise ValueError("stories input must be a list or a {stories: [...]} document")
    local_today = now.astimezone(CDMX).date()
    since = datetime.combine(local_today - timedelta(days=1), EMAIL_TIME, CDMX).astimezone(UTC)
    recent = []
    for story in values:
        if not isinstance(story, dict):
            continue
        published = story.get("first_published_at")
        if not isinstance(published, str):
            continue
        try:
            published_at = datetime.fromisoformat(published.replace("Z", "+00:00"))
            if published_at.tzinfo is None:
                continue
            if since <= published_at.astimezone(UTC) <= now.astimezone(UTC):
                recent.append(story)
        except ValueError:
            continue
    return recent


@dataclass(frozen=True)
class DispatchDecision:
    action: str
    reason: str
    items: tuple[dict[str, Any], ...] = ()


def eligibility(
    stories: Any,
    status: dict[str, Any],
    *,
    live_verified: bool,
    now: datetime,
    minimum: int = 3,
    maximum: int = 5,
) -> DispatchDecision:
    if not live_verified:
        return DispatchDecision("SKIP", "not_verified")
    if status.get("edition_state") != "FRESH":
        return DispatchDecision("SKIP", f"edition_state={status.get('edition_state', 'MISSING')}")
    if now.astimezone(CDMX).time().replace(tzinfo=None) < EMAIL_TIME:
        return DispatchDecision("SKIP", "before_0730_cdmx")
    edition_date = status.get("edition_date")
    if edition_date != now.astimezone(CDMX).date().isoformat():
        return DispatchDecision("SKIP", "edition_not_today")
    recent = _recent_stories(stories, now=now)
    if len(recent) < minimum:
        return DispatchDecision("SKIP", "no_new_edition_stories")
    complete = select_stories(recent)
    if len(complete) < minimum:
        return DispatchDecision("SKIP", "es_incomplete")
    return DispatchDecision("SEND", "eligible", tuple(complete[:maximum]))


class GhostClient:
    def __init__(self, base_url: str, admin_api_key: str, *, timeout: float = 15.0, token_clock: int | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.admin_api_key = admin_api_key
        self.timeout = timeout
        self.token_clock = token_clock

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.base_url + "/ghost/api/admin/" + path.lstrip("/")
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=body, method=method.upper(), headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Authorization": "Ghost " + admin_jwt(self.admin_api_key, self.token_clock),
        })
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GhostAPIError(exc.code, f"Ghost API {exc.code} on {method} {path}", detail) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise GhostAPIError(0, f"Ghost API unavailable on {method} {path}: {exc}") from exc
        if not raw:
            return {}
        try:
            value = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise GhostAPIError(0, f"Ghost API returned invalid JSON on {method} {path}") from exc
        if not isinstance(value, dict):
            raise GhostAPIError(0, f"Ghost API returned a non-object on {method} {path}")
        return value

    def find_slug(self, slug: str) -> dict[str, Any] | None:
        path = "posts/slug/" + urllib.parse.quote(slug, safe="") + "/"
        try:
            response = self._request("GET", path)
        except GhostAPIError as exc:
            if exc.status == 404:
                return None
            raise
        posts = response.get("posts")
        return posts[0] if isinstance(posts, list) and posts and isinstance(posts[0], dict) else None

    def create_draft(self, slug: str, email: RenderedEmail) -> dict[str, Any]:
        response = self._request("POST", "posts/?source=html", {"posts": [{
            "slug": slug,
            "title": email.subject,
            "custom_excerpt": email.preheader,
            "html": email.html,
            "status": "draft",
            "email_only": True,
        }]})
        posts = response.get("posts")
        if not isinstance(posts, list) or not posts or not isinstance(posts[0], dict):
            raise GhostAPIError(0, "Ghost create response did not contain a post")
        return posts[0]

    def publish_email(self, post: dict[str, Any], newsletter: str = "diario") -> dict[str, Any]:
        post_id = post.get("id")
        updated_at = post.get("updated_at")
        if not post_id or not updated_at:
            raise GhostAPIError(0, "Ghost draft lacks id or updated_at")
        payload = {"posts": [{
            "id": post_id,
            "updated_at": updated_at,
            "status": "published",
            "email_only": True,
            "title": post.get("title", "FCMO AI Newsletter"),
            "html": post.get("html", ""),
            "custom_excerpt": post.get("custom_excerpt", ""),
        }]}
        path = f"posts/{urllib.parse.quote(str(post_id), safe='')}/?source=html&newsletter={urllib.parse.quote(newsletter, safe='')}&email_segment=all"
        response = self._request("PUT", path, payload)
        posts = response.get("posts")
        if not isinstance(posts, list) or not posts or not isinstance(posts[0], dict):
            raise GhostAPIError(0, "Ghost publish response did not contain a post")
        return posts[0]


def dispatch(
    *,
    stories: Any,
    status: dict[str, Any],
    live_verified: bool,
    ghost_url: str,
    admin_api_key: str,
    now: datetime,
    postal_address: str,
    site_url: str = "https://fcmo-ai.github.io/FCMO-AI-Newsletter",
    newsletter: str = "diario",
    client: GhostClient | None = None,
) -> tuple[int, str]:
    decision = eligibility(stories, status, live_verified=live_verified, now=now)
    if decision.action == "SKIP":
        return 0, f"SKIP {decision.reason}"
    if not postal_address.strip():
        return 1, "ERROR missing_postal_address"
    edition_date = status["edition_date"]
    slug = f"diario-{edition_date}"
    if not ghost_url or not admin_api_key:
        return 1, "ERROR missing_ghost_configuration"
    account_url = ghost_url.rstrip("/") + "/#/portal/account"
    email = render_daily_email([item["story"] for item in decision.items], edition_date, site_url=site_url,
                               postal_address=postal_address, preferences_url=account_url,
                               unsubscribe_url=account_url)
    ghost = client or GhostClient(ghost_url, admin_api_key)
    try:
        existing = ghost.find_slug(slug)
        if existing is not None and existing.get("status") in {"sent", "published"}:
            return 0, "SKIP already_sent"
        draft = existing if existing is not None else ghost.create_draft(slug, email)
        sent = ghost.publish_email(draft, newsletter)
    except GhostAPIError as exc:
        # Keep the reason useful without ever echoing the JWT or API key.
        return 1, f"ERROR ghost_api status={exc.status}"
    return 0, f"SENT edition={edition_date} slug={sent.get('slug', slug)}"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == '--pieces':
        from tools.email_piece_dispatch import main as piece_main
        return piece_main(argv[1:])
    parser = argparse.ArgumentParser(description="Dispatch a live-verified FCMO AI Newsletter through the selected adapter.")
    parser.add_argument("--stories", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--live-verify", type=Path, required=True)
    parser.add_argument("--ghost-url", default=os.environ.get("GHOST_URL", ""))
    parser.add_argument("--admin-api-key", default=os.environ.get("GHOST_ADMIN_API_KEY", ""))
    parser.add_argument("--postal-address", default=os.environ.get("FCMO_EMAIL_POSTAL_ADDRESS", ""))
    parser.add_argument("--site-url", default=os.environ.get("FCMO_SITE_URL", "https://fcmo-ai.github.io/FCMO-AI-Newsletter"))
    parser.add_argument("--newsletter", default="diario")
    parser.add_argument("--now", help="UTC timestamp for deterministic local checks")
    parser.add_argument('--provider', default=os.environ.get('FCMO_EMAIL_PROVIDER','listmonk'))
    parser.add_argument('--email-url', default=os.environ.get('FCMO_EMAIL_PUBLIC_URL',''))
    parser.add_argument('--check', action='store_true', help='Validate all locales and provider health without sending')
    args = parser.parse_args(argv)
    try:
        status = _json_file(args.status)
        stories = _json_file(args.stories)
        now = parse_timestamp(args.now)
        if args.check:
            from tools.email_providers import Edition
            decision = eligibility(stories,status,live_verified=_verification_passed(args.live_verify),now=now)
            eligible = os.environ.get('FCMO_EMAIL_ENABLED') == 'true' and decision.action == 'SEND'
            if eligible:
                from tools.email_providers import create_provider
                from tools.email_listmonk import DeliveryError
                Edition(stories,status,_json_file(args.live_verify),now).selected()
                provider = create_provider(dict(os.environ,FCMO_EMAIL_PROVIDER=args.provider))
                try:
                    health = provider.health()
                    for warning in health.get('warnings', []):
                        if isinstance(warning, str) and re.fullmatch(r'[a-z][a-z0-9_]*', warning):
                            print('WARNING '+warning)
                except DeliveryError:
                    print('ERROR email_provider_preflight_failed')
                    return 1
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'],'a') as output:
                    output.write('eligible='+str(eligible).lower()+'\n')
                    output.write('requires_intent='+str(eligible and getattr(provider,'requires_intent',False)).lower()+'\n')
            print('ELIGIBLE' if eligible else 'SKIP '+decision.reason)
            return 0
        if os.environ.get('FCMO_EMAIL_ENABLED') != 'true':
            print('SKIP disabled')
            return 0
        if args.provider != 'ghost':
            from tools.email_providers import create_provider, Edition, dispatch_edition
            from tools.email_listmonk import DeliveryError
            decision = eligibility(stories,status,live_verified=_verification_passed(args.live_verify),now=now)
            if decision.action == 'SKIP':
                print('SKIP '+decision.reason)
                return 0
            receipt = _json_file(args.live_verify)
            if not receipt.get('source_commit') or not receipt.get('candidate_id'):
                raise ValueError('missing_authenticated_live_receipt')
            env = dict(os.environ,FCMO_EMAIL_PROVIDER=args.provider,FCMO_EMAIL_PUBLIC_URL=args.email_url)
            edition = Edition(stories,status,receipt,now,os.environ.get('FCMO_EMAIL_NAMESPACE','fcmo-diario'))
            try:
                outcome = dispatch_edition(create_provider(env),edition,enabled=True,live_verified=True)
            except DeliveryError:
                print('ERROR email_provider_outcome_unconfirmed; reconcile before retry')
                return 1
            print(json.dumps(outcome,sort_keys=True))
            return 0
        code, message = dispatch(stories=stories, status=status, live_verified=_verification_passed(args.live_verify),
                                 ghost_url=args.ghost_url, admin_api_key=args.admin_api_key, now=now,
                                 postal_address=args.postal_address, site_url=args.site_url, newsletter=args.newsletter)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR invalid_input {exc}")
        return 1
    print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
