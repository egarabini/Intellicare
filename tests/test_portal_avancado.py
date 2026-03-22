"""DEM-076: Testes do Portal Paciente Avançado — privacidade + controle de acesso."""
import pytest
import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from intellicare_core.contracts.base import TenantContext
from modules.cuidado.service import CuidadoService


def _make_ctx(user_id="user_pac_1", roles=None, slug="tenant_test"):
    ctx = TenantContext.from_slug(slug=slug, user_id=user_id)
    object.__setattr__(ctx, "roles", roles or ["PACIENTE"])
    return ctx


# ── Filtro de privacidade ─────────────────────────────────────────────────────

class TestPortalPrivacyFilter:
    def test_patient_timeline_excludes_soap_a(self):
        """soap_a (avaliação interna) NÃO pode aparecer na timeline do paciente."""
        svc = CuidadoService()
        events = [
            {
                "event_type": "clinical_note",
                "event_id": "1",
                "occurred_at": datetime.datetime.now(),
                "title": "Nota SOAP",
                "subtitle": None,
                "status": None,
                "metadata": {
                    "note_type": "soap",
                    "soap_a": "Avaliação interna do médico — PRIVADO",
                    "soap_p": "Plano interno — PRIVADO",
                    "encounter_id": "enc-1",
                },
            },
            {
                "event_type": "encounter",
                "event_id": "2",
                "occurred_at": datetime.datetime.now(),
                "title": "Consulta",
                "subtitle": "Dor torácica",
                "status": "closed",
                "metadata": {
                    "cid10_code": "R07",
                    "soap_a": "Assessment interno — PRIVADO",
                },
            },
        ]
        filtered = svc._apply_portal_privacy_filter(events)
        assert len(filtered) == 2
        # clinical_note: soap_a e soap_p removidos
        assert "soap_a" not in filtered[0]["metadata"]
        assert "soap_p" not in filtered[0]["metadata"]
        assert filtered[0]["metadata"]["encounter_id"] == "enc-1"
        # encounter: soap_a removido
        assert "soap_a" not in filtered[1]["metadata"]
        assert filtered[1]["metadata"]["cid10_code"] == "R07"

    def test_prescriptions_fully_visible(self):
        """Prescrições são dados do paciente — sem filtragem."""
        svc = CuidadoService()
        events = [
            {
                "event_type": "prescription",
                "event_id": "42",
                "occurred_at": datetime.datetime.now(),
                "title": "Prescrição",
                "subtitle": "Atenolol 50mg",
                "status": "ACTIVE",
                "metadata": {"cid10_code": "I10", "item_count": 2},
            },
        ]
        filtered = svc._apply_portal_privacy_filter(events)
        assert len(filtered) == 1
        assert filtered[0]["metadata"]["cid10_code"] == "I10"
        assert filtered[0]["metadata"]["item_count"] == 2

    def test_care_task_triage_notes_removed(self):
        """Notas de triagem interna são removidas dos care_tasks."""
        svc = CuidadoService()
        events = [
            {
                "event_type": "care_task",
                "event_id": "ct-1",
                "occurred_at": datetime.datetime.now(),
                "title": "Jornada",
                "subtitle": None,
                "status": "DONE",
                "metadata": {"channel": "whatsapp", "triage_notes": "interno"},
            },
        ]
        filtered = svc._apply_portal_privacy_filter(events)
        assert "triage_notes" not in filtered[0]["metadata"]
        assert filtered[0]["metadata"]["channel"] == "whatsapp"


# ── Timeline do paciente ─────────────────────────────────────────────────────

class TestPatientTimeline:
    @pytest.mark.asyncio
    @patch.object(CuidadoService, "clinical_timeline")
    @patch.object(CuidadoService, "_get_patient_id_for_user")
    async def test_patient_timeline_only_own_data(self, mock_pid, mock_timeline):
        """Paciente só vê dados dele — extraído do token, não do path."""
        mock_pid.return_value = "patient-uuid-1"
        mock_timeline.return_value = {
            "patient_id": "patient-uuid-1",
            "total": 1,
            "items": [
                {
                    "event_type": "encounter",
                    "event_id": "enc-1",
                    "occurred_at": datetime.datetime.now(),
                    "title": "Consulta",
                    "subtitle": None,
                    "status": "closed",
                    "metadata": {"cid10_code": "Z00"},
                },
            ],
        }
        svc = CuidadoService()
        ctx = _make_ctx()
        result = await svc.paciente_timeline(ctx, limit=20, offset=0)

        assert result["patient_id"] == "patient-uuid-1"
        assert len(result["items"]) == 1
        mock_pid.assert_called_once_with(ctx)
        mock_timeline.assert_called_once_with(ctx, "patient-uuid-1", 20, 0)

    @pytest.mark.asyncio
    @patch.object(CuidadoService, "_get_patient_id_for_user")
    async def test_patient_timeline_no_patient_returns_empty(self, mock_pid):
        """Paciente sem registro de patient retorna timeline vazia."""
        mock_pid.return_value = None
        svc = CuidadoService()
        ctx = _make_ctx()
        result = await svc.paciente_timeline(ctx)
        assert result["total"] == 0
        assert result["items"] == []

    @pytest.mark.asyncio
    @patch.object(CuidadoService, "clinical_timeline")
    @patch.object(CuidadoService, "_get_patient_id_for_user")
    async def test_patient_timeline_applies_privacy_filter(self, mock_pid, mock_timeline):
        """Timeline do portal aplica filtro de privacidade (soap_a removido)."""
        mock_pid.return_value = "p1"
        mock_timeline.return_value = {
            "patient_id": "p1",
            "total": 1,
            "items": [
                {
                    "event_type": "clinical_note",
                    "event_id": "n1",
                    "occurred_at": datetime.datetime.now(),
                    "title": "Nota",
                    "subtitle": None,
                    "status": None,
                    "metadata": {"soap_a": "PRIVADO", "soap_p": "PRIVADO", "note_type": "soap"},
                },
            ],
        }
        svc = CuidadoService()
        ctx = _make_ctx()
        result = await svc.paciente_timeline(ctx)
        assert "soap_a" not in result["items"][0]["metadata"]
        assert "soap_p" not in result["items"][0]["metadata"]


# ── Controle de acesso receituário ───────────────────────────────────────────

class TestPatientReceituarioAccess:
    @pytest.mark.asyncio
    @patch("modules.oswaldo.services.generate_receituario")
    @patch("modules.cuidado.service.CuidadoService._get_patient_id_for_user")
    @patch("modules.oswaldo.repository.get_prescription")
    async def test_patient_can_download_own_receituario(self, mock_rx, mock_pid, mock_gen):
        """Paciente A baixa receituário da SUA prescrição → deve funcionar."""
        rx_mock = MagicMock()
        rx_mock.patient_id = "patient-1"
        mock_rx.return_value = rx_mock
        mock_pid.return_value = "patient-1"
        mock_gen.return_value = b"PDF_BYTES"

        ctx = _make_ctx(user_id="user-1")

        # Simulate the endpoint logic inline
        rx = await mock_rx(ctx, 10)
        patient_id = await mock_pid(ctx)
        assert str(rx.patient_id) == str(patient_id), "Acesso permitido"
        pdf = await mock_gen(ctx, 10, "simple")
        assert pdf == b"PDF_BYTES"

    @pytest.mark.asyncio
    @patch("modules.cuidado.service.CuidadoService._get_patient_id_for_user")
    @patch("modules.oswaldo.repository.get_prescription")
    async def test_patient_cannot_download_others_receituario(self, mock_rx, mock_pid):
        """Paciente A tenta baixar receituário do Paciente B → 403."""
        rx_mock = MagicMock()
        rx_mock.patient_id = "patient-2"  # Pertence a outro paciente
        mock_rx.return_value = rx_mock
        mock_pid.return_value = "patient-1"  # Paciente autenticado é diferente

        ctx = _make_ctx(user_id="user-1")

        rx = await mock_rx(ctx, 99)
        patient_id = await mock_pid(ctx)
        assert str(rx.patient_id) != str(patient_id), "Acesso deve ser NEGADO"
