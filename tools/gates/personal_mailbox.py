from __future__ import annotations

import re
from pathlib import Path

from .common import GateFailure, GateResult, fail, public_files, rel

CODE = "PERSONAL_MAILBOX"
CONSUMER = "(?:g" + "mail|out" + "look|hot" + "mail|proton" + "mail)"
ADDRESS = re.compile(r"\b[A-Z0-9._%+-]+@" + CONSUMER + r"\.[A-Z]{2,}\b", re.I)
PRIVATE_PATTERNS = (
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"/(?:home/runner/work|srv/fcmo/agents)/"),
    re.compile(r"\b(?:INTERNAL_ONLY|DO_NOT_PUBLISH|PRIVATE_RESEARCH)\b"),
)


def check(root: Path) -> GateResult:
    files = public_files(root)
    problems = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        match = ADDRESS.search(text)
        if match:
            problems.append(f"{rel(root, path)}: personal consumer mailbox detected")
        for pattern in PRIVATE_PATTERNS:
            if pattern.search(text):
                problems.append(f"{rel(root, path)}: credential/private marker detected")
                break
    fail(CODE, problems)
    return GateResult(CODE, len(files))


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    try: result = check(args.root)
    except GateFailure as exc: raise SystemExit(f"{exc.code} FAIL: {'; '.join(exc.problems)}") from exc
    print(f"{result.code} PASS ({result.checked} files)"); return 0


if __name__ == "__main__": raise SystemExit(main())
