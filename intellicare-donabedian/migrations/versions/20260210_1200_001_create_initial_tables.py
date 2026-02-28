"""create_initial_tables

Revision ID: 001
Revises: 
Create Date: 2026-02-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schema for intellicare-donabedian module
    op.execute("CREATE SCHEMA IF NOT EXISTS intellicare_donabedian")

    # Create pillars table
    op.create_table(
        'pillars',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False, comment='Pillar name (efficacy, effectiveness, efficiency, optimality, acceptability, legitimacy, equity)'),
        sa.Column('description', sa.String(length=500), nullable=False, comment='Pillar description in Portuguese'),
        sa.Column('display_order', sa.Integer(), nullable=False, comment='Display order (1-7)'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        schema='intellicare_donabedian'
    )

    # Create indicators table
    op.create_table(
        'indicators',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False, comment='Pillar name (efficacy, effectiveness, efficiency, optimality, acceptability, legitimacy, equity)'),
        sa.Column('description', sa.String(length=500), nullable=False, comment='Pillar description in Portuguese'),
        sa.Column('display_order', sa.Integer(), nullable=False, comment='Display order (1-7)'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create indicators table
    op.create_table(
        'indicators',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False, comment='Indicator name'),
        sa.Column('description', sa.String(length=1000), nullable=False, comment='Detailed description of the indicator'),
        sa.Column('formula', sa.String(length=500), nullable=False, comment="Calculation formula (e.g., 'numerator / denominator * 100')"),
        sa.Column('unit', sa.String(length=50), nullable=False, comment='Unit of measurement (%, days, count, etc.)'),
        sa.Column('target_value', sa.Float(), nullable=False, comment='Target value to be achieved'),
        sa.Column('target_operator', sa.String(length=10), nullable=False, comment='Comparison operator for target (>=, <=, ==)'),
        sa.Column('triad_dimension', sa.String(length=20), nullable=False, comment='Donabedian triad dimension (structure, process, outcome)'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='Creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='Last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        schema='intellicare_donabedian'
    )
    
    # Create indicator_pillars table (N:N with weight)
    op.create_table(
        'indicator_pillars',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('indicator_id', sa.Integer(), nullable=False, comment='Reference to indicator'),
        sa.Column('pillar_id', sa.Integer(), nullable=False, comment='Reference to pillar'),
        sa.Column('weight', sa.Float(), nullable=False, comment='Weight/importance of this indicator in this pillar (0.0-1.0)'),
        sa.ForeignKeyConstraint(['indicator_id'], ['intellicare_donabedian.indicators.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pillar_id'], ['intellicare_donabedian.pillars.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='intellicare_donabedian'
    )
    
    # Create measurements table
    op.create_table(
        'measurements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('indicator_id', sa.Integer(), nullable=False, comment='Reference to indicator'),
        sa.Column('value', sa.Float(), nullable=False, comment='Measured value'),
        sa.Column('period_start', sa.Date(), nullable=False, comment='Start date of measurement period'),
        sa.Column('period_end', sa.Date(), nullable=False, comment='End date of measurement period'),
        sa.Column('period_type', sa.String(length=20), nullable=False, comment='Type of period (daily, weekly, monthly, quarterly, yearly)'),
        sa.Column('status', sa.String(length=10), nullable=False, comment='Status: green (met), yellow (close), red (not met)'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='Creation timestamp'),
        sa.ForeignKeyConstraint(['indicator_id'], ['intellicare_donabedian.indicators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='intellicare_donabedian'
    )
    
    # Create indexes for better query performance
    op.create_index('ix_indicators_triad_dimension', 'indicators', ['triad_dimension'], schema='intellicare_donabedian')
    op.create_index('ix_indicator_pillars_indicator_id', 'indicator_pillars', ['indicator_id'], schema='intellicare_donabedian')
    op.create_index('ix_indicator_pillars_pillar_id', 'indicator_pillars', ['pillar_id'], schema='intellicare_donabedian')
    op.create_index('ix_measurements_indicator_id', 'measurements', ['indicator_id'], schema='intellicare_donabedian')
    op.create_index('ix_measurements_period_start', 'measurements', ['period_start'], schema='intellicare_donabedian')
    op.create_index('ix_measurements_status', 'measurements', ['status'], schema='intellicare_donabedian')


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_measurements_status', table_name='measurements', schema='intellicare_donabedian')
    op.drop_index('ix_measurements_period_start', table_name='measurements', schema='intellicare_donabedian')
    op.drop_index('ix_measurements_indicator_id', table_name='measurements', schema='intellicare_donabedian')
    op.drop_index('ix_indicator_pillars_pillar_id', table_name='indicator_pillars', schema='intellicare_donabedian')
    op.drop_index('ix_indicator_pillars_indicator_id', table_name='indicator_pillars', schema='intellicare_donabedian')
    op.drop_index('ix_indicators_triad_dimension', table_name='indicators', schema='intellicare_donabedian')

    # Drop tables (in reverse order due to foreign keys)
    op.drop_table('measurements', schema='intellicare_donabedian')
    op.drop_table('indicator_pillars', schema='intellicare_donabedian')
    op.drop_table('indicators', schema='intellicare_donabedian')
    op.drop_table('pillars', schema='intellicare_donabedian')

    # Drop schema (only if empty)
    op.execute("DROP SCHEMA IF EXISTS intellicare_donabedian CASCADE")

