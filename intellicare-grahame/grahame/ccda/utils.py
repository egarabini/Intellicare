"""Utility helpers for CCDA parsing."""

from __future__ import annotations

from lxml import etree


def text_or_none(element: etree._Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    value = element.text.strip()
    return value or None


def hl7_ts_to_iso8601(ts_value: str | None) -> str | None:
    """Convert HL7 TS (YYYYMMDD[HHMMSS]) to ISO-8601."""
    if not ts_value or len(ts_value) < 8:
        return None

    year = ts_value[0:4]
    month = ts_value[4:6]
    day = ts_value[6:8]

    if len(ts_value) >= 14:
        hour = ts_value[8:10]
        minute = ts_value[10:12]
        second = ts_value[12:14]
        return f"{year}-{month}-{day}T{hour}:{minute}:{second}"

    return f"{year}-{month}-{day}"


def code_to_coding(code_el: etree._Element | None) -> dict:
    if code_el is None:
        return {}
    return {
        "system": code_el.get("codeSystem"),
        "code": code_el.get("code"),
        "display": code_el.get("displayName"),
    }


def first_match(context: etree._Element, ns: dict[str, str], *xpaths: str) -> etree._Element | None:
    """Return first matching XML node from a sequence of XPath expressions."""
    for path in xpaths:
        node = context.find(path, ns)
        if node is not None:
            return node
    return None


def extract_effective_time_point(
    context: etree._Element, ns: dict[str, str], *, xpath: str = "cda:effectiveTime"
) -> str | None:
    """
    Return a single representative datetime from HL7 effectiveTime variants.

    Priority:
    1) effectiveTime/@value (TS)
    2) effectiveTime/low/@value (IVL_TS)
    3) effectiveTime/center/@value (IVL_TS)
    4) effectiveTime/high/@value (IVL_TS fallback)
    5) effectiveTime/phase/*/@value (PIVL_TS)
    """
    node = context.find(xpath, ns)
    if node is None:
        return None

    direct = hl7_ts_to_iso8601(node.get("value"))
    if direct:
        return direct

    low = node.find("cda:low", ns)
    low_val = hl7_ts_to_iso8601(low.get("value") if low is not None else None)
    if low_val:
        return low_val

    center = node.find("cda:center", ns)
    center_val = hl7_ts_to_iso8601(center.get("value") if center is not None else None)
    if center_val:
        return center_val

    high = node.find("cda:high", ns)
    high_val = hl7_ts_to_iso8601(high.get("value") if high is not None else None)
    if high_val:
        return high_val

    phase = node.find("cda:phase", ns)
    if phase is not None:
        for sub in ("cda:low", "cda:center", "cda:high"):
            child = phase.find(sub, ns)
            val = hl7_ts_to_iso8601(child.get("value") if child is not None else None)
            if val:
                return val

    return None


def extract_effective_time_period(
    context: etree._Element, ns: dict[str, str], *, xpath: str = "cda:effectiveTime"
) -> dict[str, str] | None:
    """
    Return interval period dict from HL7 effectiveTime variants.

    Supports IVL_TS/PIVL_TS/SXPR_TS and returns available start/end.
    """
    node = context.find(xpath, ns)
    if node is None:
        return None

    start = None
    end = None

    low = node.find("cda:low", ns)
    high = node.find("cda:high", ns)
    center = node.find("cda:center", ns)
    if low is not None:
        start = hl7_ts_to_iso8601(low.get("value"))
    if high is not None:
        end = hl7_ts_to_iso8601(high.get("value"))
    if not start and center is not None:
        start = hl7_ts_to_iso8601(center.get("value"))

    if not start and not end:
        phase = node.find("cda:phase", ns)
        if phase is not None:
            low = phase.find("cda:low", ns)
            high = phase.find("cda:high", ns)
            center = phase.find("cda:center", ns)
            if low is not None:
                start = hl7_ts_to_iso8601(low.get("value"))
            if high is not None:
                end = hl7_ts_to_iso8601(high.get("value"))
            if not start and center is not None:
                start = hl7_ts_to_iso8601(center.get("value"))

    if not start and not end:
        return None

    result: dict[str, str] = {}
    if start:
        result["start"] = start
    if end:
        result["end"] = end
    return result


def extract_effective_period_frequency(
    context: etree._Element, ns: dict[str, str]
) -> dict[str, str] | None:
    """
    Extract frequency period from effectiveTime structures.

    Handles:
    - effectiveTime[@operator='A']/period
    - effectiveTime/period
    - effectiveTime/phase/period
    """
    candidates = [
        context.find("cda:effectiveTime[@operator='A']/cda:period", ns),
        context.find("cda:effectiveTime/cda:period", ns),
        context.find("cda:effectiveTime/cda:phase/cda:period", ns),
    ]
    for period in candidates:
        if period is None:
            continue
        value = period.get("value")
        unit = period.get("unit")
        if value:
            out = {"value": value}
            if unit:
                out["unit"] = unit
            return out
    return None
