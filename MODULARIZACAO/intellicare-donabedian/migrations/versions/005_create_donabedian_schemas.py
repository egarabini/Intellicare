"""
Migration for FASE 2: Create donabedian module operational/analytical schemas

This migration creates:
1. donabedian_operacional schema (transactional)
2. donabedian_analitico schema (BI/analytics)
3. Example tables for Pilares (Donabedian framework pillars)
4. RLS policies
5. Indexes for performance
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Migration metadata
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create donabedian schemas and example tables"""
    
    # ========================================================================
    # Create Schemas
    # ========================================================================
    op.execute("CREATE SCHEMA IF NOT EXISTS donabedian_operacional")
    op.execute("CREATE SCHEMA IF NOT EXISTS donabedian_analitico")
    
    # Grant permissions
    op.execute("GRANT USAGE, CREATE ON SCHEMA donabedian_operacional TO operacional_user")
    op.execute("GRANT USAGE, CREATE ON SCHEMA donabedian_operacional TO intellicare_admin")
    op.execute("GRANT USAGE ON SCHEMA donabedian_analitico TO analytics_user")
    op.execute("GRANT USAGE ON SCHEMA donabedian_analitico TO intellicare_admin")
    
    # ========================================================================
    # Create Operational Table: Pilares (Donabedian Framework Pillars)
    # ========================================================================
    op.create_table(
        'pilares',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('descricao', sa.Text),
        sa.Column('tipo', sa.String(50), nullable=False),  # ESTRUTURA, PROCESSO, RESULTADO
        sa.Column('ativo', sa.Boolean(), default=True),
        
        # Audit metadata
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        
        # Soft delete
        sa.Column('valid_to', sa.DateTime(timezone=True)),
        sa.CheckConstraint('valid_to IS NULL OR valid_to > created_at', name='ck_pilar_valid_to'),
        
        # Optimistic locking
        sa.Column('rowversion', sa.Integer(), default=1),
        
        schema='donabedian_operacional'
    )
    
    # Create indices for operational table
    op.create_index(
        'idx_donabedian_pilares_tipo',
        'pilares',
        ['tipo'],
        schema='donabedian_operacional',
        where=sa.text('valid_to IS NULL')
    )
    op.create_index(
        'idx_donabedian_pilares_ativo',
        'pilares',
        ['ativo'],
        schema='donabedian_operacional',
        where=sa.text('valid_to IS NULL')
    )
    op.create_index(
        'idx_donabedian_pilares_created_at',
        'pilares',
        ['created_at'],
        schema='donabedian_operacional'
    )
    
    # ========================================================================
    # Create Analytics Table: Pilares (denormalized)
    # ========================================================================
    op.create_table(
        'pilares',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('nome', sa.String(255)),
        sa.Column('descricao', sa.Text),
        sa.Column('tipo', sa.String(50)),
        sa.Column('ativo', sa.Boolean()),
        
        # Audit metadata
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        
        # Soft delete
        sa.Column('valid_to', sa.DateTime(timezone=True)),
        
        # Optimistic locking
        sa.Column('rowversion', sa.Integer()),
        
        # Consolidation metadata
        sa.Column('consolidated_at', sa.DateTime(timezone=True)),
        sa.Column('consolidation_source', sa.String(255)),
        
        schema='donabedian_analitico'
    )
    
    # Create indices for analytics table
    op.create_index(
        'idx_donabedian_analitico_tipo',
        'pilares',
        ['tipo'],
        schema='donabedian_analitico'
    )
    op.create_index(
        'idx_donabedian_analitico_ativo',
        'pilares',
        ['ativo'],
        schema='donabedian_analitico'
    )
    op.create_index(
        'idx_donabedian_analitico_created_at',
        'pilares',
        ['created_at'],
        schema='donabedian_analitico'
    )
    
    # ========================================================================
    # Enable RLS and Create Policies
    # ========================================================================
    op.execute("ALTER TABLE donabedian_operacional.pilares ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE donabedian_analitico.pilares ENABLE ROW LEVEL SECURITY")
    
    # Operational table policies
    op.execute("""
        CREATE POLICY operacional_users_can_access 
        ON donabedian_operacional.pilares
        FOR ALL
        USING (current_user = 'operacional_user' OR current_user = 'intellicare_admin')
    """)
    
    # Analytics table policies
    op.execute("""
        CREATE POLICY analytics_users_read_only 
        ON donabedian_analitico.pilares
        FOR SELECT
        USING (current_user = 'analytics_user' OR current_user = 'intellicare_admin')
    """)
    
    op.execute("""
        CREATE POLICY analytics_users_deny_write 
        ON donabedian_analitico.pilares
        FOR INSERT
        WITH CHECK (false)
    """)
    
    op.execute("""
        CREATE POLICY analytics_users_deny_update 
        ON donabedian_analitico.pilares
        FOR UPDATE
        WITH CHECK (false)
    """)
    
    op.execute("""
        CREATE POLICY analytics_users_deny_delete 
        ON donabedian_analitico.pilares
        FOR DELETE
        USING (false)
    """)
    
    # ========================================================================
    # Grant Permissions
    # ========================================================================
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON donabedian_operacional.pilares TO operacional_user")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON donabedian_operacional.pilares TO intellicare_admin")
    op.execute("GRANT SELECT ON donabedian_analitico.pilares TO analytics_user")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON donabedian_analitico.pilares TO intellicare_admin")


def downgrade() -> None:
    """Revert donabedian schemas and tables"""
    
    # Drop schemas (CASCADE to drop all tables)
    op.execute("DROP SCHEMA IF EXISTS donabedian_analitico CASCADE")
    op.execute("DROP SCHEMA IF EXISTS donabedian_operacional CASCADE")
