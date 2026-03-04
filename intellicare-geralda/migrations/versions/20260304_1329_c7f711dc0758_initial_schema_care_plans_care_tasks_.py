"""initial schema - care_plans, care_tasks, reminders, educational_materials

Revision ID: c7f711dc0758
Revises: 
Create Date: 2026-03-04 13:29:51.441342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7f711dc0758'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # care_plans
    op.create_table(
        'care_plans',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('patient_id', sa.String(200), nullable=False),
        sa.Column('patient_name', sa.String(200), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=True),
        sa.Column('goals', sa.JSON(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deactivation_reason', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_care_plans_patient_id', 'care_plans', ['patient_id'])
    op.create_index('ix_care_plans_active', 'care_plans', ['active'])

    # care_tasks
    op.create_table(
        'care_tasks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('plan_id', sa.Uuid(), nullable=False),
        sa.Column('patient_id', sa.String(200), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('due_time', sa.String(10), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by', sa.String(200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recurrence_rule', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_care_tasks_plan_id', 'care_tasks', ['plan_id'])
    op.create_index('idx_care_tasks_patient_id', 'care_tasks', ['patient_id'])
    op.create_index('idx_care_tasks_status', 'care_tasks', ['status'])

    # reminders
    op.create_table(
        'reminders',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('plan_id', sa.Uuid(), nullable=False),
        sa.Column('patient_id', sa.String(200), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('channel', sa.String(50), nullable=False, server_default='whatsapp'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_reminders_plan_id', 'reminders', ['plan_id'])
    op.create_index('idx_reminders_patient_id', 'reminders', ['patient_id'])
    op.create_index('idx_reminders_status', 'reminders', ['status'])

    # educational_materials
    op.create_table(
        'educational_materials',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('plan_id', sa.Uuid(), nullable=False),
        sa.Column('patient_id', sa.String(200), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('condition_codes', sa.JSON(), nullable=True),
        sa.Column('language', sa.String(10), nullable=False, server_default='pt-BR'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_educational_materials_plan_id', 'educational_materials', ['plan_id'])
    op.create_index('idx_educational_materials_patient_id', 'educational_materials', ['patient_id'])


def downgrade() -> None:
    op.drop_table('educational_materials')
    op.drop_table('reminders')
    op.drop_table('care_tasks')
    op.drop_table('care_plans')
