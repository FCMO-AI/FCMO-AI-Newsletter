"""Distinguish relative QA labels from machine paths without rewriting history."""

from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.gates.common import GateFailure
from tools.gates.no_machine_paths import check_repo


class MachinePathBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.note = self.repo / "qa.json"
        self.note.write_text("{}", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "qa.json"], check=True)

    def test_relative_qa_check_names_are_not_absolute_machine_paths(self):
        # This wording comes from the publication desk's historical QA receipt.
        self.note.write_text('"CI Chrome 153 passed DOM/ho' + 'me/layout/editorial browser QA on candidate"', encoding="utf-8")
        self.assertEqual(check_repo(self.repo).code, "NO_MACHINE_PATHS")

    def test_absolute_home_paths_still_fail_in_text_json_html_and_file_uris(self):
        path = "/ho" + "me/operator/checkout"
        for text in (path, "path=" + path, '"path":"' + path + '"',
                     '<a href="' + path + '">', "file://" + path,
                     "workspace: " + path):
            with self.subTest(text=text):
                self.note.write_text(text, encoding="utf-8")
                with self.assertRaises(GateFailure) as caught:
                    check_repo(self.repo)
                self.assertEqual(caught.exception.code, "NO_MACHINE_PATHS")
                self.assertEqual(caught.exception.problems, ("qa.json: contains forbidden home path",))


if __name__ == "__main__":
    unittest.main()
