"""Display resolver for terminology i18n overrides."""

from __future__ import annotations


def resolve_display(
    *,
    default_display: str | None,
    designations: dict[str, str] | None,
    languages: list[str] | None,
) -> str | None:
    """Resolve display from language preferences with fallback to default."""
    if not designations or not languages:
        return default_display

    normalized = {k.lower(): v for k, v in designations.items() if isinstance(k, str)}
    for language in languages:
        key = language.lower()
        if key in normalized:
            return normalized[key]
        if "-" in key:
            base = key.split("-", 1)[0]
            if base in normalized:
                return normalized[base]
    return default_display
