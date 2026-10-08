"""Field-level localization completeness, the pending notice, and the UI catalogs.

A (story, locale) pair counts as translated only when every non-empty prose
field of the English record has a native counterpart. These tests prove it on
the committed corpus (against an independent top-level recount) and on small
synthetic corpora, and they check the three reader-facing UI catalogs.
"""
from __future__ import annotations

import contextlib
import glob
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import mark_pending_localizations as mp  # noqa: E402
from tools import validate_localizations as vl  # noqa: E402

NOW = "2026-09-26T20:00:00Z"
LOCALES = ("es-419", "zh-Hans")
CATALOG_LOCALES = ("en", "es-419", "zh-Hans")
RAW_ENUM = re.compile(r"\b[a-z]+(?:_[a-z]+){2,}\b|\b[A-Z]{2,}(?:_[A-Z]+)+\b")
HAN = re.compile(r"[㐀-鿿]")
PLACEHOLDER = re.compile(r"\{([a-z][a-z0-9_]*)\}")
TOP_PROSE = ("title", "summary", "why_it_matters", "importance_rationale", "limitations",
             "contradictory_evidence", "claims", "evidence_gaps", "relationships", "technical")
NON_PROSE = {"label", "qualifier", "kind", "state", "updated_at", "target_id", "type", "id", "url", "source_url"}


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=300)


def has_text(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(has_text(v) for k, v in value.items() if k not in NON_PROSE)
    if isinstance(value, list):
        return any(has_text(v) for v in value)
    return False


def independent_backlog(locale: str, published_only: bool = False) -> set[str]:
    """Leaf-level recount from raw files, sharing no code with the tools."""
    canonical = {}
    for line in (ROOT / "corpus/data/developments.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            canonical[row["id"]] = row
    carried = ROOT / "corpus/carried.jsonl"
    if carried.is_file():
        for line in carried.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                canonical.setdefault(row["id"], row["record"])
    dead = {rid for rid, row in canonical.items() if str(row.get("status") or "").lower() in {"withdrawn", "superseded"}}
    tombstones = ROOT / "corpus/tombstones.json"
    if tombstones.is_file():
        for entry in json.loads(tombstones.read_text(encoding="utf-8")).get("tombstones") or []:
            if entry.get("reinstated_at") is None:
                dead.add(entry.get("id"))
    if published_only and (ROOT / 'release-src/data/publication-admission.json').is_file():
        # Receipts describe the committed English version, which can be a
        # carried version while an incoming update waits for native repair.
        canonical = {path.stem: json.loads(path.read_text())['brief']
                     for path in (ROOT / 'release-src/data/briefs').glob('FCMO-*.json')}
    overlays: dict[str, dict] = {}
    for path in sorted(glob.glob(str(ROOT / f"site/data/i18n/{locale}/part-*.json"))):
        for rid, row in json.loads(Path(path).read_text(encoding="utf-8"))["records"].items():
            chosen = overlays.setdefault(rid, {})
            for key, value in row.items():
                chosen.setdefault(key, value)  # ARB fields precede desk gap fills.
    delta = ROOT / f"corpus/data/locales/{locale}/records.json"
    if delta.is_file() and not published_only:
        for rid, row in json.loads(delta.read_text(encoding="utf-8"))["records"].items():
            overlays[rid] = {**overlays.get(rid, {}), **row}
    published = {r["research_id"] for r in json.loads((ROOT / "site/data/stories.json").read_text())}
    return {rid for rid, row in canonical.items() if rid not in dead
            and (not published_only or rid in published)
            and independent_pair_incomplete(row, overlays.get(rid) or {}, locale)}


def independent_pair_incomplete(source: dict, overlay: dict, locale: str) -> bool:
    # This census deliberately has no import from the validator. Compare every
    # prose position, ignoring only codes, dates, IDs and source URLs.
    def prose(value, path=()):
        if isinstance(value, dict):
            for key, child in value.items():
                if key not in NON_PROSE:
                    yield from prose(child, path + (key,))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from prose(child, path + (index,))
        elif isinstance(value, str) and value.strip():
            yield path, value

    source = dict(source)
    if not source.get("why_it_matters") and source.get("why"):
        source["why_it_matters"] = source["why"]
    source = {k: source[k] for k in TOP_PROSE if k in source}
    overlay = {k: v for k, v in overlay.items() if k in TOP_PROSE or k == "why"}
    if not source.get("why_it_matters") and source.get("why"):
        source["why_it_matters"] = source.pop("why")
    if not overlay.get("why_it_matters") and overlay.get("why"):
        overlay["why_it_matters"] = overlay["why"]
    overlay.pop("why", None)
    original = dict(prose(source))
    native = dict(prose(overlay))
    if original.keys() - native.keys():
        return True
    function_words = set("the and of to is that with for this are was which from by on not it be have its than an or as at were but their these those into".split())
    for path, text in native.items():
        words = re.findall(r"[A-Za-z][A-Za-z'’-]*", text)
        if len(words) >= 3 and " ".join(text.split()) == " ".join(original.get(path, "").split()):
            return True
        if locale == "zh-Hans":
            # Inspect each uninterrupted Latin phrase, including nested fields.
            runs = re.findall(r"(?:[A-Za-z][A-Za-z'’-]*[\s,;:()\"“”]+){5,}[A-Za-z][A-Za-z'’-]*", text)
            if any(sum(w.lower() in function_words for w in re.findall(r"[A-Za-z]+", run)) >= 2 for run in runs):
                return True
        else:
            all_words = re.findall(r"[^\W\d_]+", text, re.UNICODE)
            count = sum(w.lower() in function_words for w in all_words)
            if count >= 3 and count / max(1, len(all_words)) >= 0.12:
                return True
    return False


def leaves(value, path=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaves(item, f"{path}[{index}]")
    else:
        yield path, value


class LangText(HTMLParser):
    """Visible text, split by whether an ancestor says lang="en"."""

    VOID = {"meta", "link", "br", "img", "input", "hr"}

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[tuple[str, str | None]] = []
        self.native: list[str] = []
        self.english: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        self.stack.append((tag, dict(attrs).get("lang")))
        if tag in {"script", "style", "title"}:
            self.skip += 1

    def handle_endtag(self, tag):
        while self.stack:
            open_tag, _ = self.stack.pop()
            if open_tag in {"script", "style", "title"}:
                self.skip -= 1
            if open_tag == tag:
                break

    def handle_data(self, data):
        if self.skip or not data.strip():
            return
        langs = [lang for _, lang in self.stack if lang]
        (self.english if langs and langs[-1] == "en" else self.native).append(data)


# --------------------------------------------------------------------------- fixtures

RID_PARTIAL = "FCMO-0C0DE00A5A01"
RID_COMPLETE = "FCMO-0C0DE00A5A02"
RID_LEAK = "FCMO-0C0DE00A5A03"


def english_record(rid: str, recorded_at: str = "2026-09-20T12:00:00Z") -> dict:
    return {
        "id": rid,
        "title": "A lab releases a compact reasoning model with open weights",
        "summary": "The lab reports that the model matches larger systems on 3 of 5 public benchmarks while using 40% less compute.",
        "why_it_matters": "If the result holds under independent testing, smaller teams could train competitive reasoning models.",
        "importance_rationale": "The claim is material for the open ecosystem but has not been reproduced yet.",
        "limitations": ["The evaluation used the lab's own harness and has not been reproduced."],
        "contradictory_evidence": [],
        "claims": [{"label": "CLAIMED", "text": "The model matches larger systems on 3 of 5 benchmarks."}],
        "evidence_gaps": [{"kind": "reproduction_missing", "state": "open",
                           "description": "No independent reproduction has been published.",
                           "updated_at": "2026-09-20T12:00:00Z"}],
        "relationships": [],
        "technical": {"claimed_result": "Parity on 3 of 5 benchmarks with 40% less compute."},
        "event_at": "2026-09-08T00:00:00Z",
        "recorded_at": recorded_at,
        "primary_desk": "reasoning_posttraining",
        "status": "active",
    }


SPANISH_FULL = {
    "title": "Un laboratorio lanza un modelo compacto de razonamiento con pesos abiertos",
    "summary": "El laboratorio informa que el modelo iguala a sistemas más grandes en 3 de 5 benchmarks públicos con 40% menos cómputo.",
    "why_it_matters": "Si el resultado se sostiene con pruebas independientes, equipos más pequeños podrían entrenar modelos de razonamiento competitivos.",
    "importance_rationale": "La afirmación importa para el ecosistema abierto, pero todavía no se ha reproducido.",
    "limitations": ["La evaluación usó el arnés propio del laboratorio y no se ha reproducido."],
    "claims": [{"label": "CLAIMED", "text": "El modelo iguala a sistemas más grandes en 3 de 5 benchmarks."}],
    "evidence_gaps": [{"kind": "reproduction_missing", "state": "open",
                       "description": "No se ha publicado una reproducción independiente.",
                       "updated_at": "2026-09-20T12:00:00Z"}],
    "technical": {"claimed_result": "Paridad en 3 de 5 benchmarks con 40% menos cómputo."},
}
SPANISH_HEADLINE_ONLY = {k: SPANISH_FULL[k] for k in ("title", "summary", "why_it_matters")}
CHINESE_HEADLINE_ONLY = {
    "title": "实验室发布采用开放权重的紧凑型推理模型",
    "summary": "该实验室称，这一模型在 5 项公开基准测试中的 3 项上追平更大的系统，同时少用 40% 的算力。",
    "why_it_matters": "如果结果经得起独立检验，规模较小的团队也可能训练出有竞争力的推理模型。",
}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_fixture(root: Path, records: list[dict], packs: dict[str, dict[str, dict]]) -> tuple[Path, Path]:
    corpus = root / "corpus"
    (corpus / "data").mkdir(parents=True)
    (corpus / "data" / "developments.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    site = root / "site"
    stories = [{
        "research_id": r["id"], "headline": r["title"], "dek": r["summary"], "why_it_matters": r["why_it_matters"],
        "story_type": "STANDARD", "event_at": r["event_at"],
        "published_at": "2026-09-20T12:00:00Z", "modified_at": "2026-09-21T03:30:00Z",
    } for r in records]
    write_json(site / "data" / "stories.json", stories)
    for locale in LOCALES:
        write_json(site / "data" / "i18n" / locale / "part-airlock.json", {
            "schema": "fcmo-curated-locale-part-v1", "locale": locale, "canonical_locale": "en",
            "records": packs.get(locale, {}),
        })
    return corpus, site


# --------------------------------------------------------------------------- real corpus


class RealCorpusBacklog(unittest.TestCase):
    """The committed corpus: the backlog is measured, not assumed."""

    @classmethod
    def setUpClass(cls):
        cls.expected = {loc: independent_backlog(loc) for loc in LOCALES}
        cls.published_expected = {loc: independent_backlog(loc, published_only=True) for loc in LOCALES}
        cls.story_count = len(vl.load_corpus_canonical(ROOT / "corpus"))

    def test_independent_recount_matches_committed_locale_backlog(self):
        """The committed receipt must follow live corpus membership, not a frozen count."""
        status = json.loads((ROOT / "site/data/i18n/translation-status.json").read_text(encoding="utf-8"))
        for locale in LOCALES:
            reported = set(status["locales"][locale]["pending_ids"]) | set(
                status["locales"][locale]["failed_ids"]
            )
            self.assertEqual(reported, self.published_expected[locale], locale)

    def test_strict_validator_reports_incomplete_pairs(self):
        for locale in LOCALES:
            result = run("tools/validate_localizations.py", "--strict", "--corpus", "corpus", "--locale", locale)
            lines = result.stdout.splitlines()
            want = len(self.expected[locale])
            self.assertEqual(lines[0], f"INCOMPLETE {want}" if want else f"COMPLETE {self.story_count}", result.stdout + result.stderr)
            self.assertEqual(result.returncode, 1 if want else 0)
            listed = {line.split()[2] for line in lines if line.startswith(("PENDING ", "FAILED "))}
            self.assertEqual(listed, self.expected[locale])

    @staticmethod
    def after_grace():
        # Read publication times independently; a future incoming record cannot
        # make an overdue fixture accidentally exercise GRACE instead of BACKLOG.
        entries = json.loads((ROOT / "corpus/first-published.json").read_text())["entries"]
        records = [json.loads(line) for line in (ROOT / "corpus/data/developments.jsonl").read_text().splitlines() if line]
        stamps = [entries.get(row["id"], {}).get("first_published_at") or row.get("recorded_at")
                  for row in records]
        now = max(datetime.fromisoformat(stamp.replace("Z", "+00:00")) for stamp in stamps if stamp) + timedelta(hours=7)
        return now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def test_health_reports_backlog_after_grace(self):
        result = run("tools/translation_health.py", "--all-corpus", "--grace-hours", "6", "--now", self.after_grace())
        want = " ".join(f"{loc}={len(self.expected[loc])}" for loc in LOCALES)
        backlog = any(self.expected[loc] for loc in LOCALES)
        self.assertEqual(result.stdout.splitlines()[0], f"{'BACKLOG' if backlog else 'HEALTHY'} {want}", result.stdout + result.stderr)
        self.assertEqual(result.returncode, 1 if backlog else 0)
        payload = json.loads(result.stdout.splitlines()[1])
        self.assertEqual(payload["signal"], "BACKLOG" if backlog else "GREEN")
        for locale in LOCALES:
            self.assertEqual(set(payload["locales"][locale]["backlog_ids"]), self.expected[locale])

    def test_translation_status_reports_real_backlog(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp) / "site"
            shutil.copytree(ROOT / "site" / "data", site / "data")
            result = run("tools/mark_pending_localizations.py", "--site", str(site), "--corpus", "corpus")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            status = json.loads((site / "data/i18n/translation-status.json").read_text(encoding="utf-8"))
            union = self.published_expected["es-419"] | self.published_expected["zh-Hans"]
            self.assertEqual(set(status["pending_translation_ids"]), union)
            self.assertEqual(status["pending_translation_count"], len(union))
            self.assertEqual(status["state"], "DEGRADED_TRANSLATION_BACKLOG" if union else "COMPLETE")
            for locale in LOCALES:
                self.assertEqual(status["locales"][locale]["pending"] + status["locales"][locale]["failed"],
                                 len(self.published_expected[locale]))
                for rid in self.published_expected[locale]:
                    page = (site / "news" / mp.ROUTE_SLUG[locale] / f"{rid}.html").read_text(encoding="utf-8")
                    self.assertIn('data-translation-status="pending"', page)
                    self.assertIn(f"/news/en/{rid}.html", page)

    def test_committed_translation_status_is_truthful(self):
        status = json.loads((ROOT / "site/data/i18n/translation-status.json").read_text(encoding="utf-8"))
        union = self.published_expected["es-419"] | self.published_expected["zh-Hans"]
        self.assertEqual(set(status["pending_translation_ids"]), union)
        self.assertEqual(status["pending_translation_count"], len(union))
        for locale in LOCALES:
            rows, strict, provenance, _ = vl.effective_overlays_details(locale, ROOT / "site/data/i18n", ROOT / "corpus")
            canonical = vl.load_corpus_canonical(ROOT / "corpus")
            # This receipt measures published stories; invalid source rows stay quarantined.
            published = {row["research_id"] for row in json.loads((ROOT / "site/data/stories.json").read_text())}
            canonical = {rid: row for rid, row in canonical.items() if rid in published}
            admission = ROOT / 'release-src/data/publication-admission.json'
            if admission.is_file():
                canonical = {rid: json.loads((ROOT / f'release-src/data/briefs/{rid}.json').read_text())['brief']
                             for rid in published}
            recount = vl.summarize(vl.locale_states(canonical, rows, strict, locale, provenance))["state_counts"]
            self.assertEqual(status["locales"][locale]["state_counts"], recount)

    def test_pd1_desk_values_and_airlock_baseline_are_preserved(self):
        for locale in LOCALES:
            airlock = ROOT / "site/data/i18n" / locale / "part-airlock.json"
            fixture_root = ROOT / "tests/fixtures/localization-baselines"
            original = (fixture_root / "c4ad8f2" / f"{locale}-part-airlock.json").read_bytes()
            baseline = json.loads(original)
            airlock_doc = json.loads(airlock.read_text(encoding="utf-8"))
            # Canonical identity metadata advances with the corpus; ARB-authored
            # airlock prose and values remain byte-for-byte equivalent as JSON.
            before = baseline["records"]
            after = airlock_doc["records"]
            self.assertTrue(all(after.get(rid) == row for rid, row in before.items()))
            delta = json.loads((ROOT / f"corpus/data/locales/{locale}/records.json").read_text())["records"]
            canonical = vl.load_corpus_canonical(ROOT / "corpus")
            published = {path.stem for path in (ROOT / "release-src/data/briefs").glob("FCMO-*.json")}
            published_canonical = set(canonical) & published
            # main may receive a new corpus delta before the scheduled newsroom
            # sync composes release-src and imports it into this presentation
            # pack. Verify the pack against its published source set; do not
            # require generated output to lead the corpus writer.
            source_additions = (set(delta) & published_canonical) - set(before)
            imported_additions = set(after) - set(before)
            self.assertLessEqual(imported_additions, source_additions)
            for rid in imported_additions:
                self.assertEqual(after[rid], delta[rid])
            ui = json.loads((ROOT / "site/data/i18n" / locale / "ui.json").read_text(encoding="utf-8"))
            self.assertEqual(ui["canonical_record_count"], len(published_canonical))
            self.assertEqual(airlock_doc["canonical_source_sha256"], ui["canonical_source_sha256"])
            pd1 = json.loads((fixture_root / "b9ebe9e" / f"{locale}-part-airlock.json").read_text(encoding="utf-8"))["records"]
            desk = json.loads(airlock.with_name("part-desk.json").read_text(encoding="utf-8"))
            self.assertEqual(len(desk["records"]), 17)
            for rid, changes in desk["records"].items():
                self.assertTrue(changes)
                self.assertEqual(desk["provenance"][rid], {
                    "origin": "publication-desk", "at": "2026-09-27T00:54:13Z", "model": "gpt-5.6-sol",
                    "human_reviewed": False, "network_translation": False,
                })
                self.assertEqual(changes, {key: value for key, value in pd1[rid].items()
                                           if before[rid].get(key) != value})

    def test_arb_import_leaves_desk_pack_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            i18n = root / "i18n"
            corpus = root / "corpus"
            for locale in LOCALES:
                target = i18n / locale
                target.mkdir(parents=True)
                for name in ("part-airlock.json", "part-desk.json"):
                    shutil.copyfile(ROOT / "site/data/i18n" / locale / name, target / name)
                desk_id = next(iter(json.loads((target / "part-desk.json").read_text(encoding="utf-8"))["records"]))
                delta = {"schema": "fcmo-airlocked-locale-delta-v1", "locale": locale,
                         "records": {desk_id: SPANISH_HEADLINE_ONLY}}
                write_json(corpus / "data/locales" / locale / "records.json", delta)
            before = {locale: (i18n / locale / "part-desk.json").read_bytes() for locale in LOCALES}
            result = run("tools/sync_airlocked_locales.py", "--corpus", str(corpus), "--i18n-dir", str(i18n))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for locale in LOCALES:
                self.assertEqual((i18n / locale / "part-desk.json").read_bytes(), before[locale])

    def test_legacy_integrity_receipt_counts_field_level_backlog(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Path(tmp) / "receipt.json"
            result = run("tools/validate_localizations_partial.py", "--site", "release-src",
                         "--i18n-dir", "site/data/i18n", "--receipt", str(receipt))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            doc = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(doc["schema"], "fcmo-locale-integrity-v3")
            self.assertEqual(doc["pending_translation_count"], len(doc["pending_translation_ids"]))
            self.assertEqual(set(doc["pending_by_locale"]["es-419"]) | set(doc["failed_by_locale"]["es-419"]),
                             self.published_expected["es-419"])

    def test_v2_overlays_follow_the_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("tools/validate_localizations.py", "--strict", "--corpus", "corpus",
                         "--write-overlays", tmp, "--now", NOW)
            self.assertIn(result.returncode, (0, 1), result.stderr)
            files = sorted(Path(tmp).glob("*.json"))
            self.assertEqual(len(files), 2, [f.name for f in files])
            check = run("tests/harness/validate.py", "contracts/locale-overlay.v2.schema.json", *map(str, files))
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            for path in files:
                doc = json.loads(path.read_text(encoding="utf-8"))
                states = {rid: entry["state"] for rid, entry in doc["records"].items()}
                locale = doc["locale"]
                self.assertEqual({rid for rid, s in states.items() if s in {"PENDING", "FAILED"}},
                                 self.expected[locale])


# --------------------------------------------------------------------------- synthetic pairs


class PairStates(unittest.TestCase):
    @staticmethod
    def arb_provenance(overlay):
        return {key: {"origin": "arb"} for key in overlay}

    def test_headline_only_overlay_is_pending(self):
        status = vl.pair_status(english_record(RID_PARTIAL), dict(SPANISH_HEADLINE_ONLY), "es-419",
                                provenance=self.arb_provenance(SPANISH_HEADLINE_ONLY))
        self.assertEqual(status["state"], "PENDING")
        self.assertIn("limitations", status["missing"])
        self.assertIn("claims", status["missing"])
        self.assertEqual(set(status["complete_keys"]), {"title", "summary", "why_it_matters"})

    def test_full_overlay_is_complete(self):
        status = vl.pair_status(english_record(RID_COMPLETE), dict(SPANISH_FULL), "es-419", strict=True,
                                provenance=self.arb_provenance(SPANISH_FULL))
        self.assertEqual(status["state"], "NATIVE_ARB", status)

    def test_complete_desk_fields_are_machine_reviewed_and_missing_origin_fails(self):
        provenance = self.arb_provenance(SPANISH_FULL)
        provenance["technical"] = {"origin": "publication-desk"}
        status = vl.pair_status(english_record(RID_COMPLETE), SPANISH_FULL, "es-419", strict=True,
                                provenance=provenance)
        self.assertEqual(status["state"], "MACHINE_REVIEWED", status)
        provenance["technical"] = {}
        status = vl.pair_status(english_record(RID_COMPLETE), SPANISH_FULL, "es-419", strict=True,
                                provenance=provenance)
        self.assertEqual(status["failure"]["gate"], "UNKNOWN_ORIGIN")

    def test_arb_fields_win_and_desk_overlap_is_retained_as_alternate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "es-419"
            folder.mkdir()
            write_json(folder / "part-airlock.json", {"records": {RID_COMPLETE: SPANISH_FULL}})
            other = {**SPANISH_FULL, "title": "Un título alternativo de la mesa"}
            write_json(folder / "part-desk.json", {"records": {RID_COMPLETE: other},
                       "provenance": {RID_COMPLETE: {"origin": "publication-desk", "at": NOW,
                                                    "model": "gpt-5.6-sol", "human_reviewed": False,
                                                    "network_translation": False}}})
            rows, strict, origins, alternates = vl.load_locale_details(root, "es-419")
            self.assertEqual(rows[RID_COMPLETE], SPANISH_FULL)
            self.assertEqual(origins[RID_COMPLETE]["title"]["origin"], "arb")
            self.assertEqual(alternates[RID_COMPLETE]["title"]["value"], other["title"])
            self.assertEqual(vl.pair_status(english_record(RID_COMPLETE), rows[RID_COMPLETE], "es-419",
                                            strict=RID_COMPLETE in strict,
                                            provenance=origins[RID_COMPLETE])["state"], "NATIVE_ARB")
            bad = json.loads((folder / "part-desk.json").read_text(encoding="utf-8"))
            del bad["provenance"][RID_COMPLETE]["human_reviewed"]
            write_json(folder / "part-desk.json", bad)
            with self.assertRaisesRegex(ValueError, "invalid desk provenance"):
                vl.load_locale_details(root, "es-419")

    def test_english_left_in_place_fails(self):
        source = english_record(RID_LEAK)
        overlay = dict(SPANISH_FULL, limitations=list(source["limitations"]))
        status = vl.pair_status(source, overlay, "es-419", provenance=self.arb_provenance(overlay))
        self.assertEqual(status["state"], "FAILED")
        self.assertEqual(status["failure"]["gate"], "ENGLISH_LEAK")
        zh = dict(CHINESE_HEADLINE_ONLY,
                  why_it_matters="The result would show that smaller teams can train competitive reasoning models with far less compute.")
        self.assertEqual(vl.pair_status(source, zh, "zh-Hans", provenance=self.arb_provenance(zh))["failure"]["gate"], "ENGLISH_LEAK")

    def test_changed_numbers_fail_the_strict_tier(self):
        overlay = dict(SPANISH_FULL, summary=SPANISH_FULL["summary"].replace("40%", "45%"))
        status = vl.pair_status(english_record(RID_COMPLETE), overlay, "es-419", strict=True,
                                provenance=self.arb_provenance(overlay))
        self.assertEqual(status["state"], "FAILED")
        self.assertEqual(status["failure"]["gate"], "TOKENS_CHANGED")

    def test_empty_english_fields_are_not_required(self):
        source = english_record(RID_COMPLETE)
        self.assertNotIn("contradictory_evidence", vl.required_keys(source))
        self.assertNotIn("relationships", vl.required_keys(source))


class PendingRendering(unittest.TestCase):
    """An incomplete pair renders a localized notice, never English prose as native."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        records = [english_record(RID_PARTIAL), english_record(RID_COMPLETE), english_record(RID_LEAK)]
        self.records = {r["id"]: r for r in records}
        leak = dict(SPANISH_FULL, summary=records[2]["summary"])
        self.corpus, self.site = build_fixture(root, records, {
            "es-419": {RID_PARTIAL: SPANISH_HEADLINE_ONLY, RID_COMPLETE: SPANISH_FULL, RID_LEAK: leak},
            "zh-Hans": {RID_PARTIAL: CHINESE_HEADLINE_ONLY},
        })
        for locale in LOCALES:  # what the newsroom builder would have written
            folder = self.site / "news" / mp.ROUTE_SLUG[locale]
            folder.mkdir(parents=True)
            (folder / f"{RID_COMPLETE}.html").write_text("builder page", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            code = mp.main(["--site", str(self.site), "--corpus", str(self.corpus),
                            "--config", str(ROOT / "config/site.json")])
        self.assertEqual(code, 0)

    def tearDown(self):
        self.tmp.cleanup()

    def page(self, locale: str, rid: str) -> str:
        return (self.site / "news" / mp.ROUTE_SLUG[locale] / f"{rid}.html").read_text(encoding="utf-8")

    def english_prose(self, rid: str) -> list[str]:
        record = self.records[rid]
        texts = [text for path, text in vl.prose_leaves(record)]
        return [t for t in texts if len(t.split()) >= 4]

    def assert_no_english_as_native(self, html_text: str, rid: str) -> None:
        parser = LangText()
        parser.feed(html_text)
        native = " ".join(" ".join(parser.native).split())
        english = " ".join(" ".join(parser.english).split())
        for text in self.english_prose(rid):
            self.assertNotIn(" ".join(text.split()), native, "English prose shown as native text")
        # The only English allowed is the labelled original headline.
        self.assertEqual(english, self.records[rid]["title"])
        self.assertFalse(vl.looks_english(native, "es-419") if 'lang="es-419"' in html_text else False)

    def test_partial_pair_gets_localized_pending_page(self):
        page = self.page("es-419", RID_PARTIAL)
        self.assertIn('lang="es-419"', page)
        self.assertIn('data-translation-status="pending"', page)
        self.assertIn("Traducción pendiente", page)
        self.assertIn(f"/news/en/{RID_PARTIAL}.html", page)
        self.assertIn(SPANISH_HEADLINE_ONLY["title"], page)
        self.assertIn('<meta name="robots" content="noindex">', page)
        self.assert_no_english_as_native(page, RID_PARTIAL)

    def test_chinese_partial_page(self):
        page = self.page("zh-Hans", RID_PARTIAL)
        self.assertIn("翻译待完成", page)
        self.assertIn(CHINESE_HEADLINE_ONLY["title"], page)
        self.assert_no_english_as_native(page, RID_PARTIAL)

    def test_missing_overlay_page_has_no_english_prose(self):
        page = self.page("zh-Hans", RID_COMPLETE)
        self.assertIn("翻译待完成", page)
        self.assert_no_english_as_native(page, RID_COMPLETE)

    def test_failed_pair_shows_no_overlay_text(self):
        page = self.page("es-419", RID_LEAK)
        self.assertIn('data-l10n-state="FAILED"', page)
        self.assertNotIn(SPANISH_FULL["title"], page)
        self.assert_no_english_as_native(page, RID_LEAK)

    def test_complete_pair_keeps_builder_page(self):
        self.assertEqual(self.page("es-419", RID_COMPLETE), "builder page")

    def test_dates_are_localized_and_not_shifted(self):
        page = self.page("es-419", RID_PARTIAL)
        self.assertIn("Ocurrió el 8 de septiembre de 2026", page)
        self.assertIn("Publicado el 20 de septiembre de 2026, 06:00", page)
        # 03:30 UTC on the 21st is still the 20th in Mexico City.
        self.assertIn("Actualizado el 20 de septiembre de 2026, 21:30", page)
        self.assertNotIn("2026-09-", page.split("</head>")[1])
        self.assertIn("2026年9月8日", self.page("zh-Hans", RID_PARTIAL))

    def test_status_counts_every_incomplete_pair(self):
        status = json.loads((self.site / "data/i18n/translation-status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["locales"]["es-419"]["complete"], 1)
        self.assertEqual(status["locales"]["es-419"]["pending_ids"], [RID_PARTIAL])
        self.assertEqual(status["locales"]["es-419"]["failed_ids"], {RID_LEAK: "ENGLISH_LEAK"})
        self.assertEqual(status["locales"]["zh-Hans"]["pending"], 3)
        self.assertEqual(status["pending_translation_ids"], sorted([RID_PARTIAL, RID_COMPLETE, RID_LEAK]))
        self.assertEqual(status["native_complete_story_count"], 0)

    def test_index_marks_pending_stories(self):
        index = (self.site / "news/es/index.html").read_text(encoding="utf-8")
        self.assertIn('data-translation-status="complete"', index)
        self.assertIn('data-translation-status="pending"', index)
        self.assertIn("Razonamiento y posentrenamiento", index)
        self.assertNotIn("reasoning_posttraining", index)


class GraceWindow(unittest.TestCase):
    def test_new_story_is_in_grace_then_backlog(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus, site = build_fixture(Path(tmp), [english_record(RID_PARTIAL, "2026-09-26T18:00:00Z")], {})
            i18n = site / "data" / "i18n"
            args = ["tools/translation_health.py", "--all-corpus", "--corpus", str(corpus),
                    "--i18n-dir", str(i18n), "--grace-hours", "6"]
            early = run(*args, "--now", "2026-09-26T20:00:00Z")
            self.assertEqual(early.stdout.splitlines()[0], "GRACE es-419=1 zh-Hans=1", early.stderr)
            self.assertEqual(early.returncode, 0)
            late = run(*args, "--now", "2026-09-27T01:00:00Z")
            self.assertEqual(late.stdout.splitlines()[0], "BACKLOG es-419=1 zh-Hans=1", late.stderr)
            self.assertEqual(late.returncode, 1)


# --------------------------------------------------------------------------- UI catalogs


class UICatalogs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = {loc: json.loads((ROOT / f"i18n/ui/{loc}.json").read_text(encoding="utf-8"))
                   for loc in CATALOG_LOCALES}
        cls.config = json.loads((ROOT / "config/site.json").read_text(encoding="utf-8"))

    def reader_leaves(self, locale):
        for path, value in leaves(self.cat[locale]):
            if path.split(".")[1] in {"schema", "locale", "html_lang", "timezone", "plural_rule", "about"}:
                continue
            yield path, value

    def test_same_keys_and_placeholders(self):
        def shape(locale):
            out: dict[str, set[str]] = {}
            for path, value in self.reader_leaves(locale):
                if path.startswith(".date."):  # date patterns are per language by design
                    continue
                if path.startswith(".plurals."):  # plural categories differ by language
                    path = path.rsplit(".", 1)[0]
                out.setdefault(path, set()).update(PLACEHOLDER.findall(str(value)))
            return out
        base = shape("en")
        for locale in ("es-419", "zh-Hans"):
            self.assertEqual(shape(locale), base, locale)

    def test_catalogs_match_site_config(self):
        for entry in self.config["locales"]:
            catalog = self.cat[entry["code"]]
            self.assertEqual(catalog["schema"], "fcmo-ui-catalog-v1")
            self.assertEqual(catalog["html_lang"], entry["html_lang"])
            self.assertEqual(catalog["timezone"], self.config["timezone"])

    def test_no_raw_enum_in_reader_copy(self):
        for locale in CATALOG_LOCALES:
            for path, value in self.reader_leaves(locale):
                if isinstance(value, str):
                    self.assertIsNone(RAW_ENUM.search(value), f"{locale}{path}: {value}")

    def test_every_reader_facing_enum_has_a_label(self):
        observed: dict[str, set[str]] = {group: set() for group in (
            "desk", "development_type", "confidence", "evidence_class", "importance_tier", "record_status",
            "claim_label", "gap_kind", "gap_state", "region", "source_language", "story_type",
            "media_mode", "rights_state")}
        for line in (ROOT / "corpus/data/developments.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            observed["desk"].update(r.get("desks") or [])
            observed["desk"].add(r.get("primary_desk"))
            observed["development_type"].add(r.get("development_type"))
            observed["confidence"].add(r.get("confidence"))
            observed["evidence_class"].add(r.get("evidence_class"))
            observed["importance_tier"].add(r.get("importance_tier"))
            observed["record_status"].add(r.get("status"))
            observed["region"].update(r.get("regions") or [])
            observed["source_language"].update(r.get("source_languages") or [])
            for claim in r.get("claims") or []:
                observed["claim_label"].add(claim.get("label"))
            for gap in r.get("evidence_gaps") or []:
                observed["gap_kind"].add(gap.get("kind"))
                observed["gap_state"].add(gap.get("state"))
        for story in json.loads((ROOT / "site/data/stories.json").read_text(encoding="utf-8")):
            observed["story_type"].add(story.get("story_type"))
            observed["confidence"].add((story.get("news_value") or {}).get("confidence"))
            observed["evidence_class"].add((story.get("news_value") or {}).get("evidence"))
            media = story.get("media") or {}
            observed["media_mode"].add(media.get("mode"))
            observed["rights_state"].add(media.get("rights_state"))
        for name in ("record.v3", "stories.v2", "newsroom-status.v2"):
            schema = json.loads((ROOT / f"contracts/{name}.schema.json").read_text(encoding="utf-8"))
            enums = set()

            def walk(node):
                if isinstance(node, dict):
                    if isinstance(node.get("enum"), list):
                        enums.update(v for v in node["enum"] if isinstance(v, str))
                    for item in node.values():
                        walk(item)
                elif isinstance(node, list):
                    for item in node:
                        walk(item)
            walk(schema)
            observed.setdefault(f"contract:{name}", set()).update(enums)
        # Every value present in the current corpus must have a label. This follows
        # the live data instead of silently relaxing when the corpus fingerprint
        # changes; label() omits an unknown value rather than printing it raw.
        for locale in CATALOG_LOCALES:
            labels = self.cat[locale]["labels"]
            everything = set().union(*(set(group) for group in labels.values()))
            for group, codes in observed.items():
                for code in sorted(c for c in codes if c):
                    if group.startswith("contract:"):
                        self.assertIn(code, everything, f"{locale}: {group} enum {code} has no label")
                    else:
                        self.assertIn(code, labels[group], f"{locale}: labels.{group}.{code} missing")

    def test_no_sept_and_explicit_month_tables(self):
        for locale in CATALOG_LOCALES:
            date = self.cat[locale]["date"]
            self.assertEqual(len(date["months"]), 12)
            self.assertEqual(len(date["months_short"]), 12)
            self.assertNotIn("Sept", date["months_short"])
            for month in range(1, 13):
                for style in ("date_long", "date_medium", "date_short", "month_year", "weekday_date", "datetime"):
                    text = mp.format_date(f"2026-{month:02d}-15T18:30:00Z", locale, "minute", style)
                    self.assertIsNone(re.search(r"\bSept\b", text), text)
                    self.assertNotIn("{", text)

    def test_date_formatter(self):
        self.assertEqual(mp.format_date("2026-09-08T00:00:00Z", "en"), "September 8, 2026")
        self.assertEqual(mp.format_date("2026-09-08T00:00:00Z", "es-419"), "8 de septiembre de 2026")
        self.assertEqual(mp.format_date("2026-09-08T00:00:00Z", "zh-Hans"), "2026年9月8日")
        self.assertEqual(mp.format_date("2026-09-08T00:00:00Z", "en", style="date_medium"), "Sep 8, 2026")
        # A calendar date is never shifted into the previous day.
        self.assertEqual(mp.format_date("2026-09-08", "es-419", "day"), "8 de septiembre de 2026")
        self.assertEqual(mp.format_date("2026-09-08T00:00:00Z", "es-419", "day", "datetime"), "8 de septiembre de 2026")
        # An instant is shown in Mexico City time (UTC-6).
        self.assertEqual(mp.format_date("2026-09-08T03:00:00Z", "es-419", "minute", "datetime"),
                         "7 de septiembre de 2026, 21:00 (hora de la Ciudad de México)")
        self.assertEqual(mp.format_date("2026-09-08T03:00:00Z", "en", "minute", "datetime"),
                         "September 7, 2026, 9:00 p.m. (Mexico City time)")
        self.assertEqual(mp.format_date("2026-09", "zh-Hans"), "2026年9月")
        self.assertEqual(mp.format_date("not a date", "en"), "")

    def test_plurals_and_labels(self):
        self.assertEqual(mp.plural("en", "story", 1), "1 story")
        self.assertEqual(mp.plural("es-419", "story", 2), "2 historias")
        self.assertEqual(mp.plural("zh-Hans", "story", 1), "1 篇报道")
        self.assertEqual(mp.label("es-419", "desk", "reasoning_posttraining"), "Razonamiento y posentrenamiento")
        self.assertIsNone(mp.label("es-419", "desk", "unknown_desk_code"))

    def test_not_found_is_translated(self):
        english = self.cat["en"]["strings"]["errors"]["not_found_title"]
        for locale in ("es-419", "zh-Hans"):
            errors = self.cat[locale]["strings"]["errors"]
            for key in ("not_found_title", "not_found_body", "not_found_home"):
                self.assertNotEqual(errors[key], self.cat["en"]["strings"]["errors"][key])
                self.assertNotIn("Not Found", errors[key])
            self.assertNotEqual(errors["not_found_title"], english)

    def test_spanish_catalog_is_spanish(self):
        allowed_same = {"Hubei", "Australia", "Argentina", "Agenda", "Atom", "Blog", "China", "FCMO AI", "Global", "India", "JSON Feed",
                        "Notable", "RSS", "{date}, {time} ({tz})", "© {year} FCMO AI", "English", "Español", "简体中文"}
        english = dict(self.reader_leaves("en"))
        for path, value in self.reader_leaves("es-419"):
            if not isinstance(value, str):
                continue
            self.assertFalse(vl.looks_english(value, "es-419"), f"{path}: {value}")
            if value == english.get(path):
                self.assertIn(value, allowed_same, f"es-419{path} is still English: {value}")

    def test_chinese_catalog_is_chinese(self):
        brand = re.compile(r"FCMO|AI|RSS|Atom|JSON|Feed|English|Español|\{[a-z0-9_]+\}|[^A-Za-z]")
        for path, value in self.reader_leaves("zh-Hans"):
            if isinstance(value, str) and len(brand.sub("", value)) >= 3:
                self.assertRegex(value, HAN, f"zh-Hans{path}: {value}")


class Glossary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = (ROOT / "i18n/glossary.yml").read_text(encoding="utf-8")
        cls.doc = json.loads(text)
        try:
            import yaml
        except ImportError:  # PyYAML is optional; JSON is valid YAML
            yaml = None
        if yaml is not None:
            assert yaml.safe_load(text) == cls.doc

    @staticmethod
    def find(form: str, text: str) -> bool:
        if HAN.search(form):
            return form in text
        pattern = r"(?<![\w-])" + re.escape(form) + r"(?![\w-])"
        return re.search(pattern, text, re.IGNORECASE) is not None

    def test_glossary_is_self_consistent(self):
        self.assertEqual(self.doc["schema"], "fcmo-glossary-v1")
        self.assertEqual(self.doc["scopes"]["ui"]["severity"], "error")
        terms = self.doc["terms"]
        self.assertEqual(len({t["id"] for t in terms}), len(terms))
        self.assertEqual(len({t["en"].lower() for t in terms}), len(terms))
        for locale in LOCALES:
            preferred = {t[locale].lower() for t in terms}
            for term in terms:
                self.assertTrue(term[locale].strip(), term["id"])
                for bad in term["avoid"].get(locale, []):
                    self.assertNotIn(bad.lower(), preferred, f"{term['id']}: {bad} is also a preferred form")
        by_id = {t["id"]: t for t in terms}
        self.assertEqual(by_id["baseline"]["es-419"], "línea base")
        self.assertEqual(by_id["post_training"]["es-419"], "posentrenamiento")

    def test_ui_catalogs_have_no_glossary_conflicts(self):
        conflicts = []
        for locale in LOCALES:
            catalog = json.loads((ROOT / f"i18n/ui/{locale}.json").read_text(encoding="utf-8"))
            texts = [v for p, v in leaves(catalog) if isinstance(v, str) and not p.startswith(".about")]
            for term in self.doc["terms"]:
                for bad in term["avoid"].get(locale, []):
                    conflicts += [(locale, term["id"], bad, t) for t in texts if self.find(bad, t)]
        self.assertEqual(conflicts, [])


if __name__ == "__main__":
    unittest.main()
