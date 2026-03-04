"""OrchestratorState — shared state for all LangGraph workflows (EF-W005)."""

from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict


class AgentResponse(TypedDict, total=False):
    """Individual agent response stored in workflow state."""

    success: bool
    data: Any
    error: Optional[str]
    latency_ms: int


class OrchestratorState(TypedDict, total=False):
    """Shared mutable state threaded through all LangGraph workflow nodes.

    Fields are optional (total=False) so nodes can update only what they produce.
    """

    # ── Input ──────────────────────────────────────────────────────
    query: str
    tenant_id: str
    patient_id: Optional[str]
    workflow_id: str         # Unique execution ID (UUID)
    workflow_name: str       # e.g. "clinical_analysis"

    # ── Patient context ────────────────────────────────────────────
    ips: Optional[dict[str, Any]]

    # ── Agent results ─────────────────────────────────────────────
    agent_responses: dict[str, AgentResponse]

    # ── Synthesis ─────────────────────────────────────────────────
    synthesis: Optional[str]
    key_points: list[str]

    # ── Flow control ──────────────────────────────────────────────
    next_step: str           # Name of next node (for conditional routing)
    iterations: int          # Refinement iterations so far
    max_iterations: int      # Config-driven ceiling (default 3)

    # ── Error ─────────────────────────────────────────────────────
    error: Optional[str]
