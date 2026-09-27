"""Wire liveness: bridge writer, corpus guard wrapper, status path, edition banner,
live identity polling and the health state (WP-A1).

The corpus guard is exercised only through its CLI contract (contracts/README.md,
"corpus_guard CLI"): a stub built on the harness oracles stands in for
tools/corpus_guard.py via FCMO_CORPUS_GUARD.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for entry in (ROOT, ROOT / "tests"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from harness.clock import FakeClock  # noqa: E402
from harness.validate import validator_for  # noqa: E402
from tools import edition_banner, verify_live_newsroom, wire_status  # noqa: E402

FIXTURES = ROOT / "contracts" / "fixtures"
SCHEMAS = ROOT / "contracts"
REFERENCE = "2026-09-26T20:00:00Z"

GUARD_STUB = r'''
import argparse, json, shutil, sys
from pathlib import Path
sys.path.insert(0, {tests!r})
from harness import oracles
p = argparse.ArgumentParser()
p.add_argument("mode", choices=("check", "apply"))
p.add_argument("--published", required=True)
p.add_argument("--candidate", required=True)
p.add_argument("--tombstones")
p.add_argument("--max-missing-ratio", type=float, default=0.2)
p.add_argument("--report")
p.add_argument("--now", default="2026-09-26T20:00:00Z")
p.add_argument("--out")
a = p.parse_args()
pub, cand = Path(a.published), Path(a.candidate)
tomb_path = Path(a.tombstones) if a.tombstones else pub / "tombstones.json"
tomb = json.loads(tomb_path.read_text()) if tomb_path.is_file() else None
result = oracles.guard_corpora(pub, cand, tomb, a.max_missing_ratio)
print(oracles.guard_line(result))
if a.report:
    Path(a.report).write_text(json.dumps(oracles.guard_report(result, a.now, a.max_missing_ratio)))
if result["exit_code"] == 3:
    sys.exit(3)
if a.mode == "apply":
    out = Path(a.out)
    shutil.copytree(cand, out)
    rows = {{r["id"]: r for r in oracles.read_records(pub)}}
    lines = [json.dumps({{"id": i, "carried_since": a.now, "record": rows[i]}}) for i in result["carried"] if i in rows]
    if lines:
        (out / "carried.jsonl").write_text("\n".join(lines) + "\n")
'''


def run(*argv: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    full_env = {k: v for k, v in os.environ.items() if k != "FCMO_NOW"}
    full_env.update(env or {})
    return subprocess.run([sys.executable, *argv], cwd=ROOT, env=full_env, capture_output=True, text=True, timeout=300)


def outputs(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition("=")
        values[key] = value
    return values


def errors(schema: str, doc) -> list[str]:
    return validator_for(SCHEMAS / schema).errors(doc)


class Workspace(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def corpus(self, name: str, as_name: str) -> Path:
        target = self.tmp / as_name
        shutil.copytree(FIXTURES / name, target)
        return target


class CorpusGuardWrapperTests(Workspace):
    def setUp(self) -> None:
        super().setUp()
        self.stub = self.tmp / "corpus_guard_stub.py"
        self.stub.write_text(GUARD_STUB.format(tests=str(ROOT / "tests")), encoding="utf-8")
        self.env = {"FCMO_CORPUS_GUARD": str(self.stub)}

    def guard(self, published: Path, candidate: Path, drill: str = "") -> tuple[subprocess.CompletedProcess, dict[str, str], Path, Path]:
        out, report, gh = self.tmp / "guarded", self.tmp / "guard-report.json", self.tmp / "guard.env"
        gh.write_text("", encoding="utf-8")
        proc = run("tools/wire_status.py", "guard", "--published", str(published), "--candidate", str(candidate),
                   "--out", str(out), "--report", str(report), "--drill", drill, "--now", REFERENCE,
                   "--github-output", str(gh), env=self.env)
        return proc, outputs(gh), out, report

    def write(self, previous: Path | None, report: Path, corpus: Path, now: str = REFERENCE, **extra: str) -> tuple[subprocess.CompletedProcess, dict]:
        target = self.tmp / "wire-status.json"
        argv = ["tools/wire_status.py", "write", "--out", str(target), "--now", now, "--transport", "OK",
                "--source-mode", "MAIN", "--airlock", str(corpus / "airlock.json"),
                "--records", str(corpus / "data" / "developments.jsonl"), "--guard-report", str(report)]
        if previous:
            argv += ["--previous", str(previous)]
        for key, value in extra.items():
            argv += [f"--{key.replace('_', '-')}", value]
        proc = run(*argv)
        return proc, json.loads(target.read_text(encoding="utf-8")) if target.is_file() else {}

    def test_missing_story_is_carried_forward_and_staged(self) -> None:
        published, candidate = self.corpus("corpus-44", "published"), self.corpus("corpus-43", "candidate")
        proc, out, guarded, report = self.guard(published, candidate)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        first = proc.stdout.splitlines()[0]
        self.assertTrue(first.startswith("CARRY_FORWARD missing=FCMO-FDBE3D996243 "), first)
        self.assertEqual((out["stage"], out["verdict"], out["changed"]), ("true", "CARRY_FORWARD", "true"))
        self.assertTrue((guarded / "carried.jsonl").is_file())
        self.assertEqual(errors("corpus-guard.report.schema.json", json.loads(report.read_text())), [])
        _, wire = self.write(None, report, candidate, release_changed="true")
        self.assertEqual(wire["guard"]["verdict"], "CARRY_FORWARD")
        self.assertIn("CORPUS_CARRY_FORWARD", wire["warnings"])
        self.assertEqual(errors("wire-status.schema.json", wire), [])

    def test_regressing_snapshot_is_refused_and_never_staged(self) -> None:
        published, candidate = self.corpus("corpus-44", "published"), self.corpus("corpus-27", "candidate")
        proc, out, guarded, report = self.guard(published, candidate)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("REGRESSION_REFUSED "), proc.stdout)
        self.assertEqual((out["stage"], out["verdict"]), ("false", "REGRESSION_REFUSED"))
        self.assertFalse(guarded.exists())
        _, wire = self.write(None, report, published)
        self.assertEqual(wire["state"], "DELAYED:SNAPSHOT_REFUSED")
        self.assertIn("SNAPSHOT_REFUSED", wire["warnings"])
        self.assertEqual(errors("wire-status.schema.json", wire), [])

    def test_unchanged_release_is_only_checked(self) -> None:
        published, candidate = self.corpus("corpus-43", "published"), self.corpus("corpus-43", "candidate")
        proc, out, guarded, _ = self.guard(published, candidate)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("OK missing=- "), proc.stdout)
        self.assertEqual((out["stage"], out["changed"]), ("false", "false"))
        self.assertFalse(guarded.exists())

    def test_regressing_snapshot_drill_is_refused(self) -> None:
        published, candidate = self.corpus("corpus-43", "published"), self.corpus("corpus-43", "candidate")
        proc, out, _, _ = self.guard(published, candidate, drill="regressing_snapshot")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("REGRESSION_REFUSED "), proc.stdout)
        self.assertIn("drill=regressing_snapshot", proc.stdout)
        self.assertEqual(out["stage"], "false")
        # The candidate itself is untouched by the drill.
        self.assertEqual((candidate / "data" / "developments.jsonl").read_bytes(),
                         (FIXTURES / "corpus-43" / "data" / "developments.jsonl").read_bytes())

    def test_a_guard_that_breaks_its_contract_fails_closed(self) -> None:
        self.stub.write_text("print('something unexpected')\n", encoding="utf-8")
        published, candidate = self.corpus("corpus-44", "published"), self.corpus("corpus-43", "candidate")
        proc, out, _, _ = self.guard(published, candidate)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(out["stage"], "false")


class WireWriterTests(Workspace):
    def write(
        self,
        name: str,
        now: str,
        previous: Path | None = None,
        *extra: str,
        corpus: Path | None = None,
    ) -> tuple[subprocess.CompletedProcess, dict, dict[str, str]]:
        target, gh = self.tmp / f"{name}.json", self.tmp / f"{name}.env"
        gh.write_text("", encoding="utf-8")
        corpus = corpus or FIXTURES / "corpus-43"
        argv = ["tools/wire_status.py", "write", "--out", str(target), "--now", now, "--trigger", "schedule",
                "--airlock", str(corpus / "airlock.json"), "--records", str(corpus / "data" / "developments.jsonl"),
                "--github-output", str(gh)]
        if previous:
            argv += ["--previous", str(previous)]
        argv += list(extra) or ["--transport", "OK", "--source-mode", "MAIN"]
        proc = run(*argv)
        doc = json.loads(target.read_text(encoding="utf-8")) if target.is_file() else {}
        return proc, doc, outputs(gh)

    def test_heartbeat_commit_rule(self) -> None:
        clock = FakeClock()
        proc, first, out = self.write("t0", clock.iso())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(errors("wire-status.schema.json", first), [])
        self.assertEqual((first["state"], out["commit"], out["commit_reason"]), ("QUIET", "true", "FIRST_WRITE"))
        self.assertEqual(first["publication_authority"], "UNKNOWN")
        self.assertNotIn("last_authoritative_publication_at", first)
        self.assertEqual(first["last_release_change_at"], "2026-09-23T11:32:15Z")
        self.assertEqual(first["newest_event_at"], wire_status.newest_event_at(FIXTURES / "corpus-43" / "data" / "developments.jsonl"))
        t0 = self.tmp / "t0.json"
        _, second, out = self.write("t1", clock.ahead(hours=1), t0)
        self.assertEqual((out["commit"], out["commit_reason"]), ("false", "UNCHANGED"))
        self.assertEqual(second["state_since"], first["state_since"])
        _, _, out = self.write("t5", clock.ahead(hours=5), t0)
        self.assertEqual((out["commit"], out["commit_reason"]), ("true", "HEARTBEAT_DUE"))

    def test_checkpoint_with_red_main_changes_state(self) -> None:
        clock = FakeClock()
        self.write("t0", clock.iso())
        _, doc, out = self.write("cp", clock.ahead(hours=1), self.tmp / "t0.json",
                                 "--transport", "OK", "--source-mode", "CHECKPOINT", "--drill", "force_checkpoint",
                                 "--arb-failure", "DRILL_FORCE_CHECKPOINT", "--checkpoint-at", "2026-09-18T19:43:04+00:00")
        self.assertEqual(errors("wire-status.schema.json", doc), [])
        self.assertEqual((doc["state"], doc["arb_main"], doc["drill"]), ("DELAYED:ARB_MAIN_RED", "RED", "force_checkpoint"))
        self.assertEqual(doc["checkpoint_at"], "2026-09-18T19:43:04Z")
        self.assertEqual((out["commit"], out["commit_reason"]), ("true", "STATE_CHANGED"))

    def test_failing_transport_is_recorded_by_code_and_delays_after_grace(self) -> None:
        clock = FakeClock()
        self.write("t0", clock.iso())
        _, soon, out = self.write("f1", clock.ahead(hours=1), self.tmp / "t0.json",
                                  "--transport", "FAIL", "--transport-error", "TOKEN_MINT_FAILED")
        self.assertEqual(errors("wire-status.schema.json", soon), [])
        self.assertEqual((soon["state"], soon["transport_error"]), ("QUIET", "TOKEN_MINT_FAILED"))
        self.assertIn("TRANSPORT_FAIL", soon["warnings"])
        self.assertEqual((out["commit"], out["commit_reason"]), ("true", "RUN_KIND_CHANGED"))
        _, later, out = self.write("f7", clock.ahead(hours=7), self.tmp / "f1.json",
                                   "--transport", "FAIL", "--transport-error", "SEAL_FAIL:PRIVACY")
        self.assertEqual(later["state"], "DELAYED:TRANSPORT_FAIL")
        self.assertEqual(later["last_transport_ok_at"], clock.iso())
        self.assertEqual(out["commit_reason"], "STATE_CHANGED")
        # Anything that is not a public code is replaced, never echoed.
        _, odd, _ = self.write("odd", clock.ahead(hours=2), self.tmp / "t0.json",
                               "--transport", "FAIL", "--transport-error", "fatal: private path /x")
        self.assertEqual(odd["transport_error"], "TRANSPORT_FAIL")

    def test_private_text_is_refused_as_an_arb_failure(self) -> None:
        proc, _, _ = self.write("bad", REFERENCE, None, "--transport", "OK", "--source-mode", "MAIN",
                                "--arb-failure", "Traceback: secret detail")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("wire status FAILED", proc.stderr)

    def test_new_stories_make_the_wire_fresh(self) -> None:
        clock = FakeClock()
        self.write("t0", clock.iso())
        report = self.tmp / "report.json"
        report.write_text(json.dumps({"verdict": "OK", "missing": [], "withdrawn": [], "added": ["FCMO-000000000001"], "ratio": 0.0}))
        _, doc, out = self.write("new", clock.ahead(hours=1), self.tmp / "t0.json", "--transport", "OK",
                                 "--source-mode", "MAIN", "--release-changed", "true", "--guard-report", str(report))
        self.assertEqual((doc["state"], doc["last_new_story_at"]), ("FRESH", clock.ahead(hours=1)))
        self.assertEqual(out["commit_reason"], "STATE_CHANGED")

    def _receipt_corpus(
        self,
        *,
        day: str = "2026-09-26",
        published_at: str = "2026-09-26T13:15:00Z",
        status: str = "PUBLISHED",
        edition: str = "edition-2026-09-26-a1b2c3d4e5f6",
    ) -> Path:
        corpus = self.corpus("corpus-43", f"receipt-{len(list(self.tmp.glob('receipt-*')))}")
        path = corpus / "archive" / day.replace("-", "/") / "PUBLICATION.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "schema": "fcmo-publication-receipt-v1",
            "publication_date": day,
            "published_at": published_at,
            "edition_id": edition,
            "story_ids": ["FCMO-A1B2C3D4E5F6"] if status == "PUBLISHED" else [],
            "status": status,
        }), encoding="utf-8")
        return corpus

    def test_authoritative_published_receipt_drives_freshness_not_story_timestamp(self) -> None:
        clock = FakeClock("2026-09-26T14:00:00Z")
        corpus = self._receipt_corpus()
        proc, doc, _ = self.write("receipt-fresh", clock.iso(), corpus=corpus)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(errors("wire-status.schema.json", doc), [])
        self.assertEqual(doc["state"], "FRESH")
        self.assertEqual(doc["publication_authority"], "AUTHORITATIVE")
        self.assertEqual(doc["last_authoritative_publication_date"], "2026-09-26")
        self.assertEqual(doc["last_authoritative_publication_at"], "2026-09-26T13:15:00Z")
        self.assertEqual(doc["last_authoritative_edition_id"], "edition-2026-09-26-a1b2c3d4e5f6")
        self.assertEqual(doc["last_authoritative_publication_status"], "PUBLISHED")
        self.assertLess(wire_status.parse_utc(doc["last_new_story_at"]), wire_status.parse_utc("2026-09-26T00:00:00Z"))

    def test_authoritative_quiet_receipt_drives_quiet_even_when_release_changed(self) -> None:
        corpus = self._receipt_corpus(status="QUIET", edition="edition-2026-09-26-quiet")
        _, doc, _ = self.write(
            "receipt-quiet", "2026-09-26T14:00:00Z", None,
            "--transport", "OK", "--source-mode", "MAIN", "--release-changed", "true",
            corpus=corpus,
        )
        self.assertEqual((doc["state"], doc["last_authoritative_publication_status"]), ("QUIET", "QUIET"))

    def test_newest_valid_receipt_is_projected(self) -> None:
        corpus = self._receipt_corpus()
        newer = corpus / "archive/2026/09/27/PUBLICATION.json"
        newer.parent.mkdir(parents=True)
        newer.write_text(json.dumps({
            "schema": "fcmo-publication-receipt-v1", "publication_date": "2026-09-27",
            "published_at": "2026-09-27T13:00:00-06:00", "edition_id": "edition-2026-09-27-newest",
            "story_ids": [], "status": "QUIET",
        }), encoding="utf-8")
        _, doc, _ = self.write("receipt-newest", "2026-09-27T20:00:00Z", corpus=corpus)
        self.assertEqual(doc["last_authoritative_publication_date"], "2026-09-27")
        self.assertEqual(doc["last_authoritative_publication_at"], "2026-09-27T19:00:00Z")
        self.assertEqual(doc["last_authoritative_edition_id"], "edition-2026-09-27-newest")
        self.assertEqual(doc["state"], "QUIET")

    def test_no_receipt_never_infers_authority_from_generated_at_or_publication_artifacts(self) -> None:
        corpus = self.corpus("corpus-43", "inference-traps")
        airlock = json.loads((corpus / "airlock.json").read_text(encoding="utf-8"))
        airlock["generated_at"] = "2026-09-26T19:59:59Z"
        (corpus / "airlock.json").write_text(json.dumps(airlock), encoding="utf-8")
        (corpus / "DAILY_BRIEF.md").write_text("Published today", encoding="utf-8")
        edition = corpus / "editions/2026-09-26.html"
        edition.parent.mkdir(exist_ok=True)
        edition.write_text("published", encoding="utf-8")
        _, doc, _ = self.write("no-inference", REFERENCE, corpus=corpus)
        # Legacy classification remains compatible (and therefore may be FRESH),
        # but no publication authority or authoritative field is manufactured.
        self.assertEqual((doc["publication_authority"], doc["state"]), ("UNKNOWN", "FRESH"))
        self.assertFalse(any(key.startswith("last_authoritative_") for key in doc))

    def test_transport_failure_carries_only_previously_authoritative_publication(self) -> None:
        corpus = self._receipt_corpus()
        self.write("authority-ok", "2026-09-26T14:00:00Z", corpus=corpus)
        _, failed, _ = self.write(
            "authority-fail", "2026-09-26T15:00:00Z", self.tmp / "authority-ok.json",
            "--transport", "FAIL", "--transport-error", "TOKEN_MINT_FAILED",
            corpus=FIXTURES / "corpus-43",
        )
        self.assertEqual(failed["publication_authority"], "AUTHORITATIVE")
        self.assertEqual(failed["last_authoritative_edition_id"], "edition-2026-09-26-a1b2c3d4e5f6")

    def test_authority_change_commits_even_when_state_does_not_change(self) -> None:
        corpus = self._receipt_corpus()
        previous = json.loads((FIXTURES / "wire-status.fresh.json").read_text(encoding="utf-8"))
        airlock = json.loads((corpus / "airlock.json").read_text(encoding="utf-8"))
        previous.update({
            "release_id": airlock["release_id"],
            "corpus_digest": airlock["corpus_digest"],
            "record_count": airlock["record_count"],
            "release_changed": False,
            "guard": {"verdict": "NOT_RUN", "missing": [], "withdrawn": [], "added": 0, "ratio": 0.0},
        })
        previous_path = self.tmp / "legacy-fresh.json"
        previous_path.write_text(json.dumps(previous), encoding="utf-8")
        _, doc, out = self.write("authority-change", "2026-09-26T19:20:00Z", previous_path, corpus=corpus)
        self.assertEqual((doc["state"], out["commit"], out["commit_reason"]),
                         ("FRESH", "true", "PUBLICATION_CHANGED"))


class StagingTests(Workspace):
    def test_sealed_view_drops_only_newsroom_files(self) -> None:
        corpus = self.corpus("corpus-43", "corpus")
        for name in wire_status.NEWSROOM_FILES:
            (corpus / name).write_text("{}", encoding="utf-8")
        proc = run("tools/wire_status.py", "sealed-view", "--corpus", str(corpus), "--out", str(self.tmp / "view"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        view = sorted(p.relative_to(self.tmp / "view").as_posix() for p in (self.tmp / "view").rglob("*") if p.is_file())
        self.assertEqual(view, ["airlock.json", "data/developments.jsonl"])

    def test_stage_keeps_newsroom_files_and_takes_carried_from_the_guard(self) -> None:
        corpus = self.corpus("corpus-44", "corpus")
        release = self.corpus("corpus-43", "release")
        guarded = self.tmp / "guarded"
        guarded.mkdir()
        (guarded / "carried.jsonl").write_text('{"id": "FCMO-FDBE3D996243"}\n', encoding="utf-8")
        (corpus / "wire-status.json").write_text('{"keep": 1}', encoding="utf-8")
        (corpus / "tombstones.json").write_text('{"keep": 2}', encoding="utf-8")
        (corpus / "carried.jsonl").write_text("stale\n", encoding="utf-8")

        def fake_stage(argv, check):  # the strict stager swaps the whole directory
            self.assertEqual(argv[2:], ["stage", str(release), str(corpus)])
            shutil.rmtree(corpus)
            shutil.copytree(release, corpus)
            return subprocess.CompletedProcess(argv, 0)

        with mock.patch.object(wire_status.subprocess, "run", side_effect=fake_stage):
            wire_status.stage_corpus(release, corpus, guarded)
        self.assertEqual((corpus / "wire-status.json").read_text(), '{"keep": 1}')
        self.assertEqual((corpus / "tombstones.json").read_text(), '{"keep": 2}')
        self.assertEqual((corpus / "carried.jsonl").read_text(), '{"id": "FCMO-FDBE3D996243"}\n')
        self.assertEqual((corpus / "airlock.json").read_bytes(), (release / "airlock.json").read_bytes())
        (guarded / "carried.jsonl").unlink()
        with mock.patch.object(wire_status.subprocess, "run", side_effect=fake_stage):
            wire_status.stage_corpus(release, corpus, guarded)
        self.assertFalse((corpus / "carried.jsonl").exists())


class StatusPathTests(Workspace):
    def test_status_is_rewritten_only_when_material_or_due(self) -> None:
        corpus = self.tmp / "corpus"
        (corpus / "developments").mkdir(parents=True)
        (corpus / "index.html").write_text("ok", encoding="utf-8")
        shutil.copy(FIXTURES / "corpus-43" / "airlock.json", corpus / "airlock.json")
        status = self.tmp / "newsroom-status.json"
        status.write_text(json.dumps({"state": "NO_PUBLIC_DELTA_READY", "story_layer_count": 43,
                                      "translation_counts": {"es-419": 25, "zh-Hans": 25}}), encoding="utf-8")
        wire = self.tmp / "wire.json"
        doc = json.loads((FIXTURES / "wire-status.quiet.json").read_text(encoding="utf-8"))
        wire.write_text(json.dumps(doc), encoding="utf-8")

        def status_at(now: str) -> str:
            proc = run("tools/newsroom_receipt.py", "status", "--now", now, "--corpus", str(corpus),
                       "--wire-status", str(wire), "--status", str(status))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return proc.stdout.strip()

        self.assertEqual(status_at(REFERENCE), "STATUS QUIET wire=QUIET written=true reason=CHANGED")
        written = json.loads(status.read_text(encoding="utf-8"))
        self.assertEqual(errors("newsroom-status.v2.schema.json", written), [])
        self.assertEqual(written["translation"]["es-419"], {"complete": 25, "failed": 0, "pending": 18})
        self.assertEqual(status_at("2026-09-26T22:00:00Z"), "STATUS QUIET wire=QUIET written=false reason=UNCHANGED")
        self.assertEqual(status_at("2026-09-27T01:00:00Z"), "STATUS QUIET wire=QUIET written=true reason=HEARTBEAT_DUE")
        doc.update(json.loads((FIXTURES / "wire-status.delayed.json").read_text(encoding="utf-8")))
        wire.write_text(json.dumps(doc), encoding="utf-8")
        self.assertEqual(status_at("2026-09-27T01:30:00Z"), "STATUS DELAYED wire=DELAYED:ARB_MAIN_RED written=true reason=CHANGED")
        self.assertEqual(json.loads(status.read_text())["alerts"], ["ARB_MAIN_RED"])


class EditionBannerTests(Workspace):
    def site(self) -> Path:
        site = self.tmp / "site"
        pages = {
            "index.html": "en",
            "news/index.html": "en",
            "news/en/FCMO-000000000001.html": "en",
            "news/es/FCMO-000000000001.html": "es-419",
            "news/zh-hans/FCMO-000000000001.html": "zh-Hans",
        }
        for rel, lang in pages.items():
            path = site / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'<!doctype html><html lang="{lang}"><head></head><body class="x"><main>{rel}</main></body></html>',
                            encoding="utf-8")
        (site / "data").mkdir()
        return site

    def test_reader_script_stays_under_one_kilobyte(self) -> None:
        self.assertLessEqual(len(edition_banner.WATCH_SCRIPT.encode("utf-8")), 1024)
        self.assertNotIn("http", edition_banner.WATCH_SCRIPT)

    def test_each_state_renders_its_localized_line(self) -> None:
        expected = {
            "fresh": ("FRESH", "Updated Sep 26, 2026", "Actualizado 26 sep 2026", "更新于 2026年9月26日"),
            "quiet": ("QUIET", "No material changes since Sep 23, 2026", "Sin cambios materiales desde 23 sep 2026", "自 2026年9月23日 以来没有实质性更新"),
            "delayed": ("DELAYED", "Latest edition: Sep 23, 2026", "Última edición: 23 sep 2026", "最新一期：2026年9月23日"),
            "down": ("TRANSPORT_DOWN", "Today’s edition is delayed", "La edición de hoy está retrasada", "今日版本延迟发布"),
        }
        for name, (state, en, es, zh) in expected.items():
            status = json.loads((FIXTURES / f"newsroom-status.{name}.json").read_text(encoding="utf-8"))
            with self.subTest(state=state):
                block = edition_banner.render(status, edition_banner.LANGS, "/FCMO-AI-Newsletter/", 36)
                self.assertIn(f'data-edition-state="{state}"', block)
                for text in (en, es, zh):
                    self.assertIn(text, block)
                self.assertIn(f'data-status-updated-at="{status["status_updated_at"]}"', block)
                self.assertEqual("/FCMO-AI-Newsletter/status.html" in block, state == "TRANSPORT_DOWN")

    def test_apply_is_idempotent_and_localized_per_page(self) -> None:
        site = self.site()
        shutil.copy(FIXTURES / "newsroom-status.quiet.json", site / "data" / "newsroom-status.json")
        proc = run("tools/edition_banner.py", "--site", str(site))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("EDITION BANNER applied state=QUIET pages=5 script_bytes="), proc.stdout)
        front = (site / "index.html").read_text(encoding="utf-8")
        self.assertEqual(front.count(edition_banner.START), 1)
        self.assertLess(front.index('<body class="x">'), front.index(edition_banner.START))
        for lang in ("en", "es", "zh"):
            self.assertIn(f'<p data-l="{lang}"', front)
        spanish = (site / "news" / "es" / "FCMO-000000000001.html").read_text(encoding="utf-8")
        self.assertIn('<p data-l="es" lang="es-419">Sin cambios materiales', spanish)
        self.assertNotIn('data-l="en"', spanish)
        before = {p: p.read_bytes() for p in site.rglob("*.html")}
        self.assertEqual(run("tools/edition_banner.py", "--site", str(site)).returncode, 0)
        self.assertEqual(before, {p: p.read_bytes() for p in site.rglob("*.html")})
        self.assertEqual(run("tools/edition_banner.py", "--site", str(site), "--check").returncode, 0)
        shutil.copy(FIXTURES / "newsroom-status.delayed.json", site / "data" / "newsroom-status.json")
        stale = run("tools/edition_banner.py", "--site", str(site), "--check")
        self.assertEqual(stale.returncode, 1)
        self.assertIn("EDITION BANNER MISSING", stale.stderr)

    def test_legacy_status_gets_only_the_stale_watcher(self) -> None:
        block = edition_banner.render({"finalized_at": "2026-09-23T12:47:10Z"}, ("en",), "/", 36)
        self.assertNotIn('id="fcmo-edition"', block)
        self.assertIn('data-status-updated-at="2026-09-23T12:47:10Z"', block)
        self.assertIn(edition_banner.WATCH_SCRIPT, block)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_reader_clock_reveals_the_stale_notice_after_36h(self) -> None:
        harness = (
            "const status=Date.parse(process.argv[2]);const results=[];"
            "for(const h of [35.9,36.1]){const el={hidden:true,getAttribute:k=>({'data-status-updated-at':process.argv[2],'data-stale-after-h':'36'})[k]};"
            "global.document={getElementById:()=>el};Date.now=()=>status+h*36e5;"
            "eval(process.argv[1]);results.push(el.hidden)}console.log(JSON.stringify(results));"
        )
        proc = subprocess.run(["node", "-e", harness, edition_banner.WATCH_SCRIPT, REFERENCE],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), [True, False])


class IdentityPollingTests(unittest.TestCase):
    EXPECTED = {"release_id": "newswire-20c466f170839ac07e07bb80", "corpus_digest": "d" * 64}
    STORIES = [{"research_id": "FCMO-000000000001"}]

    def fake(self, good_after: int):
        calls: list[str] = []
        stale = json.dumps({"release_id": "newswire-000000000000000000000000", "corpus_digest": "d" * 64}).encode()
        fresh = json.dumps(self.EXPECTED).encode()
        stories = json.dumps(self.STORIES).encode()

        def get(url: str) -> bytes:
            calls.append(url)
            polls = sum(1 for c in calls if "/data/newsroom-status.json" in c)
            if "/data/stories.json" in url:
                return stories
            return fresh if polls > good_after else stale

        return calls, get

    def test_polls_with_a_cache_buster_until_the_cdn_serves_the_release(self) -> None:
        calls, get = self.fake(good_after=2)
        now = [0.0]
        with contextlib.redirect_stderr(io.StringIO()):
            attempts, live = verify_live_newsroom.poll_identity(
                "https://example.test/base", "abc123", self.EXPECTED, self.STORIES, None, 900, 30,
                get=get, clock=lambda: now[0], sleep=lambda s: now.__setitem__(0, now[0] + s))
        self.assertEqual(attempts, 3)
        self.assertEqual(live["release_id"], self.EXPECTED["release_id"])
        status_calls = [c for c in calls if "newsroom-status" in c]
        self.assertEqual(status_calls, [f"https://example.test/base/data/newsroom-status.json?v=abc123-{n}" for n in (1, 2, 3)])
        self.assertEqual(now[0], 60.0)

    def test_gives_up_after_the_deadline_with_identity_mismatch(self) -> None:
        _, get = self.fake(good_after=10**6)
        now = [0.0]
        with self.assertRaises(verify_live_newsroom.ServingFailure) as ctx, contextlib.redirect_stderr(io.StringIO()):
            verify_live_newsroom.poll_identity(
                "https://example.test/base", "abc", self.EXPECTED, self.STORIES, None, 900, 30,
                get=get, clock=lambda: now[0], sleep=lambda s: now.__setitem__(0, now[0] + s))
        self.assertEqual(ctx.exception.code, "IDENTITY_MISMATCH")
        self.assertIn("after 31 polls", str(ctx.exception))
        self.assertLessEqual(now[0], 900)


class HealthStateTests(Workspace):
    def signal(self, name: str, doc) -> str:
        path = self.tmp / f"{name}.json"
        path.write_text("" if doc is None else json.dumps(doc), encoding="utf-8")
        return f"{name}={path}"

    def health(self, wire: str, serving, editorial, translation, previous: Path | None = None, now: str = REFERENCE) -> tuple[subprocess.CompletedProcess, dict]:
        out = self.tmp / "health-state.json"
        argv = ["tools/wire_status.py", "health", "--wire-status", str(FIXTURES / wire), "--now", now, "--out", str(out),
                "--run-id", "36267562085",
                "--signal", self.signal("serving", serving), "--signal", self.signal("editorial", editorial),
                "--signal", self.signal("translation", translation)]
        if previous:
            argv += ["--previous", str(previous)]
        proc = run(*argv)
        return proc, json.loads(out.read_text(encoding="utf-8"))

    GREEN = {"status": "GREEN", "code": "OK", "detail": "fine"}

    def test_delayed_upstream_is_red_overall_with_one_alert_per_key(self) -> None:
        proc, health = self.health("wire-status.delayed.json", self.GREEN,
                                   {"status": "RED", "code": "EVENT_STALE", "detail": "old"},
                                   {"status": "RED", "code": "BACKLOG", "detail": "late"})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("HEALTH RED edition=DELAYED:ARB_MAIN_RED red=upstream,editorial"), proc.stdout)
        self.assertEqual(errors("health-state.schema.json", health), [])
        self.assertEqual(health["signals"]["serving"]["status"], "GREEN")
        self.assertEqual(health["signals"]["upstream"]["code"], "ARB_MAIN_RED")
        keys = [a["key"] for a in health["open_alerts"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(health["open_alerts"][0], {"key": "overall", "code": "DELAYED", "since": REFERENCE})

    def test_all_green_and_since_survives_the_next_check(self) -> None:
        _, first = self.health("wire-status.fresh.json", self.GREEN, self.GREEN, self.GREEN)
        self.assertEqual(errors("health-state.schema.json", first), [])
        self.assertEqual((first["overall"], first["open_alerts"]), ("GREEN", []))
        previous = self.tmp / "previous.json"
        previous.write_text(json.dumps(first), encoding="utf-8")
        _, second = self.health("wire-status.fresh.json", self.GREEN, self.GREEN, self.GREEN, previous, "2026-09-26T21:00:00Z")
        self.assertEqual(second["signals"]["serving"]["since"], first["signals"]["serving"]["since"])

    def test_an_unmeasured_required_signal_is_not_green(self) -> None:
        _, health = self.health("wire-status.fresh.json", None, self.GREEN, self.GREEN)
        self.assertEqual(errors("health-state.schema.json", health), [])
        self.assertEqual(health["signals"]["serving"]["status"], "UNKNOWN")
        self.assertEqual(health["overall"], "RED")


class EditorialSignalTests(Workspace):
    def check(self, wire: str) -> tuple[subprocess.CompletedProcess, dict]:
        out = self.tmp / "editorial.json"
        proc = run("tools/editorial_freshness.py", "check", "--wire-status", str(FIXTURES / wire),
                   "--records", str(FIXTURES / "corpus-43" / "data" / "developments.jsonl"),
                   "--now", REFERENCE, "--signal-out", str(out))
        return proc, json.loads(out.read_text(encoding="utf-8"))

    def test_quiet_wire_is_editorially_fine_but_a_delayed_one_is_not(self) -> None:
        proc, signal = self.check("wire-status.quiet.json")
        self.assertEqual((proc.returncode, signal["status"], signal["code"]), (0, "GREEN", "OK"))
        proc, signal = self.check("wire-status.delayed.json")
        self.assertEqual((proc.returncode, signal["status"], signal["code"]), (1, "RED", "EVENT_STALE"))
        self.assertTrue(proc.stdout.startswith("EDITORIAL EVENT_STALE edition=DELAYED"), proc.stdout)


if __name__ == "__main__":
    unittest.main()
