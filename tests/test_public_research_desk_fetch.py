import http.client
import unittest
from unittest import mock

from tools import public_research_desk as desk


class _TruncatedResponse:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, *_args):
        raise http.client.IncompleteRead(b"")


class FetchSourceTest(unittest.TestCase):
    def test_truncated_chunked_body_marks_source_unreachable(self):
        # 2026-10-27: a truncated chunked response raised IncompleteRead and
        # aborted the daily refresh in "Re-research the stories".
        with mock.patch.object(desk.urllib.request, "urlopen", return_value=_TruncatedResponse()):
            result = desk.fetch_source("https://example.org/source")
        self.assertEqual(result, {"url": "https://example.org/source", "reachable": False, "error": "IncompleteRead"})


if __name__ == "__main__":
    unittest.main()
