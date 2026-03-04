"""Rotas do engine de roteamento (incremento inicial)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from comunicacao.auth import get_current_user, requires_any_role, requires_role
from comunicacao.routing.models import CommunicationIntentCreate
from comunicacao.routing.engine import RoutingService
from comunicacao.auth import get_tenant_context
import comunicacao.routing.models as routing_models
from comunicacao.routing.delayed import DelayedWorker


class CommunicationIntentBatchRequest(BaseModel):
    intents: list[CommunicationIntentCreate] = Field(default_factory=list, max_length=100)


class RoutingRuleUpsertRequest(BaseModel):
    id: str
    name: str
    priority: int = 100
    active: bool = True
    severities: list[str] = Field(default_factory=list)
    recipient_types: list[routing_models.RecipientType] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    channels: list[routing_models.ChannelStep] = Field(default_factory=list)


def create_routing_router(get_state: Callable[[], dict[str, Any]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/routing", tags=["routing"])

    @router.post("/send", status_code=202)
    @requires_any_role(["comunicacao_send", "comunicacao_admin", "intellicare_admin"])
    async def routing_send(
        payload: CommunicationIntentCreate,
        user: dict[str, Any] = Depends(get_current_user),
        ctx: Any = Depends(get_tenant_context),
    ) -> dict[str, Any]:
        state = get_state()
        service: RoutingService | None = state.get("routing_service")
        if service is None:
            raise HTTPException(status_code=503, detail="routing service indisponivel")
        # Atualiza template_store e renderer do engine se alterados no state
        if "template_store" in state and hasattr(service, "template_store"):
            service.template_store = state["template_store"]
        if "template_renderer" in state and hasattr(service, "template_renderer"):
            service.template_renderer = state["template_renderer"]
        intent = await service.send_intent(payload, ctx=ctx)
        return {
            "intent_id": str(intent.id),
            "status": intent.status.value,
            "message": "intent accepted for processing",
        }

    @router.get("/intents/{intent_id}")
    @requires_any_role(["comunicacao_read", "comunicacao_admin", "intellicare_admin"])
    def routing_get_intent(
        intent_id: str,
        user: dict[str, Any] = Depends(get_current_user),
        ctx: Any = Depends(get_tenant_context),
    ) -> dict[str, Any]:
        state = get_state()
        service: RoutingService | None = state.get("routing_service")
        if service is None:
            raise HTTPException(status_code=503, detail="routing service indisponivel")
        loaded = service.get_intent(intent_id=intent_id, ctx=ctx)
        if loaded is None:
            raise HTTPException(status_code=404, detail=f"intent nao encontrada: {intent_id}")
        intent, deliveries = loaded
        return {
            "intent": intent.model_dump(mode="json"),
            "deliveries": [delivery.model_dump(mode="json") for delivery in deliveries],
            "timeline": [event.model_dump(mode="json") for event in intent.timeline],
        }

    @router.post("/send-batch", status_code=202)
    @requires_any_role(["comunicacao_send", "comunicacao_admin", "intellicare_admin"])
    async def routing_send_batch(
        payload: CommunicationIntentBatchRequest,
        user: dict[str, Any] = Depends(get_current_user),
        ctx: Any = Depends(get_tenant_context),
    ) -> dict[str, Any]:
        state = get_state()
        service: RoutingService | None = state.get("routing_service")
        if service is None:
            raise HTTPException(status_code=503, detail="routing service indisponivel")
        accepted, rejected = await service.send_batch(intents=payload.intents, ctx=ctx)
        return {
            "accepted": len(accepted),
            "rejected": rejected,
            "intent_ids": [str(item.id) for item in accepted],
        }

    @router.get("/intents")
    @requires_any_role(["comunicacao_read", "comunicacao_admin", "intellicare_admin"])
    def routing_list_intents(
        user: dict[str, Any] = Depends(get_current_user),
        ctx: Any = Depends(get_tenant_context),
    ) -> dict[str, Any]:
        state = get_state()
        service: RoutingService | None = state.get("routing_service")
        if service is None:
            raise HTTPException(status_code=503, detail="routing service indisponivel")
        items = service.list_intents(ctx=ctx)
        return {
            "items": [item.model_dump(mode="json") for item in items],
            "total": len(items),
            "page": 1,
        }

    @router.put("/intents/{intent_id}/cancel")
    @requires_any_role(["comunicacao_send", "comunicacao_admin", "intellicare_admin"])
    def routing_cancel_intent(
        intent_id: str,
        user: dict[str, Any] = Depends(get_current_user),
        ctx: Any = Depends(get_tenant_context),
    ) -> dict[str, Any]:
        state = get_state()
        service: RoutingService | None = state.get("routing_service")
        if service is None:
            raise HTTPException(status_code=503, detail="routing service indisponivel")
        intent = service.cancel_intent(intent_id=intent_id, ctx=ctx)
        if intent is None:
            raise HTTPException(status_code=404, detail=f"intent nao encontrada: {intent_id}")
        if intent.status in {routing_models.IntentStatus.COMPLETED, routing_models.IntentStatus.FAILED}:
            raise HTTPException(status_code=409, detail="intent ja finalizada, nao pode cancelar")
        return {"status": intent.status.value}

    @router.get("/metrics")
    @requires_any_role(["comunicacao_read", "comunicacao_admin", "intellicare_admin"])
    def routing_metrics(
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        state = get_state()
        service: RoutingService | None = state.get("routing_service")
        if service is None:
            raise HTTPException(status_code=503, detail="routing service indisponivel")
        return {"ok": True, **service.metrics()}

    @router.get("/scheduler/status")
    @requires_any_role(["comunicacao_read", "comunicacao_admin", "intellicare_admin"])
    def routing_scheduler_status(
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        state = get_state()
        worker: DelayedWorker | None = state.get("routing_delayed_worker")
        if worker is None:
            raise HTTPException(status_code=503, detail="routing delayed worker indisponivel")
        return worker.status()

    @router.post("/scheduler/start")
    @requires_role("comunicacao_admin")
    async def routing_scheduler_start(
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        state = get_state()
        worker: DelayedWorker | None = state.get("routing_delayed_worker")
        if worker is None:
            raise HTTPException(status_code=503, detail="routing delayed worker indisponivel")
        return await worker.start()

    @router.post("/scheduler/stop")
    @requires_role("comunicacao_admin")
    async def routing_scheduler_stop(
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        state = get_state()
        worker: DelayedWorker | None = state.get("routing_delayed_worker")
        if worker is None:
            raise HTTPException(status_code=503, detail="routing delayed worker indisponivel")
        return await worker.stop()

    @router.post("/scheduler/process-due")
    @requires_role("comunicacao_admin")
    async def routing_scheduler_process_due(
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        state = get_state()
        worker: DelayedWorker | None = state.get("routing_delayed_worker")
        if worker is None:
            raise HTTPException(status_code=503, detail="routing delayed worker indisponivel")
        processed = await worker.process_due_once()
        return {"ok": True, "processed": processed}

    @router.get("/rules")
    @requires_any_role(["comunicacao_read", "comunicacao_admin", "intellicare_admin"])
    def routing_list_rules(
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        state = get_state()
        service: RoutingService | None = state.get("routing_service")
        if service is None:
            raise HTTPException(status_code=503, detail="routing service indisponivel")
        rules = service.list_rules()
        return {"items": [rule.model_dump(mode="json") for rule in rules], "total": len(rules)}

    @router.put("/rules/{rule_id}")
    @requires_role("comunicacao_admin")
    def routing_upsert_rule(
        rule_id: str,
        payload: RoutingRuleUpsertRequest,
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        state = get_state()
        service: RoutingService | None = state.get("routing_service")
        if service is None:
            raise HTTPException(status_code=503, detail="routing service indisponivel")
        if payload.id != rule_id:
            raise HTTPException(status_code=400, detail="rule_id da URL difere do payload")
        rule = routing_models.RoutingRule(**payload.model_dump())
        saved = service.upsert_rule(rule=rule)
        return {"id": saved.id, "priority": saved.priority, "active": saved.active}

    return router
