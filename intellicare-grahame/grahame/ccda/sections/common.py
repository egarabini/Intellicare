"""Shared helpers for CCDA section discovery."""

from __future__ import annotations

from lxml import etree


def find_sections(
    root: etree._Element,
    ns: dict[str, str],
    *,
    template_roots: tuple[str, ...] = (),
    section_codes: tuple[str, ...] = (),
) -> list[etree._Element]:
    nodes: list[etree._Element] = []
    seen: set[int] = set()

    for template_root in template_roots:
        xpath = f".//cda:section[cda:templateId[@root='{template_root}']]"
        for node in root.xpath(xpath, namespaces=ns):
            node_id = id(node)
            if node_id not in seen:
                seen.add(node_id)
                nodes.append(node)

    for section_code in section_codes:
        xpath = f".//cda:section[cda:code[@code='{section_code}']]"
        for node in root.xpath(xpath, namespaces=ns):
            node_id = id(node)
            if node_id not in seen:
                seen.add(node_id)
                nodes.append(node)

    return nodes
