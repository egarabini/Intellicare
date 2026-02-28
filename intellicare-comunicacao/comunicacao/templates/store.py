"""Store em memoria para templates."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from comunicacao.templates.models import MessageTemplate


class TemplateStore(Protocol):
    def create(self, item: MessageTemplate) -> MessageTemplate: ...

    def get(self, template_id: str) -> MessageTemplate | None: ...

    def list(self) -> list[MessageTemplate]: ...

    def update(self, template_id: str, item: MessageTemplate) -> MessageTemplate | None: ...

    def deactivate(self, template_id: str) -> MessageTemplate | None: ...


class InMemoryTemplateStore:
    def __init__(self) -> None:
        self._items: dict[str, MessageTemplate] = {}

    def create(self, item: MessageTemplate) -> MessageTemplate:
        self._items[item.id] = item
        return item

    def get(self, template_id: str) -> MessageTemplate | None:
        return self._items.get(template_id)

    def list(self) -> list[MessageTemplate]:
        return sorted(self._items.values(), key=lambda x: x.id)

    def update(self, template_id: str, item: MessageTemplate) -> MessageTemplate | None:
        existing = self._items.get(template_id)
        if existing is None:
            return None
        item.version = existing.version + 1
        item.created_at = existing.created_at
        item.updated_at = datetime.now(UTC)
        self._items[template_id] = item
        return item

    def deactivate(self, template_id: str) -> MessageTemplate | None:
        existing = self._items.get(template_id)
        if existing is None:
            return None
        existing.active = False
        existing.updated_at = datetime.now(UTC)
        self._items[template_id] = existing
        return existing
