"""create routing tables

Revision ID: 20260216_0001
Revises:
Create Date: 2026-02-16 10:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260216_0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = "comunicacao_operacional"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")

    op.create_table(
        "communication_intents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_module", sa.String(length=120), nullable=False),
        sa.Column("source_event_id", sa.String(length=200), nullable=True),
        sa.Column("recipient_type", sa.String(length=40), nullable=False),
        sa.Column("recipient_id", sa.String(length=200), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("content_template_id", sa.String(length=100), nullable=True),
        sa.Column("content_params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("content_raw", sa.Text(), nullable=True),
        sa.Column("preferred_channel", sa.String(length=30), nullable=True),
        sa.Column(
            "excluded_channels",
            postgresql.ARRAY(sa.String(length=30)),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("require_ack", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("correlation_id", sa.String(length=200), nullable=False),
        sa.Column("parent_intent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("timeline", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.ForeignKeyConstraint(["parent_intent_id"], [f"{SCHEMA}.communication_intents.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("idx_intents_status", "communication_intents", ["status"], unique=False, schema=SCHEMA)
    op.create_index("idx_intents_severity", "communication_intents", ["severity"], unique=False, schema=SCHEMA)
    op.create_index("idx_intents_recipient", "communication_intents", ["recipient_id"], unique=False, schema=SCHEMA)
    op.create_index("idx_intents_correlation", "communication_intents", ["correlation_id"], unique=False, schema=SCHEMA)
    op.create_index("idx_intents_created", "communication_intents", ["created_at"], unique=False, schema=SCHEMA)
    op.create_index(
        "ux_intents_source_event",
        "communication_intents",
        ["source_module", "source_event_id"],
        unique=True,
        schema=SCHEMA,
    )

    op.create_table(
        "delivery_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("intent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'queued'")),
        sa.Column("channel_message_id", sa.String(length=300), nullable=True),
        sa.Column("channel_room_id", sa.String(length=300), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("queued_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("read_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("failed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["intent_id"], [f"{SCHEMA}.communication_intents.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("idx_deliveries_intent", "delivery_results", ["intent_id"], unique=False, schema=SCHEMA)
    op.create_index("idx_deliveries_status", "delivery_results", ["status"], unique=False, schema=SCHEMA)
    op.create_index("idx_deliveries_channel", "delivery_results", ["channel"], unique=False, schema=SCHEMA)

    op.create_table(
        "message_templates",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("channel_variants", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("params_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sample_params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("locale", sa.String(length=10), nullable=False, server_default=sa.text("'pt-BR'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_by", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("idx_templates_category", "message_templates", ["category"], unique=False, schema=SCHEMA)
    op.create_index("idx_templates_active", "message_templates", ["active"], unique=False, schema=SCHEMA)

    op.create_table(
        "routing_rules",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("action", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("institution_id", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("idx_rules_priority", "routing_rules", ["priority"], unique=False, schema=SCHEMA)
    op.create_index("idx_rules_active", "routing_rules", ["active"], unique=False, schema=SCHEMA)
    _seed_default_rules()
    _seed_default_templates()


def downgrade() -> None:
    op.drop_index("idx_rules_active", table_name="routing_rules", schema=SCHEMA)
    op.drop_index("idx_rules_priority", table_name="routing_rules", schema=SCHEMA)
    op.drop_table("routing_rules", schema=SCHEMA)

    op.drop_index("idx_templates_active", table_name="message_templates", schema=SCHEMA)
    op.drop_index("idx_templates_category", table_name="message_templates", schema=SCHEMA)
    op.drop_table("message_templates", schema=SCHEMA)

    op.drop_index("idx_deliveries_channel", table_name="delivery_results", schema=SCHEMA)
    op.drop_index("idx_deliveries_status", table_name="delivery_results", schema=SCHEMA)
    op.drop_index("idx_deliveries_intent", table_name="delivery_results", schema=SCHEMA)
    op.drop_table("delivery_results", schema=SCHEMA)

    op.drop_index("ux_intents_source_event", table_name="communication_intents", schema=SCHEMA)
    op.drop_index("idx_intents_created", table_name="communication_intents", schema=SCHEMA)
    op.drop_index("idx_intents_correlation", table_name="communication_intents", schema=SCHEMA)
    op.drop_index("idx_intents_recipient", table_name="communication_intents", schema=SCHEMA)
    op.drop_index("idx_intents_severity", table_name="communication_intents", schema=SCHEMA)
    op.drop_index("idx_intents_status", table_name="communication_intents", schema=SCHEMA)
    op.drop_table("communication_intents", schema=SCHEMA)


def _seed_default_rules() -> None:
    rules_table = sa.table(
        "routing_rules",
        sa.column("id", sa.String()),
        sa.column("name", sa.String()),
        sa.column("priority", sa.Integer()),
        sa.column("active", sa.Boolean()),
        sa.column("conditions", postgresql.JSONB()),
        sa.column("action", postgresql.JSONB()),
        sa.column("institution_id", sa.String()),
    )
    rows = [
        {
            "id": "rule_critical_professional",
            "name": "Critico profissional",
            "priority": 10,
            "active": True,
            "conditions": {"severities": ["critical"], "recipient_types": ["professional"], "categories": []},
            "action": {"channels": [{"channel": "matrix"}, {"channel": "sms"}]},
            "institution_id": None,
        },
        {
            "id": "rule_critical_patient",
            "name": "Critico paciente",
            "priority": 20,
            "active": True,
            "conditions": {"severities": ["critical"], "recipient_types": ["patient"], "categories": []},
            "action": {"channels": [{"channel": "whatsapp"}, {"channel": "sms"}, {"channel": "matrix"}]},
            "institution_id": None,
        },
        {
            "id": "rule_high_default",
            "name": "High default",
            "priority": 30,
            "active": True,
            "conditions": {"severities": ["high"], "recipient_types": [], "categories": []},
            "action": {"channels": [{"channel": "matrix"}, {"channel": "email"}]},
            "institution_id": None,
        },
        {
            "id": "rule_medium_default",
            "name": "Medium default",
            "priority": 40,
            "active": True,
            "conditions": {"severities": ["medium"], "recipient_types": [], "categories": []},
            "action": {"channels": [{"channel": "matrix"}]},
            "institution_id": None,
        },
        {
            "id": "rule_low_default",
            "name": "Low default",
            "priority": 50,
            "active": True,
            "conditions": {"severities": ["low"], "recipient_types": [], "categories": []},
            "action": {"channels": [{"channel": "email"}]},
            "institution_id": None,
        },
        {
            "id": "rule_fallback_any",
            "name": "Fallback any",
            "priority": 999,
            "active": True,
            "conditions": {"severities": [], "recipient_types": [], "categories": []},
            "action": {"channels": [{"channel": "matrix"}]},
            "institution_id": None,
        },
    ]
    op.bulk_insert(rules_table, rows, multiinsert=False)


def _seed_default_templates() -> None:
    templates_table = sa.table(
        "message_templates",
        sa.column("id", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
        sa.column("category", sa.String()),
        sa.column("version", sa.Integer()),
        sa.column("channel_variants", postgresql.JSONB()),
        sa.column("params_schema", postgresql.JSONB()),
        sa.column("sample_params", postgresql.JSONB()),
        sa.column("active", sa.Boolean()),
        sa.column("locale", sa.String()),
        sa.column("created_by", sa.String()),
    )
    common_variants = {
        "matrix": {"format": "plain", "body": "{{message}}"},
        "email": {"format": "html", "subject": "IntelliCare", "body": "<p>{{message}}</p>"},
        "push": {"format": "push_json", "title": "IntelliCare", "body": "{{message}}"},
        "whatsapp": {"format": "plain", "body": "{{message}}"},
        "sms": {"format": "plain", "body": "{{message}}", "max_length": 160},
    }
    rows = [
        {
            "id": "clinical_alert_generic",
            "name": "Alerta Clinico Generico",
            "description": "Template base para alertas clinicos",
            "category": "clinical_alert",
            "version": 1,
            "channel_variants": common_variants,
            "params_schema": {"required": ["message"], "properties": {"message": {"type": "string"}}},
            "sample_params": {"message": "Paciente com alerta clinico"},
            "active": True,
            "locale": "pt-BR",
            "created_by": "migration",
        },
        {
            "id": "medication_reminder",
            "name": "Lembrete de Medicacao",
            "description": "Template de lembrete",
            "category": "medication_reminder",
            "version": 1,
            "channel_variants": common_variants,
            "params_schema": {"required": ["message"], "properties": {"message": {"type": "string"}}},
            "sample_params": {"message": "Hora de tomar sua medicacao"},
            "active": True,
            "locale": "pt-BR",
            "created_by": "migration",
        },
        {
            "id": "teleconsult_invite",
            "name": "Convite de Teleconsulta",
            "description": "Template de convite para video",
            "category": "teleconsult",
            "version": 1,
            "channel_variants": common_variants,
            "params_schema": {"required": ["message"], "properties": {"message": {"type": "string"}}},
            "sample_params": {"message": "Sua teleconsulta foi agendada"},
            "active": True,
            "locale": "pt-BR",
            "created_by": "migration",
        },
        {
            "id": "escalation_unread_critical",
            "name": "Escalonamento de Critico sem Leitura",
            "description": "Template de escalonamento automatico",
            "category": "escalation",
            "version": 1,
            "channel_variants": common_variants,
            "params_schema": {"required": ["message"], "properties": {"message": {"type": "string"}}},
            "sample_params": {"message": "Alerta critico sem ACK no prazo"},
            "active": True,
            "locale": "pt-BR",
            "created_by": "migration",
        },
    ]
    op.bulk_insert(templates_table, rows, multiinsert=False)
