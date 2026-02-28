"""Criar tabelas Jitsi (jitsi_rooms, jitsi_participants).

Revision ID: 009
Revises: 008
Create Date: 2026-02-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Criar tabelas Jitsi."""
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TABELA: jitsi_rooms
    # ═══════════════════════════════════════════════════════════════════════════
    
    op.create_table(
        'jitsi_rooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('room_name', sa.String(length=255), nullable=False),
        sa.Column('room_type', sa.Enum('TELECONSULTA', 'MULTIDISCIPLINAR', 'GRUPO', 'TREINAMENTO', 'EMERGENCIA', name='roomtype'), nullable=False),
        sa.Column('status', sa.Enum('SCHEDULED', 'ACTIVE', 'COMPLETED', 'CANCELLED', name='roomstatus'), nullable=False),
        
        # Agendamento
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scheduled_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actual_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_end', sa.DateTime(timezone=True), nullable=True),
        
        # Configuração
        sa.Column('max_participants', sa.Integer(), nullable=False),
        sa.Column('enable_recording', sa.Boolean(), nullable=False),
        sa.Column('enable_lobby', sa.Boolean(), nullable=False),
        sa.Column('enable_chat', sa.Boolean(), nullable=False),
        sa.Column('enable_screen_sharing', sa.Boolean(), nullable=False),
        sa.Column('moderator_password', sa.String(length=255), nullable=True),
        
        # Contexto clínico
        sa.Column('patient_id', sa.String(length=255), nullable=True),
        sa.Column('intent_id', sa.String(length=255), nullable=True),
        
        # Metadados
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        schema='comunicacao_operacional'
    )
    
    # Índices para jitsi_rooms
    op.create_index(
        'ix_jitsi_rooms_room_name',
        'jitsi_rooms',
        ['room_name'],
        unique=True,
        schema='comunicacao_operacional'
    )
    op.create_index(
        'ix_jitsi_rooms_room_type',
        'jitsi_rooms',
        ['room_type'],
        schema='comunicacao_operacional'
    )
    op.create_index(
        'ix_jitsi_rooms_status',
        'jitsi_rooms',
        ['status'],
        schema='comunicacao_operacional'
    )
    op.create_index(
        'ix_jitsi_rooms_scheduled_start',
        'jitsi_rooms',
        ['scheduled_start'],
        schema='comunicacao_operacional'
    )
    op.create_index(
        'ix_jitsi_rooms_patient_id',
        'jitsi_rooms',
        ['patient_id'],
        schema='comunicacao_operacional'
    )
    op.create_index(
        'ix_jitsi_rooms_intent_id',
        'jitsi_rooms',
        ['intent_id'],
        schema='comunicacao_operacional'
    )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TABELA: jitsi_participants
    # ═══════════════════════════════════════════════════════════════════════════
    
    op.create_table(
        'jitsi_participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Usuário
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('user_name', sa.String(length=255), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('MODERATOR', 'PRESENTER', 'PARTICIPANT', name='participantrole'), nullable=False),
        
        # Participação
        sa.Column('invited_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        
        # JWT Token
        sa.Column('jwt_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        
        # Metadados
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['room_id'], ['comunicacao_operacional.jitsi_rooms.id'], ondelete='CASCADE'),
        schema='comunicacao_operacional'
    )
    
    # Índices para jitsi_participants
    op.create_index(
        'ix_jitsi_participants_room_id',
        'jitsi_participants',
        ['room_id'],
        schema='comunicacao_operacional'
    )
    op.create_index(
        'ix_jitsi_participants_user_id',
        'jitsi_participants',
        ['user_id'],
        schema='comunicacao_operacional'
    )


def downgrade() -> None:
    """Remover tabelas Jitsi."""
    
    # Remover índices de jitsi_participants
    op.drop_index('ix_jitsi_participants_user_id', table_name='jitsi_participants', schema='comunicacao_operacional')
    op.drop_index('ix_jitsi_participants_room_id', table_name='jitsi_participants', schema='comunicacao_operacional')
    
    # Remover tabela jitsi_participants
    op.drop_table('jitsi_participants', schema='comunicacao_operacional')
    
    # Remover índices de jitsi_rooms
    op.drop_index('ix_jitsi_rooms_intent_id', table_name='jitsi_rooms', schema='comunicacao_operacional')
    op.drop_index('ix_jitsi_rooms_patient_id', table_name='jitsi_rooms', schema='comunicacao_operacional')
    op.drop_index('ix_jitsi_rooms_scheduled_start', table_name='jitsi_rooms', schema='comunicacao_operacional')
    op.drop_index('ix_jitsi_rooms_status', table_name='jitsi_rooms', schema='comunicacao_operacional')
    op.drop_index('ix_jitsi_rooms_room_type', table_name='jitsi_rooms', schema='comunicacao_operacional')
    op.drop_index('ix_jitsi_rooms_room_name', table_name='jitsi_rooms', schema='comunicacao_operacional')
    
    # Remover tabela jitsi_rooms
    op.drop_table('jitsi_rooms', schema='comunicacao_operacional')
    
    # Remover enums
    op.execute('DROP TYPE IF EXISTS comunicacao_operacional.participantrole')
    op.execute('DROP TYPE IF EXISTS comunicacao_operacional.roomstatus')
    op.execute('DROP TYPE IF EXISTS comunicacao_operacional.roomtype')

