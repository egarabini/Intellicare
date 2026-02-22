"""create external channels tables

Revision ID: 010_external_channels
Revises: 009_jitsi_tables
Create Date: 2026-02-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '010_external_channels'
down_revision: Union[str, None] = '009_jitsi_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create external channels tables."""
    
    # ── 1. Push Subscriptions ──
    op.create_table(
        'push_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(200), nullable=False),
        sa.Column('subscription_type', sa.String(20), nullable=False),  # "web" | "fcm"
        
        # VAPID
        sa.Column('endpoint', sa.Text, nullable=True),
        sa.Column('p256dh_key', sa.Text, nullable=True),
        sa.Column('auth_key', sa.Text, nullable=True),
        
        # FCM
        sa.Column('fcm_token', sa.String(500), nullable=True),
        
        # Metadata
        sa.Column('device_name', sa.String(200), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('active', sa.Boolean, nullable=False, server_default=sa.text('TRUE')),
        sa.Column('last_used_at', sa.TIMESTAMP(timezone=True), nullable=True),
        
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        
        schema='comunicacao_operacional'
    )
    
    # Índices push_subscriptions
    op.create_index('idx_push_user', 'push_subscriptions', ['user_id'], schema='comunicacao_operacional')
    op.create_index('idx_push_active', 'push_subscriptions', ['active'], schema='comunicacao_operacional')
    
    # ── 2. WhatsApp Sessions ──
    op.create_table(
        'whatsapp_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('phone_number', sa.String(50), nullable=False),
        sa.Column('patient_id', sa.String(200), nullable=True),
        
        # Janela de sessão
        sa.Column('session_started_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('session_expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('active', sa.Boolean, nullable=False, server_default=sa.text('TRUE')),
        
        # Contadores
        sa.Column('messages_sent', sa.Integer, nullable=False, server_default=sa.text('0')),
        sa.Column('messages_received', sa.Integer, nullable=False, server_default=sa.text('0')),
        
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        
        schema='comunicacao_operacional'
    )
    
    # Índices whatsapp_sessions
    op.create_index('idx_wa_session_phone', 'whatsapp_sessions', ['phone_number'], schema='comunicacao_operacional')
    op.create_index('idx_wa_session_active', 'whatsapp_sessions', ['active', 'session_expires_at'], schema='comunicacao_operacional')
    
    # ── 3. External Message Log ──
    op.create_table(
        'external_message_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('channel', sa.String(20), nullable=False),  # "push" | "whatsapp" | "sms" | "email"
        sa.Column('direction', sa.String(10), nullable=False),  # "outbound" | "inbound"
        
        # Destinatário
        sa.Column('recipient_id', sa.String(200), nullable=True),
        sa.Column('recipient_address', sa.String(300), nullable=True),
        
        # Conteúdo
        sa.Column('template_name', sa.String(200), nullable=True),
        sa.Column('message_summary', sa.String(500), nullable=True),
        
        # Provider
        sa.Column('provider_message_id', sa.String(300), nullable=True),
        sa.Column('provider_status', sa.String(50), nullable=True),
        
        # Status IntelliCare
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('error_message', sa.Text, nullable=True),
        
        # Rastreamento
        sa.Column('delivery_result_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Timestamps
        sa.Column('sent_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('read_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('failed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        
        schema='comunicacao_operacional'
    )
    
    # Índices external_message_log
    op.create_index('idx_ext_msg_channel', 'external_message_log', ['channel'], schema='comunicacao_operacional')
    op.create_index('idx_ext_msg_recipient', 'external_message_log', ['recipient_id'], schema='comunicacao_operacional')
    op.create_index('idx_ext_msg_status', 'external_message_log', ['status'], schema='comunicacao_operacional')
    op.create_index('idx_ext_msg_provider', 'external_message_log', ['provider_message_id'], schema='comunicacao_operacional')
    op.create_index('idx_ext_msg_delivery', 'external_message_log', ['delivery_result_id'], schema='comunicacao_operacional')
    op.create_index('idx_ext_msg_created', 'external_message_log', ['created_at'], schema='comunicacao_operacional')
    
    # ── 4. Channel Configs ──
    op.create_table(
        'channel_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('channel', sa.String(20), nullable=False),
        sa.Column('config_key', sa.String(200), nullable=False),
        sa.Column('config_value', sa.Text, nullable=False),
        sa.Column('encrypted', sa.Boolean, nullable=False, server_default=sa.text('FALSE')),
        
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        
        schema='comunicacao_operacional'
    )
    
    # Constraint unique
    op.create_unique_constraint('uq_channel_config_key', 'channel_configs', ['channel', 'config_key'], schema='comunicacao_operacional')


def downgrade() -> None:
    """Drop external channels tables."""
    
    op.drop_table('channel_configs', schema='comunicacao_operacional')
    op.drop_table('external_message_log', schema='comunicacao_operacional')
    op.drop_table('whatsapp_sessions', schema='comunicacao_operacional')
    op.drop_table('push_subscriptions', schema='comunicacao_operacional')

