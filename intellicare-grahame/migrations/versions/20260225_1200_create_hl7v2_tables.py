"""Create HL7v2 API Keys and Audit Log tables

Revision ID: 20260225_1200
Revises: 
Create Date: 2026-02-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260225_1200'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create hl7v2_api_keys table
    op.create_table(
        'hl7v2_api_keys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('api_key', sa.String(length=64), nullable=False, comment='API Key (UUID format) - usado no header X-API-Key'),
        sa.Column('system_name', sa.String(length=255), nullable=False, comment="Nome do sistema/hospital (ex: 'Hospital São Paulo - Tasy')"),
        sa.Column('system_identifier', sa.String(length=100), nullable=False, comment="Identificador único do sistema (ex: 'HSP-TASY')"),
        sa.Column('description', sa.Text(), nullable=True, comment='Descrição adicional do sistema'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Se False, a API Key está desabilitada'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='Data de expiração (None = nunca expira)'),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False, server_default='60', comment='Máximo de requisições por minuto (0 = sem limite)'),
        sa.Column('allowed_ips', sa.Text(), nullable=True, comment="IPs permitidos (separados por vírgula, ex: '192.168.1.1,10.0.0.1')"),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), comment='Data de criação'),
        sa.Column('created_by', sa.String(length=255), nullable=True, comment='Usuário que criou a API Key'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True, comment='Última vez que a API Key foi usada'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0', comment='Número total de requisições feitas com esta API Key'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Notas administrativas'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_key')
    )
    op.create_index(op.f('ix_hl7v2_api_keys_api_key'), 'hl7v2_api_keys', ['api_key'], unique=False)
    
    # Create hl7v2_audit_logs table
    op.create_table(
        'hl7v2_audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=True, comment='API Key usada (NULL se autenticação falhou)'),
        sa.Column('request_ip', sa.String(length=45), nullable=False, comment='IP de origem da requisição'),
        sa.Column('request_user_agent', sa.String(length=500), nullable=True, comment='User-Agent do cliente'),
        sa.Column('message_control_id', sa.String(length=100), nullable=True, comment='MSH-10 (Message Control ID)'),
        sa.Column('message_type', sa.String(length=50), nullable=True, comment='MSH-9 (Message Type, ex: ADT^A04)'),
        sa.Column('sending_application', sa.String(length=255), nullable=True, comment='MSH-3 (Sending Application)'),
        sa.Column('sending_facility', sa.String(length=255), nullable=True, comment='MSH-4 (Sending Facility)'),
        sa.Column('raw_message', sa.Text(), nullable=False, comment='Mensagem HL7v2 completa (raw)'),
        sa.Column('message_size_bytes', sa.Integer(), nullable=False, comment='Tamanho da mensagem em bytes'),
        sa.Column('success', sa.Boolean(), nullable=False, comment='True se processamento foi bem-sucedido'),
        sa.Column('http_status_code', sa.Integer(), nullable=False, comment='HTTP status code da resposta'),
        sa.Column('ack_code', sa.String(length=10), nullable=True, comment='ACK code (AA, AR, AE)'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Mensagem de erro (se houver)'),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True, comment='Tempo de processamento em milissegundos'),
        sa.Column('patient_id', sa.String(length=255), nullable=True, comment='ID do Patient FHIR criado'),
        sa.Column('encounter_id', sa.String(length=255), nullable=True, comment='ID do Encounter FHIR criado'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), comment='Data/hora da requisição'),
        sa.ForeignKeyConstraint(['api_key_id'], ['hl7v2_api_keys.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hl7v2_audit_logs_api_key_id'), 'hl7v2_audit_logs', ['api_key_id'], unique=False)
    op.create_index(op.f('ix_hl7v2_audit_logs_created_at'), 'hl7v2_audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_hl7v2_audit_logs_encounter_id'), 'hl7v2_audit_logs', ['encounter_id'], unique=False)
    op.create_index(op.f('ix_hl7v2_audit_logs_message_control_id'), 'hl7v2_audit_logs', ['message_control_id'], unique=False)
    op.create_index(op.f('ix_hl7v2_audit_logs_message_type'), 'hl7v2_audit_logs', ['message_type'], unique=False)
    op.create_index(op.f('ix_hl7v2_audit_logs_patient_id'), 'hl7v2_audit_logs', ['patient_id'], unique=False)
    op.create_index(op.f('ix_hl7v2_audit_logs_request_ip'), 'hl7v2_audit_logs', ['request_ip'], unique=False)
    op.create_index(op.f('ix_hl7v2_audit_logs_success'), 'hl7v2_audit_logs', ['success'], unique=False)


def downgrade() -> None:
    # Drop hl7v2_audit_logs table
    op.drop_index(op.f('ix_hl7v2_audit_logs_success'), table_name='hl7v2_audit_logs')
    op.drop_index(op.f('ix_hl7v2_audit_logs_request_ip'), table_name='hl7v2_audit_logs')
    op.drop_index(op.f('ix_hl7v2_audit_logs_patient_id'), table_name='hl7v2_audit_logs')
    op.drop_index(op.f('ix_hl7v2_audit_logs_message_type'), table_name='hl7v2_audit_logs')
    op.drop_index(op.f('ix_hl7v2_audit_logs_message_control_id'), table_name='hl7v2_audit_logs')
    op.drop_index(op.f('ix_hl7v2_audit_logs_encounter_id'), table_name='hl7v2_audit_logs')
    op.drop_index(op.f('ix_hl7v2_audit_logs_created_at'), table_name='hl7v2_audit_logs')
    op.drop_index(op.f('ix_hl7v2_audit_logs_api_key_id'), table_name='hl7v2_audit_logs')
    op.drop_table('hl7v2_audit_logs')
    
    # Drop hl7v2_api_keys table
    op.drop_index(op.f('ix_hl7v2_api_keys_api_key'), table_name='hl7v2_api_keys')
    op.drop_table('hl7v2_api_keys')

