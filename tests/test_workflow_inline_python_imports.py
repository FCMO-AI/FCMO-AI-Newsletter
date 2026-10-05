"""Inline `shell: python` steps run from a temp file, so repo imports need PYTHONPATH."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP = re.compile(r"^(\s*)- name:", re.M)


def steps(text):
    starts = [m.start() for m in STEP.finditer(text)] + [len(text)]
    return [text[a:b] for a, b in zip(starts, starts[1:])]


class InlinePythonImports(unittest.TestCase):
    def test_inline_python_importing_repo_modules_sets_pythonpath(self):
        offenders = []
        for wf in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
            for step in steps(wf.read_text(encoding="utf-8")):
                if not re.search(r"^\s*shell:\s*python\s*$", step, re.M):
                    continue
                if not re.search(r"^\s*(from tools[.\s]|import tools\b)", step, re.M):
                    continue
                if not re.search(r"^\s*PYTHONPATH:\s*\$\{\{\s*github\.workspace\s*\}\}", step, re.M):
                    offenders.append(f"{wf.name}: {step.splitlines()[0].strip()}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
