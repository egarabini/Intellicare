"""Rocket.Chat response formatter — builds RC attachments from bot results (EF-W012)."""

from __future__ import annotations

from typing import Any, Optional


class RocketChatResponseFormatter:
    """Converts structured bot results into RC attachment format."""

    def patient_summary(
        self,
        patient_id: str,
        ips: Optional[dict],
        alerts: list[dict],
        plan: Optional[str],
    ) -> list[dict]:
        fields = [{"title": "Paciente ID", "value": patient_id, "short": True}]
        if ips:
            conditions = ips.get("conditions", [])
            fields.append({
                "title": "Condicoes",
                "value": ", ".join(str(c) for c in conditions[:5]) or "Nenhuma",
                "short": False,
            })
        if alerts:
            alert_text = "\n".join(
                f"• [{a.get('severity','?').upper()}] {a.get('title','')}" for a in alerts[:5]
            )
            fields.append({"title": "Alertas Pendentes", "value": alert_text, "short": False})
        if plan:
            fields.append({"title": "Plano de Cuidado", "value": plan[:500], "short": False})

        return [{"color": "#0066cc", "title": "Resumo do Paciente", "fields": fields}]

    def guideline_result(self, query: str, result: str) -> list[dict]:
        return [{
            "color": "#2ea44f",
            "title": f"Diretriz Clinica: {query[:60]}",
            "text": result[:1500],
        }]

    def followup_report(self, report: str) -> list[dict]:
        return [{"color": "#e36209", "title": "Relatorio de Acompanhamento", "text": report[:1500]}]

    def alert_created(self, alert_id: str, severity: str, score: int) -> list[dict]:
        color = {"critical": "#cc0000", "high": "#e36209", "medium": "#f0c800", "low": "#2ea44f"}.get(
            severity, "#888888"
        )
        return [{
            "color": color,
            "title": f"Alerta criado [{severity.upper()}]",
            "fields": [
                {"title": "ID", "value": alert_id, "short": True},
                {"title": "Score", "value": str(score), "short": True},
            ],
        }]

    def status_table(self, modules: list[dict[str, Any]]) -> list[dict]:
        lines = ["| Modulo | Status | Versao |", "|--------|--------|--------|"]
        for m in modules:
            name = m.get("name", "?")
            status = ":white_check_mark:" if m.get("healthy") else ":x:"
            version = m.get("version", "?")
            lines.append(f"| {name} | {status} | {version} |")
        return [{"color": "#0066cc", "title": "Status dos Modulos", "text": "\n".join(lines)}]

    def help_text(self, available_commands: list[str]) -> list[dict]:
        cmds = [
            "/paciente <id> — resumo clínico do paciente",
            "/guideline <pergunta> — busca diretriz clínica (Florence RAG)",
            "/resumo <id> — relatório de acompanhamento (Geralda)",
            "/alerta <id> <descricao> — criar alerta crítico manual",
            "/teleconsulta <id> — abrir sala Jitsi",
            "/status — status dos módulos IntelliCare",
            "/ajuda — esta mensagem",
        ]
        text = "\n".join(f"• `@intellicare {c}`" for c in cmds if any(c.startswith(f"/{a}") for a in available_commands) or True)
        return [{"color": "#0066cc", "title": "Comandos disponíveis", "text": text}]

    def error(self, message: str) -> list[dict]:
        return [{"color": "#cc0000", "title": "Erro", "text": message}]
