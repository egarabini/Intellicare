"""CCDA parser (CDA R2) with secure XML defaults."""

from __future__ import annotations

import time
from typing import Any, Optional

from lxml import etree

from grahame.ccda.models import CCDADocument
from grahame.ccda.sections import (
    EncountersSectionParser,
    ImmunizationsSectionParser,
    MedicationsSectionParser,
    PatientSectionParser,
    ProblemsSectionParser,
    ProceduresSectionParser,
    ResultsSectionParser,
)


class CCDAParser:
    NS = {"cda": "urn:hl7-org:v3"}

    def __init__(self) -> None:
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._section_metrics: dict[str, dict[str, Any]] = {}
        self._errors: list[dict[str, str]] = []

    def parse(self, xml_content: str) -> CCDADocument:
        self._start_time = time.time()
        self._errors = []
        self._section_metrics = {}

        parser = etree.XMLParser(
            resolve_entities=False,
            remove_comments=True,
            remove_pis=True,
            dtd_validation=False,
            load_dtd=False,
            no_network=True,
            huge_tree=False,
        )

        try:
            root = etree.fromstring(xml_content.encode("utf-8"), parser=parser)
        except etree.XMLSyntaxError as exc:
            raise ValueError(f"Invalid XML: {exc}") from exc

        if root.tag != "{urn:hl7-org:v3}ClinicalDocument":
            raise ValueError("Root element must be ClinicalDocument")

        doc_id = root.find("cda:id", self.NS)

        patient = PatientSectionParser(self.NS).parse(root)
        self._section_metrics["patient"] = {"parsed": 1, "errors": 0}

        conditions = self._parse_section_list("conditions", ProblemsSectionParser(self.NS), root)
        medications = self._parse_section_list("medications", MedicationsSectionParser(self.NS), root)
        observations = self._parse_section_list("observations", ResultsSectionParser(self.NS), root)
        procedures = self._parse_section_list("procedures", ProceduresSectionParser(self.NS), root)
        immunizations = self._parse_section_list("immunizations", ImmunizationsSectionParser(self.NS), root)
        encounters = self._parse_section_list("encounters", EncountersSectionParser(self.NS), root)

        self._end_time = time.time()
        return CCDADocument(
            source_document_id=(doc_id.get("extension") if doc_id is not None else None),
            patient=patient,
            conditions=conditions,
            medications=medications,
            observations=observations,
            procedures=procedures,
            immunizations=immunizations,
            encounters=encounters,
        )

    @property
    def processing_time_ms(self) -> float:
        if self._start_time and self._end_time:
            return (self._end_time - self._start_time) * 1000.0
        return 0.0

    @property
    def section_metrics(self) -> dict[str, dict[str, Any]]:
        return dict(self._section_metrics)

    @property
    def errors(self) -> list[dict[str, str]]:
        return list(self._errors)

    def _parse_section_list(self, section_name: str, parser: Any, root: etree._Element) -> list[Any]:
        try:
            values = parser.parse(root)
            self._section_metrics[section_name] = {"parsed": len(values), "errors": 0}
            return values
        except Exception as exc:
            self._section_metrics[section_name] = {"parsed": 0, "errors": 1}
            self._errors.append({"section": section_name, "message": str(exc)})
            return []
