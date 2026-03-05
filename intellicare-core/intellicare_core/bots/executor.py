"""
Bot Executor for IntelliCare.
Orchestrates the entire bot lifecycle constraint to the tenant's execution context.
"""
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from .models import Bot, BotExecution
from .sandbox import BotSandbox
from .client import IntelliCareClient
from .context import BotExecutionContext, EventMetadata, BotLogger
from .secrets_manager import get_tenant_bot_secrets

class BotExecutor:
    """Main entrypoint to execute a Bot and record its execution."""

    def __init__(self, session: Session):
        self.session = session
        self.sandbox = BotSandbox()

    def execute_bot(
        self, 
        bot_id: str, 
        tenant_id: str, 
        input_resource: Dict[str, Any], 
        event_metadata: EventMetadata
    ) -> BotExecution:
        """
        Executes a bot by its ID for the given tenant and resource.
        Persists the execution result and returns the BotExecution record.
        """
        # Load the bot
        bot = self.session.query(Bot).filter(
            Bot.id == bot_id, 
            Bot.tenant_id == tenant_id,
            Bot.status == "active"
        ).first()

        if not bot:
            return self._record_failure(
                bot_id, tenant_id, input_resource, event_metadata, 
                error="Bot not found, inactive, or belongs to another tenant"
            )

        # Build context
        try:
            secrets = get_tenant_bot_secrets(self.session, tenant_id, bot_id)
            client = IntelliCareClient(tenant_id=tenant_id)
            logger = BotLogger()
            
            context = BotExecutionContext(
                input_resource=input_resource,
                fhir_client=client,
                secrets=secrets,
                event_metadata=event_metadata,
                logger=logger
            )
        except Exception as e:
            return self._record_failure(
                bot_id, tenant_id, input_resource, event_metadata, 
                error=f"Context initialization failed: {str(e)}"
            )

        # Execute in sandbox
        result = self.sandbox.execute(
            code=bot.code, 
            context=context, 
            timeout=bot.timeout_seconds
        )

        # Save Execution Log
        execution = BotExecution(
            bot_id=bot.id,
            tenant_id=tenant_id,
            subscription_id=event_metadata.subscription_id,
            input_resource_type=input_resource.get("resourceType"),
            input_resource_id=input_resource.get("id"),
            interaction=event_metadata.interaction,
            success=result["success"],
            log_output=logger.get_log_output(),
            duration_ms=result.get("duration_ms"),
            error_message=result.get("error")
        )
        self.session.add(execution)
        self.session.flush() # flush to generate ID without committing outer transaction
        return execution

    def _record_failure(
        self, 
        bot_id: str, 
        tenant_id: str, 
        input_resource: Dict[str, Any], 
        event_metadata: EventMetadata,
        error: str
    ) -> BotExecution:
        """Records an execution that failed before reaching the Sandbox."""
        execution = BotExecution(
            bot_id=bot_id if bot_id else None,
            tenant_id=tenant_id,
            subscription_id=event_metadata.subscription_id,
            input_resource_type=input_resource.get("resourceType"),
            input_resource_id=input_resource.get("id"),
            interaction=event_metadata.interaction,
            success=False,
            log_output="",
            duration_ms=0,
            error_message=error
        )
        # We only add if bot_id is uuid (foreign key constraints). 
        # If bot wasn't found, we might skip insertion or rely on a nullable FK.
        if execution.bot_id:
            self.session.add(execution)
            self.session.flush()
        return execution
