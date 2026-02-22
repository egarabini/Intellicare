"""Testes para o cliente FHIR R4."""

import pytest
import httpx
import respx

from intellicare_core.fhir.client import FHIRClient, FHIRClientError


# --- Fixtures ---


@pytest.fixture
def client() -> FHIRClient:
    return FHIRClient("http://fhir.test/fhir", timeout=5)


@pytest.fixture
def client_with_auth() -> FHIRClient:
    return FHIRClient("http://fhir.test/fhir", auth_token="token-123")


# --- Dados FHIR de exemplo ---

PATIENT_RESOURCE = {
    "resourceType": "Patient",
    "id": "patient-1",
    "name": [{"given": ["Maria", "Silva"], "family": "Santos"}],
    "gender": "female",
    "birthDate": "1985-03-15",
    "identifier": [
        {"system": "http://saude.gov.br/fhir/r4/br-cpf", "value": "12345678901"}
    ],
}

BUNDLE_OBSERVATIONS = {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 2,
    "entry": [
        {
            "resource": {
                "resourceType": "Observation",
                "id": "obs-1",
                "code": {
                    "coding": [{"code": "2160-0", "display": "Creatinina"}]
                },
                "valueQuantity": {"value": 1.5, "unit": "mg/dL"},
                "effectiveDateTime": "2026-01-15T10:00:00Z",
                "referenceRange": [
                    {"low": {"value": 0.7}, "high": {"value": 1.2}}
                ],
            }
        },
        {
            "resource": {
                "resourceType": "Observation",
                "id": "obs-2",
                "code": {
                    "coding": [{"code": "33914-3", "display": "eGFR"}]
                },
                "valueQuantity": {"value": 52.3, "unit": "mL/min/1.73m2"},
                "effectiveDateTime": "2026-01-15T10:00:00Z",
            }
        },
    ],
}

BUNDLE_CONDITIONS = {
    "resourceType": "Bundle",
    "type": "searchset",
    "entry": [
        {
            "resource": {
                "resourceType": "Condition",
                "id": "cond-1",
                "code": {
                    "coding": [{"code": "N18.3", "display": "DRC Estagio 3"}]
                },
                "clinicalStatus": {
                    "coding": [{"code": "active"}]
                },
            }
        }
    ],
}

BUNDLE_ALLERGIES = {
    "resourceType": "Bundle",
    "type": "searchset",
    "entry": [
        {
            "resource": {
                "resourceType": "AllergyIntolerance",
                "id": "allergy-1",
                "code": {"text": "Dipirona"},
                "reaction": [
                    {
                        "manifestation": [
                            {"coding": [{"display": "Urticaria"}]}
                        ],
                        "severity": "high",
                    }
                ],
            }
        }
    ],
}

BUNDLE_MEDICATIONS = {
    "resourceType": "Bundle",
    "type": "searchset",
    "entry": [
        {
            "resource": {
                "resourceType": "MedicationRequest",
                "id": "med-1",
                "medicationCodeableConcept": {
                    "coding": [{"code": "C09AA02", "display": "Enalapril"}],
                    "text": "Enalapril 10mg",
                },
                "status": "active",
                "dosageInstruction": [{"text": "10mg 1x/dia"}],
            }
        }
    ],
}

EMPTY_BUNDLE = {"resourceType": "Bundle", "type": "searchset", "entry": []}


# --- Tests: Construcao ---


class TestFHIRClientInit:
    def test_trailing_slash_removed(self) -> None:
        c = FHIRClient("http://fhir.test/fhir/")
        assert c.base_url == "http://fhir.test/fhir"

    def test_default_headers(self, client: FHIRClient) -> None:
        assert client._headers["Accept"] == "application/fhir+json"
        assert client._headers["Content-Type"] == "application/fhir+json"

    def test_auth_header(self, client_with_auth: FHIRClient) -> None:
        assert client_with_auth._headers["Authorization"] == "Bearer token-123"

    def test_no_auth_header(self, client: FHIRClient) -> None:
        assert "Authorization" not in client._headers


class TestBuildUrl:
    def test_resource_type_only(self, client: FHIRClient) -> None:
        assert client._build_url("Patient") == "http://fhir.test/fhir/Patient"

    def test_resource_with_id(self, client: FHIRClient) -> None:
        url = client._build_url("Patient", "123")
        assert url == "http://fhir.test/fhir/Patient/123"


# --- Tests: Requisicoes ---


class TestGetResource:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client: FHIRClient) -> None:
        respx.get("http://fhir.test/fhir/Patient/patient-1").mock(
            return_value=httpx.Response(200, json=PATIENT_RESOURCE)
        )
        result = await client.get_resource("Patient", "patient-1")
        assert result["id"] == "patient-1"
        assert result["resourceType"] == "Patient"

    @respx.mock
    @pytest.mark.asyncio
    async def test_not_found(self, client: FHIRClient) -> None:
        respx.get("http://fhir.test/fhir/Patient/nope").mock(
            return_value=httpx.Response(404, json={"issue": "not found"})
        )
        with pytest.raises(FHIRClientError) as exc_info:
            await client.get_resource("Patient", "nope")
        assert exc_info.value.status_code == 404

    @respx.mock
    @pytest.mark.asyncio
    async def test_timeout(self, client: FHIRClient) -> None:
        respx.get("http://fhir.test/fhir/Patient/slow").mock(
            side_effect=httpx.ReadTimeout("timeout")
        )
        with pytest.raises(FHIRClientError) as exc_info:
            await client.get_resource("Patient", "slow")
        assert exc_info.value.status_code == 408

    @respx.mock
    @pytest.mark.asyncio
    async def test_connection_error(self, client: FHIRClient) -> None:
        respx.get("http://fhir.test/fhir/Patient/fail").mock(
            side_effect=httpx.ConnectError("refused")
        )
        with pytest.raises(FHIRClientError) as exc_info:
            await client.get_resource("Patient", "fail")
        assert exc_info.value.status_code is None


class TestSearch:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_resources(self, client: FHIRClient) -> None:
        respx.get("http://fhir.test/fhir/Observation").mock(
            return_value=httpx.Response(200, json=BUNDLE_OBSERVATIONS)
        )
        results = await client.search("Observation", {"patient": "patient-1"})
        assert len(results) == 2
        assert results[0]["resourceType"] == "Observation"

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_bundle(self, client: FHIRClient) -> None:
        respx.get("http://fhir.test/fhir/Observation").mock(
            return_value=httpx.Response(200, json=EMPTY_BUNDLE)
        )
        results = await client.search("Observation", {"patient": "nobody"})
        assert results == []


class TestGetPatient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_patient(self, client: FHIRClient) -> None:
        respx.get("http://fhir.test/fhir/Patient/patient-1").mock(
            return_value=httpx.Response(200, json=PATIENT_RESOURCE)
        )
        result = await client.get_patient("patient-1")
        assert result["gender"] == "female"


class TestSearchByCpf:
    @respx.mock
    @pytest.mark.asyncio
    async def test_search_by_cpf(self, client: FHIRClient) -> None:
        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [{"resource": PATIENT_RESOURCE}],
        }
        respx.get("http://fhir.test/fhir/Patient").mock(
            return_value=httpx.Response(200, json=bundle)
        )
        results = await client.search_patient_by_cpf("12345678901")
        assert len(results) == 1


class TestGetObservations:
    @respx.mock
    @pytest.mark.asyncio
    async def test_with_code(self, client: FHIRClient) -> None:
        respx.get("http://fhir.test/fhir/Observation").mock(
            return_value=httpx.Response(200, json=BUNDLE_OBSERVATIONS)
        )
        results = await client.get_observations("patient-1", code="2160-0")
        assert len(results) == 2


class TestCheckConnection:
    @respx.mock
    @pytest.mark.asyncio
    async def test_healthy(self, client: FHIRClient) -> None:
        respx.get("http://fhir.test/fhir/metadata").mock(
            return_value=httpx.Response(200, json={"resourceType": "CapabilityStatement"})
        )
        assert await client.check_connection() is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_unreachable(self, client: FHIRClient) -> None:
        respx.get("http://fhir.test/fhir/metadata").mock(
            side_effect=httpx.ConnectError("refused")
        )
        assert await client.check_connection() is False


# --- Tests: Parsers ---


class TestParseConditions:
    def test_parses_coding(self) -> None:
        raw = BUNDLE_CONDITIONS["entry"][0]["resource"]
        result = FHIRClient._parse_conditions([raw])
        assert len(result) == 1
        assert result[0].code == "N18.3"
        assert result[0].display == "DRC Estagio 3"
        assert result[0].clinical_status == "active"

    def test_empty_list(self) -> None:
        assert FHIRClient._parse_conditions([]) == []

    def test_missing_coding(self) -> None:
        raw = {"code": {}, "clinicalStatus": {"coding": [{"code": "active"}]}}
        result = FHIRClient._parse_conditions([raw])
        assert result[0].code == "unknown"


class TestParseObservations:
    def test_parses_quantity(self) -> None:
        raw = BUNDLE_OBSERVATIONS["entry"][0]["resource"]
        result = FHIRClient._parse_observations([raw])
        assert result[0].value == 1.5
        assert result[0].unit == "mg/dL"
        assert result[0].reference_low == 0.7
        assert result[0].reference_high == 1.2
        assert result[0].is_abnormal is True  # 1.5 > 1.2

    def test_parses_date(self) -> None:
        raw = BUNDLE_OBSERVATIONS["entry"][0]["resource"]
        result = FHIRClient._parse_observations([raw])
        assert result[0].date is not None
        assert result[0].date.year == 2026

    def test_no_reference_range(self) -> None:
        raw = BUNDLE_OBSERVATIONS["entry"][1]["resource"]
        result = FHIRClient._parse_observations([raw])
        assert result[0].reference_low is None
        assert result[0].reference_high is None


class TestParseAllergies:
    def test_parses_allergy(self) -> None:
        raw = BUNDLE_ALLERGIES["entry"][0]["resource"]
        result = FHIRClient._parse_allergies([raw])
        assert result[0].substance == "Dipirona"
        assert result[0].reaction == "Urticaria"
        assert result[0].severity == "high"

    def test_empty(self) -> None:
        assert FHIRClient._parse_allergies([]) == []


class TestParseMedications:
    def test_parses_medication(self) -> None:
        raw = BUNDLE_MEDICATIONS["entry"][0]["resource"]
        result = FHIRClient._parse_medications([raw])
        assert result[0].name == "Enalapril 10mg"
        assert result[0].code == "C09AA02"
        assert result[0].dosage == "10mg 1x/dia"
        assert result[0].status == "active"


# --- Tests: Patient Summary ---


class TestGetPatientSummary:
    @respx.mock
    @pytest.mark.asyncio
    async def test_full_summary(self, client: FHIRClient) -> None:
        respx.get("http://fhir.test/fhir/Patient/patient-1").mock(
            return_value=httpx.Response(200, json=PATIENT_RESOURCE)
        )
        respx.get("http://fhir.test/fhir/Condition").mock(
            return_value=httpx.Response(200, json=BUNDLE_CONDITIONS)
        )
        respx.get("http://fhir.test/fhir/Observation").mock(
            return_value=httpx.Response(200, json=BUNDLE_OBSERVATIONS)
        )
        respx.get("http://fhir.test/fhir/AllergyIntolerance").mock(
            return_value=httpx.Response(200, json=BUNDLE_ALLERGIES)
        )
        respx.get("http://fhir.test/fhir/MedicationRequest").mock(
            return_value=httpx.Response(200, json=BUNDLE_MEDICATIONS)
        )

        summary = await client.get_patient_summary("patient-1")
        assert summary.patient_id == "patient-1"
        assert summary.name == "Maria Silva Santos"
        assert summary.gender == "female"
        assert summary.cpf == "12345678901"
        assert summary.birth_date is not None
        assert summary.birth_date.year == 1985
        assert len(summary.conditions) == 1
        assert len(summary.observations) == 2
        assert len(summary.allergies) == 1
        assert len(summary.medications) == 1
        assert summary.age is not None
        assert summary.age >= 40  # nascida em 1985, estamos em 2026

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_clinical_data(self, client: FHIRClient) -> None:
        patient_minimal = {
            "resourceType": "Patient",
            "id": "patient-2",
            "gender": "male",
        }
        respx.get("http://fhir.test/fhir/Patient/patient-2").mock(
            return_value=httpx.Response(200, json=patient_minimal)
        )
        respx.get("http://fhir.test/fhir/Condition").mock(
            return_value=httpx.Response(200, json=EMPTY_BUNDLE)
        )
        respx.get("http://fhir.test/fhir/Observation").mock(
            return_value=httpx.Response(200, json=EMPTY_BUNDLE)
        )
        respx.get("http://fhir.test/fhir/AllergyIntolerance").mock(
            return_value=httpx.Response(200, json=EMPTY_BUNDLE)
        )
        respx.get("http://fhir.test/fhir/MedicationRequest").mock(
            return_value=httpx.Response(200, json=EMPTY_BUNDLE)
        )

        summary = await client.get_patient_summary("patient-2")
        assert summary.name == ""
        assert summary.cpf == ""
        assert summary.birth_date is None
        assert summary.age is None
        assert summary.conditions == []
        assert summary.observations == []
