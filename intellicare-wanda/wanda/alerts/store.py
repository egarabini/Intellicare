"""Alert store — SQLAlchemy repository for ClinicalAlertModel (EF-W007)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AlertStore:
    """Persists and retrieves ClinicalAlertModel records.

    Requires an async SQLAlchemy session factory.
    Falls back gracefully when DB is unavailable (log-only mode).
    """

    def __init__(self, session_factory: Optional[Any] = None) -> None:
        self._factory = session_factory

    async def save_alert(self, alert_dict: dict[str, Any]) -> bool:
        """Persist a new alert. Returns True on success."""
        if self._factory is None:
            logger.debug("AlertStore: no DB, skipping persist for %s", alert_dict.get("alert_id"))
            return False
        try:
            from wanda.database.models import ClinicalAlertModel  # noqa: PLC0415

            async with self._factory() as session:
                model = ClinicalAlertModel(
                    alert_id=alert_dict["alert_id"],
                    patient_id=alert_dict["patient_id"],
                    source_agent=alert_dict["source_agent"],
                    alert_type=alert_dict["alert_type"],
                    severity=alert_dict.get("adjusted_severity", alert_dict["severity"]),
                    title=alert_dict["title"],
                    description=alert_dict.get("description", ""),
                    recommended_action=alert_dict.get("recommended_action", ""),
                    clinical_data=alert_dict.get("clinical_data", {}),
                    priority_score=alert_dict.get("priority_score", 0),
                    is_consolidated=alert_dict.get("is_consolidated", False),
                    consolidated_from=alert_dict.get("consolidated_from", []),
                    status="pending",
                    idempotency_key=alert_dict.get("idempotency_key"),
                )
                session.add(model)
                await session.commit()
                return True
        except Exception as exc:
            logger.error("AlertStore.save_alert failed: %s", exc)
            return False

    async def get_pending(
        self,
        limit: int = 50,
        patient_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Retrieve pending alerts ordered by priority_score DESC."""
        if self._factory is None:
            return []
        try:
            from sqlalchemy import select  # noqa: PLC0415
            from wanda.database.models import ClinicalAlertModel  # noqa: PLC0415

            async with self._factory() as session:
                stmt = (
                    select(ClinicalAlertModel)
                    .where(ClinicalAlertModel.status == "pending")
                    .order_by(ClinicalAlertModel.priority_score.desc())
                    .limit(limit)
                )
                if patient_id:
                    stmt = stmt.where(ClinicalAlertModel.patient_id == patient_id)
                result = await session.execute(stmt)
                rows = result.scalars().all()
                return [self._to_dict(r) for r in rows]
        except Exception as exc:
            logger.error("AlertStore.get_pending failed: %s", exc)
            return []

    async def get_by_patient(self, patient_id: str) -> list[dict[str, Any]]:
        if self._factory is None:
            return []
        try:
            from sqlalchemy import select  # noqa: PLC0415
            from wanda.database.models import ClinicalAlertModel  # noqa: PLC0415

            async with self._factory() as session:
                stmt = (
                    select(ClinicalAlertModel)
                    .where(ClinicalAlertModel.patient_id == patient_id)
                    .order_by(ClinicalAlertModel.created_at.desc())
                    .limit(100)
                )
                result = await session.execute(stmt)
                return [self._to_dict(r) for r in result.scalars().all()]
        except Exception as exc:
            logger.error("AlertStore.get_by_patient failed: %s", exc)
            return []

    async def acknowledge(
        self, alert_id: str, acknowledged_by: str
    ) -> bool:
        if self._factory is None:
            return False
        try:
            from sqlalchemy import select  # noqa: PLC0415
            from wanda.database.models import ClinicalAlertModel  # noqa: PLC0415

            async with self._factory() as session:
                stmt = select(ClinicalAlertModel).where(
                    ClinicalAlertModel.alert_id == alert_id
                )
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                if row is None:
                    return False
                row.status = "acknowledged"
                row.acknowledged_by = acknowledged_by
                row.acknowledged_at = datetime.now(timezone.utc)
                await session.commit()
                return True
        except Exception as exc:
            logger.error("AlertStore.acknowledge failed: %s", exc)
            return False

    async def resolve(
        self, alert_id: str, resolved_by: str, notes: str = ""
    ) -> bool:
        if self._factory is None:
            return False
        try:
            from sqlalchemy import select  # noqa: PLC0415
            from wanda.database.models import ClinicalAlertModel  # noqa: PLC0415

            async with self._factory() as session:
                stmt = select(ClinicalAlertModel).where(
                    ClinicalAlertModel.alert_id == alert_id
                )
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                if row is None:
                    return False
                row.status = "resolved"
                row.resolved_by = resolved_by
                row.resolved_at = datetime.now(timezone.utc)
                row.resolution_notes = notes
                await session.commit()
                return True
        except Exception as exc:
            logger.error("AlertStore.resolve failed: %s", exc)
            return False

    async def get_stats(self) -> dict[str, int]:
        if self._factory is None:
            return {}
        try:
            from sqlalchemy import func, select  # noqa: PLC0415
            from wanda.database.models import ClinicalAlertModel  # noqa: PLC0415

            async with self._factory() as session:
                stmt = select(
                    ClinicalAlertModel.status,
                    func.count().label("cnt"),
                ).group_by(ClinicalAlertModel.status)
                result = await session.execute(stmt)
                return {row.status: row.cnt for row in result}
        except Exception as exc:
            logger.error("AlertStore.get_stats failed: %s", exc)
            return {}

    @staticmethod
    def _to_dict(model: Any) -> dict[str, Any]:
        return {
            "alert_id": str(model.alert_id),
            "patient_id": model.patient_id,
            "source_agent": model.source_agent,
            "alert_type": model.alert_type,
            "severity": model.severity,
            "title": model.title,
            "description": model.description,
            "recommended_action": model.recommended_action,
            "priority_score": model.priority_score,
            "status": model.status,
            "acknowledged_by": model.acknowledged_by,
            "resolved_by": model.resolved_by,
            "idempotency_key": model.idempotency_key,
        }
