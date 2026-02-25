"""Prompts para Geralda AI."""

from geralda.ai.prompts.system_prompt import (
    GERALDA_SYSTEM_PROMPT,
    build_system_prompt,
    EMERGENCY_PROMPT,
    SAFETY_GUIDELINES,
)
from geralda.ai.prompts.care_prompts import (
    CREATE_CARE_PLAN_PROMPT,
    EXPLAIN_TASK_PROMPT,
    ADHERENCE_ANALYSIS_PROMPT,
    MOTIVATIONAL_MESSAGE_PROMPT,
    create_plan_prompt,
    task_explanation_prompt,
    adherence_check_prompt,
    reminder_customization_prompt,
    education_search_prompt,
)

__all__ = [
    "GERALDA_SYSTEM_PROMPT",
    "build_system_prompt",
    "EMERGENCY_PROMPT",
    "SAFETY_GUIDELINES",
    "CREATE_CARE_PLAN_PROMPT",
    "EXPLAIN_TASK_PROMPT",
    "ADHERENCE_ANALYSIS_PROMPT",
    "MOTIVATIONAL_MESSAGE_PROMPT",
    "create_plan_prompt",
    "task_explanation_prompt",
    "adherence_check_prompt",
    "reminder_customization_prompt",
    "education_search_prompt",
]
