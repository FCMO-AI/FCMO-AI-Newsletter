from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / ".github" / "workflows" / "newswire-bridge.yml"


class PublicationSealGateTests(unittest.TestCase):
    def test_bridge_uses_private_publication_seal_not_broad_test_discovery(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        # Footnote: broad private unittest discovery couples reader availability to
        # unrelated agent/query/control-plane tests. ARB's explicit seal owns the
        # subset that can change public bytes or public semantics.
        self.assertIn("python tools/validate_publication_plane.py", text)
        self.assertNotIn("python -m unittest discover -s tests", text)

    def test_publication_seal_stays_inside_private_log_boundary(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        seal = text.index("python tools/validate_publication_plane.py")
        redirect = text.index('>"$PRIVATE_LOG" 2>&1', seal)
        cleanup = text.index('rm -f "$PRIVATE_LOG"', redirect)
        self.assertLess(seal, redirect)
        self.assertLess(redirect, cleanup)


if __name__ == "__main__":
    unittest.main()
