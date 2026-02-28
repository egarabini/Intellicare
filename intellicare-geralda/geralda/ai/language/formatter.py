"""Formatador de saída em diferentes estilos."""


class OutputFormatter:
    """Formata respostas em estilos esperados pela suíte de testes."""

    @staticmethod
    def format_short(conditions: list[str], message: str, max_chars: int = 280) -> str:
        header = f"Condições: {', '.join(conditions)}. " if conditions else ""
        text = f"{header}{message}".strip()
        return text if len(text) <= max_chars else text[: max_chars - 3] + "..."

    @staticmethod
    def format_long(patient_name: str, conditions: list[str], goals: list[str], tasks: list[str]) -> str:
        return (
            f"Plano de cuidado de {patient_name}\n"
            f"Condições: {', '.join(conditions) if conditions else 'Não informado'}\n"
            f"Metas: {', '.join(goals) if goals else 'Não informado'}\n"
            f"Tarefas: {', '.join(tasks) if tasks else 'Nenhuma tarefa'}"
        )

    @staticmethod
    def format_topics(topics: list[str]) -> str:
        if not topics:
            return "- Nenhum tópico disponível."
        return "\n".join(f"- {topic}" for topic in topics)

    @staticmethod
    def format_reminder(task: str, time: str, instructions: str = "", emoji: str = "") -> str:
        details = f" | {instructions}" if instructions else ""
        icon = f"{emoji} " if emoji else ""
        return f"{icon}{time} - {task}{details}"

    @staticmethod
    def format_care_summary(
        plan_conditions: list,
        plan_goals: list,
        task_count: int,
        completed_count: int,
        adherence_rate: float,
        level: str = "basico",
    ) -> str:
        return (
            f"Resumo ({level}): condições={', '.join(map(str, plan_conditions)) or 'nenhuma'}, "
            f"metas={', '.join(map(str, plan_goals)) or 'nenhuma'}, "
            f"tarefas={completed_count}/{task_count}, adesão={adherence_rate:.0f}%"
        )

    @staticmethod
    def format_schedule(schedule_items: list[dict]) -> str:
        if not schedule_items:
            return "Sem tarefas na agenda."
        return "\n".join(f"{item.get('time', '--:--')} - {item.get('task', '')}" for item in schedule_items)

    @staticmethod
    def format_medications(medications: list[dict]) -> str:
        if not medications:
            return "Nenhuma medicação cadastrada."
        lines = []
        for med in medications:
            lines.append(
                f"{med.get('name', 'Medicamento')} | {med.get('frequency', 'frequência não informada')} | {med.get('time', '--:--')}"
            )
        return "\n".join(lines)
