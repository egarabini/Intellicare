"""Service layer for custom FHIR operations."""

from __future__ import annotations

import asyncio
import re
import time
from collections import deque
from typing import Any

import httpx
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.config import config
from grahame.models.custom_operation import CustomOperation, CustomOperationAudit
from grahame.services.bot_service import BotService
from grahame.services.custom_operation_repository import CustomOperationRepository

_OPERATION_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_NATIVE_FHIR_OPERATIONS = {
    "everything",
    "summary",
    "expand",
    "validate",
    "evaluate-measure",
    "find",
    "book",
    "ai",
    "ccda-import",
}


class CustomOpsService:
    """Lookup, validation and execution orchestrator for tenant custom operations."""

    _in_memory_rate_windows: dict[str, deque[float]] = {}

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        request: Request | None = None,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.request = request
        self.repo = CustomOperationRepository(session)

    @staticmethod
    def validate_operation_name(name: str) -> None:
        if not _OPERATION_NAME_RE.match(name):
            raise HTTPException(status_code=400, detail="Invalid operation name format")
        if name in _NATIVE_FHIR_OPERATIONS:
            raise HTTPException(status_code=400, detail=f"Operation '{name}' conflicts with native FHIR op")

    @staticmethod
    def _validate_handler(handler_type: str, handler_config: dict[str, Any]) -> None:
        if handler_type not in {"url", "bot", "inline"}:
            raise HTTPException(status_code=400, detail="handlerType must be one of: url|bot|inline")
        if handler_type == "url" and not handler_config.get("url"):
            raise HTTPException(status_code=400, detail="handlerConfig.url is required for URL handlers")
        if handler_type == "bot" and not handler_config.get("bot_id"):
            raise HTTPException(status_code=400, detail="handlerConfig.bot_id is required for bot handlers")
        if handler_type == "inline":
            raise HTTPException(status_code=400, detail="Inline handlers are not enabled yet")

    async def create(self, payload: dict[str, Any]) -> CustomOperation:
        name = payload.get("name", "").strip()
        self.validate_operation_name(name)
        op_type = payload.get("type", "system")
        if op_type not in {"instance", "system"}:
            raise HTTPException(status_code=400, detail="type must be instance|system")
        resource_type = payload.get("resourceType")
        if op_type == "instance" and not resource_type:
            raise HTTPException(status_code=400, detail="resourceType is required for instance operations")
        handler_type = payload.get("handlerType")
        handler_config = payload.get("handlerConfig", {})
        self._validate_handler(handler_type, handler_config)
        timeout_seconds = int(payload.get("timeoutSeconds", config.custom_op_default_timeout))
        rate_limit = int(payload.get("rateLimitPerMinute", config.custom_op_rate_limit))

        existing = await self.repo.get_by_tenant_and_name(self.tenant_id, name, resource_type)
        if existing and existing.op_type == op_type and existing.resource_type == resource_type:
            raise HTTPException(status_code=409, detail="Operation already exists")

        operation = CustomOperation(
            tenant_id=self.tenant_id,
            name=name,
            op_type=op_type,
            resource_type=resource_type if op_type == "instance" else None,
            handler_type=handler_type,
            handler_config=handler_config,
            timeout_seconds=max(1, timeout_seconds),
            rate_limit_per_minute=max(1, rate_limit),
        )
        return await self.repo.create(operation)

    async def update(self, operation_id: str, payload: dict[str, Any]) -> CustomOperation | None:
        operation = await self.repo.get(self.tenant_id, operation_id)
        if operation is None:
            return None
        if "name" in payload:
            name = payload["name"].strip()
            self.validate_operation_name(name)
            operation.name = name
        if "type" in payload:
            op_type = payload["type"]
            if op_type not in {"instance", "system"}:
                raise HTTPException(status_code=400, detail="type must be instance|system")
            operation.op_type = op_type
        if "resourceType" in payload:
            operation.resource_type = payload["resourceType"]
        if operation.op_type == "instance" and not operation.resource_type:
            raise HTTPException(status_code=400, detail="resourceType is required for instance operations")
        if "handlerType" in payload or "handlerConfig" in payload:
            handler_type = payload.get("handlerType", operation.handler_type)
            handler_config = payload.get("handlerConfig", operation.handler_config)
            self._validate_handler(handler_type, handler_config)
            operation.handler_type = handler_type
            operation.handler_config = handler_config
        if "timeoutSeconds" in payload:
            operation.timeout_seconds = max(1, int(payload["timeoutSeconds"]))
        if "rateLimitPerMinute" in payload:
            operation.rate_limit_per_minute = max(1, int(payload["rateLimitPerMinute"]))
        return await self.repo.update(operation)

    async def delete(self, operation_id: str) -> bool:
        return await self.repo.delete(self.tenant_id, operation_id)

    async def get(self, operation_id: str) -> CustomOperation | None:
        return await self.repo.get(self.tenant_id, operation_id)

    async def list(self) -> list[CustomOperation]:
        return await self.repo.list(self.tenant_id)

    async def lookup(self, name: str, resource_type: str | None = None) -> CustomOperation | None:
        return await self.repo.get_by_tenant_and_name(self.tenant_id, name, resource_type)

    async def _check_rate_limit(self, operation: CustomOperation) -> None:
        key = f"{self.tenant_id}:{operation.name}"
        limiter = getattr(self.request.app.state, "rate_limiter", None) if self.request else None
        if limiter:
            allowed, _current, _limit, _reset = await limiter.check_rate_limit(
                key=key,
                limit=operation.rate_limit_per_minute,
                window_seconds=60,
            )
            if not allowed:
                raise HTTPException(status_code=429, detail="Custom operation rate limit exceeded")
            return

        now = time.time()
        window = self._in_memory_rate_windows.setdefault(key, deque())
        while window and (now - window[0]) > 60:
            window.popleft()
        if len(window) >= operation.rate_limit_per_minute:
            raise HTTPException(status_code=429, detail="Custom operation rate limit exceeded")
        window.append(now)

    async def _audit(
        self,
        *,
        operation: CustomOperation,
        status: str,
        started_at: float,
        http_status_code: int | None = None,
        error_message: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> None:
        requester = None
        if self.request:
            requester = self.request.headers.get("X-User-ID") or self.request.headers.get("X-On-Behalf-Of")
        entry = CustomOperationAudit(
            tenant_id=self.tenant_id,
            operation_id=operation.id,
            operation_name=operation.name,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            http_status_code=http_status_code,
            error_message=error_message,
            duration_ms=max(0, int((time.time() - started_at) * 1000)),
            requester=requester,
        )
        self.session.add(entry)
        await self.session.commit()

    async def _execute_url(
        self,
        operation: CustomOperation,
        request_params: dict[str, Any],
        resource: dict[str, Any] | None,
    ) -> dict[str, Any]:
        url = operation.handler_config.get("url")
        headers = operation.handler_config.get("headers") or {}
        timeout = httpx.Timeout(operation.timeout_seconds)
        payload = {
            "tenantId": self.tenant_id,
            "operation": {
                "id": operation.id,
                "name": operation.name,
                "type": operation.op_type,
                "resourceType": operation.resource_type,
            },
            "request": request_params,
            "resource": resource,
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Custom handler returned status {response.status_code}")
        data = response.json()
        if isinstance(data, dict):
            return data
        return {
            "resourceType": "Parameters",
            "parameter": [{"name": "result", "valueString": str(data)}],
        }

    async def _execute_bot(
        self,
        operation: CustomOperation,
        request_params: dict[str, Any],
        resource: dict[str, Any] | None,
    ) -> dict[str, Any]:
        bot_id = operation.handler_config.get("bot_id")
        svc = BotService(self.session, self.tenant_id)
        input_payload = {
            "resourceType": "Parameters",
            "meta": {"tag": [{"system": "urn:intellicare:custom-op", "code": operation.name}]},
            "parameter": [
                {"name": "operation", "valueString": operation.name},
                {"name": "payload", "valueString": str(request_params)},
                {"name": "resource", "valueString": str(resource or {})},
            ],
        }
        result = await svc.execute(bot_id, input_payload)
        output = result.get("output")
        if isinstance(output, dict):
            return output
        return {
            "resourceType": "Parameters",
            "parameter": [
                {"name": "executionId", "valueString": str(result.get("id", ""))},
                {"name": "success", "valueBoolean": bool(result.get("success", False))},
                {"name": "result", "valueString": str(result.get("log_output", output or ""))},
            ],
        }

    async def execute(
        self,
        operation: CustomOperation,
        request_params: dict[str, Any],
        resource: dict[str, Any] | None = None,
        *,
        resource_id: str | None = None,
    ) -> dict[str, Any]:
        started_at = time.time()
        try:
            await self._check_rate_limit(operation)
            if operation.handler_type == "url":
                response = await asyncio.wait_for(
                    self._execute_url(operation, request_params, resource),
                    timeout=operation.timeout_seconds,
                )
            elif operation.handler_type == "bot":
                response = await asyncio.wait_for(
                    self._execute_bot(operation, request_params, resource),
                    timeout=operation.timeout_seconds,
                )
            else:
                raise HTTPException(status_code=400, detail="Inline handlers are not enabled yet")

            await self._audit(
                operation=operation,
                status="success",
                started_at=started_at,
                http_status_code=200,
                resource_type=resource.get("resourceType") if resource else operation.resource_type,
                resource_id=resource_id,
            )
            return response
        except asyncio.TimeoutError as exc:
            await self._audit(
                operation=operation,
                status="timeout",
                started_at=started_at,
                http_status_code=504,
                error_message="Operation timeout",
                resource_type=resource.get("resourceType") if resource else operation.resource_type,
                resource_id=resource_id,
            )
            raise HTTPException(status_code=504, detail="Custom operation timeout") from exc
        except HTTPException as exc:
            await self._audit(
                operation=operation,
                status="error",
                started_at=started_at,
                http_status_code=exc.status_code,
                error_message=str(exc.detail),
                resource_type=resource.get("resourceType") if resource else operation.resource_type,
                resource_id=resource_id,
            )
            raise
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            await self._audit(
                operation=operation,
                status="error",
                started_at=started_at,
                http_status_code=502,
                error_message=str(exc),
                resource_type=resource.get("resourceType") if resource else operation.resource_type,
                resource_id=resource_id,
            )
            raise HTTPException(status_code=502, detail="Custom operation handler unavailable") from exc
