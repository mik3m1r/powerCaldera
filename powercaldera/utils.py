"""Utilidades compartidas de powerCaldera."""

from __future__ import annotations


def truncate(text: str, max_len: int) -> str:
    """Trunca texto con ellipsis si excede max_len."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "\u2026"
