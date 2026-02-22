"""Renderizador simples de templates (substituicao por placeholders)."""

from __future__ import annotations

from typing import Any

from comunicacao.templates.models import MessageTemplate, TemplateVariant


class TemplateRenderer:
    def render(
        self,
        template: MessageTemplate,
        channel: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        variant = template.channel_variants.get(channel)
        if variant is None:
            raise ValueError(f"canal nao encontrado no template: {channel}")
        return self._render_variant(variant=variant, params=params)

    def preview(self, template: MessageTemplate, params: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
        payload = params or template.sample_params
        return {
            channel: self._render_variant(variant=variant, params=payload)
            for channel, variant in template.channel_variants.items()
        }

    def validate(self, template: MessageTemplate, params: dict[str, Any]) -> list[str]:
        required = template.params_schema.get("required", [])
        errors: list[str] = []
        for key in required:
            if key not in params:
                errors.append(f"Missing: {key}")
        return errors

    def _render_variant(self, variant: TemplateVariant, params: dict[str, Any]) -> dict[str, Any]:
        body = variant.body
        for key, value in params.items():
            body = body.replace(f"{{{{{key}}}}}", str(value))
            body = body.replace(f"{{{{ {key} }}}}", str(value))
        if variant.max_length is not None and len(body) > variant.max_length:
            body = body[: variant.max_length]
        output: dict[str, Any] = {"format": variant.format, "body": body}
        if variant.subject is not None:
            subject = variant.subject
            for key, value in params.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(value))
                subject = subject.replace(f"{{{{ {key} }}}}", str(value))
            output["subject"] = subject
        if variant.title is not None:
            title = variant.title
            for key, value in params.items():
                title = title.replace(f"{{{{{key}}}}}", str(value))
                title = title.replace(f"{{{{ {key} }}}}", str(value))
            output["title"] = title
        return output

