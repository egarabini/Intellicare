"""API routes for the Rocket.Chat bot (EF-W012)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/bot", tags=["bot"])


class WebhookPayload(BaseModel):
    token: str = ""
    channel_id: str = ""
    channel_name: str = ""
    user_id: str = ""
    user_name: str = ""
    text: str = ""
    trigger_word: str = "@intellicare"
    user_token: str = ""


def _get_handler(request: Request):  # type: ignore[return]
    handler = getattr(request.app.state, "bot_handler", None)
    if handler is None:
        raise HTTPException(status_code=503, detail="RC Bot nao disponivel (enable_rc_bot=False)")
    return handler


@router.post("/command", summary="Webhook Rocket.Chat")
async def bot_command(payload: WebhookPayload, request: Request):
    handler = _get_handler(request)
    result = await handler.handle_webhook(payload.model_dump())
    return result


@router.get("/status", summary="Status do bot")
async def bot_status(request: Request):
    handler = _get_handler(request)
    return {
        "status": "online",
        "metrics": handler.metrics,
    }


@router.get("/commands", summary="Comandos disponíveis")
async def list_commands(request: Request):
    _get_handler(request)
    from wanda.bot.models import BotCommand  # noqa: PLC0415
    return {"commands": [c.value for c in BotCommand]}


@router.get("/metrics", summary="Métricas por comando")
async def bot_metrics(request: Request):
    handler = _get_handler(request)
    return handler.metrics


@router.get("/log", summary="Últimos 50 comandos (admin)")
async def bot_log(request: Request):
    handler = _get_handler(request)
    return {"commands": handler.recent_commands}
