"""HL7v2 PID Segment to FHIR R4 Patient Converter.

This module converts HL7v2 PID (Patient Identification) segments to FHIR R4 Patient resources.

Mapping:
    PID-3 (Patient ID List) → Patient.identifier
    PID-5 (Patient Name) → Patient.name
    PID-7 (Date of Birth) → Patient.birthDate
    PID-8 (Administrative Sex) → Patient.gender
    PID-10 (Race) → Patient.extension (US Core race)
    PID-11 (Address) → Patient.address
    PID-13 (Phone Number) → Patient.telecom
    PID-22 (Ethnicity) → Patient.extension (US Core ethnicity)

Example Usage:
    converter = PatientConverter()
    patient = converter.convert(pid_segment, msh_segment)
"""

from typing import Optional

from ..segments import MSHSegment, PIDSegment


class PatientConverter:
    """Convert HL7v2 PID segment to FHIR R4 Patient resource."""

    def convert(self, pid: PIDSegment, msh: MSHSegment) -> dict:
        """Convert PID segment to FHIR Patient resource.

        Args:
            pid: PID segment from HL7v2 message
            msh: MSH segment (for metadata like source system)

        Returns:
            FHIR R4 Patient resource as dict
        """
        patient = {
            "resourceType": "Patient",
            "meta": {
                "source": f"urn:hl7:{msh.sending_application}:{msh.sending_facility}",
            },
        }

        # Build identifiers (PID-3)
        identifiers = self._build_identifiers(pid)
        if identifiers:
            patient["identifier"] = identifiers

        # Build name (PID-5)
        name = self._build_name(pid)
        if name:
            patient["name"] = [name]

        # Build birthDate (PID-7)
        if pid.datetime_of_birth:
            # Convert from ISO8601 datetime to FHIR date (YYYY-MM-DD)
            birth_date = pid.datetime_of_birth.split("T")[0]
            patient["birthDate"] = birth_date

        # Build gender (PID-8)
        if pid.administrative_sex:
            patient["gender"] = pid.administrative_sex

        # Build address (PID-11)
        address = self._build_address(pid)
        if address:
            patient["address"] = [address]

        # Build telecom (PID-13)
        telecom = self._build_telecom(pid)
        if telecom:
            patient["telecom"] = [telecom]

        # Build extensions (race, ethnicity)
        extensions = self._build_extensions(pid)
        if extensions:
            patient["extension"] = extensions

        return patient

    def _build_identifiers(self, pid: PIDSegment) -> list[dict]:
        """Build FHIR identifiers from PID-3 (Patient ID List)."""
        identifiers = []

        for cx in pid.patient_id_list:
            if not cx.get("id"):
                continue

            identifier = {
                "use": "usual",
                "value": cx["id"],
            }

            # Map identifier type to system
            identifier_type = cx.get("identifier_type", "")
            system = self._map_identifier_system(identifier_type, cx.get("assigning_authority"))
            if system:
                identifier["system"] = system

            # Add type coding if available
            if identifier_type:
                identifier["type"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": identifier_type,
                        }
                    ]
                }

            identifiers.append(identifier)

        return identifiers

    def _build_name(self, pid: PIDSegment) -> Optional[dict]:
        """Build FHIR name from PID-5 (Patient Name)."""
        if not pid.patient_name:
            return None

        name = {"use": "official"}

        if pid.patient_name.get("family"):
            name["family"] = pid.patient_name["family"]

        given_names = []
        if pid.patient_name.get("given"):
            given_names.append(pid.patient_name["given"])
        if pid.patient_name.get("middle"):
            given_names.append(pid.patient_name["middle"])

        if given_names:
            name["given"] = given_names

        if pid.patient_name.get("prefix"):
            name["prefix"] = [pid.patient_name["prefix"]]

        if pid.patient_name.get("suffix"):
            name["suffix"] = [pid.patient_name["suffix"]]

        return name if len(name) > 1 else None  # Return None if only "use" is present

    def _build_address(self, pid: PIDSegment) -> Optional[dict]:
        """Build FHIR address from PID-11 (Address)."""
        if not pid.address:
            return None

        address = {"use": "home"}

        if pid.address.get("street"):
            address["line"] = [pid.address["street"]]

        if pid.address.get("city"):
            address["city"] = pid.address["city"]

        if pid.address.get("state"):
            address["state"] = pid.address["state"]

        if pid.address.get("postal_code"):
            address["postalCode"] = pid.address["postal_code"]

        if pid.address.get("country"):
            address["country"] = pid.address["country"]

        return address if len(address) > 1 else None

    def _build_telecom(self, pid: PIDSegment) -> Optional[dict]:
        """Build FHIR telecom from PID-13 (Phone Number)."""
        if not pid.phone_number or not pid.phone_number.get("number"):
            return None

        return {
            "system": "phone",
            "value": pid.phone_number["number"],
            "use": pid.phone_number.get("use", "home"),
        }

    def _build_extensions(self, pid: PIDSegment) -> list[dict]:
        """Build FHIR extensions for race and ethnicity."""
        extensions = []

        # Race extension (US Core)
        if pid.race and pid.race.get("code"):
            extensions.append({
                "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
                "extension": [
                    {
                        "url": "ombCategory",
                        "valueCoding": {
                            "system": "urn:oid:2.16.840.1.113883.6.238",
                            "code": pid.race["code"],
                            "display": pid.race.get("text", ""),
                        },
                    }
                ],
            })

        # Ethnicity extension (US Core)
        if pid.ethnicity and pid.ethnicity.get("code"):
            extensions.append({
                "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
                "extension": [
                    {
                        "url": "ombCategory",
                        "valueCoding": {
                            "system": "urn:oid:2.16.840.1.113883.6.238",
                            "code": pid.ethnicity["code"],
                            "display": pid.ethnicity.get("text", ""),
                        },
                    }
                ],
            })

        return extensions

    def _map_identifier_system(self, identifier_type: str, assigning_authority: Optional[str] = None) -> Optional[str]:
        """Map HL7v2 identifier type to FHIR system URI."""
        # Common Brazilian identifier types
        type_mapping = {
            "CPF": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
            "CNS": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns",
            "RG": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/rg",
            "MR": "http://terminology.hl7.org/CodeSystem/v2-0203",  # Medical Record Number
            "PI": "http://terminology.hl7.org/CodeSystem/v2-0203",  # Patient Internal Identifier
        }

        if identifier_type in type_mapping:
            return type_mapping[identifier_type]

        # Use assigning authority as system if available
        if assigning_authority:
            return f"urn:oid:{assigning_authority}"

        return None

