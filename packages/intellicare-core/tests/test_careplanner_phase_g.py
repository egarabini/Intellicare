"""Testes DEM-042 — notificacoes CarePlanner."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from modules.careplanner.integrations import notify_clinico_replied


@pytest.mark.asyncio
async def test_notify_replied_publica_broadcast():
    """notify_clinico_replied deve publicar broadcast mesmo sem clinico_ref."""
    ctx = MagicMock()
    ctx.tenant_id = "tenant_alfa"

    with patch(
        "modules.notifications.redis_pubsub.publish_broadcast",
        new_callable=AsyncMock,
    ) as mock_broadcast:
        await notify_clinico_replied(
            ctx=ctx,
            correlation_id=uuid4(),
            task_type="CHECK_IN",
            patient_ref="paciente.teste",
            clinico_ref=None,
            content="Estou bem, obrigado",
        )
        mock_broadcast.assert_called_once()
        call_payload = mock_broadcast.call_args[0][1]
        assert call_payload["data"]["module"] == "careplanner"
        assert call_payload["data"]["event"] == "REPLIED"


@pytest.mark.asyncio
async def test_notify_replied_persiste_para_clinico():
    """notify_clinico_replied deve persistir no banco quando clinico_ref fornecido."""
    ctx = MagicMock()
    ctx.tenant_id = "tenant_alfa"

    with patch(
        "modules.notifications.service.NotificationService.send",
        new_callable=AsyncMock,
    ) as mock_send, patch(
        "modules.notifications.redis_pubsub.publish_broadcast",
        new_callable=AsyncMock,
    ):
        await notify_clinico_replied(
            ctx=ctx,
            correlation_id=uuid4(),
            task_type="CHECK_IN",
            patient_ref="paciente.teste",
            clinico_ref="dr.silva",
            content="Estou com dor",
        )
        mock_send.assert_called_once()
        notif_arg = mock_send.call_args[0][1]
        assert notif_arg.user_id == "dr.silva"
        assert notif_arg.type == "message"
        assert notif_arg.priority == "high"
