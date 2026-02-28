"""Testes para FHIRService."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.models.fhir_resource import FHIRResource
from grahame.services.fhir_service import FHIRService

from .conftest import OBSERVATION_HEARTRATE, PATIENT_SANTOS, PATIENT_SILVA


class TestFHIRServiceGet:
    async def test_get_existing_resource(
        self, session: AsyncSession, patient_silva: FHIRResource
    ):
        svc = FHIRService(session)
        row = await svc.get("Patient", "patient-123")
        assert row.fhir_id == "patient-123"
        assert row.resource["name"][0]["family"] == "Silva"

    async def test_get_not_found(self, session: AsyncSession):
        svc = FHIRService(session)
        with pytest.raises(HTTPException) as exc:
            await svc.get("Patient", "inexistente")
        assert exc.value.status_code == 404

    async def test_get_deleted_returns_404(
        self, session: AsyncSession, patient_silva: FHIRResource
    ):
        patient_silva.active = False
        await session.commit()
        svc = FHIRService(session)
        with pytest.raises(HTTPException) as exc:
            await svc.get("Patient", "patient-123")
        assert exc.value.status_code == 404


class TestFHIRServiceSearch:
    async def test_search_empty(self, session: AsyncSession):
        svc = FHIRService(session)
        results = await svc.search("Patient")
        assert results == []

    async def test_search_returns_all(
        self, session: AsyncSession, patient_silva: FHIRResource
    ):
        svc = FHIRService(session)
        results = await svc.search("Patient")
        assert len(results) == 1

    async def test_search_by_name_family(
        self, session: AsyncSession, patient_silva: FHIRResource
    ):
        svc = FHIRService(session)
        results = await svc.search_patient_by_name("silva")
        assert len(results) == 1
        assert results[0].fhir_id == "patient-123"

    async def test_search_by_name_given(
        self, session: AsyncSession, patient_silva: FHIRResource
    ):
        svc = FHIRService(session)
        results = await svc.search_patient_by_name("joão")
        assert len(results) == 1

    async def test_search_by_name_no_match(
        self, session: AsyncSession, patient_silva: FHIRResource
    ):
        svc = FHIRService(session)
        results = await svc.search_patient_by_name("naoexiste")
        assert results == []

    async def test_search_observation_by_patient(
        self, session: AsyncSession, observation_heartrate: FHIRResource
    ):
        svc = FHIRService(session)
        results = await svc.search_observation_by_patient("patient-123")
        assert len(results) == 1
        assert results[0].fhir_id == "obs-001"

    async def test_search_observation_by_patient_ref(
        self, session: AsyncSession, observation_heartrate: FHIRResource
    ):
        svc = FHIRService(session)
        results = await svc.search_observation_by_patient("Patient/patient-123")
        assert len(results) == 1

    async def test_search_observation_by_other_patient(
        self, session: AsyncSession, observation_heartrate: FHIRResource
    ):
        svc = FHIRService(session)
        results = await svc.search_observation_by_patient("patient-456")
        assert results == []

    async def test_search_respects_limit(self, session: AsyncSession):
        svc = FHIRService(session)
        for i in range(5):
            resource = {**PATIENT_SILVA, "id": f"p-{i}"}
            await svc.upsert(resource)
        await session.commit()

        results = await svc.search("Patient", limit=3)
        assert len(results) == 3


class TestFHIRServiceUpsert:
    async def test_create_new_resource(self, session: AsyncSession):
        svc = FHIRService(session)
        row = await svc.upsert(PATIENT_SILVA)
        assert row.fhir_id == "patient-123"
        assert row.resource_type == "Patient"
        assert row.active is True

    async def test_upsert_updates_existing(
        self, session: AsyncSession, patient_silva: FHIRResource
    ):
        svc = FHIRService(session)
        updated = {**PATIENT_SILVA, "gender": "unknown"}
        row = await svc.upsert(updated)
        assert row.resource["gender"] == "unknown"
        assert row.fhir_id == "patient-123"

    async def test_upsert_missing_resource_type(self, session: AsyncSession):
        svc = FHIRService(session)
        with pytest.raises(HTTPException) as exc:
            await svc.upsert({"id": "x"})
        assert exc.value.status_code == 422

    async def test_upsert_missing_id(self, session: AsyncSession):
        svc = FHIRService(session)
        with pytest.raises(HTTPException) as exc:
            await svc.upsert({"resourceType": "Patient"})
        assert exc.value.status_code == 422

    async def test_upsert_restores_deleted(
        self, session: AsyncSession, patient_silva: FHIRResource
    ):
        svc = FHIRService(session)
        await svc.delete("Patient", "patient-123")
        await session.commit()

        row = await svc.upsert(PATIENT_SILVA)
        assert row.active is True


class TestFHIRServiceDelete:
    async def test_soft_delete(
        self, session: AsyncSession, patient_silva: FHIRResource
    ):
        svc = FHIRService(session)
        await svc.delete("Patient", "patient-123")
        await session.commit()

        assert patient_silva.active is False

    async def test_delete_not_found(self, session: AsyncSession):
        svc = FHIRService(session)
        with pytest.raises(HTTPException) as exc:
            await svc.delete("Patient", "ghost")
        assert exc.value.status_code == 404


class TestFHIRServiceMultiTenant:
    async def test_tenant_isolation(self, session: AsyncSession):
        svc_a = FHIRService(session, tenant_id="tenant-a")
        svc_b = FHIRService(session, tenant_id="tenant-b")

        await svc_a.upsert(PATIENT_SILVA)
        await session.commit()

        results_a = await svc_a.search("Patient")
        results_b = await svc_b.search("Patient")

        assert len(results_a) == 1
        assert len(results_b) == 0
