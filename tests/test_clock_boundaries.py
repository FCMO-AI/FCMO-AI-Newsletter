"""Clock boundaries of newsroom liveness (contracts/README.md, "Wire status").

Liveness comes from ``corpus/wire-status.json`` (the bridge heartbeat), never from
the Airlock generation time. These tests move a fake clock across the old
30/36/48 h airlock-age gates and the new wire thresholds, and drive the real CLIs
(``--now`` flag, ``FCMO_NOW`` fallback) as the workflows do.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for entry in (ROOT, ROOT / "tests"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from harness import oracles  # noqa: E402
from harness.clock import FakeClock  # noqa: E402
from harness.serve import start_server  # noqa: E402
from harness.validate import validator_for  # noqa: E402
from tools import edition_banner, newsroom_receipt, wire_status  # noqa: E402

FIXTURES = ROOT / "contracts" / "fixtures"
WIRE_SCHEMA = ROOT / "contracts" / "wire-status.schema.json"
STATUS_SCHEMA = ROOT / "contracts" / "newsroom-status.v2.schema.json"
BASE_PATH = "/FCMO-AI-Newsletter/"


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def at(start: str, hours: float) -> str:
    """Contract timestamp ``hours`` after ``start``."""
    return FakeClock(start).advance(hours=hours).iso()


def run(*argv: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    full_env = {k: v for k, v in os.environ.items() if k != "FCMO_NOW"}
    full_env.update(env or {})
    return subprocess.run([sys.executable, *argv], cwd=ROOT, env=full_env, capture_output=True, text=True, timeout=300)


def quiet_wire(clock: FakeClock, unchanged_for_h: float) -> dict:
    """A healthy bridge heartbeat 8 minutes ago; content unchanged for ``unchanged_for_h``."""
    wire = fixture("wire-status.quiet.json")
    last = clock.ago(hours=unchanged_for_h)
    wire.update({
        "run_at": clock.ago(minutes=8),
        "last_transport_ok_at": clock.ago(minutes=8),
        "last_release_change_at": last,
        "last_new_story_at": last,
        "state_since": last,
    })
    return wire


class Newsroom:
    """A throwaway corpus + published status whose release and builder match."""

    def __init__(self, root: Path, *, builder_digest: str | None = None) -> None:
        self.root = root
        self.corpus = root / "corpus"
        (self.corpus / "developments").mkdir(parents=True)
        (self.corpus / "index.html").write_text("ok", encoding="utf-8")
        airlock = json.loads((FIXTURES / "corpus-43" / "airlock.json").read_text(encoding="utf-8"))
        (self.corpus / "airlock.json").write_text(json.dumps(airlock), encoding="utf-8")
        self.status = root / "site" / "data" / "newsroom-status.json"
        self.status.parent.mkdir(parents=True)
        self.status.write_text(json.dumps({
            "schema": "fcmo-newsroom-status-v1",
            "state": "NO_PUBLIC_DELTA_READY",
            "release_id": airlock["release_id"],
            "corpus_digest": airlock["corpus_digest"],
            "builder_digest": builder_digest or newsroom_receipt.builder_digest(ROOT),
            "story_layer_count": 43,
            "finalized_at": "2026-09-23T12:00:00Z",
            "translation_counts": {"es-419": 25, "zh-Hans": 25},
        }), encoding="utf-8")
        self.wire = root / "wire-status.json"

    def write_wire(self, doc: dict) -> Path:
        self.wire.write_text(json.dumps(doc), encoding="utf-8")
        return self.wire

    def preflight(self, now: str) -> tuple[int, list[str], dict, str]:
        proc = run("tools/newsroom_receipt.py", "preflight", "--now", now, "--corpus", str(self.corpus),
                   "--wire-status", str(self.wire), "--status", str(self.status))
        lines = proc.stdout.splitlines()
        detail = json.loads(lines[1]) if len(lines) > 1 else {}
        return proc.returncode, lines, detail, proc.stderr


class ClockBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    # -- acceptance 1a ------------------------------------------------------------------
    def test_unchanged_content_with_fresh_wire_stays_quiet_past_the_old_airlock_gates(self) -> None:
        for hours in (31, 37, 49):
            with self.subTest(unchanged_for_h=hours):
                clock = FakeClock()
                newsroom = Newsroom(self.root / f"q{hours}")
                wire = quiet_wire(clock, hours)
                self.assertEqual(validator_for(WIRE_SCHEMA).errors(wire), [])
                newsroom.write_wire(wire)
                code, lines, detail, _ = newsroom.preflight(clock.iso())
                self.assertEqual(code, 0, lines)
                self.assertEqual(lines[0], "QUIET")
                self.assertEqual(detail["path"], "status")
                self.assertEqual(detail["state"], "NO_PUBLIC_DELTA")
                classify = run("tools/wire_status.py", "classify", "--wire-status", str(newsroom.wire), "--now", clock.iso())
                self.assertEqual(classify.returncode, 0, classify.stdout)
                self.assertTrue(classify.stdout.startswith("QUIET "))
                # The status-only path records the quiet edition for the banner.
                status = run("tools/newsroom_receipt.py", "status", "--now", clock.iso(), "--corpus", str(newsroom.corpus),
                             "--wire-status", str(newsroom.wire), "--status", str(newsroom.status))
                self.assertEqual(status.returncode, 0, status.stderr)
                self.assertTrue(status.stdout.startswith("STATUS QUIET wire=QUIET written=true"), status.stdout)
                written = json.loads(newsroom.status.read_text(encoding="utf-8"))
                self.assertEqual(validator_for(STATUS_SCHEMA).errors(written), [])
                self.assertEqual(written["edition_state"], "QUIET")
                self.assertEqual(written["quiet_since"], wire["last_release_change_at"])

    # -- acceptance 1b ------------------------------------------------------------------
    def test_wire_heartbeat_older_than_30h_is_transport_down(self) -> None:
        wire = fixture("wire-status.quiet.json")
        newsroom = Newsroom(self.root / "down")
        newsroom.write_wire(wire)
        now = at(wire["run_at"], 31)
        code, lines, detail, _ = newsroom.preflight(now)
        self.assertEqual(code, 1)
        self.assertEqual(lines[0], "TRANSPORT_DOWN")
        self.assertEqual(detail["wire_reason"], "WIRE_STALE")
        classify = run("tools/wire_status.py", "classify", "--wire-status", str(newsroom.wire), "--now", now)
        self.assertEqual(classify.returncode, 1)
        self.assertTrue(classify.stdout.startswith("TRANSPORT_DOWN reason=WIRE_STALE"), classify.stdout)
        # The shipped fixture is the same situation at the reference time.
        fixed = run("tools/wire_status.py", "classify", "--wire-status", str(FIXTURES / "wire-status.down.json"),
                    "--now", "2026-09-26T20:00:00Z")
        self.assertEqual(fixed.returncode, 1)
        self.assertTrue(fixed.stdout.startswith("TRANSPORT_DOWN"))
        # A missing wire status is also TRANSPORT_DOWN (blind means not fresh).
        newsroom.wire.unlink()
        code, lines, detail, _ = newsroom.preflight(now)
        self.assertEqual((code, lines[0], detail["wire_reason"]), (1, "TRANSPORT_DOWN", "WIRE_STATUS_MISSING"))

    def test_thirty_hour_boundary_is_exact(self) -> None:
        clock = FakeClock()
        wire = quiet_wire(clock, 40)
        self.assertEqual(wire_status.classify(wire, at(wire["run_at"], 30))[0], "QUIET")
        self.assertEqual(wire_status.classify(wire, at(wire["run_at"], 30 + 1 / 60))[0], "TRANSPORT_DOWN")

    # -- acceptance 1c ------------------------------------------------------------------
    def test_checkpoint_with_red_main_is_delayed_while_serving_stays_green(self) -> None:
        clock = FakeClock()
        newsroom = Newsroom(self.root / "delayed")
        newsroom.write_wire(fixture("wire-status.delayed.json"))
        code, lines, detail, _ = newsroom.preflight(clock.iso())
        self.assertEqual(code, 0)
        self.assertEqual(lines[0], "DELAYED:ARB_MAIN_RED")
        self.assertEqual(detail["edition_state"], "DELAYED")
        # publication-freshness is red ...
        freshness = run("tools/wire_status.py", "classify", "--wire-status", str(newsroom.wire), "--now", clock.iso())
        self.assertEqual(freshness.returncode, 1)
        self.assertTrue(freshness.stdout.startswith("DELAYED:ARB_MAIN_RED reason=ARB_MAIN_RED"), freshness.stdout)
        # ... while serving (availability + identity) is green on the same site.
        status = run("tools/newsroom_receipt.py", "status", "--now", clock.iso(), "--corpus", str(newsroom.corpus),
                     "--wire-status", str(newsroom.wire), "--status", str(newsroom.status))
        self.assertEqual(status.returncode, 0, status.stderr)
        written = json.loads(newsroom.status.read_text(encoding="utf-8"))
        self.assertEqual((written["edition_state"], written["edition_reason"]), ("DELAYED", "ARB_MAIN_RED"))
        self.assertEqual(validator_for(STATUS_SCHEMA).errors(written), [])
        site = self.minimal_site(written)
        with start_server(site, base=BASE_PATH) as server:
            serving = run("tools/verify_live_newsroom.py", "--serving-only", "--base-url", server.url,
                          "--status", str(site / "data" / "newsroom-status.json"),
                          "--stories", str(site / "data" / "stories.json"),
                          "--identity-timeout-s", "0", "--signal-out", str(self.root / "serving.json"),
                          env={"FCMO_LIVE_FETCH_PAUSE_S": "0"})
        self.assertEqual(serving.returncode, 0, serving.stdout + serving.stderr)
        self.assertTrue(serving.stdout.startswith("SERVING OK"), serving.stdout)
        signal = json.loads((self.root / "serving.json").read_text(encoding="utf-8"))
        self.assertEqual((signal["status"], signal["code"]), ("GREEN", "OK"))
        # Readers see the delayed edition in all three languages on the front page.
        banner = edition_banner.render(written, edition_banner.LANGS, BASE_PATH, 36)
        self.assertIn('data-edition-state="DELAYED"', banner)
        for text in ("Today’s edition is delayed", "La edición de hoy está retrasada", "今日版本延迟发布"):
            self.assertIn(text, banner)

    # -- acceptance 1d ------------------------------------------------------------------
    def test_builder_change_rebuilds_even_with_a_stale_upstream(self) -> None:
        clock = FakeClock()
        for name, want_code, want_line, warning in (
            ("wire-status.delayed.json", 0, "DELAYED:ARB_MAIN_RED", "REBUILD_WITH_DELAYED"),
            ("wire-status.down.json", 1, "TRANSPORT_DOWN", "REBUILD_WITH_TRANSPORT_DOWN"),
        ):
            with self.subTest(wire=name):
                newsroom = Newsroom(self.root / name, builder_digest="0" * 64)
                newsroom.write_wire(fixture(name))
                code, lines, detail, stderr = newsroom.preflight(clock.iso())
                self.assertEqual(code, want_code)
                self.assertEqual(lines[0], want_line)
                self.assertEqual(detail["path"], "rebuild")
                self.assertEqual(detail["reason"], "BUILDER_CHANGED")
                self.assertEqual(detail["warning"], warning)
                self.assertIn(f"WARNING {warning} reason=BUILDER_CHANGED", stderr)

    # -- the classifier against the independent oracle ------------------------------------
    def test_classifier_matches_the_contract_oracle_across_the_clock(self) -> None:
        offsets_h = (-1, -0.2, -0.3, 0, 5, 6.5, 23.9, 24.1, 29.9, 30, 30.1, 31, 36, 37, 49, 95.9, 96.1, 120)
        wires = {name: fixture(f"wire-status.{name}.json") for name in ("fresh", "quiet", "delayed", "down")}
        failing = copy.deepcopy(wires["quiet"])
        failing.update({"transport": "FAIL", "transport_error": "TOKEN_MINT_FAILED", "warnings": ["TRANSPORT_FAIL"],
                        "last_transport_ok_at": "2026-09-26T15:00:00Z"})
        wires["failing"] = failing
        refused = copy.deepcopy(wires["quiet"])
        refused["guard"] = {"verdict": "REGRESSION_REFUSED", "missing": [], "withdrawn": [], "added": 0, "ratio": 0.39}
        wires["refused"] = refused
        checkpoint = copy.deepcopy(wires["delayed"])
        checkpoint.update({"arb_main": "GREEN", "arb_main_failures": []})
        wires["checkpoint"] = checkpoint
        thresholds = oracles.load_thresholds()
        seen = set()
        for name, wire in wires.items():
            for hours in offsets_h:
                now = at("2026-09-26T20:00:00Z", hours)
                with self.subTest(wire=name, offset_h=hours):
                    mine = wire_status.classify(wire, now)
                    self.assertEqual(mine, oracles.classify_wire(wire, now, thresholds))
                    self.assertEqual(wire_status.freshness_exit(mine[0]), oracles.freshness_exit_code(mine[0]))
                    seen.add(mine[0])
        for state in ("FRESH", "QUIET", "TRANSPORT_DOWN", "DELAYED:ARB_MAIN_RED", "DELAYED:TRANSPORT_FAIL",
                      "DELAYED:SNAPSHOT_REFUSED", "DELAYED:CHECKPOINT_STALE", "DELAYED:STORY_SUPPLY"):
            self.assertIn(state, seen)
        self.assertEqual(wire_status.classify(None, "2026-09-26T20:00:00Z"), ("TRANSPORT_DOWN", "WIRE_STATUS_MISSING"))

    def test_env_clock_is_used_when_no_flag_is_given(self) -> None:
        wire = FIXTURES / "wire-status.quiet.json"
        with_env = run("tools/wire_status.py", "classify", "--wire-status", str(wire), env={"FCMO_NOW": "2026-09-28T02:00:00Z"})
        with_flag = run("tools/wire_status.py", "classify", "--wire-status", str(wire), "--now", "2026-09-28T02:00:00Z")
        self.assertEqual(with_env.stdout, with_flag.stdout)
        self.assertTrue(with_env.stdout.startswith("TRANSPORT_DOWN"), with_env.stdout)
        flag_wins = run("tools/wire_status.py", "classify", "--wire-status", str(wire), "--now", "2026-09-26T20:00:00Z",
                        env={"FCMO_NOW": "2026-09-28T02:00:00Z"})
        self.assertTrue(flag_wins.stdout.startswith("QUIET"), flag_wins.stdout)

    # -- helpers ------------------------------------------------------------------------
    def minimal_site(self, status: dict) -> Path:
        """Every availability route plus the identity files, served like Pages."""
        from tools import verify_live_newsroom

        site = self.root / "served"
        (site / "data").mkdir(parents=True)
        (site / "index.html").write_text("<!doctype html><title>FCMO AI Newsletter</title>", encoding="utf-8")
        for route in verify_live_newsroom.AVAILABILITY_ROUTES:
            target = site / route.lstrip("/")
            if route.endswith("/"):
                target = target / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("ok", encoding="utf-8")
        stories = [{"research_id": f"FCMO-{i:012X}"} for i in range(status.get("story_layer_count") or 1)]
        (site / "data" / "stories.json").write_text(json.dumps(stories), encoding="utf-8")
        (site / "data" / "newsroom-status.json").write_text(json.dumps(status), encoding="utf-8")
        return site


if __name__ == "__main__":
    unittest.main()
