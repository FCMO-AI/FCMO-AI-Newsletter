"""The public brand boundary must reject the internal umbrella name."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.gates.common import GateFailure
from tools.gates import no_fcmo_group


class NoFcmoGroupGateTests(unittest.TestCase):
    def test_rejects_case_variants_in_built_html_and_api(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text("<title>FcMo GROUP</title>", encoding="utf-8")
            (root / "agent.json").write_text('{"brand":"FCMO Group"}', encoding="utf-8")
            with patch.object(no_fcmo_group, "SOURCE_ROOTS", ()):
                with self.assertRaises(GateFailure) as error:
                    no_fcmo_group.check(root)
            self.assertEqual(error.exception.code, "NO_FCMO_GROUP")
            self.assertTrue(any("index.html" in item for item in error.exception.problems))
            self.assertTrue(any("agent.json" in item for item in error.exception.problems))

    def test_scans_reader_facing_source_strings(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            (source / "ui.json").write_text('{"name":"FCMO\tGroup"}', encoding="utf-8")
            public = source / "public"
            public.mkdir()
            (public / "agent.json").write_text("{}", encoding="utf-8")
            with patch.object(no_fcmo_group, "ROOT", source), patch.object(no_fcmo_group, "SOURCE_ROOTS", ("ui.json",)):
                with self.assertRaises(GateFailure) as error:
                    no_fcmo_group.check(public)
            self.assertIn("source: ui.json:1", error.exception.problems)


if __name__ == "__main__":
    unittest.main()
