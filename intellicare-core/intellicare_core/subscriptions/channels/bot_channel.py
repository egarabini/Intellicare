"""Bot channel: execute an IntelliCare Bot triggered by a FHIR Subscription.

channel_endpoint format: ``Bot/{bot_id}``

The channel fetches the Bot record from intellicare-grahame, builds a
BotExecutionContext and runs the bot code inside the sandbox engine.
Failures are handled by the caller's retry/audit logic.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from ..models import ChannelResult, SubscriptionRecord

logger = logging.getLogger(__name__)

_BOT_ID_RE = re.compile(r"^Bot/(.+)$")


def _extract_bot_id(endpoint: Optional[str]) -> Optional[str]:
    if not endpoint:
        return None
    m = _BOT_ID_RE.match(endpoint.strip())
    return m.group(1) if m else None


async def send_bot_notification(
    subscription: SubscriptionRecord,
    resource: dict,
) -> ChannelResult:
    """Execute the bot referenced by ``subscription.channel_endpoint``.

    Requires:
        - ``channel_endpoint`` = ``"Bot/{bot_id}"``
        - ``X-Grahame-URL`` in ``channel_header`` (optional — falls back to env)

    The bot execution is delegated to :class:`intellicare_core.bots.BotExecutor`.
    """
    bot_id = _extract_bot_id(subscription.channel_endpoint)
    if not bot_id:
        return ChannelResult(
            subscription_id=subscription.id,
            success=False,
            error=(
                f"Invalid bot channel_endpoint: {subscription.channel_endpoint!r}. "
                "Expected format: 'Bot/<bot_id>'"
            ),
        )

    grahame_url = (subscription.channel_header or {}).get("X-Grahame-URL")

    try:
        from intellicare_core.bots.models import Bot
        from intellicare_core.bots.executor import BotExecutor
        from intellicare_core.bots.context import EventMetadata
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import asyncio
        import os
        
        db_url = os.getenv("DATABASE_URL")
        # Ensure we use sync psycopg for the executor session since the executor uses sync sqlalchemy
        if db_url and db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
            
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        
        def _run_bot_sync():
            with SessionLocal() as session:
                executor = BotExecutor(session)
                meta = EventMetadata(
                    subscription_id=subscription.id,
                    interaction="create", # TODO: dynamic interaction
                )
                
                # Execute bot blocks execution based on strictly enforced timeouts.
                result = executor.execute_bot(
                    bot_id=bot_id,
                    tenant_id=subscription.tenant_id,
                    input_resource=resource,
                    event_metadata=meta
                )
                
                return ChannelResult(
                    subscription_id=subscription.id,
                    success=result.success,
                    error=result.error_message,
                )
                
        # Run sync DB operations and python sandbox in a separate thread
        loop = asyncio.get_running_loop()
        channel_result = await loop.run_in_executor(None, _run_bot_sync)
        return channel_result

    except ImportError as exc:
        return ChannelResult(
            subscription_id=subscription.id,
            success=False,
            error=f"intellicare_core.bots not available: {exc}",
        )
    except Exception as exc:
        logger.error("bot.channel_error bot_id=%s error=%s", bot_id, exc)
        return ChannelResult(
            subscription_id=subscription.id,
            success=False,
            error=str(exc),
        )
