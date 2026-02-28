"""Parser for CCDA problem list section."""

from __future__ import annotations

from lxml import etree

from grahame.ccda.models import ConditionInfo
from grahame.ccda.sections.common import find_sections
from grahame.ccda.utils import code_to_coding, extract_effective_time_point, first_match


class ProblemsSectionParser:
    TEMPLATE_ROOTS = (
        "2.16.840.1.113883.10.20.22.2.5.1",  # Problem Section (entries required)
        "2.16.840.1.113883.10.20.22.2.5",  # Problem Section (entries optional)
    )
    SECTION_CODES = ("11450-4",)
    PROBLEM_STATUS_TEMPLATE = "2.16.840.1.113883.10.20.22.4.6"

    def __init__(self, ns: dict[str, str]):
        self.ns = ns

    def parse(self, root: etree._Element) -> list[ConditionInfo]:
        conditions: list[ConditionInfo] = []
        sections = find_sections(
            root,
            self.ns,
            template_roots=self.TEMPLATE_ROOTS,
            section_codes=self.SECTION_CODES,
        )
        for section in sections:
            obs_nodes = section.xpath(
                ".//cda:entry/cda:observation | "
                ".//cda:entry/cda:act/cda:entryRelationship/cda:observation",
                namespaces=self.ns,
            )
            seen: set[int] = set()
            for obs in obs_nodes:
                if id(obs) in seen:
                    continue
                seen.add(id(obs))

                value_code = first_match(
                    obs,
                    self.ns,
                    "cda:value[@code]",
                    ".//cda:entryRelationship/cda:observation/cda:value[@code]",
                )
                code = code_to_coding(
                    value_code if value_code is not None else obs.find("cda:code", self.ns)
                )

                status = self._extract_status(obs)
                onset = extract_effective_time_point(obs, self.ns)
                severity_el = obs.find(
                    ".//cda:entryRelationship[@typeCode='SUBJ']//cda:value", self.ns
                )
                severity = code_to_coding(severity_el) if severity_el is not None else None
                if code.get("code"):
                    conditions.append(
                        ConditionInfo(code=code, status=status, onset=onset, severity=severity)
                    )
        return conditions

    def _extract_status(self, obs: etree._Element) -> str:
        direct = obs.find("cda:statusCode", self.ns)
        if direct is not None and direct.get("code"):
            return direct.get("code")

        nested_status_nodes = obs.xpath(
            (
                ".//cda:entryRelationship/cda:observation"
                f"[cda:templateId[@root='{self.PROBLEM_STATUS_TEMPLATE}']]/cda:value"
            ),
            namespaces=self.ns,
        )
        nested_status = nested_status_nodes[0] if nested_status_nodes else None
        if nested_status is None:
            return "unknown"

        raw = (nested_status.get("code") or "").strip().lower()
        status_map = {
            "55561003": "active",  # SNOMED Active
            "73425007": "completed",  # SNOMED Inactive
            "active": "active",
            "inactive": "completed",
            "resolved": "completed",
            "completed": "completed",
        }
        return status_map.get(raw, raw or "unknown")
