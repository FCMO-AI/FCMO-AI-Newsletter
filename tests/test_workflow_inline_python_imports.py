"""Inline `shell: python` steps run from a temp file, so repo imports need PYTHONPATH."""
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class InlinePythonImports(unittest.TestCase):
    def test_inline_python_importing_repo_modules_sets_pythonpath(self):
        offenders = []
        for wf in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
            doc = yaml.safe_load(wf.read_text(encoding="utf-8")) or {}
            for job_name, job in (doc.get("jobs") or {}).items():
                for step in job.get("steps") or []:
                    if step.get("shell") != "python":
                        continue
                    body = step.get("run") or ""
                    if "from tools" not in body and "import tools" not in body:
                        continue
                    env = {**(job.get("env") or {}), **(step.get("env") or {})}
                    if "github.workspace" not in str(env.get("PYTHONPATH", "")):
                        offenders.append(f"{wf.name}:{job_name}:{step.get('name')}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
