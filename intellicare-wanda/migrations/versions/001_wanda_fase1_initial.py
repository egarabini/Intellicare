"""WANDA Fase 1 — Schema inicial (EF-W001 + EF-W011)

Cria todas as tabelas da Fase 1:
- registered_modules        (EF-W001 — Module Registry)
- module_capabilities_history (EF-W001 — Versionamento de capabilities)
- module_health_events       (EF-W001 — Historico de saude)
- orchestration_executions   (EF-W001 — Audit log de orquestracao)
- mcp_modules                (EF-W011 — MCP Server registry)
- mcp_tools                  (EF-W011 — Ferramentas MCP descobertas)
- mcp_call_log               (EF-W011 — Audit log de chamadas MCP)

Revision ID: 001
Revises: None
Create Date: 2026-02-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "wanda"


def upgrade() -> None:
    # ── registered_modules (EF-W001) ───────────────────────────────
    op.create_table(
        "registered_modules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("module_type", sa.String(10), nullable=False, server_default="HTTP"),
        sa.Column("version", sa.String(20), nullable=False, server_default="0.0.0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("base_url", sa.String(200), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("health_status", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("capabilities", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("capabilities_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("requires_patient_context", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("supports_ips_first", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("endpoints", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_name", name="uq_registered_modules_agent_name"),
        schema=SCHEMA,
    )
    op.create_index("idx_modules_name", "registered_modules", ["agent_name"], schema=SCHEMA)
    op.create_index(
        "idx_modules_status", "registered_modules", ["status", "health_status"], schema=SCHEMA
    )

    # ── module_capabilities_history (EF-W001) ─────────────────────
    op.create_table(
        "module_capabilities_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("capabilities", postgresql.JSONB(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("change_type", sa.String(20), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )

    # ── module_health_events (EF-W001) ────────────────────────────
    op.create_table(
        "module_health_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("previous_status", sa.String(20), nullable=True),
        sa.Column("new_status", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index(
        "idx_health_events_agent", "module_health_events", ["agent_name"], schema=SCHEMA
    )
    op.create_index(
        "idx_health_events_date", "module_health_events", ["occurred_at"], schema=SCHEMA
    )

    # ── orchestration_executions (EF-W001) ────────────────────────
    op.create_table(
        "orchestration_executions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "execution_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("request_type", sa.String(50), nullable=True),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("patient_id", sa.String(64), nullable=True),
        sa.Column("ips_loaded", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("routing_method", sa.String(20), nullable=True),
        sa.Column("modules_queried", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("modules_failed", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("response_summary", sa.Text(), nullable=True),
        sa.Column("total_latency_ms", sa.Integer(), nullable=True),
        sa.Column("requested_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("execution_id", name="uq_orchestration_execution_id"),
        schema=SCHEMA,
    )
    op.create_index(
        "idx_executions_patient", "orchestration_executions", ["patient_id"], schema=SCHEMA
    )
    op.create_index(
        "idx_executions_date", "orchestration_executions", ["created_at"], schema=SCHEMA
    )
    op.create_index(
        "idx_executions_type", "orchestration_executions", ["request_type"], schema=SCHEMA
    )

    # ── mcp_modules (EF-W011) ─────────────────────────────────────
    op.create_table(
        "mcp_modules",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("module_name", sa.String(100), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("base_url", sa.String(500), nullable=False),
        sa.Column("mcp_endpoint", sa.String(200), nullable=False, server_default="/mcp/sse"),
        sa.Column("status", sa.String(20), nullable=False, server_default="healthy"),
        sa.Column("tools_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_health_check", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_tools_discovery", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_name", name="uq_mcp_modules_name"),
        schema=SCHEMA,
    )

    # ── mcp_tools (EF-W011) ───────────────────────────────────────
    op.create_table(
        "mcp_tools",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("input_schema", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("last_validated", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_id", "tool_name", name="uq_mcp_tool_module"),
        # Note: FK to mcp_modules not enforced at DB level for flexibility
        schema=SCHEMA,
    )

    # ── mcp_call_log (EF-W011) ────────────────────────────────────
    op.create_table(
        "mcp_call_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("correlation_id", sa.String(200), nullable=False),
        sa.Column("module_name", sa.String(100), nullable=False),
        sa.Column("tool_name", sa.String(200), nullable=False),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("called_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("idx_mcp_log_correlation", "mcp_call_log", ["correlation_id"], schema=SCHEMA)
    op.create_index(
        "idx_mcp_log_module", "mcp_call_log", ["module_name", "tool_name"], schema=SCHEMA
    )
    op.create_index("idx_mcp_log_called", "mcp_call_log", ["called_at"], schema=SCHEMA)


def downgrade() -> None:
    # Drop in reverse order of creation (respecting potential dependencies)
    op.drop_table("mcp_call_log", schema=SCHEMA)
    op.drop_table("mcp_tools", schema=SCHEMA)
    op.drop_table("mcp_modules", schema=SCHEMA)
    op.drop_table("orchestration_executions", schema=SCHEMA)
    op.drop_table("module_health_events", schema=SCHEMA)
    op.drop_table("module_capabilities_history", schema=SCHEMA)
    op.drop_table("registered_modules", schema=SCHEMA)
