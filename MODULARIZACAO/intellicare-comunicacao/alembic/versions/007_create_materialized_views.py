"""Create materialized views for dashboards

Revision ID: 007_materialized_views
Revises: 006_rocketchat_integration
Create Date: 2026-02-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_materialized_views'
down_revision = '006_rocketchat_integration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create materialized views for dashboard queries."""
    
    # 1. Materialized View: SLA Dashboard
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS comunicacao_analitico.team_communication_sla AS
        SELECT 
            ci.id AS intent_id,
            ci.recipient_id,
            ci.severity,
            ci.category,
            ci.created_at,
            ci.delivered_at,
            ci.failed_at,
            cd.channel,
            cd.status,
            EXTRACT(EPOCH FROM (COALESCE(ci.delivered_at, ci.failed_at, NOW()) - ci.created_at)) AS response_time_seconds,
            -- Determinar team_id e team_name (assumindo que recipient_id é um user_id que tem team)
            -- TODO: Ajustar JOIN com tabela de usuários quando disponível
            'TEAM-' || SUBSTRING(ci.recipient_id FROM 1 FOR 8) AS team_id,
            'Equipe ' || SUBSTRING(ci.recipient_id FROM 1 FOR 8) AS team_name,
            -- SLA target baseado em severidade
            CASE 
                WHEN ci.severity = 'CRITICAL' THEN 300  -- 5 minutos
                WHEN ci.severity = 'HIGH' THEN 900      -- 15 minutos
                WHEN ci.severity = 'MEDIUM' THEN 3600   -- 1 hora
                ELSE 7200                                -- 2 horas
            END AS sla_target_seconds,
            -- Verificar se está dentro do SLA
            EXTRACT(EPOCH FROM (COALESCE(ci.delivered_at, ci.failed_at, NOW()) - ci.created_at)) <= 
            CASE 
                WHEN ci.severity = 'CRITICAL' THEN 300
                WHEN ci.severity = 'HIGH' THEN 900
                WHEN ci.severity = 'MEDIUM' THEN 3600
                ELSE 7200
            END AS within_sla
        FROM comunicacao_operacional.communication_intents ci
        LEFT JOIN comunicacao_operacional.communication_dispatches cd ON cd.intent_id = ci.id
        WHERE ci.created_at > NOW() - INTERVAL '90 days'  -- Últimos 90 dias
        ORDER BY ci.created_at DESC;
    """)
    
    # Criar índices na materialized view
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_team_sla_created_at 
        ON comunicacao_analitico.team_communication_sla(created_at);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_team_sla_team_id 
        ON comunicacao_analitico.team_communication_sla(team_id);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_team_sla_severity 
        ON comunicacao_analitico.team_communication_sla(severity);
    """)
    
    # 2. Materialized View: LGPD Compliance
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS comunicacao_analitico.lgpd_compliance_view AS
        SELECT 
            cp.patient_id,
            cp.consent_given_at,
            cp.consent_withdrawn_at,
            cp.legal_basis,
            cp.quiet_hours_start,
            cp.quiet_hours_end,
            cp.created_at,
            cp.updated_at,
            -- Calcular status de consentimento
            CASE 
                WHEN cp.consent_withdrawn_at IS NOT NULL THEN 'withdrawn'
                WHEN cp.consent_given_at IS NOT NULL THEN 'active'
                ELSE 'pending'
            END AS consent_status,
            -- Contar comunicações bloqueadas (via audit log)
            (
                SELECT COUNT(*) 
                FROM comunicacao_operacional.lgpd_audit_log al 
                WHERE al.patient_id = cp.patient_id 
                AND al.action = 'BLOCKED'
                AND al.created_at > NOW() - INTERVAL '30 days'
            ) AS blocked_count_30d,
            -- Contar overrides
            (
                SELECT COUNT(*) 
                FROM comunicacao_operacional.lgpd_audit_log al 
                WHERE al.patient_id = cp.patient_id 
                AND al.action = 'OVERRIDE'
                AND al.created_at > NOW() - INTERVAL '30 days'
            ) AS override_count_30d,
            -- Última comunicação
            (
                SELECT MAX(ci.created_at)
                FROM comunicacao_operacional.communication_intents ci
                WHERE ci.recipient_id = cp.patient_id
            ) AS last_communication_at
        FROM comunicacao_operacional.communication_preferences cp
        ORDER BY cp.updated_at DESC;
    """)
    
    # Criar índices na materialized view
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_lgpd_compliance_patient_id 
        ON comunicacao_analitico.lgpd_compliance_view(patient_id);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_lgpd_compliance_consent_status 
        ON comunicacao_analitico.lgpd_compliance_view(consent_status);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_lgpd_compliance_legal_basis 
        ON comunicacao_analitico.lgpd_compliance_view(legal_basis);
    """)
    
    # 3. Criar função para refresh automático (opcional - requer pg_cron)
    op.execute("""
        CREATE OR REPLACE FUNCTION comunicacao_analitico.refresh_materialized_views()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY comunicacao_analitico.team_communication_sla;
            REFRESH MATERIALIZED VIEW CONCURRENTLY comunicacao_analitico.lgpd_compliance_view;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Drop materialized views."""
    
    # Drop função de refresh
    op.execute("DROP FUNCTION IF EXISTS comunicacao_analitico.refresh_materialized_views();")
    
    # Drop materialized views
    op.execute("DROP MATERIALIZED VIEW IF EXISTS comunicacao_analitico.lgpd_compliance_view;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS comunicacao_analitico.team_communication_sla;")

