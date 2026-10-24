#!/usr/bin/env python3
"""Inventory the tests whose outcome depends on the live corpus or release data.

A test module is data-dependent when it reads the files the hourly refresh
rewrites (corpus/, site/data/, release-src/, release-overlay/, READY_TO_PUBLISH.md)
instead of its own fixtures, or when it runs a tool/build over them.

Two signals, deliberately independent:

* ``--static``  reads each tests/test_*.py and looks for those paths (and for
  the tools that consume them). Cheap, over-approximate.
* ``--probe MODULE...``  runs each module in a child process under a Python
  audit hook and records which data files it really opened. Under-approximate
  for subprocesses (reported as ``spawns``), exact for in-process reads.

Output is JSON on stdout. The refresh guard (tools/refresh_guard.py) runs the
list in tests/refresh_guard_modules.txt, which is curated from this inventory.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOTS = ("corpus/", "site/data/", "release-src/", "release-overlay/", "READY_TO_PUBLISH.md")
STATIC = re.compile(
    r"corpus/|\"corpus\"|'corpus'|site/data|stories\.v2|developments\.jsonl|release-src|release-overlay|"
    r"READY_TO_PUBLISH|/ [\"']site[\"']|ROOT / [\"']site[\"']")
TOOLS = re.compile(r"tools/paper/build|tools[/.]gates|run_all|story_layer|ingest_corpus|verify_release|ui_label_coverage")

_HOOK = r"""
import json, sys, unittest
from pathlib import Path
root = Path(sys.argv[1]).resolve(); mod = sys.argv[2]
roots = tuple(str(root / r) for r in %r)
seen = set(); spawns = [0]
def hook(event, args):
    if event == "open" and isinstance(args[0], str):
        p = str(Path(args[0]).resolve()) if not args[0].startswith("/") else args[0]
        if p.startswith(roots): seen.add(str(Path(p).relative_to(root)).split("/")[0] + "/" + (str(Path(p).relative_to(root)).split("/")[1] if "/" in str(Path(p).relative_to(root)) else ""))
    elif event == "subprocess.Popen": spawns[0] += 1
sys.addaudithook(hook)
sys.path[:0] = [str(root), str(root / "tests")]
suite = unittest.defaultTestLoader.loadTestsFromName(mod)
res = unittest.TextTestRunner(stream=open("/dev/null", "w")).run(suite)
print(json.dumps({"module": mod, "tests": res.testsRun, "ok": res.wasSuccessful(), "reads": sorted(seen), "spawns": spawns[0]}))
""" % (DATA_ROOTS,)


def static_scan(root: Path = ROOT) -> list[dict]:
    rows = []
    for path in sorted((root / "tests").glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        data = sorted({m.group(0) for m in STATIC.finditer(text)})
        tools = sorted({m.group(0) for m in TOOLS.finditer(text)})
        if data or tools:
            rows.append({"module": path.stem, "data_refs": data, "tool_refs": tools})
    return rows


def probe(module: str, root: Path = ROOT, timeout: int = 600) -> dict:
    try:
        out = subprocess.run([sys.executable, "-c", _HOOK, str(root), f"tests.{module}"], cwd=root,
                             capture_output=True, text=True, timeout=timeout)
        return json.loads(out.stdout.strip().splitlines()[-1])
    except Exception as exc:  # report, never hide
        return {"module": module, "error": f"{type(exc).__name__}: {exc}"[:200]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--static", action="store_true")
    ap.add_argument("--probe", nargs="+", metavar="MODULE")
    args = ap.parse_args(argv)
    result: dict = {}
    if args.static or not args.probe:
        result["static"] = static_scan()
    if args.probe:
        result["probe"] = [probe(m) for m in args.probe]
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
