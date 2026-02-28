"""BotService — CRUD + execution for FHIR Bots in intellicare-grahame."""

from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.models.bot import Bot, BotExecution, BotSecret


class BotService:
    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        self.session = session
        self.tenant_id = tenant_id

    # ── Bot CRUD ───────────────────────────────────────────────────────────

    async def create(self, data: dict) -> Bot:
        bot = Bot(
            tenant_id=self.tenant_id,
            name=data["name"],
            description=data.get("description"),
            code=data.get("code", ""),
            runtime=data.get("runtime", "sandbox"),
            status=data.get("status", "active"),
            timeout_seconds=data.get("timeoutSeconds", data.get("timeout_seconds", 30)),
            created_by=data.get("createdBy"),
        )
        self.session.add(bot)
        await self.session.commit()
        await self.session.refresh(bot)
        return bot

    async def get(self, bot_id: str) -> Optional[Bot]:
        result = await self.session.execute(
            select(Bot).where(Bot.id == bot_id, Bot.tenant_id == self.tenant_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Bot]:
        q = select(Bot).where(Bot.tenant_id == self.tenant_id)
        if status:
            q = q.where(Bot.status == status)
        q = q.limit(limit).offset(offset)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def update(self, bot_id: str, data: dict) -> Optional[Bot]:
        bot = await self.get(bot_id)
        if bot is None:
            return None
        for field, key in [
            ("name", "name"),
            ("description", "description"),
            ("status", "status"),
            ("runtime", "runtime"),
        ]:
            if key in data:
                setattr(bot, field, data[key])
        if "code" in data:
            bot.code = data["code"]
            bot.code_version += 1
        if "timeoutSeconds" in data:
            bot.timeout_seconds = data["timeoutSeconds"]
        bot.updated_at = datetime.datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(bot)
        return bot

    async def delete(self, bot_id: str) -> bool:
        bot = await self.get(bot_id)
        if bot is None:
            return False
        bot.status = "inactive"
        bot.updated_at = datetime.datetime.utcnow()
        await self.session.commit()
        return True

    # ── Secrets ────────────────────────────────────────────────────────────

    async def set_secret(self, bot_id: str, name: str, plaintext: str) -> BotSecret:
        from intellicare_core.bots.secrets_manager import SecretsManager  # noqa: PLC0415

        mgr = SecretsManager()
        encrypted = mgr.encrypt_secret(plaintext)

        # Upsert
        result = await self.session.execute(
            select(BotSecret).where(
                BotSecret.tenant_id == self.tenant_id,
                BotSecret.bot_id == bot_id,
                BotSecret.name == name,
            )
        )
        secret = result.scalar_one_or_none()
        if secret:
            secret.value_encrypted = encrypted
        else:
            secret = BotSecret(
                tenant_id=self.tenant_id,
                bot_id=bot_id,
                name=name,
                value_encrypted=encrypted,
            )
            self.session.add(secret)
        await self.session.commit()
        await self.session.refresh(secret)
        return secret

    async def get_secrets_encrypted(self, bot_id: str) -> dict[str, str]:
        """Return {name: ciphertext} for bot — caller decrypts."""
        result = await self.session.execute(
            select(BotSecret).where(
                BotSecret.tenant_id == self.tenant_id,
                BotSecret.bot_id == bot_id,
            )
        )
        return {s.name: s.value_encrypted for s in result.scalars().all()}

    # ── Execution ──────────────────────────────────────────────────────────

    async def execute(self, bot_id: str, input_resource: dict) -> dict:
        """Execute a bot and persist the execution log. Returns BotExecutionResult dict."""
        bot = await self.get(bot_id)
        if bot is None:
            raise ValueError(f"Bot/{bot_id} not found")
        if bot.status != "active":
            raise ValueError(f"Bot/{bot_id} is not active")

        try:
            from intellicare_core.bots import BotExecutor, BotRecord, EventMetadata  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(f"intellicare_core.bots not available: {exc}") from exc

        secrets_enc = await self.get_secrets_encrypted(bot_id)
        bot_record = BotRecord(
            id=bot.id,
            tenant_id=bot.tenant_id,
            name=bot.name,
            code=bot.code,
            runtime=bot.runtime,
            status=bot.status,
            timeout_seconds=bot.timeout_seconds,
        )
        meta = EventMetadata(
            interaction="execute",
            resource_type=input_resource.get("resourceType"),
            resource_id=input_resource.get("id"),
            tenant_id=self.tenant_id,
        )
        executor = BotExecutor()
        result = await executor.execute(
            bot_record, input_resource, encrypted_secrets=secrets_enc, event_metadata=meta
        )

        # Persist execution log
        execution = BotExecution(
            id=result.id,
            bot_id=bot_id,
            tenant_id=self.tenant_id,
            input_resource_type=result.input_resource_type,
            input_resource_id=result.input_resource_id,
            interaction=result.interaction,
            success=result.success,
            log_output=result.log_output,
            duration_ms=int(result.duration_ms),
            error_message=result.error_message,
        )
        self.session.add(execution)
        await self.session.commit()

        return result.model_dump()

    async def list_executions(
        self, bot_id: str, *, limit: int = 20
    ) -> list[BotExecution]:
        result = await self.session.execute(
            select(BotExecution)
            .where(BotExecution.bot_id == bot_id, BotExecution.tenant_id == self.tenant_id)
            .order_by(BotExecution.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
