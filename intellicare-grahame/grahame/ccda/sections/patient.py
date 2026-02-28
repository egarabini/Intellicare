"""Parser for recordTarget/patientRole."""

from __future__ import annotations

from lxml import etree

from grahame.ccda.models import PatientInfo
from grahame.ccda.utils import hl7_ts_to_iso8601, text_or_none


class PatientSectionParser:
    def __init__(self, ns: dict[str, str]):
        self.ns = ns

    def parse(self, root: etree._Element) -> PatientInfo:
        patient_role = root.find(".//cda:recordTarget/cda:patientRole", self.ns)
        if patient_role is None:
            raise ValueError("Missing recordTarget/patientRole")

        patient = patient_role.find("cda:patient", self.ns)
        if patient is None:
            raise ValueError("Missing patient element")

        identifiers: list[dict] = []
        for ii in patient_role.findall("cda:id", self.ns):
            identifiers.append(
                {
                    "system": ii.get("root"),
                    "value": ii.get("extension"),
                    "assigner": ii.get("assigningAuthorityName"),
                }
            )

        name_el = patient.find("cda:name", self.ns)
        given = [text_or_none(g) or "" for g in name_el.findall("cda:given", self.ns)] if name_el is not None else []
        family = text_or_none(name_el.find("cda:family", self.ns)) if name_el is not None else None
        name = {
            "use": "official",
            "given": [g for g in given if g],
            "family": family or "",
            "text": " ".join([g for g in [*given, family or ""] if g]).strip() or "Unknown",
        }

        gender_code = patient.find("cda:administrativeGenderCode", self.ns)
        gender = {"M": "male", "F": "female", "U": "unknown"}.get(
            gender_code.get("code") if gender_code is not None else None,
            "unknown",
        )

        birth_time = patient.find("cda:birthTime", self.ns)
        birth_date = hl7_ts_to_iso8601(birth_time.get("value") if birth_time is not None else None)

        race_el = patient.find("cda:raceCode", self.ns)
        race = None
        if race_el is not None:
            race = {
                "system": race_el.get("codeSystem"),
                "code": race_el.get("code"),
                "display": race_el.get("displayName"),
            }

        addr_el = patient_role.find("cda:addr", self.ns)
        address = None
        if addr_el is not None:
            lines = [text_or_none(x) for x in addr_el.findall("cda:streetAddressLine", self.ns)]
            address = {
                "use": "home",
                "type": "both",
                "line": [x for x in lines if x],
                "city": text_or_none(addr_el.find("cda:city", self.ns)),
                "state": text_or_none(addr_el.find("cda:state", self.ns)),
                "postalCode": text_or_none(addr_el.find("cda:postalCode", self.ns)),
                "country": text_or_none(addr_el.find("cda:country", self.ns)),
            }

        telecom = patient_role.find("cda:telecom", self.ns)
        phone = None
        if telecom is not None:
            value = telecom.get("value")
            if value and value.startswith("tel:"):
                value = value[4:]
            phone = {"system": "phone", "value": value, "use": "mobile"}

        return PatientInfo(
            identifiers=identifiers,
            name=name,
            gender=gender,
            birth_date=birth_date,
            race=race,
            address=address,
            phone=phone,
        )
