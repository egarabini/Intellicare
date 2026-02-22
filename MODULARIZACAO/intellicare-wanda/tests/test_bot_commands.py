"""Tests for bot command handlers (EF-W012)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from wanda.bot.formatter import RocketChatResponseFormatter


@pytest.fixture
def formatter():
    return RocketChatResponseFormatter()


# ── /paciente ─────────────────────────────────────────────────────

class TestPacienteCommand:
    @pytest.mark.asyncio
    async def test_no_patient_id_returns_error(self, formatter):
        from wanda.bot.commands.paciente import handle_paciente
        text, attachments = await handle_paciente("", None, {}, None, formatter)
        assert "Informe" in text
        assert attachments == []

    @pytest.mark.asyncio
    async def test_with_patient_id_and_no_modules(self, formatter):
        from wanda.bot.commands.paciente import handle_paciente
        text, attachments = await handle_paciente("p1", None, {}, None, formatter)
        assert "p1" in text
        assert isinstance(attachments, list)

    @pytest.mark.asyncio
    async def test_with_florence_response(self, formatter):
        from wanda.bot.commands.paciente import handle_paciente
        http_mock = AsyncMock()
        http_mock.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            json=lambda: {"conditions": ["Diabetes", "HAS"]},
        ))
        module_urls = {"intellicare-florence": "http://florence:8002"}
        text, attachments = await handle_paciente("p1", http_mock, module_urls, None, formatter)
        assert "p1" in text
        assert len(attachments) > 0


# ── /guideline ────────────────────────────────────────────────────

class TestGuidelineCommand:
    @pytest.mark.asyncio
    async def test_no_query_returns_error(self, formatter):
        from wanda.bot.commands.guideline import handle_guideline
        text, attachments = await handle_guideline("", None, {}, formatter)
        assert "Informe" in text

    @pytest.mark.asyncio
    async def test_with_florence_rag_response(self, formatter):
        from wanda.bot.commands.guideline import handle_guideline
        http_mock = AsyncMock()
        http_mock.post = AsyncMock(return_value=MagicMock(
            status_code=200,
            json=lambda: {"answer": "Metformina é indicada como primeira linha..."},
        ))
        text, attachments = await handle_guideline(
            "tratamento diabetes", http_mock,
            {"intellicare-florence": "http://florence:8002"}, formatter
        )
        assert isinstance(attachments, list)
        assert len(attachments) > 0

    @pytest.mark.asyncio
    async def test_florence_connection_error_graceful(self, formatter):
        from wanda.bot.commands.guideline import handle_guideline
        http_mock = AsyncMock()
        http_mock.post = AsyncMock(side_effect=Exception("connection refused"))
        text, attachments = await handle_guideline(
            "tratamento dm2", http_mock,
            {"intellicare-florence": "http://florence:8002"}, formatter
        )
        # Should gracefully return error info, not raise
        assert isinstance(attachments, list)


# ── /resumo ───────────────────────────────────────────────────────

class TestResumoCommand:
    @pytest.mark.asyncio
    async def test_no_patient_id(self, formatter):
        from wanda.bot.commands.resumo import handle_resumo
        text, _ = await handle_resumo("", None, {}, formatter)
        assert "Informe" in text

    @pytest.mark.asyncio
    async def test_with_geralda_response(self, formatter):
        from wanda.bot.commands.resumo import handle_resumo
        http_mock = AsyncMock()
        http_mock.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            json=lambda: {"report": "Paciente compareceu a 3 consultas..."},
        ))
        text, attachments = await handle_resumo(
            "p1", http_mock, {"intellicare-geralda": "http://geralda:8006"}, formatter
        )
        assert "p1" in text
        assert len(attachments) > 0

    @pytest.mark.asyncio
    async def test_geralda_connection_error_graceful(self, formatter):
        from wanda.bot.commands.resumo import handle_resumo
        http_mock = AsyncMock()
        http_mock.get = AsyncMock(side_effect=Exception("timeout"))
        text, attachments = await handle_resumo(
            "p1", http_mock, {"intellicare-geralda": "http://geralda:8006"}, formatter
        )
        assert "p1" in text
        assert isinstance(attachments, list)


# ── /alerta ───────────────────────────────────────────────────────

class TestAlertaCommand:
    @pytest.mark.asyncio
    async def test_no_patient_returns_error(self, formatter):
        from wanda.bot.commands.alerta import handle_alerta
        text, _ = await handle_alerta("", "desc", "nurse1", None, formatter)
        assert "Informe" in text

    @pytest.mark.asyncio
    async def test_no_description_returns_error(self, formatter):
        from wanda.bot.commands.alerta import handle_alerta
        text, _ = await handle_alerta("p1", "", "nurse1", None, formatter)
        assert "Informe" in text

    @pytest.mark.asyncio
    async def test_creates_critical_alert(self, formatter):
        from wanda.bot.commands.alerta import handle_alerta
        hub = MagicMock()
        hub.receive_alert = AsyncMock(return_value=MagicMock(
            alert_id="a1", status="accepted", priority_score=90
        ))
        text, attachments = await handle_alerta("p1", "Paciente caiu", "dr-1", hub, formatter)
        assert "p1" in text
        hub.receive_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_hub_returns_error_text(self, formatter):
        from wanda.bot.commands.alerta import handle_alerta
        text, _ = await handle_alerta("p1", "desc", "user", None, formatter)
        assert "AlertHub" in text or "não disponível" in text.lower() or "disponivel" in text.lower()


# ── /ajuda ────────────────────────────────────────────────────────

class TestAjudaCommand:
    @pytest.mark.asyncio
    async def test_returns_help_text(self, formatter):
        from wanda.bot.commands.ajuda import handle_ajuda
        text, attachments = await handle_ajuda(formatter)
        assert "Olá" in text or "assistente" in text.lower()
        assert len(attachments) > 0

    @pytest.mark.asyncio
    async def test_attachments_contain_commands(self, formatter):
        from wanda.bot.commands.ajuda import handle_ajuda
        _, attachments = await handle_ajuda(formatter)
        combined = str(attachments)
        assert "/paciente" in combined or "paciente" in combined


# ── /status ───────────────────────────────────────────────────────

class TestStatusCommand:
    @pytest.mark.asyncio
    async def test_no_modules_returns_empty_table(self, formatter):
        from wanda.bot.commands.status import handle_status
        text, attachments = await handle_status(None, {}, formatter)
        assert len(attachments) > 0

    @pytest.mark.asyncio
    async def test_with_healthy_module(self, formatter):
        from wanda.bot.commands.status import handle_status
        http_mock = AsyncMock()
        http_mock.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            json=lambda: {"status": "healthy", "version": "2.0.0"},
        ))
        text, attachments = await handle_status(
            http_mock, {"intellicare-florence": "http://florence:8002"}, formatter
        )
        assert len(attachments) > 0
        assert "florence" in str(attachments).lower()

    @pytest.mark.asyncio
    async def test_with_module_connection_error(self, formatter):
        from wanda.bot.commands.status import handle_status
        http_mock = AsyncMock()
        http_mock.get = AsyncMock(side_effect=Exception("connection refused"))
        text, attachments = await handle_status(
            http_mock, {"intellicare-oswaldo": "http://oswaldo:8001"}, formatter
        )
        # Should still return status table (module marked unhealthy)
        assert len(attachments) > 0


# ── /teleconsulta ──────────────────────────────────────────────────

class TestTeleconsultaCommand:
    @pytest.mark.asyncio
    async def test_no_patient_id_returns_error(self, formatter):
        from wanda.bot.commands.teleconsulta import handle_teleconsulta
        text, attachments = await handle_teleconsulta("", None, {}, "user1", formatter)
        assert "Informe" in text
        assert attachments == []

    @pytest.mark.asyncio
    async def test_no_comunicacao_url_returns_unavailable(self, formatter):
        from wanda.bot.commands.teleconsulta import handle_teleconsulta
        text, attachments = await handle_teleconsulta("p1", None, {}, "user1", formatter)
        assert "p1" in text
        # Should return unavailable (no URL configured)
        assert isinstance(attachments, list)

    @pytest.mark.asyncio
    async def test_comunicacao_returns_room_url(self, formatter):
        from wanda.bot.commands.teleconsulta import handle_teleconsulta
        http_mock = AsyncMock()
        http_mock.post = AsyncMock(return_value=MagicMock(
            status_code=201,
            json=lambda: {"room_url": "https://meet.jit.si/intellicare-p1-abc123"},
        ))
        module_urls = {"intellicare-comunicacao": "http://comunicacao:8005"}
        text, attachments = await handle_teleconsulta("p1", http_mock, module_urls, "dr1", formatter)
        assert "p1" in text
        assert any("jit.si" in str(a) for a in attachments)

    @pytest.mark.asyncio
    async def test_comunicacao_returns_url_field(self, formatter):
        from wanda.bot.commands.teleconsulta import handle_teleconsulta
        http_mock = AsyncMock()
        http_mock.post = AsyncMock(return_value=MagicMock(
            status_code=200,
            json=lambda: {"url": "https://meet.jit.si/room-xyz"},
        ))
        module_urls = {"intellicare-comunicacao": "http://comunicacao:8005"}
        text, attachments = await handle_teleconsulta("p1", http_mock, module_urls, "nurse1", formatter)
        assert "p1" in text
        assert any("jit.si" in str(a) for a in attachments)

    @pytest.mark.asyncio
    async def test_comunicacao_request_error_graceful(self, formatter):
        from wanda.bot.commands.teleconsulta import handle_teleconsulta
        import httpx
        http_mock = AsyncMock()
        http_mock.post = AsyncMock(side_effect=Exception("connection refused"))
        module_urls = {"intellicare-comunicacao": "http://comunicacao:8005"}
        text, attachments = await handle_teleconsulta("p1", http_mock, module_urls, "user1", formatter)
        # Should gracefully degrade
        assert "p1" in text
        assert isinstance(attachments, list)
