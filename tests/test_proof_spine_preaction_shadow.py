#!/usr/bin/env python3
"""Focused regressions for the evidence-only pre-action shadow receipt."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent / "tools"
SPEC = importlib.util.spec_from_file_location(
    "proof_spine_preaction_shadow_receipt",
    TOOLS / "proof_spine_preaction_shadow_receipt.py",
)
shadow = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(TOOLS))
sys.modules[SPEC.name] = shadow
SPEC.loader.exec_module(shadow)


def integrity(*, canonical: int, complete: int, pending: list[str]) -> dict:
    return {
        "schema": "fcmo-locale-integrity-v3",
        "canonical_story_count": canonical,
        "native_complete_story_count": complete,
        "pending_translation_count": len(pending),
        "pending_translation_ids": pending,
        "required_locales": ["es-419", "zh-Hans"],
        "state": "COMPLETE" if not pending else "DEGRADED_TRANSLATION_BACKLOG",
        "network_translation": False,
        "human_reviewed": False,
    }


# Footnote: an evidence adapter may report completeness, but it must not invent a
# Proof Spine VALID state or deploy permission. COMPLETE is deliberately project-local
# observation vocabulary consumed later by a separately reviewed contract.
def test_complete_integrity_stays_observational():
    result = shadow.classify_integrity_receipt(integrity(canonical=43, complete=43, pending=[]))
    assert result["state"] == "COMPLETE"
    assert result["pending_translation_count"] == 0
    assert "VALID" not in result.values()


# Footnote: the real field discriminator is one canonical Story missing both native
# editions. Preserve the exact fact as INCOMPLETE_NATIVE_EDITIONS rather than letting
# a health grace window or a green Pages result reinterpret it as release-ready.
def test_pending_identity_is_immediately_visible_to_shadow():
    result = shadow.classify_integrity_receipt(
        integrity(canonical=43, complete=42, pending=["FCMO-7EBD0FA07C12"])
    )
    assert result["state"] == "INCOMPLETE_NATIVE_EDITIONS"
    assert result["pending_translation_count"] == 1
    assert result["pending_translation_ids"] == ["FCMO-7EBD0FA07C12"]


# Footnote: inconsistent counts are not positive failure evidence; they are an
# epistemic boundary. UNKNOWN prevents a malformed producer receipt from authoring a
# false accusation or a false green result downstream.
def test_inconsistent_counts_become_unknown():
    doc = integrity(canonical=43, complete=42, pending=["FCMO-7EBD0FA07C12"])
    doc["native_complete_story_count"] = 43
    result = shadow.classify_integrity_receipt(doc)
    assert result["state"] == "UNKNOWN"


# Footnote: schema drift must also fail closed epistemically rather than silently
# accepting a shape the adapter no longer knows how to interpret.
def test_unknown_schema_becomes_unknown():
    doc = integrity(canonical=43, complete=43, pending=[])
    doc["schema"] = "future-schema"
    result = shadow.classify_integrity_receipt(doc)
    assert result["state"] == "UNKNOWN"


if __name__ == "__main__":
    import unittest

    class AdapterTests(unittest.TestCase):
        pass

    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            setattr(AdapterTests, name, staticmethod(value))
    unittest.main(verbosity=2)
