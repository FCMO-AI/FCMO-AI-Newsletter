from pathlib import Path
import tempfile
import unittest

from tools.verify_release import check_no_fcmo_group


class NoFcmoGroupTests(unittest.TestCase):
    def test_rejects_banned_name_in_reader_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "release-src"
            source.mkdir()
            (source / "index.html").write_text("<title>FCMO Group</title>", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "release-src/index.html"):
                check_no_fcmo_group(root / "publish", source_roots=(source,))

    def test_rejects_banned_name_in_assembled_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            publication = Path(temp) / "publish"
            publication.mkdir()
            (publication / "about.html").write_text("<p>FcMo GROUP</p>", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "about.html"):
                check_no_fcmo_group(publication, source_roots=())

    def test_allows_unrelated_text_and_names(self):
        with tempfile.TemporaryDirectory() as temp:
            publication = Path(temp) / "publish"
            publication.mkdir()
            (publication / "about.html").write_text("FCMO and FCMO AI Newsletter", encoding="utf-8")
            check_no_fcmo_group(publication, source_roots=())


if __name__ == "__main__":
    unittest.main()
