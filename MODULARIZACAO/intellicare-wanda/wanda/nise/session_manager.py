"""Nise session manager — Redis TTL + PostgreSQL for LGPD archive (EF-W013)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from wanda.nise.models import NiseSession, SessionStatus

logger = logging.getLogger(__name__)

_SESSION_KEY = "wanda:nise:session:{session_id}"
_SESSION_TTL = 7200  # 2 hours


class NiseSessionManager:
    """Creates, retrieves, and archives Dr. Nise chat sessions.

    Redis: active session state (TTL 2h)
    PostgreSQL: permanent LGPD archive via NiseSessionModel
    """

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        session_factory: Optional[Any] = None,
        ttl_seconds: int = _SESSION_TTL,
        max_history: int = 20,
    ) -> None:
        self._redis = redis_client
        self._db = session_factory
        self._ttl = ttl_seconds
        self._max_history = max_history
        self._memory: dict[str, NiseSession] = {}  # in-memory fallback

    # ------------------------------------------------------------------
    # Get or create
    # ------------------------------------------------------------------

    async def get_or_create(
        self, patient_id: str, session_id: Optional[str], channel: str = "web"
    ) -> NiseSession:
        if session_id:
            existing = await self._load(session_id)
            if existing and existing.status == SessionStatus.ACTIVE:
                return existing

        session = NiseSession(patient_id=patient_id, channel=channel)
        await self._save(session)
        logger.debug("New Nise session %s for patient %s", session.session_id, patient_id)
        return session

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def append_message(self, session: NiseSession, role: str, content: str) -> None:
        session.history.append({"role": role, "content": content})
        if len(session.history) > self._max_history * 2:
            session.history = session.history[-(self._max_history * 2):]
        session.message_count += 1
        await self._save(session)

    async def flag_message(self, session: NiseSession) -> None:
        session.flagged_count += 1
        await self._save(session)

    async def escalate(self, session: NiseSession) -> None:
        session.escalated = True
        session.status = SessionStatus.ESCALATED
        await self._save(session)

    async def end_session(self, session: NiseSession) -> None:
        session.status = SessionStatus.ENDED
        session.ended_at = datetime.now(timezone.utc)
        await self._save(session)
        await self._archive(session)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _save(self, session: NiseSession) -> None:
        key = _SESSION_KEY.format(session_id=session.session_id)
        data = {
            "patient_id": session.patient_id,
            "session_id": session.session_id,
            "channel": session.channel,
            "started_at": session.started_at.isoformat(),
            "message_count": session.message_count,
            "flagged_count": session.flagged_count,
            "escalated": session.escalated,
            "status": session.status.value,
            "history": session.history,
        }
        if self._redis is not None:
            try:
                await self._redis.set(key, json.dumps(data), ex=self._ttl)
                return
            except Exception as exc:
                logger.warning("Redis session save failed: %s", exc)
        self._memory[session.session_id] = session

    async def _load(self, session_id: str) -> Optional[NiseSession]:
        key = _SESSION_KEY.format(session_id=session_id)
        if self._redis is not None:
            try:
                raw = await self._redis.get(key)
                if raw:
                    data = json.loads(raw)
                    return self._from_dict(data)
            except Exception as exc:
                logger.warning("Redis session load failed: %s", exc)
        return self._memory.get(session_id)

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> NiseSession:
        session = NiseSession(
            patient_id=data["patient_id"],
            channel=data.get("channel", "web"),
            session_id=data["session_id"],
        )
        session.message_count = data.get("message_count", 0)
        session.flagged_count = data.get("flagged_count", 0)
        session.escalated = data.get("escalated", False)
        session.status = SessionStatus(data.get("status", "ACTIVE"))
        session.history = data.get("history", [])
        return session

    async def _archive(self, session: NiseSession) -> None:
        """Persist session to PostgreSQL for LGPD long-term archive."""
        if self._db is None:
            return
        try:
            from wanda.database.models import NiseSessionModel  # noqa: PLC0415

            async with self._db() as db_session:
                model = NiseSessionModel(
                    patient_id=session.patient_id,
                    session_id=session.session_id,
                    channel=session.channel,
                    started_at=session.started_at,
                    ended_at=session.ended_at,
                    message_count=session.message_count,
                    flagged_count=session.flagged_count,
                    escalated=session.escalated,
                    status=session.status.value,
                )
                db_session.add(model)
                await db_session.commit()
        except Exception as exc:
            logger.error("Failed to archive Nise session %s: %s", session.session_id, exc)
