"""Audit logger — records all Nise messages to PostgreSQL for LGPD compliance (EF-W013)."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class NiseAuditLogger:
    """Persists each message exchange to the nise_messages table.

    Stores: session_id, role (patient/nise), content, flagged, created_at.
    Silently no-ops when DB is not configured.
    """

    def __init__(self, session_factory: Optional[Any] = None) -> None:
        self._db = session_factory
        self._buffer: list[dict[str, Any]] = []  # in-memory log when DB unavailable

    async def log(
        self,
        session_id: str,
        role: str,
        content: str,
        flagged: bool = False,
    ) -> None:
        entry = {
            "session_id": session_id,
            "role": role,
            "content": content[:5000],  # truncate for DB
            "flagged": flagged,
        }
        if self._db is None:
            self._buffer.append(entry)
            if len(self._buffer) > 1000:
                self._buffer = self._buffer[-500:]
            return
        try:
            from wanda.database.models import NiseMessageModel  # noqa: PLC0415

            async with self._db() as session:
                msg = NiseMessageModel(
                    session_id=session_id,
                    role=role,
                    content=content[:5000],
                    flagged=flagged,
                )
                session.add(msg)
                await session.commit()
        except Exception as exc:
            logger.error("NiseAuditLogger.log failed: %s", exc)
            self._buffer.append(entry)

    @property
    def recent_logs(self) -> list[dict[str, Any]]:
        return list(self._buffer[-50:])
