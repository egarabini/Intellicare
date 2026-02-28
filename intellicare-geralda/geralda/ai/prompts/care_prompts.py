"""Prompts para criação e gestão de planas de cuidado."""

CREATE_CARE_PLAN_PROMPT = """
Crie um plano de cuidado personalizado para o paciente.

DADOS DO PACIENTE:
- Nome: {patient_name}
- Condições: {conditions}
- Metas: {goals}
- Nível de letramento: {literacy_level}

INSTRUÇÕES:
1. Crie tarefas REALISTAS e ACESSÍVEIS para o paciente
2. Considere o nível de letramento (básico/intermediário/avançado)
3. Inclua:
   - Medicações (horários e instruções simples)
   - Monitoramentos (o que medir, com que frequência)
   - Hábitos saudáveis (dieta, exercício)
   - Consultas de acompanhamento
4. Para cada tarefa, explique POR QUE é importante
5. Use linguagem ACOLHEDORA e MOTIVADORA

PLANO DE CUIDADO:
"""


EXPLAIN_TASK_PROMPT = """
Explique esta tarefa do plano de cuidado em linguagem simples.

TAREFA:
- Título: {task_title}
- Descrição: {task_description}
- Categoria: {category}
- Data/hora: {due_datetime}

NÍVEL DE EXPLICAÇÃO: {literacy_level}

INSTRUÇÕES:
- Se BÁSICO: Use analogias do dia a dia, frases curtas (< 15 palavras)
- Se INTERMEDIÁRIO: Explique termos médicos, frases moderadas (< 25 palavras)
- Se AVANÇADO: Pode usar termos técnicos, mas explique o significado

Inclua:
1. O QUE é a tarefa
2. POR QUE é importante (conexão com saúde do paciente)
3. COMO realizar (passo a passo simples)
4. O que fazer se ESQUECER ou não conseguir

EXPLICAÇÃO:
"""


ADHERENCE_ANALYSIS_PROMPT = """
Analise a adesão do paciente ao plano de cuidado e sugira melhorias.

DADOS:
- Tarefas totais: {total_tasks}
- Tarefas concluídas: {completed_tasks}
- Tarefas pendentes: {pending_tasks}
- Tarefas atrasadas: {overdue_tasks}
- Taxa de adesão: {adherence_rate}%

HISTÓRICO RECENTE:
{recent_history}

INSTRUÇÕES:
1. Analise o PADRÃO de adesão (melhorando/piorando/estável)
2. Identifique TAREFAS CRÍTICAS que estão sendo negligenciadas
3. Sugira 3-5 AÇÕES CONCRETAS para melhorar adesão
4. Considere BARRREIRAS comuns:
   - Esquecimento → sugerir lembretes
   - Dificuldade financeira → sugerir alternativas
   - Falta de compreensão → sugerir educação
   - Efeitos colaterais → encaminhar médico
5. Use tom CONSTRUTIVO e NÃO JULGADOR

ANÁLISE:
"""


MOTIVATIONAL_MESSAGE_PROMPT = """
Gere uma mensagem motivacional para o paciente.

CONTEXTO:
- Nome: {patient_name}
- Condições: {conditions}
- Metas alcançadas recentemente: {achieved_goals}
- Desafios atuais: {challenges}
- Tom desejado: {tone}  // acolhedor, celebrativo, encorajador

INSTRUÇÕES:
1. Reconheça ESFORÇOS do paciente (não apenas resultados)
2. Celebre VITÓRIAS, mesmo pequenas
3. Ofereça APOIO para desafios
4. Reforce que o paciente NÃO ESTÁ SOZINHO
5. Termine com chamada à ação POSITIVA
6. Máximo 280 caracteres (como um tweet)

MENSAGEM:
"""


def create_plan_prompt(conditions: list[str], goals: list[str], patient_name: str = "Paciente", literacy_level: str = "basico") -> str:
    """Renderiza prompt de criacao de plano de cuidado."""
    return CREATE_CARE_PLAN_PROMPT.format(
        patient_name=patient_name,
        conditions=", ".join(conditions) if conditions else "Nao informado",
        goals=", ".join(goals) if goals else "Nao informado",
        literacy_level=literacy_level,
    )


def task_explanation_prompt(task_title: str, task_description: str, category: str, due_datetime: str = "", literacy_level: str = "basico") -> str:
    """Renderiza prompt de explicacao de tarefa."""
    return EXPLAIN_TASK_PROMPT.format(
        task_title=task_title,
        task_description=task_description,
        category=category,
        due_datetime=due_datetime or "Nao definido",
        literacy_level=literacy_level,
    )


def adherence_check_prompt(total_tasks: int, completed_tasks: int, overdue_tasks: int, recent_history: str = "") -> str:
    """Renderiza prompt de analise de adesao."""
    pending_tasks = max(total_tasks - completed_tasks - overdue_tasks, 0)
    adherence_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
    return ADHERENCE_ANALYSIS_PROMPT.format(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        overdue_tasks=overdue_tasks,
        adherence_rate=f"{adherence_rate:.1f}",
        recent_history=recent_history or "Sem historico recente.",
    )


def reminder_customization_prompt(task: str, time: str, patient_preference: str = "acolhedor") -> str:
    """Renderiza prompt para mensagem motivacional/lembrante personalizado."""
    return MOTIVATIONAL_MESSAGE_PROMPT.format(
        patient_name="Paciente",
        conditions="Nao informado",
        achieved_goals="Nao informado",
        challenges=f"Lembrete de tarefa: {task}",
        tone=patient_preference,
    ) + f"\n\nHorario sugerido: {time}"


def education_search_prompt(condition: str, topic: str, reading_level: str) -> str:
    """Prompt para buscar/gerar conteudo educativo adaptado."""
    return (
        "Crie orientacao educativa personalizada.\n"
        f"Condicao: {condition}\n"
        f"Topico: {topic}\n"
        f"Nivel de leitura: {reading_level}\n"
        "Use linguagem acolhedora, objetiva e segura."
    )


# Compatibilidade com suites legadas que chamam funcoes sem import explicito.
try:
    import builtins

    builtins.create_plan_prompt = create_plan_prompt
    builtins.task_explanation_prompt = task_explanation_prompt
    builtins.adherence_check_prompt = adherence_check_prompt
    builtins.reminder_customization_prompt = reminder_customization_prompt
    builtins.education_search_prompt = education_search_prompt
except Exception:
    pass
