"""Convert parsed CCDA content into FHIR R4 resource dicts."""

from __future__ import annotations

from uuid import uuid4

from grahame.ccda.models import CCDADocument
from grahame.ccda.terminology import (
    map_condition_status,
    map_encounter_status,
    map_immunization_status,
    map_medication_request_status,
    map_observation_status,
    map_procedure_status,
    normalize_coding,
    normalize_system,
)


class CCDAFHIRConverter:
    def convert(self, doc: CCDADocument) -> list[dict]:
        patient = self._to_patient(doc)
        patient_ref = f"Patient/{patient['id']}"
        resources: list[dict] = [patient]

        for item in doc.conditions:
            condition_code = normalize_coding(item.code)
            resources.append(
                {
                    "resourceType": "Condition",
                    "id": self._new_id("cond"),
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": map_condition_status(item.status),
                            }
                        ]
                    },
                    "code": {"coding": [condition_code]} if condition_code else {},
                    "subject": {"reference": patient_ref},
                    **({"onsetDateTime": item.onset} if item.onset else {}),
                }
            )

        for item in doc.medications:
            med_code = normalize_coding(item.medication_code)
            resources.append(
                {
                    "resourceType": "MedicationRequest",
                    "id": self._new_id("med"),
                    "status": map_medication_request_status(item.status),
                    "intent": "order",
                    "medicationCodeableConcept": {"coding": [med_code]} if med_code else {},
                    "subject": {"reference": patient_ref},
                }
            )

        for item in doc.observations:
            obs_code = normalize_coding(item.code)
            obs = {
                "resourceType": "Observation",
                "id": self._new_id("obs"),
                "status": map_observation_status(item.status),
                "code": {"coding": [obs_code]} if obs_code else {},
                "subject": {"reference": patient_ref},
            }
            if item.value and item.value.get("value") is not None:
                obs["valueQuantity"] = {
                    "value": self._to_number(item.value.get("value")),
                    "unit": item.value.get("unit"),
                }
            if item.effective:
                obs["effectiveDateTime"] = item.effective
            resources.append(obs)

        for item in doc.procedures:
            proc_code = normalize_coding(item.code)
            resources.append(
                {
                    "resourceType": "Procedure",
                    "id": self._new_id("proc"),
                    "status": map_procedure_status(item.status),
                    "code": {"coding": [proc_code]} if proc_code else {},
                    "subject": {"reference": patient_ref},
                    **({"performedDateTime": item.performed} if item.performed else {}),
                }
            )

        for item in doc.immunizations:
            vaccine_code = normalize_coding(item.vaccine_code)
            resources.append(
                {
                    "resourceType": "Immunization",
                    "id": self._new_id("imm"),
                    "status": map_immunization_status(item.status),
                    "vaccineCode": {"coding": [vaccine_code]} if vaccine_code else {},
                    "patient": {"reference": patient_ref},
                    **({"occurrenceDateTime": item.occurrence} if item.occurrence else {}),
                    **({"lotNumber": item.lot_number} if item.lot_number else {}),
                }
            )

        for item in doc.encounters:
            class_code = normalize_coding(item.class_code)
            resources.append(
                {
                    "resourceType": "Encounter",
                    "id": self._new_id("enc"),
                    "status": map_encounter_status(item.status),
                    "class": {
                        "system": class_code.get("system")
                        or "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": class_code.get("code"),
                        "display": class_code.get("display"),
                    },
                    "subject": {"reference": patient_ref},
                    **({"period": item.period} if item.period else {}),
                }
            )

        return resources

    def _to_patient(self, doc: CCDADocument) -> dict:
        patient_id = self._patient_id(doc)
        payload = {
            "resourceType": "Patient",
            "id": patient_id,
            "identifier": [
                {
                    "system": normalize_system(ident.get("system")),
                    "value": ident.get("value"),
                }
                for ident in doc.patient.identifiers
                if ident.get("value")
            ],
            "name": [
                {
                    "use": doc.patient.name.get("use") or "official",
                    "family": doc.patient.name.get("family"),
                    "given": doc.patient.name.get("given", []),
                }
            ],
            "gender": doc.patient.gender,
            **({"birthDate": doc.patient.birth_date} if doc.patient.birth_date else {}),
        }
        if doc.patient.address:
            payload["address"] = [doc.patient.address]
        if doc.patient.phone:
            payload["telecom"] = [doc.patient.phone]
        return payload

    def _patient_id(self, doc: CCDADocument) -> str:
        for ident in doc.patient.identifiers:
            if ident.get("value"):
                return ident["value"]
        return self._new_id("pat")

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}-{uuid4().hex[:12]}"

    @staticmethod
    def _to_number(raw):
        if raw is None:
            return None
        try:
            if "." in str(raw):
                return float(raw)
            return int(raw)
        except Exception:
            return raw
