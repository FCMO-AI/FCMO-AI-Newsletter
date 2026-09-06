from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / ".github" / "workflows" / "newswire-bridge.yml"


class PublicationSealGateTests(unittest.TestCase):
    def test_bridge_uses_atomic_private_publication_seal_not_broad_test_discovery(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        # Footnote: broad private unittest discovery couples reader availability to
        # unrelated agent/query/control-plane tests. ARB's atomic publication seal
        # owns the exact dependency closure that can change public bytes or semantics.
        self.assertIn("python tools/publication_seal.py", text)
        self.assertNotIn("python -m unittest discover -s tests", text)
        # The bridge must not reimplement the private seal as a loose command list;
        # one upstream authority keeps validation/build semantics from drifting.
        for direct in (
            "python tools/validate_publication_plane.py",
            "python tools/build_publication.py --check-determinism",
            "python tools/build_public_locales.py build",
            "python tools/build_airlock_receipt.py",
        ):
            self.assertNotIn(direct, text)

    def test_publication_seal_stays_inside_private_log_boundary(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        seal = text.index("python tools/publication_seal.py")
        redirect = text.index('>"$PRIVATE_LOG" 2>&1', seal)
        safe_reason = text.index("grep -E '^SEAL_FAIL:[A-Z0-9_]+'", redirect)
        cleanup = text.index('rm -f "$PRIVATE_LOG"', safe_reason)
        self.assertLess(seal, redirect)
        self.assertLess(redirect, safe_reason)
        self.assertLess(safe_reason, cleanup)


if __name__ == "__main__":
    unittest.main()
