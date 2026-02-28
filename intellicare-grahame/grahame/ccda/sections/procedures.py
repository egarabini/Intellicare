"""Parser for CCDA procedures section."""

from __future__ import annotations

from lxml import etree

from grahame.ccda.models import ProcedureInfo
from grahame.ccda.sections.common import find_sections
from grahame.ccda.utils import code_to_coding, extract_effective_time_point


class ProceduresSectionParser:
    TEMPLATE_ROOTS = (
        "2.16.840.1.113883.10.20.22.2.7.1",  # Procedures Section (entries required)
        "2.16.840.1.113883.10.20.22.2.7",  # Procedures Section (entries optional)
    )
    SECTION_CODES = ("47519-4",)

    def __init__(self, ns: dict[str, str]):
        self.ns = ns

    def parse(self, root: etree._Element) -> list[ProcedureInfo]:
        procedures: list[ProcedureInfo] = []
        sections = find_sections(
            root,
            self.ns,
            template_roots=self.TEMPLATE_ROOTS,
            section_codes=self.SECTION_CODES,
        )
        for section in sections:
            for proc in section.xpath(".//cda:procedure", namespaces=self.ns):
                code = code_to_coding(proc.find("cda:code", self.ns))
                perf = extract_effective_time_point(proc, self.ns)
                status_el = proc.find("cda:statusCode", self.ns)
                status = status_el.get("code") if status_el is not None else "completed"
                if code.get("code"):
                    procedures.append(ProcedureInfo(code=code, performed=perf, status=status))
        return procedures
