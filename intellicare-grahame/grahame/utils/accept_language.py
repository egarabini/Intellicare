"""Accept-Language parser helpers (RFC 7231 simplified)."""

from __future__ import annotations


def parse_accept_language(
    header_value: str | None,
    *,
    default_language: str = "pt-BR",
) -> list[str]:
    """Return ordered language preferences by quality (q) value."""
    if not header_value or not header_value.strip():
        return [default_language]

    weighted: list[tuple[float, int, str]] = []
    for index, raw_item in enumerate(header_value.split(",")):
        item = raw_item.strip()
        if not item:
            continue
        lang = item
        q = 1.0
        if ";" in item:
            parts = [p.strip() for p in item.split(";") if p.strip()]
            lang = parts[0]
            for param in parts[1:]:
                if param.startswith("q="):
                    try:
                        q = float(param[2:])
                    except ValueError:
                        q = 0.0
        if lang:
            weighted.append((q, index, lang))

    if not weighted:
        return [default_language]

    weighted.sort(key=lambda x: (-x[0], x[1]))
    ordered = [lang for _q, _idx, lang in weighted]

    # Add base language fallback when a region variant appears first (pt-BR -> pt).
    expanded: list[str] = []
    for lang in ordered:
        if lang not in expanded:
            expanded.append(lang)
        if "-" in lang:
            base = lang.split("-", 1)[0]
            if base and base not in expanded:
                expanded.append(base)
    return expanded
