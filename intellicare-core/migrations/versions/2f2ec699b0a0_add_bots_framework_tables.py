"""Add bots framework tables

Revision ID: 2f2ec699b0a0
Revises: 004
Create Date: 2026-03-04 21:40:25.270054

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f2ec699b0a0'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # bots table
    op.create_table(
        'bots',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('code_version', sa.Integer(), nullable=True),
        sa.Column('runtime', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('run_as_user', sa.Boolean(), nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bots_tenant_id'), 'bots', ['tenant_id'], unique=False)

    # bot_secrets table
    op.create_table(
        'bot_secrets',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('bot_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('value_encrypted', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'bot_id', 'name', name='uix_tenant_bot_secret_name')
    )
    op.create_index(op.f('ix_bot_secrets_tenant_id'), 'bot_secrets', ['tenant_id'], unique=False)

    # bot_executions table
    op.create_table(
        'bot_executions',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bot_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('subscription_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('input_resource_type', sa.String(), nullable=True),
        sa.Column('input_resource_id', sa.String(), nullable=True),
        sa.Column('interaction', sa.String(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('log_output', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bot_executions_bot_id'), 'bot_executions', ['bot_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_bot_executions_bot_id'), table_name='bot_executions')
    op.drop_table('bot_executions')
    
    op.drop_index(op.f('ix_bot_secrets_tenant_id'), table_name='bot_secrets')
    op.drop_table('bot_secrets')
    
    op.drop_index(op.f('ix_bots_tenant_id'), table_name='bots')
    op.drop_table('bots')

