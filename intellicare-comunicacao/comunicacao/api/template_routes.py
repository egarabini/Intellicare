"""Rotas de templates de mensagens."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from comunicacao.auth import get_current_user, requires_any_role, requires_role
from comunicacao.templates.models import MessageTemplate
from comunicacao.templates.renderer import TemplateRenderer
from comunicacao.templates.store import TemplateStore


class TemplatePreviewRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)
    channel: str | None = None


class TemplateValidateRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)


def create_template_router(get_state: Callable[[], dict[str, Any]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

    @router.post("", status_code=201)
    @requires_role("comunicacao_admin")
    def create_template(
        payload: MessageTemplate,
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        state = get_state()
        store: TemplateStore | None = state.get("template_store")
        if store is None:
            raise HTTPException(status_code=503, detail="template store indisponivel")
        if store.get(payload.id):
            raise HTTPException(status_code=409, detail=f"template ja existe: {payload.id}")
        saved = store.create(payload)
        return {"id": saved.id, "version": saved.version}

    @router.get("")
    @requires_any_role(["comunicacao_read", "comunicacao_admin", "intellicare_admin"])
    def list_templates(
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        state = get_state()
        store: TemplateStore | None = state.get("template_store")
        if store is None:
            raise HTTPException(status_code=503, detail="template store indisponivel")
        items = store.list()
        return {"items": [item.model_dump(mode="json") for item in items], "total": len(items)}

    @router.get("/{template_id}")
    @requires_any_role(["comunicacao_read", "comunicacao_admin", "intellicare_admin"])
    def get_template(
        template_id: str,
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        state = get_state()
        store: TemplateStore | None = state.get("template_store")
        if store is None:
            raise HTTPException(status_code=503, detail="template store indisponivel")
        template = store.get(template_id)
        if template is None:
            raise HTTPException(status_code=404, detail=f"template nao encontrado: {template_id}")
        return template.model_dump(mode="json")

    @router.put("/{template_id}")
    @requires_role("comunicacao_admin")
    def update_template(
        template_id: str,
        payload: MessageTemplate,
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        if payload.id != template_id:
            raise HTTPException(status_code=400, detail="template_id da URL difere do payload")
        state = get_state()
        store: TemplateStore | None = state.get("template_store")
        if store is None:
            raise HTTPException(status_code=503, detail="template store indisponivel")
        updated = store.update(template_id=template_id, item=payload)
        if updated is None:
            raise HTTPException(status_code=404, detail=f"template nao encontrado: {template_id}")
        return {"id": updated.id, "version": updated.version}

    @router.delete("/{template_id}")
    @requires_role("comunicacao_admin")
    def delete_template(
        template_id: str,
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        state = get_state()
        store: TemplateStore | None = state.get("template_store")
        if store is None:
            raise HTTPException(status_code=503, detail="template store indisponivel")
        deleted = store.deactivate(template_id=template_id)
        if deleted is None:
            raise HTTPException(status_code=404, detail=f"template nao encontrado: {template_id}")
        return {"deactivated": True}

    @router.post("/{template_id}/preview")
    @requires_any_role(["comunicacao_read", "comunicacao_admin", "intellicare_admin"])
    def preview_template(
        template_id: str,
        payload: TemplatePreviewRequest,
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        state = get_state()
        store: TemplateStore | None = state.get("template_store")
        renderer: TemplateRenderer | None = state.get("template_renderer")
        if store is None or renderer is None:
            raise HTTPException(status_code=503, detail="servico de template indisponivel")
        template = store.get(template_id)
        if template is None:
            raise HTTPException(status_code=404, detail=f"template nao encontrado: {template_id}")
        if payload.channel:
            return {payload.channel: renderer.render(template=template, channel=payload.channel, params=payload.params)}
        return renderer.preview(template=template, params=payload.params or None)

    @router.post("/{template_id}/validate")
    @requires_any_role(["comunicacao_read", "comunicacao_admin", "intellicare_admin"])
    def validate_template(
        template_id: str,
        payload: TemplateValidateRequest,
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        state = get_state()
        store: TemplateStore | None = state.get("template_store")
        renderer: TemplateRenderer | None = state.get("template_renderer")
        if store is None or renderer is None:
            raise HTTPException(status_code=503, detail="servico de template indisponivel")
        template = store.get(template_id)
        if template is None:
            raise HTTPException(status_code=404, detail=f"template nao encontrado: {template_id}")
        errors = renderer.validate(template=template, params=payload.params)
        return {"valid": len(errors) == 0, "errors": errors}

    return router
