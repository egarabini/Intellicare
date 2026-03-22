"""DEM-071 — Testes da Linha do Tempo Clínica.

Cobre:
  - TimelineEvent / ClinicalTimelineResponse schemas
  - CuidadoService.clinical_timeline() aggregator
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.cuidado.schemas import (
    ClinicalTimelineResponse,
    TimelineEvent,
)
from modules.cuidado.service import CuidadoService
from intellicare_core.contracts.base import TenantContext


CLINICO_CTX = TenantContext(
    tenant_id="tenant_dev",
    schema="tenant_tenant_dev",
    user_id="clinico-uid",
    roles=["CLINICO"],
    email="clinico@test.dev",
)

NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestTimelineSchemas:
    def test_timeline_event_encounter(self):
        ev = TimelineEvent(
            event_type="encounter",
            event_id=str(uuid.uuid4()),
            occurred_at=NOW,
            title="Consulta — NORMAL",
            subtitle="Dor lombar",
            status="open",
            metadata={"cid10_code": "M54.5"},
        )
        assert ev.event_type == "encounter"
        assert ev.metadata["cid10_code"] == "M54.5"

    def test_timeline_event_note(self):
        ev = TimelineEvent(
            event_type="clinical_note",
            event_id="42",
            occurred_at=NOW,
            title="Nota SOAP — Dr. João",
            subtitle="Paciente relata melhora...",
        )
        assert ev.status is None
        assert ev.metadata is None

    def test_timeline_event_prescription(self):
        ev = TimelineEvent(
            event_type="prescription",
            event_id="7",
            occurred_at=NOW,
            title="Prescrição — Dr. Maria",
            subtitle="Dipirona, Omeprazol",
            status="ACTIVE",
            metadata={"item_count": 2},
        )
        assert ev.status == "ACTIVE"

    def test_timeline_event_care_task(self):
        ev = TimelineEvent(
            event_type="care_task",
            event_id=str(uuid.uuid4()),
            occurred_at=NOW,
            title="Jornada follow_up (whatsapp)",
            status="SENT",
        )
        assert ev.event_type == "care_task"

    def test_clinical_timeline_response(self):
        resp = ClinicalTimelineResponse(
            patient_id=str(uuid.uuid4()),
            total=2,
            items=[
                TimelineEvent(
                    event_type="encounter",
                    event_id="1",
                    occurred_at=NOW,
                    title="Consulta",
                ),
                TimelineEvent(
                    event_type="prescription",
                    event_id="2",
                    occurred_at=NOW,
                    title="Prescrição",
                ),
            ],
        )
        assert resp.total == 2
        assert len(resp.items) == 2


# ---------------------------------------------------------------------------
# Service aggregator tests
# ---------------------------------------------------------------------------

def _make_mappings(rows: list[dict]):
    """Builds a mock Result that supports .mappings().all()"""
    m = MagicMock()
    m.mappings.return_value.all.return_value = rows
    return m


class TestClinicalTimelineService:

    @pytest.mark.asyncio
    @patch("modules.cuidado.service.tenant_session")
    async def test_timeline_aggregates_encounters_and_notes(self, mock_ts):
        """Timeline should merge encounters + notes and sort by occurred_at DESC."""
        enc_id = str(uuid.uuid4())
        pid = uuid.uuid4()

        encounters = [
            {
                "id": enc_id, "status": "closed", "chief_complaint": "Dor",
                "priority": "normal", "cid10_code": "M54", "prescription": None,
                "opened_at": datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc),
                "closed_at": datetime(2026, 3, 20, 11, 0, tzinfo=timezone.utc),
            },
        ]
        notes = [
            {
                "id": 1, "encounter_id": enc_id, "note_type": "SOAP",
                "author_name": "Dr. João", "soap_s": "Paciente refere dor lombar",
                "soap_o": None, "soap_a": None, "soap_p": None,
                "free_text": None,
                "created_at": datetime(2026, 3, 20, 10, 15, tzinfo=timezone.utc),
            },
        ]
        prescriptions: list[dict] = []  # empty

        # Mock the tenant_session context manager and db.execute
        mock_db = AsyncMock()
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_mappings(encounters)
            elif call_count == 2:
                return _make_mappings(notes)
            elif call_count == 3:
                return _make_mappings(prescriptions)
            elif call_count == 4:
                # _table_exists for care_tasks
                return MagicMock(first=MagicMock(return_value=None))
            return _make_mappings([])

        mock_db.execute = AsyncMock(side_effect=side_effect)

        ctx_mgr = AsyncMock()
        ctx_mgr.__aenter__ = AsyncMock(return_value=mock_db)
        ctx_mgr.__aexit__ = AsyncMock(return_value=False)
        mock_ts.return_value = ctx_mgr

        svc = CuidadoService()
        result = await svc.clinical_timeline(CLINICO_CTX, pid, limit=50, offset=0)

        assert result["patient_id"] == str(pid)
        assert result["total"] == 2  # 1 encounter + 1 note
        assert result["items"][0]["occurred_at"] > result["items"][1]["occurred_at"]
        # Encounter at 10:00 < Note at 10:15 → note first (DESC)
        assert result["items"][0]["event_type"] == "clinical_note"
        assert result["items"][1]["event_type"] == "encounter"

    @pytest.mark.asyncio
    @patch("modules.cuidado.service.tenant_session")
    async def test_timeline_empty_for_new_patient(self, mock_ts):
        """New patient with no history returns empty list."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=[
            _make_mappings([]),  # encounters
            _make_mappings([]),  # notes
            _make_mappings([]),  # prescriptions
            MagicMock(first=MagicMock(return_value=None)),  # _table_exists → no care_tasks
        ])

        ctx_mgr = AsyncMock()
        ctx_mgr.__aenter__ = AsyncMock(return_value=mock_db)
        ctx_mgr.__aexit__ = AsyncMock(return_value=False)
        mock_ts.return_value = ctx_mgr

        svc = CuidadoService()
        result = await svc.clinical_timeline(CLINICO_CTX, uuid.uuid4())

        assert result["total"] == 0
        assert result["items"] == []

    @pytest.mark.asyncio
    @patch("modules.cuidado.service.tenant_session")
    async def test_timeline_with_prescriptions_and_care_tasks(self, mock_ts):
        """Timeline includes prescriptions and care tasks when present."""
        pid = uuid.uuid4()
        rx_items = json.dumps([{"drug": "Dipirona", "posology": "1x/dia", "duration": "7d"}])

        prescriptions = [{
            "id": 5, "encounter_id": str(uuid.uuid4()), "cid10_code": "J06",
            "cid10_desc": "IVAS", "items": rx_items, "notes": None,
            "status": "ACTIVE", "author_name": "Dra. Ana",
            "created_at": datetime(2026, 3, 19, 14, 0, tzinfo=timezone.utc),
        }]
        care_tasks = [{
            "correlation_id": uuid.uuid4(), "task_type": "follow_up",
            "status": "SENT", "channel": "whatsapp",
            "metadata": {"template_code": "pos_consulta"},
            "created_at": datetime(2026, 3, 21, 9, 0, tzinfo=timezone.utc),
        }]

        mock_db = AsyncMock()
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_mappings([])  # encounters
            elif call_count == 2:
                return _make_mappings([])  # notes
            elif call_count == 3:
                return _make_mappings(prescriptions)
            elif call_count == 4:
                # _table_exists → care_tasks exists
                return MagicMock(first=MagicMock(return_value=(1,)))
            elif call_count == 5:
                return _make_mappings(care_tasks)
            return _make_mappings([])

        mock_db.execute = AsyncMock(side_effect=side_effect)

        ctx_mgr = AsyncMock()
        ctx_mgr.__aenter__ = AsyncMock(return_value=mock_db)
        ctx_mgr.__aexit__ = AsyncMock(return_value=False)
        mock_ts.return_value = ctx_mgr

        svc = CuidadoService()
        result = await svc.clinical_timeline(CLINICO_CTX, pid)

        assert result["total"] == 2
        types = {item["event_type"] for item in result["items"]}
        assert "prescription" in types
        assert "care_task" in types
        # Care task (Mar 21) should be first (most recent)
        assert result["items"][0]["event_type"] == "care_task"

    @pytest.mark.asyncio
    @patch("modules.cuidado.service.tenant_session")
    async def test_timeline_pagination(self, mock_ts):
        """Offset/limit correctly paginates results."""
        pid = uuid.uuid4()
        # Create 5 encounters
        encounters = [
            {
                "id": str(uuid.uuid4()), "status": "closed",
                "chief_complaint": f"Queixa {i}", "priority": "normal",
                "cid10_code": None, "prescription": None,
                "opened_at": datetime(2026, 3, i + 1, 10, 0, tzinfo=timezone.utc),
                "closed_at": None,
            }
            for i in range(5)
        ]

        mock_db = AsyncMock()
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_mappings(encounters)
            elif call_count in (2, 3):
                return _make_mappings([])
            elif call_count == 4:
                return MagicMock(first=MagicMock(return_value=None))
            return _make_mappings([])

        mock_db.execute = AsyncMock(side_effect=side_effect)

        ctx_mgr = AsyncMock()
        ctx_mgr.__aenter__ = AsyncMock(return_value=mock_db)
        ctx_mgr.__aexit__ = AsyncMock(return_value=False)
        mock_ts.return_value = ctx_mgr

        svc = CuidadoService()
        result = await svc.clinical_timeline(CLINICO_CTX, pid, limit=2, offset=0)

        assert result["total"] == 5
        assert len(result["items"]) == 2
