"""Celery workers for async subscription notification processing.

Celery is an optional dependency. If not installed, import silently degrades
and async dispatch is used directly.
"""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

try:
    from celery import shared_task  # type: ignore[import]

    @shared_task(  # type: ignore[misc]
        bind=True,
        max_retries=4,
        default_retry_delay=2,
        name="intellicare.subscriptions.process_notification",
    )
    def process_subscription_notification(
        self,  # type: ignore[misc]
        subscription_dict: dict,
        resource: dict,
        tenant_id: str,
        event_type: str = "create",
    ) -> None:
        """Celery task: dispatch subscription notification with exponential backoff.

        Args:
            subscription_dict:  Serialised SubscriptionRecord (dict).
            resource:           FHIR resource dict that triggered the notification.
            tenant_id:          Tenant context.
            event_type:         "create" | "update" | "delete"
        """
        from .dispatcher import dispatch  # noqa: PLC0415
        from .models import SubscriptionRecord  # noqa: PLC0415

        sub = SubscriptionRecord(**subscription_dict)
        try:
            loop = asyncio.new_event_loop()
            try:
                result, _audit = loop.run_until_complete(dispatch(sub, resource, tenant_id))
            finally:
                loop.close()
            if not result.success:
                raise RuntimeError(result.error or "dispatch failed")
        except Exception as exc:
            countdown = 2 ** self.request.retries
            logger.warning(
                "subscription.retry subscription_id=%s attempt=%d countdown=%d error=%s",
                sub.id,
                self.request.retries + 1,
                countdown,
                exc,
            )
            raise self.retry(exc=exc, countdown=countdown)

except ImportError:

    def process_subscription_notification(*args, **kwargs) -> None:  # type: ignore[misc]
        raise RuntimeError("Celery not installed — use async dispatch() directly")
