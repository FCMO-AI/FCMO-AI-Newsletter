"""Battery for tools/refresh_guard.py: the three real failure shapes of 2026-10-23.

Each case builds a small candidate release from the repository's own fixtures
(real tools, real catalogs, a slice of the real corpus and Story layer), injects
one failure shape, and requires that

* the refresh guard reports it as an error BEFORE anything is pushed, and
* the downstream gate that failed Deploy goes red on the same candidate
  (so the case is a real failure shape, not a guard artefact).

A clean candidate must pass. The workflow test pins that the guard runs before
the commit/push step, which is what keeps main green.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import refresh_guard as guard  # noqa: E402

LINKED = ("tools", "editorial", "design", "site-src", "contracts", "config", "legal", "scaffold")
ROWS = 120  # corpus-count-ok: size of the fixture corpus slice (the guard only inspects counts >= 100)
STORIES = 6


def build_candidate(tmp: Path) -> Path:
    """A self-contained candidate tree: real code, a corpus slice, a Story-layer slice."""
    for name in LINKED:
        if (ROOT / name).exists():
            os.symlink(ROOT / name, tmp / name)
    shutil.copytree(ROOT / "i18n", tmp / "i18n", ignore=shutil.ignore_patterns("__pycache__"))
    (tmp / "tests/fixtures").mkdir(parents=True)
    shutil.copy(ROOT / "tests/fixtures/ui_enum_snapshot.json", tmp / "tests/fixtures/ui_enum_snapshot.json")
    for name in ("test_no_frozen_corpus_counts.py", "test_c6_design_contract.py"):
        shutil.copy(ROOT / "tests" / name, tmp / "tests" / name)
    (tmp / "corpus/data").mkdir(parents=True)
    (tmp / "site/data").mkdir(parents=True)
    rows = (ROOT / "corpus/data/developments.jsonl").read_text(encoding="utf-8").splitlines()[:ROWS]
    (tmp / "corpus/data/developments.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")
    doc = json.loads((ROOT / "site/data/stories.v2.json").read_text(encoding="utf-8"))
    doc["stories"] = doc["stories"][:STORIES]
    (tmp / "site/data/stories.v2.json").write_text(json.dumps(doc), encoding="utf-8")
    legacy = json.loads((ROOT / "site/data/stories.json").read_text(encoding="utf-8"))[:STORIES]
    (tmp / "site/data/stories.json").write_text(json.dumps(legacy), encoding="utf-8")
    shutil.copy(ROOT / "site/data/newsroom-status.json", tmp / "site/data/newsroom-status.json")
    return tmp


def errors(findings, check):
    return [f for f in findings if f["check"] == check and f["severity"] == "error"]


def unittest_in(root: Path, module: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "unittest", f"tests.{module}"], cwd=root, text=True,
                          capture_output=True, env=dict(os.environ, PYTHONPATH=str(root / "tests")))


class RefreshGuardBattery(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="refresh-guard-bat-")
        self.addCleanup(self._tmp.cleanup)
        self.root = build_candidate(Path(self._tmp.name))

    def edit_rows(self, mutate):
        path = self.root / "corpus/data/developments.jsonl"
        rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        mutate(rows)
        path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    def test_clean_candidate_passes_every_check(self):
        found = guard.run_checks(self.root)
        self.assertEqual([], [f for f in found if f["severity"] == "error"], found)

    def test_case1_story_count_equal_to_a_frozen_literal(self):
        # Today's record count appears as a literal in a count context in a test: correct for one day.
        (self.root / "tests/test_zz_frozen.py").write_text(
            "import unittest\nclass T(unittest.TestCase):\n    def test_n(self):\n"
            f"        self.assertEqual(len(rows), {ROWS})\n", encoding="utf-8")
        bad = errors(guard.run_checks(self.root, ["frozen_counts"]), "frozen_counts")
        self.assertEqual(1, len(bad), bad)
        self.assertIn("test_zz_frozen.py", bad[0]["message"])
        # Deploy's own gate is red on the same candidate.
        red = unittest_in(self.root, "test_no_frozen_corpus_counts")
        self.assertNotEqual(0, red.returncode, red.stderr[-400:])

    def test_case2_new_unlabelled_values_never_block_what_deploy_does_not_block(self):
        # A new region, desk and source language with no label, in a group with no generic fallback.
        def mutate(rows):
            rows[0]["regions"] = ["new-region-a", "New-Region-B"]
            rows[0]["source_languages"] = ["hi-new"]
            rows[0]["primary_desk"] = "a-desk-nobody-labelled-yet"
        self.edit_rows(mutate)
        for locale in ("en", "es-419", "zh-Hans"):
            path = self.root / f"i18n/ui/{locale}.json"
            catalog = json.loads(path.read_text(encoding="utf-8"))
            catalog["labels"]["region"].pop("other", None)
            catalog["labels"]["source_language"].pop("other", None)
            catalog["labels"]["desk"].pop("other", None)
            path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
        found = guard.run_checks(self.root, ["ui_labels"])
        self.assertEqual([], errors(found, "ui_labels"), found)
        for needle in ("labels.region.new-region-a", "labels.source_language.hi-new", "a-desk-nobody-labelled-yet"):
            self.assertTrue(any(f["severity"] == "warning" and needle in f["message"] for f in found), needle)
        # Deploy's label gate (frozen snapshot + contract enums) returns nothing for the same candidate.
        ulc = guard._import("tools.ui_label_coverage")
        gate = ulc.load_snapshot(self.root / "tests/fixtures/ui_enum_snapshot.json")
        gate.update(ulc.contract_enums(self.root))
        self.assertEqual([], [m for m in ulc.missing_labels(ulc.load_catalogs(self.root), gate)
                              if "a-desk-nobody" in m or "hi-new" in m or "new-region" in m])

    def test_case2c_a_label_the_deploy_gate_requires_going_missing_is_an_error(self):
        # The refresh cannot write i18n/ui, so this is a wiring proof: the guard runs Deploy's own gate.
        path = self.root / "i18n/ui/en.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        group = catalog["labels"]["desk"]
        victim = next(k for k in group if k != "other")
        del group[victim]
        path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
        bad = errors(guard.run_checks(self.root, ["ui_labels"]), "ui_labels")
        self.assertTrue(any(f"labels.desk.{victim}" in f["message"] for f in bad), bad)

    def test_case2b_new_region_with_the_generic_fallback_warns_but_does_not_block(self):
        self.edit_rows(lambda rows: rows[0].__setitem__("regions", ["a-region-nobody-labelled-yet"]))
        found = guard.run_checks(self.root, ["ui_labels"])
        self.assertEqual([], errors(found, "ui_labels"))
        self.assertTrue(any(f["severity"] == "warning" and "a-region-nobody-labelled-yet" in f["message"] for f in found))

    def test_case3_headline_with_a_verified_word(self):
        path = self.root / "site/data/stories.v2.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["stories"][0]["headline"] = "Machine-verified proofs land in the first release"
        path.write_text(json.dumps(doc), encoding="utf-8")
        # The newsroom's own words are exempt, so the candidate passes the scoped guard ...
        self.assertEqual([], errors(guard.run_checks(self.root, ["verified_headings"]), "verified_headings"))
        # ... and the unscoped guard that failed Deploy on 2026-10-23 is red on the same pages.
        i18n = guard._import("tools.paper.i18n")
        design = guard._import("tests.test_c6_design_contract")
        page = "<h1>Machine-verified proofs land in the first release</h1>"
        self.assertEqual(1, len(design.verified_chrome_headings(page, set())))
        self.assertEqual([], design.verified_chrome_headings(page, {i18n.headline(doc["stories"][0], "en", i18n.load_catalogs(self.root)["en"])}))

    def test_case3b_a_chrome_heading_that_says_verified_is_caught_in_a_built_page(self):
        pages = Path(self._tmp.name) / "pages"
        (pages / "a").mkdir(parents=True)
        (pages / "a/index.html").write_text("<h2>Recently verified</h2><h2>Claimed, not verified</h2>", encoding="utf-8")
        bad = guard.verified_headings_in_pages([pages / "a/index.html"], set())
        self.assertEqual(1, len(bad), bad)
        self.assertIn("Recently verified", bad[0])


class RefreshWorkflowOrder(unittest.TestCase):
    WORKFLOW = ROOT / ".github/workflows/daily-refresh.yml"

    @staticmethod
    def guard_precedes_push(text: str) -> bool:
        guard_at = text.find("tools/refresh_guard.py")
        push_at = text.find("git push origin HEAD:main")
        commit_at = text.find("git commit -m")
        return -1 < guard_at < commit_at < push_at

    def test_guard_runs_before_the_candidate_is_committed_or_pushed(self):
        self.assertTrue(self.guard_precedes_push(self.WORKFLOW.read_text(encoding="utf-8")))

    def test_the_old_workflow_shape_is_red(self):
        old = "run: python tests/oraculos/verificar_traduccion.py\n git commit -m x\n git push origin HEAD:main\n"
        self.assertFalse(self.guard_precedes_push(old))

    def test_guard_step_is_not_optional(self):
        text = self.WORKFLOW.read_text(encoding="utf-8")
        step = text[text.index("- name: Guard the candidate"):text.index("- name: Commit only what")]
        self.assertNotIn("continue-on-error", step)
        self.assertNotIn("|| true", step)
        self.assertIn("steps.preflight.outputs.path == 'rebuild' || steps.preflight.outputs.path == 'status'", step)

    def test_every_module_that_builds_the_paper_from_live_data_is_listed(self):
        # The in-process probe misses these (they build in a subprocess), so the static scan decides.
        inventory = guard._import("tools.data_dependent_tests")
        listed = {l.strip() for l in (ROOT / guard.MODULE_LIST).read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.lstrip().startswith("#")}
        browser_only = {"test_v4_mobile_first_viewport"}  # needs Chromium, installed only by Deploy
        not_live = {  # name the data files or build only as TEXT or as fixtures; reviewed one by one
            "test_agent_layer": "builds from tests/fixtures",
            "test_pages_workflow": "reads workflow text", "test_protected_publishing": "reads workflow text",
            "test_newswire_bridge_workflow": "reads workflow text", "test_refresh_guard": "this battery",
        }
        builders = {r["module"] for r in inventory.static_scan()
                    if any(x in r["data_refs"] for x in ("site/data", "stories.v2"))
                    and "tools/paper/build" in r["tool_refs"]}
        self.assertTrue({"test_c6_one_fcmo", "test_design_v2", "test_v4_localized_kickers"} <= builders, builders)
        self.assertEqual(set(), builders - listed - browser_only - set(not_live))

    def test_listed_modules_exist(self):
        listed = [l.strip() for l in (ROOT / guard.MODULE_LIST).read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.lstrip().startswith("#")]
        self.assertTrue(listed)
        for name in listed:
            self.assertTrue((ROOT / "tests" / f"{name}.py").is_file(), name)


class RefreshFailureDiagnostics(unittest.TestCase):
    def test_first_assertion_survives_a_later_long_diff_in_the_job_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir()
            (root / "tests/__init__.py").write_text("")
            (root / guard.MODULE_LIST).write_text("test_failure\n")
            (root / "tests/test_failure.py").write_text(
                "import unittest\nclass T(unittest.TestCase):\n"
                " def test_a_first(self):\n"
                "  self.assertEqual('CLAIMED', 'DEMONSTRATED', "
                "'FCMO-000000000001 es-419 claims[7].label')\n"
                " def test_z_long_diff(self):\n"
                "  self.maxDiff = None\n"
                "  self.assertEqual(list(range(80)), list(range(80, 160)))\n")
            findings = guard.run_modules(root, workers=1)
            self.assertEqual(len(findings), 1)
            annotations, count, summary = guard.render(findings)
            self.assertEqual(count, 1)
            for output in (annotations, summary):
                self.assertIn("test_a_first", output)
                self.assertIn("AssertionError", output)
                self.assertIn("FCMO-000000000001 es-419 claims[7].label", output)
            self.assertNotIn("test_z_long_diff", summary)
            target = root / "summary.md"
            with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(target)}), \
                    mock.patch.object(guard, "run_checks", return_value=[]), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(guard.main(["--root", str(root), "--tests"]), 1)
            self.assertEqual(target.read_text(), summary)

    def test_diagnostics_do_not_publish_private_failure_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir()
            (root / "tests/__init__.py").write_text("")
            (root / guard.MODULE_LIST).write_text("test_failure\n")
            sensitive = "github_pat_" + "x" * 30
            (root / "tests/test_failure.py").write_text(
                "import unittest\nclass T(unittest.TestCase):\n"
                f" def test_private(self): self.fail({sensitive!r})\n")
            annotations, count, summary = guard.render(guard.run_modules(root, workers=1))
            self.assertEqual(count, 1)
            for output in (annotations, summary):
                self.assertNotIn(sensitive, output)
                self.assertNotIn(str(root), output)
                self.assertIn("test_private", output)

    def test_import_errors_and_process_exit_without_unittest_are_explicit(self):
        private_path = str(Path(tempfile.gettempdir()) / "refresh-guard-private.py")
        imported = guard.first_failure(
            "ERROR: test_example (unittest.loader._FailedTest.test_example)\n" + "-" * 70 +
            f'\nTraceback (most recent call last):\n  File "{private_path}", line 1\n' +
            "ImportError: cannot import example\n\n" + "-" * 70 + "\nRan 1 test\n", 1)
        self.assertIn("test_example", imported)
        self.assertIn("ImportError: cannot import example", imported)
        self.assertNotIn(private_path, imported)
        self.assertIn("código 2", guard.first_failure("unstructured private process output", 2))

    def test_subtest_parameters_and_markdown_cannot_leak_or_escape_the_summary(self):
        token = "github_pat_" + "x" * 30
        diagnostic = guard.first_failure(
            f"FAIL: test_private (fixture.T.test_private) (token='{token}')\n" + "-" * 70 +
            "\nAssertionError: False is not true\n", 1)
        self.assertNotIn(token, diagnostic)
        finding = guard.Finding(check="module:test_private", severity="error", message=diagnostic + "\n</pre><script>x</script>")
        annotation, _, summary = guard.render([finding])
        self.assertNotIn("<script>", summary)
        self.assertIn("%0A", annotation)


if __name__ == "__main__":
    unittest.main()
