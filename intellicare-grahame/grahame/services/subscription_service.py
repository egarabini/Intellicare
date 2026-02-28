"""SubscriptionService — CRUD and delivery tracking for FHIR Subscriptions."""

from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.models.subscription import Subscription, SubscriptionAudit

MAX_SUBSCRIPTIONS_PER_TENANT = 100
MAX_ERROR_COUNT = 5  # Deactivate subscription after this many consecutive failures


class SubscriptionService:
    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        self.session = session
        self.tenant_id = tenant_id

    # ── CRUD ───────────────────────────────────────────────────────────────

    async def create(self, data: dict) -> Subscription:
        """Create a new subscription, enforcing per-tenant rate limit."""
        existing = await self._count_active()
        if existing >= MAX_SUBSCRIPTIONS_PER_TENANT:
            raise ValueError(
                f"Tenant {self.tenant_id!r} already has {MAX_SUBSCRIPTIONS_PER_TENANT} "
                "active subscriptions"
            )
        channel = data.get("channel", {})
        sub = Subscription(
            tenant_id=self.tenant_id,
            status=data.get("status", "requested"),
            criteria=data["criteria"],
            reason=data.get("reason"),
            channel_type=channel["type"],
            channel_endpoint=channel.get("endpoint"),
            channel_header=channel.get("header"),
            channel_payload=channel.get("payload", "application/fhir+json"),
        )
        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(sub)
        await self._audit(sub.id, "created", details={"criteria": sub.criteria})
        return sub

    async def get(self, subscription_id: str) -> Optional[Subscription]:
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.id == subscription_id,
                Subscription.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Subscription]:
        q = select(Subscription).where(Subscription.tenant_id == self.tenant_id)
        if status:
            q = q.where(Subscription.status == status)
        q = q.limit(limit).offset(offset)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def update(self, subscription_id: str, data: dict) -> Optional[Subscription]:
        sub = await self.get(subscription_id)
        if sub is None:
            return None
        for field in ("status", "criteria", "reason"):
            if field in data:
                setattr(sub, field, data[field])
        if "channel" in data:
            ch = data["channel"]
            if "type" in ch:
                sub.channel_type = ch["type"]
            if "endpoint" in ch:
                sub.channel_endpoint = ch["endpoint"]
            if "header" in ch:
                sub.channel_header = ch["header"]
        sub.updated_at = datetime.datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(sub)
        await self._audit(sub.id, "updated", details={"status": sub.status})
        return sub

    async def delete(self, subscription_id: str) -> bool:
        sub = await self.get(subscription_id)
        if sub is None:
            return False
        sub.status = "off"
        sub.active = False
        sub.updated_at = datetime.datetime.utcnow()
        await self.session.commit()
        await self._audit(sub.id, "deactivated")
        return True

    # ── Delivery tracking ──────────────────────────────────────────────────

    async def record_delivery_result(
        self,
        subscription_id: str,
        *,
        success: bool,
        status_code: Optional[int] = None,
        error: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        channel_type: Optional[str] = None,
    ) -> None:
        """Update error counter and deactivate if error threshold reached."""
        sub = await self.get(subscription_id)
        if sub is None:
            return
        if success:
            sub.error_count = 0
        else:
            sub.error_count += 1
            if sub.error_count >= MAX_ERROR_COUNT:
                sub.status = "error"
                sub.active = False
                await self._audit(
                    sub.id,
                    "deactivated",
                    details={"reason": f"error_count={sub.error_count}"},
                )
        sub.updated_at = datetime.datetime.utcnow()
        await self.session.commit()
        event = "dispatched" if success else "failed"
        await self._audit(
            subscription_id,
            event,
            resource_type=resource_type,
            resource_id=resource_id,
            channel_type=channel_type,
            status_code=status_code,
            error=error,
        )

    # ── Fetcher for evaluate_subscriptions() ──────────────────────────────

    async def fetch_active(self, tenant_id: str, resource_type: str) -> list:
        """Async fetcher compatible with intellicare_core SubscriptionFetcher signature.

        Returns a list of SubscriptionRecord (Pydantic) for the evaluator.
        """
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.tenant_id == tenant_id,
                Subscription.status == "active",
                Subscription.active == True,  # noqa: E712
            )
        )
        subs = result.scalars().all()
        # Filter by resource_type derived from criteria prefix
        filtered = [
            s
            for s in subs
            if "?" not in s.criteria or s.criteria.split("?")[0] == resource_type
        ]
        try:
            from intellicare_core.subscriptions import SubscriptionRecord  # noqa: PLC0415
        except ImportError:
            return []

        return [
            SubscriptionRecord(
                id=s.id,
                tenant_id=s.tenant_id,
                status=s.status,
                criteria=s.criteria,
                channel_type=s.channel_type,
                channel_endpoint=s.channel_endpoint,
                channel_header=s.channel_header,
                error_count=s.error_count,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in filtered
        ]

    # ── Internal ───────────────────────────────────────────────────────────

    async def _count_active(self) -> int:
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.tenant_id == self.tenant_id,
                Subscription.active == True,  # noqa: E712
            )
        )
        return len(result.scalars().all())

    async def _audit(
        self,
        subscription_id: str,
        event_type: str,
        *,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        channel_type: Optional[str] = None,
        status_code: Optional[int] = None,
        error: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        audit = SubscriptionAudit(
            subscription_id=subscription_id,
            tenant_id=self.tenant_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            channel_type=channel_type,
            status_code=status_code,
            error=error,
            details=details or {},
        )
        self.session.add(audit)
        await self.session.commit()
