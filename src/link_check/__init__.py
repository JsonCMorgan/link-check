"""Offline-first URL triage before you click (portfolio + phone API companion)."""

from link_check.analyze import analyze_link
from link_check.message import analyze_message

__all__ = ["analyze_link", "analyze_message", "__version__"]

__version__ = "0.1.0"