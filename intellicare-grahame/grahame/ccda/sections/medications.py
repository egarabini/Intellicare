"""Parser for CCDA medication section."""

from __future__ import annotations

from lxml import etree

from grahame.ccda.models import MedicationInfo
from grahame.ccda.sections.common import find_sections
from grahame.ccda.utils import (
    code_to_coding,
    extract_effective_period_frequency,
    first_match,
)


class MedicationsSectionParser:
    TEMPLATE_ROOTS = (
        "2.16.840.1.113883.10.20.22.2.1.1",  # Medications Section (entries required)
        "2.16.840.1.113883.10.20.22.2.1",  # Medications Section (entries optional)
        "2.16.840.1.113883.10.20.22.4.16",  # Medication Activity (some exporters put on section)
    )
    SECTION_CODES = ("10160-0",)

    def __init__(self, ns: dict[str, str]):
        self.ns = ns

    def parse(self, root: etree._Element) -> list[MedicationInfo]:
        medications: list[MedicationInfo] = []
        sections = find_sections(
            root,
            self.ns,
            template_roots=self.TEMPLATE_ROOTS,
            section_codes=self.SECTION_CODES,
        )
        for section in sections:
            sa_nodes = section.xpath(
                ".//cda:entry/cda:substanceAdministration | "
                ".//cda:entry/cda:act/cda:entryRelationship/cda:substanceAdministration",
                namespaces=self.ns,
            )
            seen: set[int] = set()
            for sa in sa_nodes:
                if id(sa) in seen:
                    continue
                seen.add(id(sa))

                med_code = code_to_coding(
                    first_match(
                        sa,
                        self.ns,
                        ".//cda:consumable//cda:code",
                        ".//cda:entryRelationship//cda:consumable//cda:code",
                        ".//cda:entryRelationship//cda:supply//cda:code",
                    )
                )
                dose_el = sa.find("cda:doseQuantity", self.ns)
                dosage = (
                    {"value": dose_el.get("value"), "unit": dose_el.get("unit")}
                    if dose_el is not None
                    else {}
                )
                route = code_to_coding(
                    first_match(
                        sa,
                        self.ns,
                        "cda:routeCode",
                        ".//cda:entryRelationship/cda:substanceAdministration/cda:routeCode",
                    )
                ) or None
                freq = extract_effective_period_frequency(sa, self.ns)
                status_el = first_match(
                    sa,
                    self.ns,
                    "cda:statusCode",
                    ".//cda:entryRelationship/cda:substanceAdministration/cda:statusCode",
                )
                status = status_el.get("code") if status_el is not None else "active"
                if med_code.get("code"):
                    medications.append(
                        MedicationInfo(
                            medication_code=med_code,
                            dosage=dosage,
                            route=route,
                            frequency=freq,
                            status=status,
                        )
                    )
        return medications
