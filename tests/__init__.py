"""Newsletter test package for explicit unittest discovery from the repository root."""

from pathlib import Path
import sys


# Existing harness modules intentionally use ``from harness import ...`` when
# discovered from ``tests`` directly; retain that import surface for packaged
# discovery as well.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)
