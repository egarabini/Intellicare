"""Testes para FHIRDataStore (metodos utilitarios, sem DB)."""

from datetime import datetime, timezone

from oswaldo.datastore.fhir_datastore import FHIRDataStore


class TestExtractors:
    """Testa metodos de extracao sem necessidade de DB."""

    def _make_store(self) -> FHIRDataStore:
        # Nao conecta de fato — so para testar metodos utilitarios
        store = object.__new__(FHIRDataStore)
        return store

    def test_extract_patient_id_from_subject(self) -> None:
        store = self._make_store()
        resource = {"subject": {"reference": "Patient/p-123"}}
        assert store._extract_patient_id(resource) == "p-123"

    def test_extract_patient_id_from_patient_key(self) -> None:
        store = self._make_store()
        resource = {"patient": {"reference": "Patient/p-456"}}
        assert store._extract_patient_id(resource) == "p-456"

    def test_extract_patient_id_from_patient_id_field(self) -> None:
        store = self._make_store()
        resource = {"patient_id": "p-789"}
        assert store._extract_patient_id(resource) == "p-789"

    def test_extract_patient_id_none(self) -> None:
        store = self._make_store()
        resource = {}
        assert store._extract_patient_id(resource) is None

    def test_extract_code_from_coding(self) -> None:
        store = self._make_store()
        resource = {"code": {"coding": [{"code": "33914-3", "system": "http://loinc.org"}]}}
        assert store._extract_code(resource) == "33914-3"

    def test_extract_code_empty_coding(self) -> None:
        store = self._make_store()
        resource = {"code": {"coding": []}}
        assert store._extract_code(resource) is None

    def test_extract_code_no_code(self) -> None:
        store = self._make_store()
        resource = {}
        assert store._extract_code(resource) is None

    def test_extract_created_at_from_meta(self) -> None:
        store = self._make_store()
        resource = {"meta": {"lastUpdated": "2024-01-15T10:30:00Z"}}
        dt = store._extract_created_at(resource)
        assert isinstance(dt, datetime)
        assert dt.year == 2024
        assert dt.month == 1

    def test_extract_created_at_from_effective(self) -> None:
        store = self._make_store()
        resource = {"effectiveDateTime": "2024-06-20T14:00:00Z"}
        dt = store._extract_created_at(resource)
        assert dt.year == 2024
        assert dt.month == 6

    def test_extract_created_at_fallback_now(self) -> None:
        store = self._make_store()
        resource = {}
        dt = store._extract_created_at(resource)
        assert isinstance(dt, datetime)
        # Should be recent (within last minute)
        diff = (datetime.now(timezone.utc) - dt).total_seconds()
        assert diff < 60

    def test_extract_non_reference_subject(self) -> None:
        store = self._make_store()
        resource = {"subject": {"reference": "Organization/org-1"}}
        assert store._extract_patient_id(resource) is None
