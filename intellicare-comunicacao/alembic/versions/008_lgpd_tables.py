"""Create LGPD compliance tables

Revision ID: 008_lgpd_tables
Revises: 007_materialized_views
Create Date: 2026-02-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID


# revision identifiers, used by Alembic.
revision = '008_lgpd_tables'
down_revision = '007_materialized_views'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create LGPD compliance tables."""
    
    # ── 1. Tabela de Preferências de Comunicação ──
    op.create_table(
        'communication_preferences',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('patient_id', sa.String(200), nullable=False, unique=True, index=True),
        
        # Preferências por canal (6 canais)
        sa.Column('rocketchat_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sms_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('whatsapp_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('push_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('jitsi_enabled', sa.Boolean(), nullable=False, server_default='true'),
        
        # Quiet hours (horários silenciosos)
        sa.Column('quiet_hours', JSON, nullable=True),
        
        # Consentimento
        sa.Column('consent_given', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('consent_given_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consent_version', sa.String(20), nullable=True),
        sa.Column('consent_expires_at', sa.DateTime(timezone=True), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        schema='comunicacao_operacional'
    )
    
    # Índices para performance
    op.create_index(
        'idx_comm_pref_patient_id',
        'communication_preferences',
        ['patient_id'],
        unique=True,
        schema='comunicacao_operacional'
    )
    
    # ── 2. Tabela de Log de Consentimento (Append-Only) ──
    op.create_table(
        'consent_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('patient_id', sa.String(200), nullable=False, index=True),
        
        # Status do consentimento
        sa.Column('consent_status', sa.String(20), nullable=False),  # GRANTED, WITHDRAWN, EXPIRED, RENEWED, REJECTED
        sa.Column('consent_version', sa.String(20), nullable=False),
        sa.Column('consent_given_at', sa.DateTime(timezone=True), nullable=False),
        
        # Metadados (IP, user agent, etc.)
        sa.Column('metadata', JSON, nullable=True),
        
        # Timestamp (imutável)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        schema='comunicacao_operacional'
    )
    
    # Índices
    op.create_index(
        'idx_consent_log_patient_id',
        'consent_log',
        ['patient_id'],
        schema='comunicacao_operacional'
    )
    op.create_index(
        'idx_consent_log_created_at',
        'consent_log',
        ['created_at'],
        schema='comunicacao_operacional'
    )
    
    # ── 3. Tabela de Audit Trail (Append-Only com Hash Chain) ──
    op.create_table(
        'audit_trail',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # Referências
        sa.Column('intent_id', sa.String(200), nullable=True, index=True),
        sa.Column('delivery_id', sa.String(200), nullable=True, index=True),
        
        # Tipo de comunicação
        sa.Column('intent_type', sa.String(50), nullable=False),
        sa.Column('template_name', sa.String(100), nullable=True),
        sa.Column('channel', sa.String(20), nullable=False),
        
        # Destinatário (pseudonimizado)
        sa.Column('recipient_type', sa.String(40), nullable=False),
        sa.Column('recipient_hash', sa.String(64), nullable=True, index=True),
        sa.Column('patient_hash', sa.String(64), nullable=True, index=True),
        
        # Status e erro
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        
        # LGPD
        sa.Column('legal_basis', sa.String(50), nullable=True),
        sa.Column('lgpd_override', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('lgpd_reason', sa.Text(), nullable=True),
        sa.Column('consent_status', sa.String(20), nullable=True),
        
        # Severidade e origem
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('source_module', sa.String(100), nullable=True),
        sa.Column('source_event_id', sa.String(200), nullable=True),
        
        # Hash chain (blockchain simplificado)
        sa.Column('previous_hash', sa.String(64), nullable=True),
        sa.Column('entry_hash', sa.String(64), nullable=False, unique=True),
        
        # Metadados adicionais
        sa.Column('metadata', JSON, nullable=True),
        
        # Timestamp (imutável)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),

        schema='comunicacao_operacional'
    )

    # Índices para performance
    op.create_index(
        'idx_audit_trail_intent_id',
        'audit_trail',
        ['intent_id'],
        schema='comunicacao_operacional'
    )
    op.create_index(
        'idx_audit_trail_delivery_id',
        'audit_trail',
        ['delivery_id'],
        schema='comunicacao_operacional'
    )
    op.create_index(
        'idx_audit_trail_patient_hash',
        'audit_trail',
        ['patient_hash'],
        schema='comunicacao_operacional'
    )
    op.create_index(
        'idx_audit_trail_created_at',
        'audit_trail',
        ['created_at'],
        schema='comunicacao_operacional'
    )
    op.create_index(
        'idx_audit_trail_entry_hash',
        'audit_trail',
        ['entry_hash'],
        unique=True,
        schema='comunicacao_operacional'
    )
    op.create_index(
        'idx_audit_trail_legal_basis',
        'audit_trail',
        ['legal_basis'],
        schema='comunicacao_operacional'
    )

    # ── 4. Trigger para Prevenir UPDATE/DELETE em Audit Trail ──
    # Audit trail é APPEND-ONLY (imutável)
    op.execute("""
        CREATE OR REPLACE FUNCTION comunicacao_operacional.prevent_audit_trail_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit trail é imutável - UPDATE e DELETE não são permitidos';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER prevent_audit_trail_update
        BEFORE UPDATE ON comunicacao_operacional.audit_trail
        FOR EACH ROW
        EXECUTE FUNCTION comunicacao_operacional.prevent_audit_trail_modification();
    """)

    op.execute("""
        CREATE TRIGGER prevent_audit_trail_delete
        BEFORE DELETE ON comunicacao_operacional.audit_trail
        FOR EACH ROW
        EXECUTE FUNCTION comunicacao_operacional.prevent_audit_trail_modification();
    """)

    # ── 5. Trigger para Prevenir UPDATE/DELETE em Consent Log ──
    # Consent log também é APPEND-ONLY
    op.execute("""
        CREATE TRIGGER prevent_consent_log_update
        BEFORE UPDATE ON comunicacao_operacional.consent_log
        FOR EACH ROW
        EXECUTE FUNCTION comunicacao_operacional.prevent_audit_trail_modification();
    """)

    op.execute("""
        CREATE TRIGGER prevent_consent_log_delete
        BEFORE DELETE ON comunicacao_operacional.consent_log
        FOR EACH ROW
        EXECUTE FUNCTION comunicacao_operacional.prevent_audit_trail_modification();
    """)

    # ── 6. Trigger para Atualizar updated_at em Preferences ──
    op.execute("""
        CREATE OR REPLACE FUNCTION comunicacao_operacional.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER update_communication_preferences_updated_at
        BEFORE UPDATE ON comunicacao_operacional.communication_preferences
        FOR EACH ROW
        EXECUTE FUNCTION comunicacao_operacional.update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop LGPD compliance tables."""

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_communication_preferences_updated_at ON comunicacao_operacional.communication_preferences")
    op.execute("DROP TRIGGER IF EXISTS prevent_consent_log_delete ON comunicacao_operacional.consent_log")
    op.execute("DROP TRIGGER IF EXISTS prevent_consent_log_update ON comunicacao_operacional.consent_log")
    op.execute("DROP TRIGGER IF EXISTS prevent_audit_trail_delete ON comunicacao_operacional.audit_trail")
    op.execute("DROP TRIGGER IF EXISTS prevent_audit_trail_update ON comunicacao_operacional.audit_trail")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS comunicacao_operacional.update_updated_at_column()")
    op.execute("DROP FUNCTION IF EXISTS comunicacao_operacional.prevent_audit_trail_modification()")

    # Drop tables
    op.drop_table('audit_trail', schema='comunicacao_operacional')
    op.drop_table('consent_log', schema='comunicacao_operacional')
    op.drop_table('communication_preferences', schema='comunicacao_operacional')

