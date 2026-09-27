#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.gates import (binding_complete, english_leak, glossary_consistency,
                         id_set_equality, locale_complete, personal_mailbox,
                         remote_script, size_budget)
from tools.gates.common import GateFailure, GateResult

GATES = (
    id_set_equality.check,
    binding_complete.check,
    remote_script.check,
    personal_mailbox.check,
    english_leak.check,
    locale_complete.check,
    size_budget.check,
    glossary_consistency.check,
)


def run(root: Path) -> list[GateResult]:
    if not root.is_dir(): raise GateFailure("PUBLICATION_ROOT", [f"not a directory: {root}"])
    results = []
    for gate in GATES: results.append(gate(root))
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run every deterministic pre-deploy publication gate.")
    parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    try: results = run(args.root)
    except GateFailure as exc:
        print(f"GATE FAIL [{exc.code}]", file=sys.stderr)
        for problem in exc.problems: print(f"- {problem}", file=sys.stderr)
        return 1
    for result in results:
        for warning in result.warnings: print(f"{result.code} WARN: {warning}")
        print(f"{result.code} PASS ({result.checked})")
    print(f"GATES PASS ({len(results)}/{len(GATES)})")
    return 0


if __name__ == "__main__": raise SystemExit(main())
