"""Calculo simplificado de confidence score."""

from __future__ import annotations


def score_from_text(text: str) -> float:
    cleaned = text.strip()
    if not cleaned:
        return 0.0
    length = len(cleaned)
    if length < 20:
        return 0.55
    if length < 120:
        return 0.75
    return 0.9

