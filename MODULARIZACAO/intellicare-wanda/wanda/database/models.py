"""SQLAlchemy ORM models for Wanda persistent storage (EF-W001 + EF-W011 + EF-W006/W007/W013)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all Wanda ORM models."""

    pass


# ── EF-W001: Module Registry ──────────────────────────────────────


class RegisteredModuleModel(Base):
    """Persistent registration of ecosystem modules (HTTP + MCP).

    Evolves the in-memory ModuleRegistry from v1.0 into PostgreSQL.
    """

    __tablename__ = "registered_modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    module_type: Mapped[str] = mapped_column(
        String(10), nullable=False, default="HTTP"
    )  # HTTP | MCP
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="0.0.0")
    description: Mapped[str] = mapped_column(Text, nullable=True, default="")
    base_url: Mapped[str] = mapped_column(String(200), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, inactive, deprecated
    health_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unknown"
    )  # healthy, unhealthy, degraded, unknown

    capabilities: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    capabilities_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    requires_patient_context: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    supports_ips_first: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    endpoints: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_health_check_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_modules_name", "agent_name"),
        Index("idx_modules_status", "status", "health_status"),
    )


class ModuleCapabilitiesHistoryModel(Base):
    """Version history of module capabilities."""

    __tablename__ = "module_capabilities_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    capabilities: Mapped[dict] = mapped_column(JSONB, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    change_type: Mapped[str] = mapped_column(
        String(20), nullable=True
    )  # added, modified, removed


class ModuleHealthEventModel(Base):
    """Health event log for uptime tracking."""

    __tablename__ = "module_health_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # went_healthy, went_unhealthy, went_degraded
    previous_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_health_events_agent", "agent_name"),
        Index("idx_health_events_date", "occurred_at"),
    )


class OrchestrationExecutionModel(Base):
    """Audit log of orchestration executions."""

    __tablename__ = "orchestration_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    request_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # analyze, query, orchestrate
    query: Mapped[str | None] = mapped_column(Text, nullable=True)
    patient_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ips_loaded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Routing
    routing_method: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # keyword, llm, direct
    modules_queried: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    modules_failed: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)

    # Result
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    response_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Audit
    requested_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_executions_patient", "patient_id"),
        Index("idx_executions_date", "created_at"),
        Index("idx_executions_type", "request_type"),
    )


# ── EF-W011: MCP Module Registry ──────────────────────────────────


class MCPModuleModel(Base):
    """Registration of MCP Servers (MINERVA, PIERRE)."""

    __tablename__ = "mcp_modules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    module_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    mcp_endpoint: Mapped[str] = mapped_column(
        String(200), nullable=False, default="/mcp/sse"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="healthy"
    )  # healthy, degraded, unavailable
    tools_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    last_health_check: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_tools_discovery: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class MCPToolModel(Base):
    """Tools available from MCP Servers."""

    __tablename__ = "mcp_tools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    tool_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    input_schema: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    last_validated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("module_id", "tool_name", name="uq_mcp_tool_module"),
    )


class MCPCallLogModel(Base):
    """Audit log of MCP tool invocations."""

    __tablename__ = "mcp_call_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    correlation_id: Mapped[str] = mapped_column(String(200), nullable=False)
    module_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(200), nullable=False)
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # success, error, timeout
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    called_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_mcp_log_correlation", "correlation_id"),
        Index("idx_mcp_log_module", "module_name", "tool_name"),
        Index("idx_mcp_log_called", "called_at"),
    )


# ── EF-W006: Event Coordinations ──────────────────────────────────


class EventCoordinationModel(Base):
    """Audit trail of proactive event coordinations (EF-W006)."""

    __tablename__ = "event_coordinations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    coordination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    patient_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    agents_notified: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    agents_failed: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    workflow_triggered: Mapped[str | None] = mapped_column(String(50), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(20), nullable=True)

    coordination_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    coordinated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_coordinations_event", "event_id"),
        Index("idx_coordinations_patient", "patient_id"),
        Index("idx_coordinations_date", "coordinated_at"),
    )


# ── EF-W007: Clinical Alerts ───────────────────────────────────────


class ClinicalAlertModel(Base):
    """Clinical alerts received from agents, deduplicated and managed (EF-W007)."""

    __tablename__ = "clinical_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_agent: Mapped[str] = mapped_column(String(50), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    priority_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    is_consolidated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consolidated_from: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, acknowledged, resolved, expired, deduplicated

    acknowledged_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    escalation_scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    escalated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    escalated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_alerts_patient", "patient_id"),
        Index("idx_alerts_status", "status"),
        Index("idx_alerts_severity_status", "severity", "status"),
        Index("idx_alerts_created", "created_at"),
    )


# ── EF-W013: Dr. Nise Sessions ────────────────────────────────────


class NiseSessionModel(Base):
    """Patient education chatbot sessions — LGPD health record (EF-W013)."""

    __tablename__ = "nise_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)  # portal | rocketchat

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    flagged_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    escalated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="ACTIVE"
    )  # ACTIVE | ENDED | ESCALATED

    __table_args__ = (Index("idx_nise_sessions_patient", "patient_id"),)


class NiseMessageModel(Base):
    """Individual messages in a Dr. Nise session — LGPD 2-year retention (EF-W013)."""

    __tablename__ = "nise_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # patient | nise
    content: Mapped[str] = mapped_column(Text, nullable=False)
    flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_nise_messages_session", "session_id", "created_at"),
    )
