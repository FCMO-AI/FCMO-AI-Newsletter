"""Public workflow output is an independent ARB privacy boundary.

No YAML dependency: only literal run blocks are admitted in ARB workflows.
Fixtures execute the actual shell blocks, with synthetic tools and no network.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
SILENCE = (
    "set +x\n"
    "exec 3>&1 >/dev/null 2>&1\n"
    "trap 'rc=$?; printf \"step_exit=%s\\n\" \"$rc\" >&3' EXIT\n"
)


def run_blocks(text: str) -> list[str]:
    lines = text.splitlines()
    blocks = []
    for i, line in enumerate(lines):
        match = re.match(r"^(\s*)(?:- )?run:\s*(.*)$", line)
        if not match:
            continue
        indent, value = match.groups()
        if line.lstrip().startswith('- run:'):
            indent += '  '
        if value != "|":
            blocks.append(value + "\n")
            continue
        body = []
        for following in lines[i + 1:]:
            if following.strip() and len(following) - len(following.lstrip()) <= len(indent):
                break
            body.append(following[len(indent) + 2:])
        blocks.append("\n".join(body).rstrip() + "\n")
    return blocks


def privacy_errors(text: str) -> list[str]:
    """Fail closed for every shell step in a workflow that can materialize ARB.

    Whole-step suppression also covers git/cp/read failures, rejected candidates,
    command substitutions, echo/cat/tee and new diagnostics added to a step.
    Only the numeric EXIT receipt may use the saved public descriptor.
    """
    errors = []
    if not re.search(r"AI-Research-Breakthroughs|fcmo-(?:newswire-private|arb-)", text):
        return errors
    for forbidden in (r"GITHUB_STEP_SUMMARY", r"ACTIONS_STEP_DEBUG", r"\bcache:",
                      r"uses:\s*[^\s]*?(?:artifact|cache)[^\s]*", r"repository:\s*.*AI-Research-Breakthroughs"):
        if re.search(forbidden, text, re.I):
            errors.append("public persistence or private checkout action")
    refs = re.findall(r"uses:\s*(\S+)([^\n]*)", text)
    for ref, comment in refs:
        if ref.split('@')[0] not in {
            'actions/checkout', 'actions/setup-python', 'actions/create-github-app-token'
        }:
            errors.append("unreviewed action can expose the private checkout")
        if not re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", ref) or not re.search(r"# v\d", comment):
            errors.append("action must have a full SHA and version comment")
    blocks = run_blocks(text)
    if not blocks:
        errors.append("missing literal shell steps")
    for block in blocks:
        if not block.startswith(SILENCE):
            errors.append("shell step exposes stdout/stderr (including failure paths)")
            continue
        body = block[len(SILENCE):]
        # Only these numeric receipts may use the saved public descriptor.
        body = body.replace("  printf 'probe_exit=%d\\n' \"$rc\" >&3\n", "")
        body = body.replace("printf 'probe_failures=%d\\n' \"$failures\" >&3\n", "")
        body = body.replace("printf 'RELEASE_DIR=%s\\n' \"$RELEASE_DIR\" >> \"$GITHUB_ENV\"\n", "")
        # Only fixed runner-temporary paths and a validated stage boolean may escape.
        body = body.replace('printf \'CODES=%s\\n\' "$CODES" >> "$GITHUB_ENV"\n', "")
        body = body.replace('case "$GUARD_STAGE" in true|false) printf \'stage=%s\\n\' "$GUARD_STAGE" >> "$GITHUB_OUTPUT" ;; *) exit 1 ;; esac\n', "")
        # Probe heredoc rows are data for the isolated bash child, not executed here.
        body = re.sub(r"(?m)^(?:INTEGRITY_RATCHET|TEST_SUITE|OPERATIONAL_PROBES|NATIVE_EDITION_COVERAGE)\|python [^\n]+\n", "", body)
        if re.search(r"GITHUB_(?:ENV|OUTPUT|PATH)", body):
            errors.append("shell step exports candidate/private bytes to runner channels")
        if re.search(r"(?:[>&]\s*3\b|/dev/(?:stdout|stderr|fd)|/proc/[^\s]*/fd|\bexec\b|set\s+-[^\n]*x)", body):
            errors.append("shell step reopens a public output channel")
        # Candidate/private programs must not inherit the saved log descriptor.
        for line in body.splitlines():
            if re.search(r"\bpython\b|bash -o pipefail", line) and not line.lstrip().startswith(("#", '"python', "import ", "from ")):
                if "3>&-" not in line:
                    errors.append("child process inherits public descriptor")
    return errors


class ArbWorkflowPrivacyTests(unittest.TestCase):
    def test_all_arb_workflows_have_no_public_diagnostic_or_persistence_channel(self):
        for path in sorted(WORKFLOWS.glob("*.y*ml")):
            with self.subTest(workflow=path.name):
                self.assertEqual(privacy_errors(path.read_text()), [])

    def test_retired_backfill_cannot_return_as_a_public_workflow(self):
        self.assertFalse((WORKFLOWS / 'backfill-arb-native-locales-once.yml').exists())

    def test_actual_shell_blocks_have_valid_bash_syntax(self):
        for path in WORKFLOWS.glob('*.y*ml'):
            if 'AI-Research-Breakthroughs' not in path.read_text():
                continue
            for block in run_blocks(path.read_text()):
                result = subprocess.run(['bash', '-n'], input=block, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_guard_exports_only_a_boolean_after_isolating_candidate_output(self):
        block = next(block for block in run_blocks((WORKFLOWS / 'newswire-bridge.yml').read_text())
                     if 'GUARD_STAGE=' in block)
        marker = 'PRIVATE_FIXTURE_QUESTION_NEXT_STEP_BLOB_SHA'
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'codes').mkdir()
            (root / 'bin').mkdir()
            fake = root / 'bin/python'
            fake.write_text(r"""#!/usr/bin/python3
import os, pathlib, sys
marker = 'PRIVATE_FIXTURE_QUESTION_NEXT_STEP_BLOB_SHA'
print(marker)
print(marker, file=sys.stderr)
try:
    os.write(3, marker.encode())
except OSError:
    pass
for key in ('GITHUB_ENV', 'GITHUB_OUTPUT', 'GITHUB_STEP_SUMMARY'):
    if key in os.environ:
        pathlib.Path(os.environ[key]).write_text(marker)
path = pathlib.Path(sys.argv[sys.argv.index('--github-output') + 1])
path.write_text('stage=' + pathlib.Path(os.environ['HOME'], 'stage').read_text() + '\n')
""")
            fake.chmod(0o755)
            env = dict(os.environ, PATH=str(root / 'bin') + os.pathsep + os.environ['PATH'],
                       HOME=str(root), RUNNER_TEMP=str(root), CODES=str(root / 'codes'),
                       RELEASE_DIR=str(root / 'candidate'), FCMO_DRILL='')
            for key in ('GITHUB_ENV', 'GITHUB_OUTPUT', 'GITHUB_STEP_SUMMARY'):
                env[key] = str(root / key)
            for value in ('true', 'false', marker, 'true\nstage=false'):
                (root / 'stage').write_text(value)
                for key in ('GITHUB_ENV', 'GITHUB_OUTPUT', 'GITHUB_STEP_SUMMARY'):
                    Path(env[key]).write_text('')
                result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', block],
                                        cwd=root, env=env, text=True, capture_output=True)
                valid = value in ('true', 'false')
                with self.subTest(value=value):
                    self.assertEqual(result.returncode, 0 if valid else 1)
                    self.assertEqual(result.stdout, f'step_exit={result.returncode}\n')
                    self.assertEqual(result.stderr, '')
                    self.assertEqual(Path(env['GITHUB_OUTPUT']).read_text(), f'stage={value}\n' if valid else '')
                    for key in ('GITHUB_ENV', 'GITHUB_STEP_SUMMARY'):
                        self.assertEqual(Path(env[key]).read_text(), '')

    def test_guard_rejects_output_and_upload_regressions(self):
        good = "name: synthetic\n# AI-Research-Breakthroughs\nsteps:\n  - run: |\n" + "".join(
            "      " + line + "\n" for line in (SILENCE + "true\n").splitlines())
        self.assertEqual(privacy_errors(good), [])
        for mutation in (
            good.replace(" 2>&1", ""), good.replace("set +x", "set -x"),
            good.replace("      true", '      cat "$PRIVATE_LOG" >&3'),
            good.replace("      true", '      echo "$PRIVATE_SHA" >&3'),
            good.replace("      true", '      tee /dev/stderr < "$PRIVATE_LOG"'),
            good + "  - uses: actions/upload-artifact@v4\n    if: always()\n",
            good + "  - uses: actions/cache@v4\n", good + "# GITHUB_STEP_SUMMARY\n",
            good + "  - uses: third-party/dump@" + 'a' * 40 + " # v1\n",
            good.replace("      true", '      cat "$PRIVATE_LOG" >> "$GITHUB_OUTPUT"'),
            good.replace("      true", '      echo "$PRIVATE_SHA" >> "$GITHUB_ENV"'),
            good.replace("      true", "      python tools/arb.py orient --json"),
        ):
            with self.subTest(mutation=mutation):
                self.assertTrue(privacy_errors(mutation))

    def test_actual_private_steps_discard_synthetic_success_failure_and_exception_output(self):
        # Public marker intentionally includes workflow commands and a forged
        # SEAL_FAIL line: neither line may be promoted as a sanitized reason.
        marker = "PRIVATE_FIXTURE_QUESTION_NEXT_STEP_BLOB_SHA"
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            binary = root / "bin"
            binary.mkdir()
            fake_python = binary / "python"
            fake_python.write_text("""#!/usr/bin/env python3
import os, pathlib, sys
if sys.argv[1:] == ['-']:
    exec(sys.stdin.read())
    raise SystemExit(0)
print(os.environ.get('FIXTURE_MARKER', 'PRIVATE_FIXTURE_QUESTION_NEXT_STEP_BLOB_SHA'))
print('::warning::PRIVATE_FIXTURE_QUESTION_NEXT_STEP_BLOB_SHA', file=sys.stderr)
print('SEAL_FAIL:PRIVATE_FIXTURE_QUESTION_NEXT_STEP_BLOB_SHA')
for key in ('GITHUB_STEP_SUMMARY', 'GITHUB_ENV', 'GITHUB_OUTPUT'):
    if key in os.environ:
        pathlib.Path(os.environ[key]).write_text('PRIVATE_FIXTURE_QUESTION_NEXT_STEP_BLOB_SHA')
try:
    os.write(3, b'PRIVATE_FIXTURE_QUESTION_NEXT_STEP_BLOB_SHA')
except OSError:
    pass
mode = pathlib.Path(os.environ['HOME'], 'fixture-mode').read_text()
if mode == 'exception':
    raise RuntimeError('PRIVATE_FIXTURE_QUESTION_NEXT_STEP_BLOB_SHA')
if mode == 'failure':
    raise SystemExit(7)
print('SEAL_OK')
""")
            fake_python.chmod(0o755)
            fake_git = binary / "git"
            fake_git.write_text("""#!/usr/bin/env python3
import json, pathlib, sys
if pathlib.Path(__import__('os').environ['HOME'], 'fixture-mode').read_text() == 'git-failure':
    print('PRIVATE_FIXTURE_QUESTION_NEXT_STEP_BLOB_SHA', file=sys.stderr)
    raise SystemExit(23)
if 'clone' in sys.argv:
    root = pathlib.Path(sys.argv[-1])
    (root / 'state').mkdir(parents=True, exist_ok=True)
    (root / 'state' / 'PUBLICATION_READY.json').write_text(json.dumps({
        'schema': 'arb-publication-ready-v1', 'state': 'READY',
        'policy': 'immutable-sealed-snapshot', 'source_commit': 'a' * 40}))
print('PRIVATE_FIXTURE_QUESTION_NEXT_STEP_BLOB_SHA', file=sys.stderr)
if 'rev-parse' in sys.argv:
    print('a' * 40)
""")
            fake_git.chmod(0o755)
            env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ['PATH'],
                       RUNNER_TEMP=str(root), HOME=str(root), APP_TOKEN='synthetic-test-token', FCMO_DRILL='', CODES=str(root / 'codes'))
            (root / 'codes').mkdir()
            for key in ('GITHUB_STEP_SUMMARY', 'GITHUB_ENV', 'GITHUB_OUTPUT'):
                env[key] = str(root / key)
                Path(env[key]).touch()
            for mode in ('success', 'failure', 'exception', 'git-failure'):
                (root / 'fixture-mode').write_text(mode)
                env['RELEASE_DIR'] = str(root / 'fcmo-newswire-airlocked-release')
                for workflow in ('newswire-bridge.yml', 'translation-source-health.yml'):
                    for block in run_blocks((WORKFLOWS / workflow).read_text()):
                        # Run private selection, probes, seal, health and the first
                        # public verifier (the rejected candidate is still tainted).
                        if not any(token in block for token in (
                                'tools/publication_seal.py', 'tools/arb.py',
                                'tools/build_publication.py',
                                'newswire_bridge_partial_locales.py verify "$RELEASE_DIR"',
                                'clone --quiet')):
                            continue
                        # Do not execute promotion/reset/staging blocks.
                        if 'git reset' in block or 'git push' in block:
                            continue
                        for name in ('fcmo-newswire-private-source', 'fcmo-arb-translation-health'):
                            source = root / name
                            (source / 'state').mkdir(parents=True, exist_ok=True)
                            (source / 'state' / 'PUBLICATION_READY.json').write_text(json.dumps({
                                'schema': 'arb-publication-ready-v1', 'state': 'READY',
                                'policy': 'immutable-sealed-snapshot', 'source_commit': 'a' * 40}))
                        (root / 'fcmo-newswire-private-source.sha').write_text('a' * 40 + '\n')
                        for key in ('GITHUB_STEP_SUMMARY', 'GITHUB_ENV', 'GITHUB_OUTPUT'):
                            Path(env[key]).write_text('')
                        with self.subTest(workflow=workflow, mode=mode, command=block[:50]):
                            result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', block],
                                                    env=env, cwd=root, capture_output=True, text=True, timeout=15)
                            self.assertNotIn(marker, result.stdout + result.stderr)
                            self.assertEqual(result.stderr, '')
                            if mode == 'success':
                                self.assertEqual(result.returncode, 0, result.stdout)
                            if mode == 'git-failure' and 'git ' in block:
                                self.assertNotEqual(result.returncode, 0)
                            self.assertRegex(result.stdout, r'^(?:probe_exit=\d+\n)*(?:probe_failures=\d+\n)?step_exit=\d+\n$')
                            for key in ('GITHUB_STEP_SUMMARY', 'GITHUB_ENV', 'GITHUB_OUTPUT'):
                                self.assertNotIn(marker, Path(env[key]).read_text())
                            for receipt in (root / 'codes').glob('*'):
                                if receipt.is_file():
                                    self.assertNotIn(marker, receipt.read_text())


if __name__ == '__main__':
    unittest.main()
