"""Parser for CCDA encounters section."""

from __future__ import annotations

from lxml import etree

from grahame.ccda.models import EncounterInfo
from grahame.ccda.sections.common import find_sections
from grahame.ccda.utils import code_to_coding, extract_effective_time_period


class EncountersSectionParser:
    TEMPLATE_ROOTS = (
        "2.16.840.1.113883.10.20.22.2.22.1",  # Encounters Section (entries required)
        "2.16.840.1.113883.10.20.22.2.22",  # Encounters Section (entries optional)
    )
    SECTION_CODES = ("46240-8",)

    def __init__(self, ns: dict[str, str]):
        self.ns = ns

    def parse(self, root: etree._Element) -> list[EncounterInfo]:
        encounters: list[EncounterInfo] = []
        sections = find_sections(
            root,
            self.ns,
            template_roots=self.TEMPLATE_ROOTS,
            section_codes=self.SECTION_CODES,
        )
        for section in sections:
            for enc in section.xpath(".//cda:encounter", namespaces=self.ns):
                class_code = code_to_coding(enc.find("cda:code", self.ns))
                period = extract_effective_time_period(enc, self.ns) or {}
                loc = enc.find(".//cda:participantRole/cda:playingEntity/cda:name", self.ns)
                location = {"display": loc.text.strip()} if loc is not None and loc.text else None
                discharge = code_to_coding(enc.find(".//cda:dischargeDispositionCode", self.ns)) or None
                status_el = enc.find("cda:statusCode", self.ns)
                status = status_el.get("code") if status_el is not None else "finished"
                if class_code.get("code"):
                    encounters.append(
                        EncounterInfo(
                            class_code=class_code,
                            period=period,
                            location=location,
                            discharge_disposition=discharge,
                            status=status,
                        )
                    )
        return encounters
