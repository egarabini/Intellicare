"""Parser for CCDA immunization section."""

from __future__ import annotations

from lxml import etree

from grahame.ccda.models import ImmunizationInfo
from grahame.ccda.sections.common import find_sections
from grahame.ccda.utils import code_to_coding, extract_effective_time_point, hl7_ts_to_iso8601


class ImmunizationsSectionParser:
    TEMPLATE_ROOTS = (
        "2.16.840.1.113883.10.20.22.2.2.1",  # Immunizations Section (entries required)
        "2.16.840.1.113883.10.20.22.2.2",  # Immunizations Section (entries optional)
    )
    SECTION_CODES = ("11369-6",)

    def __init__(self, ns: dict[str, str]):
        self.ns = ns

    def parse(self, root: etree._Element) -> list[ImmunizationInfo]:
        immunizations: list[ImmunizationInfo] = []
        sections = find_sections(
            root,
            self.ns,
            template_roots=self.TEMPLATE_ROOTS,
            section_codes=self.SECTION_CODES,
        )
        for section in sections:
            for sa in section.xpath(".//cda:substanceAdministration", namespaces=self.ns):
                vaccine = code_to_coding(sa.find(".//cda:consumable//cda:code", self.ns))
                occ = extract_effective_time_point(sa, self.ns)
                lot = sa.find(".//cda:manufacturedMaterial/cda:lotNumberText", self.ns)
                exp = sa.find(".//cda:manufacturedMaterial/cda:expirationTime", self.ns)
                status_el = sa.find("cda:statusCode", self.ns)
                status = status_el.get("code") if status_el is not None else "completed"
                if vaccine.get("code"):
                    immunizations.append(
                        ImmunizationInfo(
                            vaccine_code=vaccine,
                            occurrence=occ,
                            lot_number=lot.text.strip() if lot is not None and lot.text else None,
                            expiration=hl7_ts_to_iso8601(exp.get("value") if exp is not None else None),
                            status=status,
                        )
                    )
        return immunizations
