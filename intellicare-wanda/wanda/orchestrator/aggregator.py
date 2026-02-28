"""Response aggregator — combines outputs from multiple modules into a cohesive response."""

from wanda.discovery.models import ModuleResponse, OrchestrationResult, RoutingDecision


MODULE_DISPLAY_NAMES = {
    "intellicare-oswaldo": "Oswaldo (Doencas Cronicas)",
    "intellicare-florence": "Florence (Inteligencia Clinica)",
    "intellicare-zilda": "Zilda (Dados de Saude Brasileiros)",
    "intellicare-geralda": "Geralda (Acompanhamento do Paciente)",
    "intellicare-donabedian": "Donabedian (Avaliacao de Qualidade)",
    "intellicare-comunicacao": "Comunicacao",
}


class ResponseAggregator:
    """Aggregates responses from multiple modules into a structured output."""

    def aggregate(
        self,
        query: str,
        responses: list[ModuleResponse],
        routing: RoutingDecision | None = None,
        safety_warnings: list[str] | None = None,
    ) -> OrchestrationResult:
        """Combine module responses into a single orchestration result."""
        successful = [r for r in responses if r.success]
        failed = [r for r in responses if not r.success]
        modules_used = [r.module_name for r in successful]

        # Build aggregated text
        parts = []

        for resp in successful:
            display = MODULE_DISPLAY_NAMES.get(resp.module_name, resp.module_name)
            data = resp.data

            if "data" in data:
                content = data["data"]
            else:
                content = data

            parts.append(self._format_module_response(display, content))

        # Note failures
        if failed:
            error_parts = []
            for r in failed:
                display = MODULE_DISPLAY_NAMES.get(r.module_name, r.module_name)
                error_parts.append(f"- {display}: {r.error}")
            parts.append(
                "Modulos com falha:\n" + "\n".join(error_parts)
            )

        aggregated = "\n\n---\n\n".join(parts) if parts else "Nenhum modulo retornou resultados."

        return OrchestrationResult(
            query=query,
            modules_used=modules_used,
            responses=responses,
            aggregated_response=aggregated,
            routing_decision=routing,
            safety_warnings=safety_warnings or [],
        )

    def _format_module_response(self, display_name: str, content: dict | list | str) -> str:
        """Format a single module's response for display."""
        header = f"**{display_name}**"

        if isinstance(content, str):
            return f"{header}\n{content}"

        if isinstance(content, list):
            if len(content) == 0:
                return f"{header}\nSem resultados."
            items = []
            for item in content[:10]:  # Limit to 10 items
                if isinstance(item, dict):
                    summary = self._summarize_dict(item)
                    items.append(f"- {summary}")
                else:
                    items.append(f"- {item}")
            text = "\n".join(items)
            if len(content) > 10:
                text += f"\n... e mais {len(content) - 10} resultados"
            return f"{header}\n{text}"

        if isinstance(content, dict):
            return f"{header}\n{self._format_dict(content)}"

        return f"{header}\n{content}"

    def _summarize_dict(self, d: dict) -> str:
        """Create a one-line summary of a dict."""
        # Pick meaningful keys for summary
        for key in ["title", "name", "description", "message", "id"]:
            if key in d:
                return str(d[key])
        # Fallback: first 3 key=value pairs
        items = [f"{k}={v}" for k, v in list(d.items())[:3]]
        return ", ".join(items)

    def _format_dict(self, d: dict, indent: int = 0) -> str:
        """Format a dict for readable display."""
        lines = []
        prefix = "  " * indent
        for key, value in d.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}- **{key}**:")
                lines.append(self._format_dict(value, indent + 1))
            elif isinstance(value, list) and len(value) > 0:
                lines.append(f"{prefix}- **{key}**: {len(value)} item(s)")
            else:
                lines.append(f"{prefix}- **{key}**: {value}")
        return "\n".join(lines)
