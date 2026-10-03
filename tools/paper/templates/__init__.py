"""Semantic HTML templates for the static newspaper."""

from .layout import document
from .pages import archive_page, front_page, simple_page, status_page, story_page

__all__ = ["archive_page", "document", "front_page", "simple_page", "status_page", "story_page"]
