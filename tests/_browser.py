"""Shared browser-dependency gates for unittest tests.

Local runs retain the historical skip behavior. CI and explicit release runs
must fail when a browser dependency is unavailable, so missing coverage cannot
look like a green suite.
"""
from __future__ import annotations

from functools import wraps
import os
from pathlib import Path
from typing import Callable, TypeVar
import unittest


F = TypeVar("F", bound=Callable[..., object])


def browser_available(value: object) -> bool:
    if isinstance(value, (str, Path)):
        return Path(value).exists()
    return bool(value)


def browser_is_required() -> bool:
    return os.environ.get("FCMO_REQUIRE_BROWSER") == "1" or os.environ.get("CI", "").lower() == "true"


def unavailable_message(reason: str) -> str:
    return f"BROWSER_UNAVAILABLE (FCMO_REQUIRE_BROWSER): {reason}"


def skip_or_fail(testcase: unittest.TestCase, reason: str) -> None:
    """Skip locally, or fail the current test when browser coverage is required."""
    if browser_is_required():
        testcase.fail(unavailable_message(reason))
    testcase.skipTest(reason)


def skip_unless_browser(check: Callable[[], object], reason: str) -> Callable[[F], F]:
    """Decorate a browser test without deciding availability at import time."""
    def decorate(test: F) -> F:
        @wraps(test)
        def guarded(testcase: unittest.TestCase, *args: object, **kwargs: object) -> object:
            try:
                available = browser_available(check())
            except Exception:
                available = False
            if not available:
                skip_or_fail(testcase, reason)
            return test(testcase, *args, **kwargs)

        return guarded  # type: ignore[return-value]

    return decorate
