"""Encounter Converter — PV1 segment to FHIR R4 Encounter resource.

This module converts HL7v2 PV1 (Patient Visit) segments to FHIR R4 Encounter resources.

Mapping:
- PV1-1 (Set ID) → Encounter.identifier (usual)
- PV1-2 (Patient Class) → Encounter.class (I→imp, O→amb, E→emer, P→imp)
- PV1-3 (Assigned Location) → Encounter.location
- PV1-4 (Admission Type) → Encounter.hospitalization.admitSource
- PV1-44 (Admit DateTime) → Encounter.period.start
- MSH-10 (Message Control ID) → Encounter.identifier (official)

References:
- FHIR R4 Encounter: https://hl7.org/fhir/R4/encounter.html
- HL7v2 PV1 Segment: https://hl7-definition.caristix.com/v2/HL7v2.5.1/Segments/PV1
"""

from typing import Optional

from ..segments import PV1Segment, MSHSegment


class EncounterConverter:
    """Convert HL7v2 PV1 segment to FHIR R4 Encounter resource."""

    def convert(
        self, pv1: PV1Segment, msh: MSHSegment, patient_id: Optional[str] = None
    ) -> dict:
        """Convert PV1 segment to FHIR Encounter resource.

        Args:
            pv1: PV1 segment from HL7v2 message
            msh: MSH segment (for metadata like source system and message control ID)
            patient_id: Optional FHIR Patient ID to reference (if None, uses "unknown")

        Returns:
            FHIR R4 Encounter resource as dict
        """
        encounter = {
            "resourceType": "Encounter",
            "status": "in-progress",  # Default status for new encounters
            "meta": {
                "source": f"urn:hl7:{msh.sending_application}:{msh.sending_facility}",
            },
        }

        # Build identifiers (MSH-10 + PV1-1)
        identifiers = self._build_identifiers(pv1, msh)
        if identifiers:
            encounter["identifier"] = identifiers

        # Build class (PV1-2)
        encounter_class = self._build_class(pv1)
        if encounter_class:
            encounter["class"] = encounter_class

        # Build subject reference (Patient)
        subject_ref = patient_id if patient_id else "unknown"
        encounter["subject"] = {"reference": f"Patient/{subject_ref}"}

        # Build location (PV1-3)
        location = self._build_location(pv1)
        if location:
            encounter["location"] = location

        # Build hospitalization (PV1-4)
        hospitalization = self._build_hospitalization(pv1)
        if hospitalization:
            encounter["hospitalization"] = hospitalization

        # Build period (PV1-44)
        period = self._build_period(pv1)
        if period:
            encounter["period"] = period

        return encounter

    def _build_identifiers(self, pv1: PV1Segment, msh: MSHSegment) -> list:
        """Build Encounter identifiers from MSH-10 and PV1-1."""
        identifiers = []

        # MSH-10 (Message Control ID) → official identifier
        if msh.message_control_id:
            identifiers.append({
                "use": "official",
                "system": f"urn:hl7:{msh.sending_application}:{msh.sending_facility}",
                "value": msh.message_control_id,
            })

        # PV1-1 (Set ID) → usual identifier
        if pv1.set_id:
            identifiers.append({
                "use": "usual",
                "value": pv1.set_id,
            })

        return identifiers

    def _build_class(self, pv1: PV1Segment) -> Optional[dict]:
        """Build Encounter class from PV1-2 (Patient Class).

        FHIR Encounter.class uses v3-ActCode system:
        - imp: Inpatient encounter
        - amb: Ambulatory
        - emer: Emergency
        """
        if not pv1.patient_class:
            return None

        # PV1-2 is already mapped by PV1Segment._map_patient_class()
        # I→imp, O→amb, E→emer, P→imp
        return {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": pv1.patient_class,
        }

    def _build_location(self, pv1: PV1Segment) -> Optional[list]:
        """Build Encounter location from PV1-3 (Assigned Location)."""
        if not pv1.assigned_location:
            return None

        location_display = pv1.assigned_location.get("point_of_care")
        if not location_display:
            return None

        return [{
            "location": {
                "reference": "Location/unknown",
                "display": location_display,
            }
        }]

    def _build_hospitalization(self, pv1: PV1Segment) -> Optional[dict]:
        """Build Encounter hospitalization from PV1-4 (Admission Type)."""
        if not pv1.admission_type:
            return None

        admit_code = pv1.admission_type.get("code")
        if not admit_code:
            return None

        return {
            "admitSource": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0007",
                    "code": admit_code,
                }]
            }
        }

    def _build_period(self, pv1: PV1Segment) -> Optional[dict]:
        """Build Encounter period from PV1-44 (Admit DateTime)."""
        if not pv1.admit_datetime:
            return None

        return {
            "start": pv1.admit_datetime,
        }

