"""Cliente Matrix para envio de mensagens no IntelliCare."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

try:
    from nio import AsyncClient, InviteMemberEvent, LoginResponse, MatrixRoom, RoomMessageText
except ImportError:  # pragma: no cover - fallback para ambiente sem dependencia
    AsyncClient = None  # type: ignore[assignment]
    LoginResponse = object  # type: ignore[assignment]
    InviteMemberEvent = object  # type: ignore[assignment]
    MatrixRoom = object  # type: ignore[assignment]
    RoomMessageText = object  # type: ignore[assignment]

from comunicacao.config import ComunicacaoConfig

logger = logging.getLogger(__name__)


class MatrixClientService:
    """Servico para autenticar e enviar mensagens no Matrix."""

    def __init__(self, config: ComunicacaoConfig):
        self.config = config
        self.client = None
        self._bot_task: asyncio.Task[None] | None = None
        self._bot_callbacks_registered = False

        if AsyncClient is None:
            logger.warning("matrix-nio nao instalado; servico Matrix em modo degradado")
            return

        self.client = AsyncClient(
            self.config.matrix_homeserver_url,
            self.config.matrix_username,
            device_id=self.config.matrix_device_id,
        )

    async def login(self) -> bool:
        """Realiza login no homeserver Matrix."""
        if self.client is None:
            return False

        try:
            response = await asyncio.wait_for(
                self.client.login(
                    password=self.config.matrix_password,
                    device_name="intellicare-comunicacao",
                ),
                timeout=self.config.matrix_login_timeout_seconds,
            )
        except TimeoutError:
            logger.error("Matrix login timed out after %ss", self.config.matrix_login_timeout_seconds)
            return False
        if isinstance(response, LoginResponse):
            logger.info("Matrix login success for %s", self.config.matrix_username)
            return True

        logger.error("Matrix login failed: %s", response)
        return False

    async def ensure_login(self) -> bool:
        if self.client is None:
            return False
        if getattr(self.client, "logged_in", False):
            return True
        return await self.login()

    async def send_text_message(self, room_id: str, message: str) -> dict[str, Any]:
        """Envia mensagem de texto para sala Matrix."""
        try:
            if not room_id:
                return {"ok": False, "error": "room_id is required"}

            if self.client is None:
                return {"ok": False, "error": "matrix-nio nao instalado"}

            if not await self.ensure_login():
                return {"ok": False, "error": "matrix login failed"}

            response = await asyncio.wait_for(
                self.client.room_send(
                    room_id=room_id,
                    message_type="m.room.message",
                    content={"msgtype": "m.text", "body": message},
                ),
                timeout=self.config.matrix_send_timeout_seconds,
            )

            event_id = getattr(response, "event_id", None)
            if event_id:
                return {"ok": True, "room_id": room_id, "event_id": event_id}

            return {"ok": False, "room_id": room_id, "error": str(response)}
        except TimeoutError:
            return {
                "ok": False,
                "room_id": room_id,
                "error": f"matrix send timed out after {self.config.matrix_send_timeout_seconds}s",
            }
        except Exception as exc:
            return {"ok": False, "room_id": room_id, "error": str(exc)}

    async def create_room(
        self,
        name: str,
        topic: str | None = None,
        is_direct: bool = False,
        invite: list[str] | None = None,
    ) -> dict[str, Any]:
        """Cria uma sala Matrix."""
        try:
            if not name:
                return {"ok": False, "error": "room name is required"}
            if self.client is None:
                return {"ok": False, "error": "matrix-nio nao instalado"}
            if not await self.ensure_login():
                return {"ok": False, "error": "matrix login failed"}

            response = await self.client.room_create(
                name=name,
                topic=topic or "",
                is_direct=is_direct,
                invite=invite or [],
                preset="private_chat",
            )
            room_id = getattr(response, "room_id", None)
            if room_id:
                return {"ok": True, "room_id": room_id}
            return {"ok": False, "error": str(response)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def invite_user_to_room(self, room_id: str, user_id: str) -> dict[str, Any]:
        """Convida um usuario Matrix para uma sala."""
        try:
            if not room_id:
                return {"ok": False, "error": "room_id is required"}
            if not user_id:
                return {"ok": False, "error": "user_id is required"}
            if self.client is None:
                return {"ok": False, "error": "matrix-nio nao instalado"}
            if not await self.ensure_login():
                return {"ok": False, "error": "matrix login failed"}

            response = await self.client.room_invite(room_id=room_id, user_id=user_id)
            if response.__class__.__name__ == "RoomInviteResponse":
                return {"ok": True, "room_id": room_id, "user_id": user_id}
            if getattr(response, "transport_response", None) and getattr(response.transport_response, "status", None) == 200:
                return {"ok": True, "room_id": room_id, "user_id": user_id}
            return {"ok": False, "room_id": room_id, "user_id": user_id, "error": str(response)}
        except Exception as exc:
            return {"ok": False, "room_id": room_id, "user_id": user_id, "error": str(exc)}

    def bot_status(self) -> dict[str, Any]:
        running = self._bot_task is not None and not self._bot_task.done()
        return {"ok": True, "running": running, "mode": "geralda-basic"}

    async def start_bot(self, help_message: str | None = None) -> dict[str, Any]:
        """Inicia bot basico da Geralda com !ajuda e auto-join em convites."""
        if self.client is None:
            return {"ok": False, "error": "matrix-nio nao instalado"}
        if self._bot_task is not None and not self._bot_task.done():
            return {"ok": True, "running": True, "already_running": True}
        if not await self.ensure_login():
            return {"ok": False, "error": "matrix login failed"}

        if not self._bot_callbacks_registered:
            await self._register_bot_callbacks(help_message=help_message)
            self._bot_callbacks_registered = True

        self._bot_task = asyncio.create_task(self._bot_sync_loop(), name="geralda-bot-sync")
        return {"ok": True, "running": True}

    async def stop_bot(self) -> dict[str, Any]:
        if self._bot_task is None or self._bot_task.done():
            self._bot_task = None
            return {"ok": True, "running": False}

        self._bot_task.cancel()
        try:
            await self._bot_task
        except asyncio.CancelledError:
            pass
        finally:
            self._bot_task = None
        return {"ok": True, "running": False}

    async def _register_bot_callbacks(self, help_message: str | None = None) -> None:
        assert self.client is not None
        msg = help_message or (
            "Oi, eu sou a Geralda. Comandos: !ajuda, !status. "
            "Posso apoiar no acompanhamento do paciente."
        )

        async def on_invite(room: MatrixRoom, event: InviteMemberEvent) -> None:
            if getattr(event, "state_key", None) == self.config.matrix_username:
                await self.client.join(room.room_id)

        async def on_message(room: MatrixRoom, event: RoomMessageText) -> None:
            sender = getattr(event, "sender", "")
            body = (getattr(event, "body", "") or "").strip().lower()
            if sender == self.config.matrix_username:
                return
            if body.startswith("!ajuda"):
                await self.send_text_message(room.room_id, msg)
            elif body.startswith("!status"):
                await self.send_text_message(room.room_id, "Geralda online e pronta para apoiar.")

        self.client.add_event_callback(on_invite, InviteMemberEvent)
        self.client.add_event_callback(on_message, RoomMessageText)

    async def _bot_sync_loop(self) -> None:
        assert self.client is not None
        while True:
            await self.client.sync(timeout=30_000, full_state=False)

    async def logout(self) -> None:
        if self.client is not None and getattr(self.client, "logged_in", False):
            await self.client.logout()

    async def close(self) -> None:
        await self.stop_bot()
        if self.client is not None:
            await self.client.close()
