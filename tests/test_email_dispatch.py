from __future__ import annotations

import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for entry in (ROOT, ROOT / "tests"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from harness.mock_ghost import MockGhost  # noqa: E402
from tools.email_dispatch import dispatch, eligibility  # noqa: E402
from tools.email_render import render_daily_email, select_stories  # noqa: E402


FIXTURES = ROOT / "contracts" / "fixtures"


def fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class EmailDispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.stories = fixture("stories.v2.json")
        # The dispatch contract requires new stories since the previous send.
        for story in self.stories["stories"]:
            story["first_published_at"] = "2026-09-26T11:00:00Z"
        self.status = fixture("newsroom-status.fresh.json")
        self.now = datetime(2026, 9, 26, 14, 0, tzinfo=timezone.utc)
        self.verified = True

    def test_renderer_is_native_spanish_and_has_plain_text(self) -> None:
        items = select_stories(self.stories)
        self.assertGreaterEqual(len(items), 3)
        email = render_daily_email(self.stories, self.status["edition_date"], postal_address="Domicilio de prueba")
        self.assertIn("Lo esencial hoy", email.html)
        self.assertIn("Por qué importa", email.html)
        self.assertIn("Domicilio de prueba", email.text)
        self.assertNotIn("<script", email.html.lower())
        self.assertIn("FCMO AI Newsletter:", email.subject)

    def test_second_run_is_idempotent(self) -> None:
        with MockGhost() as ghost:
            first = dispatch(stories=self.stories, status=self.status, live_verified=True, ghost_url=ghost.url,
                             admin_api_key=ghost.admin_key, now=self.now, postal_address="Domicilio de prueba")
            second = dispatch(stories=self.stories, status=self.status, live_verified=True, ghost_url=ghost.url,
                              admin_api_key=ghost.admin_key, now=self.now, postal_address="Domicilio de prueba")
            self.assertEqual(first[0], 0, first)
            self.assertEqual(second, (0, "SKIP already_sent"))
            self.assertEqual(len(ghost.emails), 1)

    def test_live_verification_failure_and_delayed_are_safe_skips(self) -> None:
        with MockGhost() as ghost:
            code, output = dispatch(stories=self.stories, status=self.status, live_verified=False, ghost_url=ghost.url,
                                    admin_api_key=ghost.admin_key, now=self.now, postal_address="Domicilio de prueba")
            self.assertEqual((code, output), (0, "SKIP not_verified"))
            delayed = copy.deepcopy(self.status)
            delayed["edition_state"] = "DELAYED"
            code, output = dispatch(stories=self.stories, status=delayed, live_verified=True, ghost_url=ghost.url,
                                    admin_api_key=ghost.admin_key, now=self.now, postal_address="Domicilio de prueba")
            self.assertEqual((code, output), (0, "SKIP edition_state=DELAYED"))
            self.assertEqual(ghost.count("POST"), 0)

    def test_incomplete_es_is_safe_skip(self) -> None:
        incomplete = copy.deepcopy(self.stories)
        for story in incomplete["stories"]:
            story["l10n"]["es-419"]["state"] = "PENDING"
        with MockGhost() as ghost:
            result = dispatch(stories=incomplete, status=self.status, live_verified=True, ghost_url=ghost.url,
                              admin_api_key=ghost.admin_key, now=self.now, postal_address="Domicilio de prueba")
            self.assertEqual(result, (0, "SKIP es_incomplete"))
            self.assertEqual(ghost.count("POST"), 0)

    def test_missing_native_field_never_falls_back_to_english(self) -> None:
        incomplete = copy.deepcopy(self.stories)
        for story in incomplete["stories"]:
            story["l10n"]["es-419"]["fields"].pop("summary", None)
        self.assertEqual(eligibility(incomplete, self.status, live_verified=True, now=self.now).reason,
                         "es_incomplete")

    def test_old_corpus_does_not_become_a_new_daily_email(self) -> None:
        stale = fixture("stories.v2.json")
        self.assertEqual(eligibility(stale, self.status, live_verified=True, now=self.now).reason,
                         "no_new_edition_stories")

    def test_sent_email_uses_only_new_stories(self) -> None:
        older = self.stories["stories"][0]
        older["first_published_at"] = "2026-09-01T12:00:00Z"
        older["importance"] = 100
        example = next(story for story in self.stories["stories"]
                       if story["status"] == "live" and story["l10n"]["es-419"]["state"] == "NATIVE_ARB")
        for suffix in ("000001", "000002"):
            additional = copy.deepcopy(example)
            additional["id"] = "FCMO-TEST00" + suffix
            self.stories["stories"].append(additional)

        class Client:
            subject = ""
            def find_slug(self, slug): return None
            def create_draft(self, slug, email):
                self.subject = email.subject
                return {"id": "draft-1", "updated_at": "2026-09-26T14:00:00Z",
                        "title": email.subject, "html": email.html}
            def publish_email(self, post, newsletter): return {"slug": "diario-2026-09-26"}

        client = Client()
        self.assertEqual(len(eligibility(self.stories, self.status, live_verified=True,
                                         now=self.now).items), 5)
        code, _ = dispatch(stories=self.stories, status=self.status, live_verified=True,
                           ghost_url="https://ghost.example", admin_api_key="unused",
                           now=self.now, postal_address="Domicilio de prueba", client=client)
        self.assertEqual(code, 0)
        self.assertNotIn(older["l10n"]["es-419"]["fields"]["title"], client.subject)

    def test_missing_edition_date_does_not_send(self) -> None:
        status = copy.deepcopy(self.status)
        status.pop("edition_date")
        self.assertEqual(eligibility(self.stories, status, live_verified=True, now=self.now).reason,
                         "edition_not_today")

    def test_publish_failure_leaves_draft_and_retry_reuses_it(self) -> None:
        with MockGhost() as ghost:
            ghost.fail(status=503, method="PUT", path="/ghost/api/admin/posts/", times=1)
            failed = dispatch(stories=self.stories, status=self.status, live_verified=True, ghost_url=ghost.url,
                              admin_api_key=ghost.admin_key, now=self.now, postal_address="Domicilio de prueba")
            self.assertEqual(failed, (1, "ERROR ghost_api status=503"))
            self.assertEqual(ghost.count("POST", "/ghost/api/admin/posts/"), 1)
            succeeded = dispatch(stories=self.stories, status=self.status, live_verified=True, ghost_url=ghost.url,
                                 admin_api_key=ghost.admin_key, now=self.now, postal_address="Domicilio de prueba")
            self.assertEqual(succeeded[0], 0, succeeded)
            self.assertEqual(ghost.count("POST", "/ghost/api/admin/posts/"), 1)
            self.assertEqual(len(ghost.emails), 1)


if __name__ == "__main__":
    unittest.main()
