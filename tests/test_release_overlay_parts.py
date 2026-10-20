"""Payload parts retain numeric order once a release grows past 99 chunks."""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import apply_final_release, build_final_release


class ReleaseOverlayPartOrder(unittest.TestCase):
    def test_builder_and_assembler_order_one_hundred_parts_numerically(self):
        payload = bytes(range(75))
        encoded = base64.b64encode(payload).decode("ascii")
        self.assertEqual(len(encoded), 100)
        with tempfile.TemporaryDirectory() as temporary:
            overlay = Path(temporary)
            parts = overlay / "parts"
            parts.mkdir()
            for number, chunk in enumerate(encoded, 1):
                (parts / f"part-{number:02d}.b64").write_text(chunk, encoding="ascii")

            disk_parts, disk_encoded = build_final_release.disk_encoded_parts(overlay)
            self.assertEqual(len(disk_parts), 100)
            self.assertEqual(disk_encoded, encoded)

            manifest = {
                "parts": 100,
                "base64_sha256": hashlib.sha256(encoded.encode("ascii")).hexdigest(),
                "archive_sha256": hashlib.sha256(payload).hexdigest(),
            }
            with patch.object(apply_final_release, "OVERLAY", overlay):
                self.assertEqual(apply_final_release.reconstruct(manifest), payload)


if __name__ == "__main__":
    unittest.main()
