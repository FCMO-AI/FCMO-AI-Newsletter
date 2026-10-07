"""The email product name is consistent across reader-facing email surfaces."""
from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = "FCMO AI Diario"


EMAIL_SURFACES = (
    "tools/email_render.py",
    "tools/email_dispatch.py",
    "tools/email_listmonk.py",
    "tools/email_providers",
    "ops/email/bootstrap.py",
    "ops/email/offline_e2e.py",
    "ops/email/email.env.example",
    "tools/paper/templates/subscribe.py",
    "tools/paper/community.py",
    "ops/email/static/email-templates",
    "legal/email-privacy.json",
    "legal/email-privacy-kit.json",
    "legal/email-privacy-brevo.json",
    "legal/PRIVACY.md",
    "community/config/subscriptions.json",
    "community/ghost-theme/partials/subscription-choices.hbs",
    "community/ghost-theme/partials/subscription-choices.hbs.in",
    ".github/workflows/dispatch-email.yml",
    ".github/workflows/operator-alerts.yml",
    ".github/workflows/backup-email.yml",
    "REPORT-L27.md",
    "docs/EMAIL-PROVIDERS.md",
    "reports/email-preview",
)


def surface_files(path: Path):
    if path.is_file():
        yield path
    elif path.is_dir():
        yield from sorted(item for item in path.rglob("*") if item.is_file())


class EmailBrandTests(unittest.TestCase):
    def test_product_name_is_canonical_and_rendered_as_sender_header(self):
        from tools.email_render import PAPER_NAME, render_daily_email

        self.assertEqual(PAPER_NAME, "FCMO AI Newsletter")
        stories = json.loads((ROOT / "site/data/stories.v2.json").read_text(encoding="utf-8"))["stories"]
        for locale in ("en", "es-419", "zh-Hans"):
            with self.subTest(locale=locale):
                email = render_daily_email(stories, "2026-10-06", locale=locale)
                self.assertTrue(email.subject.startswith("FCMO AI Newsletter:"))
                self.assertIn(">FCMO AI Newsletter</p>", email.html)
                self.assertIn("FCMO AI Newsletter", email.text)

    def test_reader_facing_email_surfaces_use_newsletter_brand(self):
        matches = []
        for relative in EMAIL_SURFACES:
            for path in surface_files(ROOT / relative):
                try:
                    content = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                if FORBIDDEN in content:
                    matches.append(f"{path.relative_to(ROOT)}: {FORBIDDEN}")
        self.assertEqual(matches, [], "email surfaces still use the old product name:\n" + "\n".join(matches))


if __name__ == "__main__":
    unittest.main()
