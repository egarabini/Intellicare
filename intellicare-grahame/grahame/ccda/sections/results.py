"""Parser for CCDA results section."""

from __future__ import annotations

from lxml import etree

from grahame.ccda.models import ObservationInfo
from grahame.ccda.sections.common import find_sections
from grahame.ccda.utils import code_to_coding, extract_effective_time_point, first_match


class ResultsSectionParser:
    TEMPLATE_ROOTS = (
        "2.16.840.1.113883.10.20.22.2.3.1",  # Results Section (entries required)
        "2.16.840.1.113883.10.20.22.2.3",  # Results Section (entries optional)
    )
    SECTION_CODES = ("30954-2",)

    def __init__(self, ns: dict[str, str]):
        self.ns = ns

    def parse(self, root: etree._Element) -> list[ObservationInfo]:
        observations: list[ObservationInfo] = []
        sections = find_sections(
            root,
            self.ns,
            template_roots=self.TEMPLATE_ROOTS,
            section_codes=self.SECTION_CODES,
        )
        for section in sections:
            obs_nodes = section.xpath(
                ".//cda:entry/cda:observation | "
                ".//cda:entry/cda:organizer/cda:component/cda:observation",
                namespaces=self.ns,
            )
            seen: set[int] = set()
            for obs in obs_nodes:
                if id(obs) in seen:
                    continue
                seen.add(id(obs))

                code = code_to_coding(
                    first_match(
                        obs,
                        self.ns,
                        "cda:code",
                        ".//cda:entryRelationship/cda:observation/cda:code",
                    )
                )
                value_el = first_match(
                    obs,
                    self.ns,
                    "cda:value",
                    ".//cda:entryRelationship/cda:observation/cda:value",
                )
                value = None
                unit = None
                if value_el is not None:
                    value = {"value": value_el.get("value"), "unit": value_el.get("unit")}
                    unit = value_el.get("unit")
                effective = extract_effective_time_point(obs, self.ns) or extract_effective_time_point(
                    obs, self.ns, xpath=".//cda:entryRelationship/cda:observation/cda:effectiveTime"
                )
                status_el = first_match(
                    obs,
                    self.ns,
                    "cda:statusCode",
                    ".//cda:entryRelationship/cda:observation/cda:statusCode",
                )
                status = status_el.get("code") if status_el is not None else "final"
                rr_low = obs.find(".//cda:referenceRange//cda:low", self.ns)
                rr_high = obs.find(".//cda:referenceRange//cda:high", self.ns)
                reference_range = None
                if rr_low is not None or rr_high is not None:
                    reference_range = {
                        "low": rr_low.get("value") if rr_low is not None else None,
                        "high": rr_high.get("value") if rr_high is not None else None,
                        "unit": (
                            rr_low.get("unit")
                            if rr_low is not None
                            else rr_high.get("unit")
                            if rr_high is not None
                            else None
                        ),
                    }
                if code.get("code"):
                    observations.append(
                        ObservationInfo(
                            code=code,
                            value=value,
                            unit=unit,
                            effective=effective,
                            reference_range=reference_range,
                            status=status,
                        )
                    )
        return observations
