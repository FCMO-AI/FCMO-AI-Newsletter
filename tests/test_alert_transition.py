"""Operator alerts and the generated PRODUCTION_STATUS.md (WP-C2).

The GitHub REST API is simulated by an in-process HTTP server that keeps
issues, comments and workflow runs in memory, so the tools run end to end
(argument parsing, HTTP, JSON) exactly as in the workflow, with no network.
"""
from __future__ import annotations

import copy
import io
import json
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
FIXTURES = ROOT / "contracts" / "fixtures"
WORKFLOW = ROOT / ".github" / "workflows" / "operator-alerts.yml"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import alert_transition  # noqa: E402
import status_report  # noqa: E402

REPO = "FCMO-AI/FCMO-AI-Newsletter"
BOT = "github-actions[bot]"


class FakeGitHub:
    """In-memory GitHub REST API: issues, comments and workflow runs."""

    def __init__(self) -> None:
        self.issues: list[dict] = []
        self.comments: list[dict] = []
        self.runs: dict[str, list[dict]] = {}
        self.requests: list[tuple[str, str]] = []
        self.fail_with: int | None = None
        self.auth_headers: list[str | None] = []
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # silence
                pass

            def _send(self, code: int, payload) -> None:
                raw = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def _body(self):
                length = int(self.headers.get("Content-Length") or 0)
                return json.loads(self.rfile.read(length)) if length else None

            def _route(self, method: str) -> None:
                url = urlparse(self.path)
                query = {k: v[0] for k, v in parse_qs(url.query).items()}
                fake.requests.append((method, url.path))
                fake.auth_headers.append(self.headers.get("Authorization"))
                if fake.fail_with:
                    return self._send(fake.fail_with, {"message": "boom"})
                prefix = f"/repos/{REPO}"
                if not url.path.startswith(prefix):
                    return self._send(404, {"message": "Not Found"})
                path = url.path[len(prefix):]
                body = self._body() if method in {"POST", "PATCH"} else None
                if method == "GET" and path == "/issues":
                    rows = [i for i in fake.issues if i["state"] == query.get("state", "open")]
                    if "creator" in query:
                        rows = [i for i in rows if i["user"]["login"] == query["creator"]]
                    page, per = int(query.get("page", 1)), int(query.get("per_page", 30))
                    return self._send(200, rows[(page - 1) * per: page * per])
                if method == "POST" and path == "/issues":
                    issue = {
                        "number": len(fake.issues) + 1,
                        "title": body["title"],
                        "body": body.get("body", ""),
                        "labels": [{"name": n} for n in body.get("labels", [])],
                        "state": "open",
                        "user": {"login": BOT},
                    }
                    fake.issues.append(issue)
                    return self._send(201, issue)
                match = re.fullmatch(r"/issues/(\d+)(/comments)?", path)
                if match:
                    issue = next((i for i in fake.issues if i["number"] == int(match.group(1))), None)
                    if issue is None:
                        return self._send(404, {"message": "Not Found"})
                    if match.group(2) and method == "POST":
                        comment = {"issue": issue["number"], "body": body["body"]}
                        fake.comments.append(comment)
                        return self._send(201, comment)
                    if method == "PATCH":
                        issue.update(body)
                        return self._send(200, issue)
                match = re.fullmatch(r"/actions/workflows/([^/]+)/runs", path)
                if match and method == "GET":
                    runs = [r for r in fake.runs.get(match.group(1), []) if r.get("head_branch", "main") == query.get("branch", "main")]
                    runs = sorted(runs, key=lambda r: r["created_at"], reverse=True)[: int(query.get("per_page", 30))]
                    return self._send(200, {"total_count": len(runs), "workflow_runs": runs})
                return self._send(404, {"message": "Not Found"})

            def do_GET(self):
                self._route("GET")

            def do_POST(self):
                self._route("POST")

            def do_PATCH(self):
                self._route("PATCH")

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    # helpers
    def writes(self) -> list[tuple[str, str]]:
        return [r for r in self.requests if r[0] != "GET"]

    def open_issues(self) -> list[dict]:
        return [i for i in self.issues if i["state"] == "open"]

    def add_run(self, workflow: str, conclusion: str, minute: int, event: str = "schedule") -> None:
        runs = self.runs.setdefault(workflow, [])
        runs.append(
            {
                "id": 36000000000 + len(runs) + 1,
                "event": event,
                "status": "completed",
                "conclusion": conclusion,
                "head_branch": "main",
                "created_at": f"2026-09-26T{10 + minute // 60:02d}:{minute % 60:02d}:00Z",
                "run_started_at": f"2026-09-26T{10 + minute // 60:02d}:{minute % 60:02d}:00Z",
            }
        )


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class AlertCase(unittest.TestCase):
    def setUp(self) -> None:
        self.api = FakeGitHub()
        self.addCleanup(self.api.close)
        self.tmp = Path(tempfile.mkdtemp(prefix="c2-alerts-"))

    def write_health(self, doc: dict | str | None, name: str = "health-state.json") -> Path:
        path = self.tmp / name
        if doc is None:
            if path.exists():
                path.unlink()
        elif isinstance(doc, str):
            path.write_text(doc, encoding="utf-8")
        else:
            path.write_text(json.dumps(doc), encoding="utf-8")
        return path

    def run_tool(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        env_backup = dict(alert_transition.os.environ)
        alert_transition.os.environ["GITHUB_TOKEN"] = "test-token-not-real"
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = alert_transition.main([*argv, "--repo", REPO, "--api-url", self.api.url])
        finally:
            alert_transition.os.environ.clear()
            alert_transition.os.environ.update(env_backup)
        return code, out.getvalue(), err.getvalue()

    def health(self, doc) -> tuple[int, str]:
        code, out, _ = self.run_tool("health", "--health", str(self.write_health(doc)))
        return code, out.strip()


class HealthTransitionTests(AlertCase):
    def test_green_to_red_opens_exactly_one_issue(self) -> None:
        code, line = self.health(load("health-state.green.json"))
        self.assertEqual((code, line), (0, "NOOP key=overall state=GREEN"))
        self.assertEqual(self.api.writes(), [])

        code, line = self.health(load("health-state.red.json"))
        self.assertEqual(code, 0)
        self.assertTrue(line.startswith("OPENED key=overall issue=#1 "), line)
        self.assertEqual(len(self.api.issues), 1)
        self.assertEqual(self.api.writes(), [("POST", f"/repos/{REPO}/issues")])
        issue = self.api.issues[0]
        self.assertIn("DELAYED:ARB_MAIN_RED", issue["title"])
        self.assertIn("upstream:ARB_MAIN_RED", issue["body"])
        self.assertIn("editorial:EVENT_STALE", issue["body"])
        self.assertEqual(issue["labels"], [{"name": "operator-alert"}])
        self.assertIn("https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/36268000002", issue["body"])
        self.assertTrue(all(h == "Bearer test-token-not-real" for h in self.api.auth_headers))

    def test_red_to_red_creates_nothing(self) -> None:
        self.health(load("health-state.green.json"))
        self.health(load("health-state.red.json"))
        writes_after_open = len(self.api.writes())
        for _ in range(3):
            code, line = self.health(load("health-state.red.json"))
            self.assertEqual(code, 0)
            self.assertTrue(line.startswith("UNCHANGED key=overall issue=#1"), line)
        self.assertEqual(len(self.api.writes()), writes_after_open, "RED→RED must not write anything")
        self.assertEqual(len(self.api.issues), 1)
        self.assertEqual(self.api.comments, [])

    def test_red_to_green_closes_the_issue(self) -> None:
        self.health(load("health-state.green.json"))
        self.health(load("health-state.red.json"))
        code, line = self.health(load("health-state.green.json"))
        self.assertEqual((code, line), (0, "CLOSED key=overall issue=#1 state=GREEN"))
        self.assertEqual(self.api.open_issues(), [])
        self.assertEqual(self.api.issues[0]["state"], "closed")
        self.assertEqual(self.api.issues[0]["state_reason"], "completed")
        self.assertEqual(len(self.api.comments), 1)
        self.assertIn("Recovered", self.api.comments[0]["body"])
        # A later green run finds nothing to close.
        code, line = self.health(load("health-state.green.json"))
        self.assertEqual(line, "NOOP key=overall state=GREEN")

    def test_new_red_episode_after_recovery_opens_a_new_issue(self) -> None:
        for doc in ("green", "red", "green", "red"):
            self.health(load(f"health-state.{doc}.json"))
        self.assertEqual([i["state"] for i in self.api.issues], ["closed", "open"])

    def test_red_with_changed_signals_updates_without_new_issue(self) -> None:
        self.health(load("health-state.red.json"))
        changed = load("health-state.red.json")
        changed["signals"]["editorial"].update(status="GREEN", code="OK", detail="Quiet day.")
        changed["open_alerts"] = [a for a in changed["open_alerts"] if a["key"] != "editorial"]
        code, line = self.health(changed)
        self.assertEqual(code, 0)
        self.assertTrue(line.startswith("UPDATED key=overall issue=#1 codes=upstream:ARB_MAIN_RED"), line)
        self.assertEqual(len(self.api.issues), 1)
        self.assertEqual(len(self.api.comments), 1)
        self.assertIn("editorial:EVENT_STALE", self.api.comments[0]["body"])
        # Same signals again: nothing more.
        writes = len(self.api.writes())
        self.health(changed)
        self.assertEqual(len(self.api.writes()), writes)

    def test_missing_or_invalid_health_state_is_red_not_green(self) -> None:
        code, line = self.health(None)
        self.assertEqual(code, 0)
        self.assertTrue(line.startswith("OPENED key=overall issue=#1 codes=health:HEALTH_STATE_MISSING"), line)
        code, line = self.health("{not json")
        self.assertTrue(line.startswith("UPDATED key=overall issue=#1 codes=health:HEALTH_STATE_INVALID"), line)
        forged = load("health-state.red.json")
        forged["overall"] = "GREEN"  # contradicts its red required signals
        code, line = self.health(forged)
        self.assertTrue(line.startswith("UNCHANGED key=overall issue=#1 codes=health:HEALTH_STATE_INVALID"), line)
        self.assertEqual(len(self.api.open_issues()), 1)

    def test_marker_copied_into_a_foreign_issue_is_ignored(self) -> None:
        self.api.issues.append(
            {
                "number": 1,
                "title": "spoof",
                "body": alert_transition.marker("overall", ["upstream:ARB_MAIN_RED"]),
                "labels": [],
                "state": "open",
                "user": {"login": "someone-else"},
            }
        )
        code, line = self.health(load("health-state.red.json"))
        self.assertTrue(line.startswith("OPENED key=overall issue=#2"), line)
        code, line = self.health(load("health-state.green.json"))
        self.assertEqual(line, "CLOSED key=overall issue=#2 state=GREEN")
        self.assertEqual(self.api.issues[0]["state"], "open", "a foreign issue is never touched")

    def test_dry_run_writes_nothing(self) -> None:
        code, out, _ = self.run_tool("health", "--health", str(self.write_health(load("health-state.red.json"))), "--dry-run")
        self.assertEqual((code, out.strip()), (0, "WOULD_OPENED key=overall codes=upstream:ARB_MAIN_RED,editorial:EVENT_STALE"))
        self.assertEqual(self.api.writes(), [])

    def test_api_failure_exits_1_without_leaking_the_token(self) -> None:
        self.api.fail_with = 502
        code, out, err = self.run_tool("health", "--health", str(self.write_health(load("health-state.red.json"))))
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("GITHUB_HTTP_502", err)
        self.assertNotIn("test-token-not-real", err)

    def test_usage_errors_exit_2(self) -> None:
        code, _, _ = self.run_tool("health", "--health", str(self.write_health(load("health-state.red.json"))), "--run-id", "12; rm")
        self.assertEqual(code, 2)
        code, _, _ = self.run_tool("workflow", "--workflow-id", "1", "--workflow-path", ".github/workflows/x y.yml")
        self.assertEqual(code, 2)


class WorkflowFailureTests(AlertCase):
    PAGES = ("--workflow-id", "4242", "--workflow-path", ".github/workflows/pages.yml", "--workflow-name", "Deploy FCMO AI Newsletter")

    def wf(self) -> tuple[int, str]:
        code, out, _ = self.run_tool("workflow", *self.PAGES)
        return code, out.strip()

    def test_one_failure_does_not_alert(self) -> None:
        self.api.add_run("4242", "success", 0)
        self.api.add_run("4242", "failure", 10)
        self.assertEqual(self.wf(), (0, "NOOP key=workflow:pages failures=1"))
        self.assertEqual(self.api.writes(), [])

    def test_two_consecutive_failures_open_one_issue_then_success_closes(self) -> None:
        self.api.add_run("4242", "success", 0)
        self.api.add_run("4242", "failure", 10)
        self.api.add_run("4242", "failure", 20)
        code, line = self.wf()
        self.assertEqual((code, line), (0, "OPENED key=workflow:pages issue=#1 failures=2"))
        issue = self.api.issues[0]
        self.assertIn("Deploy FCMO AI Newsletter", issue["title"])
        self.assertIn("failed 2 times in a row", issue["body"])
        # A third failure writes nothing.
        self.api.add_run("4242", "failure", 30)
        writes = len(self.api.writes())
        self.assertEqual(self.wf(), (0, "UNCHANGED key=workflow:pages issue=#1 failures=3"))
        self.assertEqual(len(self.api.writes()), writes)
        # Recovery closes it.
        self.api.add_run("4242", "success", 40)
        self.assertEqual(self.wf(), (0, "CLOSED key=workflow:pages issue=#1 failures=0"))
        self.assertEqual(self.api.open_issues(), [])

    def test_skipped_and_cancelled_runs_neither_count_nor_reset(self) -> None:
        self.api.add_run("4242", "failure", 0)
        self.api.add_run("4242", "skipped", 5, event="workflow_run")
        self.api.add_run("4242", "cancelled", 7)
        self.api.add_run("4242", "failure", 10)
        self.api.add_run("4242", "skipped", 12, event="workflow_run")
        self.assertEqual(self.wf(), (0, "OPENED key=workflow:pages issue=#1 failures=2"))

    def test_timed_out_and_startup_failure_count_as_failures(self) -> None:
        self.api.add_run("4242", "timed_out", 0)
        self.api.add_run("4242", "startup_failure", 10)
        self.assertEqual(self.wf()[1], "OPENED key=workflow:pages issue=#1 failures=2")

    def test_workflow_and_health_alerts_are_independent(self) -> None:
        self.health(load("health-state.red.json"))
        self.api.add_run("4242", "failure", 0)
        self.api.add_run("4242", "failure", 10)
        self.assertEqual(self.wf()[1], "OPENED key=workflow:pages issue=#2 failures=2")
        self.health(load("health-state.green.json"))
        self.assertEqual([i["state"] for i in self.api.issues], ["closed", "open"])

    def test_bridge_failure_streak_has_its_own_key(self) -> None:
        for minute in (0, 60):
            self.api.add_run("77", "failure", minute)
        code, out, _ = self.run_tool("workflow", "--workflow-id", "77", "--workflow-path", ".github/workflows/newswire-bridge.yml")
        self.assertEqual(out.strip(), "OPENED key=workflow:newswire-bridge issue=#1 failures=2")

    def test_failure_streak_pure(self) -> None:
        runs = [
            {"id": 1, "conclusion": "success", "created_at": "2026-09-26T01:00:00Z"},
            {"id": 2, "conclusion": "failure", "created_at": "2026-09-26T02:00:00Z"},
            {"id": 3, "conclusion": "skipped", "created_at": "2026-09-26T03:00:00Z"},
            {"id": 4, "conclusion": "failure", "created_at": "2026-09-26T04:00:00Z"},
        ]
        streak, newest, newest_failed = alert_transition.failure_streak(runs)
        self.assertEqual((streak, newest["id"], newest_failed["id"]), (2, 4, 4))
        self.assertEqual(alert_transition.failure_streak([])[0], 0)


class StatusReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="c2-status-"))

    def run_report(self, *argv: str) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = status_report.main(list(argv))
        return code, out.getvalue().strip()

    def test_red_fixture_is_delayed_never_operational(self) -> None:
        out = self.tmp / "PRODUCTION_STATUS.md"
        code, line = self.run_report("--health", str(FIXTURES / "health-state.red.json"), "--out", str(out))
        self.assertEqual(code, 0)
        self.assertTrue(line.startswith("WROTE PRODUCTION_STATUS.md state=DELAYED "), line)
        text = out.read_text(encoding="utf-8")
        self.assertIn("**Canonical operating state:** `DELAYED` — `ARB_MAIN_RED`", text)
        self.assertNotIn("OPERATIONAL", text)
        self.assertIn("| upstream | yes | `RED` | `ARB_MAIN_RED` |", text)
        self.assertIn("| overall | `DELAYED` | 2026-09-20T07:10:00Z |", text)

    def test_every_state_is_named_and_none_says_operational(self) -> None:
        red = load("health-state.red.json")
        green = load("health-state.green.json")
        down = copy.deepcopy(red)
        down["signals"]["serving"].update(status="RED", code="IDENTITY_MISMATCH")
        transport = copy.deepcopy(red)
        transport["edition_state"] = "TRANSPORT_DOWN"
        transport["signals"]["transport"].update(status="RED", code="TRANSPORT_DOWN")
        degraded = copy.deepcopy(green)
        degraded["overall"] = "RED"
        degraded["signals"]["editorial"].update(status="RED", code="EVENT_STALE")
        fresh = copy.deepcopy(green)
        fresh["edition_state"] = "FRESH"
        cases = {
            "DELAYED": red,
            "QUIET": green,
            "FRESH": fresh,
            "DOWN": down,
            "TRANSPORT_DOWN": transport,
            "DEGRADED": degraded,
        }
        for expected, doc in cases.items():
            with self.subTest(expected=expected):
                self.assertEqual(status_report.health_problems(doc), [])
                text, state, _ = status_report.render(doc)
                self.assertEqual(state, expected)
                self.assertNotIn("OPERATIONAL", text)

    def test_unreadable_health_is_unknown(self) -> None:
        out = self.tmp / "PRODUCTION_STATUS.md"
        code, line = self.run_report("--health", str(self.tmp / "missing.json"), "--out", str(out), "--now", "2026-09-26T20:00:00Z")
        self.assertEqual(code, 0)
        self.assertTrue(line.startswith("WROTE PRODUCTION_STATUS.md state=UNKNOWN"), line)
        text = out.read_text(encoding="utf-8")
        self.assertIn("**Canonical operating state:** `UNKNOWN`", text)
        self.assertIn("HEALTH_STATE_MISSING", text)
        bad = self.tmp / "bad.json"
        bad.write_text(json.dumps({"schema": "fcmo-health-state-v1", "overall": "GREEN"}), encoding="utf-8")
        code, line = self.run_report("--health", str(bad), "--out", str(out))
        self.assertIn("state=UNKNOWN", line)

    def test_if_changed_skips_same_state_and_refreshes_daily(self) -> None:
        out = self.tmp / "PRODUCTION_STATUS.md"
        red = load("health-state.red.json")
        path = self.tmp / "h.json"
        path.write_text(json.dumps(red), encoding="utf-8")
        self.assertTrue(self.run_report("--health", str(path), "--out", str(out), "--if-changed")[1].startswith("WROTE"))
        # One hour later, same state, new ages in details: unchanged.
        later = copy.deepcopy(red)
        later["checked_at"] = "2026-09-26T21:17:00Z"
        later["run_id"] = "36268000003"
        later["signals"]["editorial"]["detail"] = "Newest story event is 363.1h old (limit 36h)."
        path.write_text(json.dumps(later), encoding="utf-8")
        self.assertTrue(self.run_report("--health", str(path), "--out", str(out), "--if-changed")[1].startswith("UNCHANGED"))
        self.assertIn("36268000002", out.read_text(encoding="utf-8"))
        # 25 h later, same state: refreshed so the snapshot never looks abandoned.
        later["checked_at"] = "2026-09-27T21:18:00Z"
        path.write_text(json.dumps(later), encoding="utf-8")
        self.assertTrue(self.run_report("--health", str(path), "--out", str(out), "--if-changed")[1].startswith("WROTE"))
        # A state change is written at once.
        path.write_text(json.dumps(load("health-state.green.json")), encoding="utf-8")
        code, line = self.run_report("--health", str(path), "--out", str(out), "--if-changed")
        self.assertTrue(line.startswith("WROTE PRODUCTION_STATUS.md state=QUIET"), line)

    def test_check_mode(self) -> None:
        out = self.tmp / "PRODUCTION_STATUS.md"
        health = str(FIXTURES / "health-state.red.json")
        self.run_report("--health", health, "--out", str(out))
        self.assertEqual(self.run_report("--health", health, "--out", str(out), "--check")[0], 0)
        out.write_text(out.read_text(encoding="utf-8").replace("`DELAYED`", "`OPERATIONAL`"), encoding="utf-8")
        code, line = self.run_report("--health", health, "--out", str(out), "--check")
        self.assertEqual(code, 1)
        self.assertTrue(line.startswith("STALE"), line)

    def test_committed_production_status_is_generated_and_not_operational(self) -> None:
        text = (ROOT / "PRODUCTION_STATUS.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("<!-- GENERATED by tools/status_report.py"), "PRODUCTION_STATUS.md must be generated")
        self.assertRegex(text, status_report.DIGEST_RE)
        self.assertNotIn("OPERATIONAL", text)
        state = re.search(r"\*\*Canonical operating state:\*\* `([A-Z_]+)`", text).group(1)
        self.assertIn(state, status_report.MEANING)

    def test_cli_acceptance_command(self) -> None:
        """PLAN §4.1 WP-C2: `status_report.py --health <red fixture>` names DELAYED (run on a copy)."""
        out = self.tmp / "PRODUCTION_STATUS.md"
        proc = subprocess.run(
            [sys.executable, str(TOOLS / "status_report.py"), "--health", str(FIXTURES / "health-state.red.json"), "--out", str(out)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("state=DELAYED", proc.stdout)
        self.assertNotIn("OPERATIONAL", out.read_text(encoding="utf-8"))


class OperatorAlertsWorkflowTests(unittest.TestCase):
    WATCHED = {
        "Autonomous newsroom production health": "newsroom-health.yml",
        "Pull airlocked newswire with GitHub App": "newswire-bridge.yml",
        "Refresh the autonomous newsroom from the sanitized corpus": "daily-refresh.yml",
        "Deploy FCMO AI Newsletter": "pages.yml",
    }

    def setUp(self) -> None:
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def workflow(self) -> dict:
        try:
            import yaml  # type: ignore
        except ImportError:  # CI's stdlib-only Python: text checks below still run
            return {}
        doc = yaml.safe_load(self.text)
        doc["on"] = doc.pop(True, doc.get("on"))  # YAML 1.1 reads `on` as True
        return doc

    def test_triggers_on_every_watched_workflow_by_its_real_name(self) -> None:
        for name, filename in self.WATCHED.items():
            with self.subTest(name=name):
                self.assertIn(f"- '{name}'", self.text)
                source = (ROOT / ".github" / "workflows" / filename).read_text(encoding="utf-8")
                self.assertRegex(source, rf"(?m)^name: {re.escape(name)}\s*$")
        doc = self.workflow()
        if doc:
            watched = doc["on"]["workflow_run"]["workflows"]
            self.assertTrue(set(self.WATCHED) <= set(watched))
            self.assertEqual(doc["on"]["workflow_run"]["types"], ["completed"])
            self.assertEqual(doc["permissions"], {"contents": "read"})
            self.assertEqual(doc["concurrency"]["cancel-in-progress"], False)
            health = doc["jobs"]["health-transition"]
            self.assertEqual(health["permissions"], {"actions": "read", "contents": "write", "issues": "write"})
            failure = doc["jobs"]["workflow-failure"]
            self.assertEqual(failure["permissions"], {"actions": "read", "contents": "read", "issues": "write"})

    def test_health_job_uses_the_artifact_and_regenerates_status(self) -> None:
        self.assertIn("--name health-state", self.text)
        self.assertIn("tools/alert_transition.py health", self.text)
        self.assertIn("tools/status_report.py", self.text)
        self.assertIn("--if-changed", self.text)
        self.assertIn("git push origin HEAD:main", self.text)
        # Skipped/cancelled health runs measured nothing.
        self.assertIn("github.event.workflow_run.conclusion == 'failure'", self.text)
        self.assertNotIn("conclusion == 'skipped'", self.text)

    def test_failure_job_threshold_and_no_script_injection(self) -> None:
        self.assertIn("--threshold 2", self.text)
        # Event fields reach the shell only through env, never interpolated into `run:`.
        for line in self.text.splitlines():
            if "${{" in line and "github.event.workflow_run" in line:
                stripped = line.strip()
                self.assertRegex(stripped, r"^(group:|[A-Z_]+:|\(github|github\.event|if:)", stripped)


if __name__ == "__main__":
    unittest.main()
