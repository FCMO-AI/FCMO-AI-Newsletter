"""Publication clocks are independent of daily supply and checkout depth."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools import story_layer, taxonomy

FIXTURES = Path(__file__).resolve().parents[1] / "contracts/fixtures"
FIRST = "2026-10-08T09:00:48Z"
LATER = "2026-10-09T00:49:52Z"
NOW = "2026-10-10T12:00:00Z"


class PublicationHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.corpus = self.repo / "corpus"
        self.site = self.repo / "site"
        (self.corpus / "data").mkdir(parents=True)
        (self.site / "data").mkdir(parents=True)
        seed = taxonomy.read_jsonl(FIXTURES / "corpus-44/data/developments.jsonl")[0]
        seed.update(title="A fixture laboratory publishes a research result",
                    summary="The fixture laboratory describes a result awaiting independent review.",
                    why_it_matters="Independent review would establish whether the result is useful.",
                    importance_rationale="The result remains a claim pending independent review.",
                    claims=[{"label": "CLAIMED", "text": "The laboratory reports a research result."}],
                    limitations=[], contradictory_evidence=[], evidence_gaps=[], relationships=[], technical={})
        self.rid = seed["id"]
        (self.corpus / "data/developments.jsonl").write_text(json.dumps(seed) + "\n")
        for locale, text in (("es-419", "El laboratorio informa un resultado pendiente de revisión independiente."),
                             ("zh-Hans", "实验室报告了一项尚待独立审查的研究结果。")):
            native = {key: text for key in ("title", "summary", "why_it_matters", "importance_rationale")}
            native["claims"] = [{"label": "CLAIMED", "text": text}]
            path = self.corpus / f"data/locales/{locale}/records.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"schema": "fcmo-airlocked-locale-delta-v1", "locale": locale,
                                        "records": {self.rid: native}}))
        self.git("init", "--quiet")
        self.write_publication(FIRST)
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.org",
                 "commit", "--quiet", "-m", "Publish fixture")
        self.write_publication(LATER)
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.org",
                 "commit", "--quiet", "-m", "Refresh fixture")

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True)

    def write_publication(self, stamp):
        (self.site / "data/stories.json").write_text(json.dumps([
            {"research_id": self.rid, "published_at": stamp}]))

    def build(self, repo, previous=None):
        return story_layer.build_stories(story_layer.StoryInputs(
            self.corpus, repo, self.site, None, NOW, previous=previous))

    def test_earliest_history_wins_over_a_later_current_publication(self):
        full = self.build(self.repo)
        story = full["stories"][0]
        self.assertEqual(story["first_published_at"], FIRST)
        ledger, tombstones, _ = story_layer.update_ledger(self.corpus, self.repo, self.site, NOW)
        self.assertEqual(ledger["entries"][self.rid]["first_published_at"], FIRST)
        (self.corpus / "first-published.json").write_text(json.dumps(ledger))
        (self.corpus / "tombstones.json").write_text(json.dumps(tombstones))
        again, _, changes = story_layer.update_ledger(self.corpus, self.repo, self.site, NOW)
        self.assertEqual(again, ledger)
        self.assertEqual(changes, [])

    def test_previous_v2_preserves_history_without_a_frozen_ledger(self):
        full = self.build(self.repo)
        shallow = self.build(None, previous=full)
        self.assertEqual(shallow, full)

    def test_shallow_ledger_uses_previous_v2_instead_of_a_later_v1_clock(self):
        full = self.build(self.repo)
        (self.site / "data/stories.v2.json").write_text(json.dumps(full))
        ledger, _, _ = story_layer.update_ledger(self.corpus, None, self.site, NOW)
        self.assertEqual(ledger["entries"][self.rid]["first_published_at"], FIRST)

    def test_frozen_ledger_wins_over_history_and_previous_v2(self):
        full = self.build(self.repo)
        frozen = {"first_published_at": LATER, "url_date": "2026-10-08", "slug": "frozen-route"}
        ledger = {"schema": story_layer.LEDGER_SCHEMA, "entries": {self.rid: frozen}}
        (self.corpus / "first-published.json").write_text(json.dumps(ledger))
        for repo in (self.repo, None):
            with self.subTest(history=repo is not None):
                story = self.build(repo, previous=full)["stories"][0]
                for key, value in frozen.items():
                    self.assertEqual(story[key], value)
                again, _, changes = story_layer.update_ledger(self.corpus, repo, self.site, NOW)
                self.assertEqual(again, ledger)
                self.assertEqual(changes, [])


if __name__ == "__main__":
    unittest.main()
