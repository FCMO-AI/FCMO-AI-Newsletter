#!/usr/bin/env python3
"""Pre-push guard for the autonomous refresh: the day's data must not break the deploy.

The refresh builds the candidate release in the working tree and pushes it to
main. Deploy (pages.yml) then runs the full regression suite on that exact tree.
Three failures on 2026-10-23 were caused by DATA the refresh had just brought in
(a story count equal to a literal in a test, a region value with no label, a
story headline that tripped a heading guard), and each was found only after main
had already moved. This tool runs the data-dependent gates on the candidate
BEFORE the commit/push step, so a bad candidate never reaches main.

Checks (each takes a repository root, so the battery can aim it at a fixture):

* ``frozen_counts``   no test freezes a current corpus quantity
                      (same function as tests/test_no_frozen_corpus_counts.py).
* ``ui_labels``       every reader-facing enum value in the candidate renders
                      through a catalog label or the generic ``other`` fallback.
                      A value with no label AND no fallback is a failure; a value
                      that merely uses the fallback is a warning (readers are safe).
* ``verified_headings`` build the paper from the candidate Story layer and check
                      every home and story page for a chrome heading that says
                      «verified» (same function as tests/test_c6_design_contract.py).

Containment choice: FAIL BEFORE PUSH, never hold back single stories. The refresh
cannot hold a story by itself: holds come from the airlocked corpus (quarantine,
tombstones), which this workflow is not allowed to write, and two of the three
shapes are not about a story at all. Failing keeps main and Pages on the last
good release; operator-alerts.yml opens an issue after two consecutive failures.

``--tests`` also runs the data-dependent unittest modules listed in
tests/refresh_guard_modules.txt (one module name per line).
"""
from __future__ import annotations

import argparse
import html
import importlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "/FCMO-AI-Newsletter/"
LOCALES = ("en", "es-419", "zh-Hans")
MODULE_LIST = "tests/refresh_guard_modules.txt"
FALLBACK_LABEL = "other"


class Finding(dict):
    """{'check', 'severity': 'error'|'warning', 'message'}"""


def _import(name: str):
    """Import checked-in code. The code under test is this repository's own; ``root`` only selects the DATA."""
    for entry in (str(ROOT), str(ROOT / "tests")):
        if entry not in sys.path:
            sys.path.insert(0, entry)
    return importlib.import_module(name)


def frozen_counts(root: Path) -> list[Finding]:
    module = _import("tests.test_no_frozen_corpus_counts")
    return [Finding(check="frozen_counts", severity="error", message=line) for line in module.find_frozen(root)]


def ui_labels(root: Path) -> list[Finding]:
    ulc = _import("tools.ui_label_coverage")
    observed = ulc.observed_live(root)
    catalogs = ulc.load_catalogs(root)
    findings = []
    for locale in ulc.LOCALES:
        labels = catalogs[locale]["labels"]
        for group, codes in observed.items():
            for code in sorted(codes):
                if code in labels.get(group, {}):
                    continue
                if labels.get(group, {}).get(FALLBACK_LABEL):
                    findings.append(Finding(check="ui_labels", severity="warning",
                                            message=f"{locale}: labels.{group}.{code} missing, renders the generic label"))
                else:
                    findings.append(Finding(check="ui_labels", severity="error",
                                            message=f"{locale}: labels.{group}.{code} missing and labels.{group}.{FALLBACK_LABEL} "
                                                    "has no generic fallback: readers would see the raw code or nothing"))
    return findings


def verified_headings_in_pages(pages: list[Path], headlines: set[str]) -> list[str]:
    design = importlib.import_module("tests.test_c6_design_contract")
    bad = []
    for page in pages:
        for text in design.verified_chrome_headings(page.read_text(encoding="utf-8", errors="replace"), headlines):
            bad.append(f"{page.name if page.name != 'index.html' else page.parent.name}: {text[:80]!r}")
    return bad


def verified_headings(root: Path) -> list[Finding]:
    _import("tests.test_c6_design_contract")
    i18n = _import("tools.paper.i18n")
    stories = json.loads((root / "site/data/stories.v2.json").read_text(encoding="utf-8"))["stories"]
    catalogs = i18n.load_catalogs(root)
    headlines = {i18n.headline(story, code, catalog) for story in stories for code, catalog in catalogs.items()}
    with tempfile.TemporaryDirectory(prefix="refresh-guard-") as tmp:
        out = Path(tmp) / "site"
        built = subprocess.run([sys.executable, str(root / "tools/paper/build.py"),
                                "--stories", str(root / "site/data/stories.v2.json"),
                                "--status", str(root / "site/data/newsroom-status.json"),
                                "--editorial", str(root / "editorial"), "--out", str(out), "--base", BASE],
                               cwd=root, text=True, capture_output=True)
        if built.returncode:
            return [Finding(check="verified_headings", severity="error",
                            message="the paper build failed on the candidate: " + (built.stderr or built.stdout)[-300:])]
        routes = json.loads((out / "data/routes.json").read_text(encoding="utf-8"))
        pages = [out / prefix / "index.html" for prefix in ("", "es", "zh")]
        pages += [out / row["path"] / "index.html" for row in routes if row["kind"] == "story"]
        bad = verified_headings_in_pages([p for p in pages if p.is_file()], headlines)
    return [Finding(check="verified_headings", severity="error", message="verified-as-heading: " + b) for b in bad]


CHECKS = {"frozen_counts": frozen_counts, "ui_labels": ui_labels, "verified_headings": verified_headings}


def run_checks(root: Path, names=None) -> list[Finding]:
    findings: list[Finding] = []
    for name in names or CHECKS:
        findings.extend(CHECKS[name](root))
    return findings


def run_modules(root: Path, workers: int = 4) -> list[Finding]:
    """Run each listed module in its own process, ``workers`` at a time (the slowest sets the wall time)."""
    from concurrent.futures import ThreadPoolExecutor

    listed = [l.strip() for l in (root / MODULE_LIST).read_text(encoding="utf-8").splitlines()
              if l.strip() and not l.lstrip().startswith("#")]
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(filter(None, [str(root / "tests"), os.environ.get("PYTHONPATH", "")])))

    def one(module: str) -> Finding | None:
        done = subprocess.run([sys.executable, "-m", "unittest", f"tests.{module}"], cwd=root, text=True,
                              capture_output=True, env=env)
        if done.returncode == 0:
            return None
        tail = "\n".join(done.stderr.strip().splitlines()[-25:])
        return Finding(check=f"module:{module}", severity="error",
                       message=f"{module} failed on the candidate:\n{tail}")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return [f for f in pool.map(one, listed) if f]


def render(findings: list[Finding]) -> tuple[str, int, str]:
    errors = [f for f in findings if f["severity"] == "error"]
    lines = []
    for f in findings:
        level = "error" if f["severity"] == "error" else "warning"
        lines.append(f"::{level} title=Refresh guard {f['check']}::{f['message'].splitlines()[0]}")
    summary = ["## Refresh guard", ""]
    if not errors:
        summary.append("The candidate release passed every data-dependent gate." + (f" {len(findings)} warning(s)." if findings else ""))
    else:
        summary += ["**The candidate release was NOT pushed.** Main and the live site stay on the last good release.", ""]
    summary += [f"- `{f['check']}` ({f['severity']}): {f['message']}" for f in findings[:50]]
    return "\n".join(lines) + "\n", len(errors), "\n".join(summary) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--check", action="append", choices=sorted(CHECKS))
    ap.add_argument("--tests", action="store_true", help="also run the data-dependent unittest modules")
    args = ap.parse_args(argv)
    findings = run_checks(args.root.resolve(), args.check)
    if args.tests:
        findings += run_modules(args.root.resolve())
    annotations, errors, summary = render(findings)
    sys.stdout.write(annotations)
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a", encoding="utf-8") as fh:
            fh.write(summary)
    else:
        sys.stdout.write(summary)
    if errors:
        print(f"refresh guard: {errors} error(s); the candidate must not be pushed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
