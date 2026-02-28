"""Create Oswaldo tables in oswaldo schema.

Revision ID: 001_create_oswaldo_tables
Revises: 
Create Date: 2026-02-12 23:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_create_oswaldo_tables'
down_revision = None
branch_labels = None
depends_on = None

# Schema name
SCHEMA = 'oswaldo'


def upgrade() -> None:
    """Create oswaldo tables in oswaldo schema."""
    
    # Ensure schema exists
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    
    # Create condicao_cronica table
    op.create_table(
        'condicao_cronica',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paciente_cpf_hash', sa.String(64), nullable=False),
        sa.Column('cid10', sa.String(10), nullable=False),
        sa.Column('data_diagnostico', sa.Date(), nullable=False),
        sa.Column('medico_diagnosticador', sa.String(100), nullable=True),
        sa.Column('confirmacao_exames', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDENTE_VALIDACAO'),
        sa.Column('gravidade_inicial', sa.String(20), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        schema=SCHEMA
    )
    op.create_index('ix_condicao_cronica_paciente_cpf_hash', 'condicao_cronica', ['paciente_cpf_hash'], unique=False, schema=SCHEMA)
    op.create_index('ix_condicao_cronica_cid10', 'condicao_cronica', ['cid10'], unique=False, schema=SCHEMA)
    op.create_index('ix_condicao_cronica_status', 'condicao_cronica', ['status'], unique=False, schema=SCHEMA)
    op.create_index('ix_condicao_cronica_criado_em', 'condicao_cronica', ['criado_em'], unique=False, schema=SCHEMA)
    op.create_index('idx_paciente_status', 'condicao_cronica', ['paciente_cpf_hash', 'status'], unique=False, schema=SCHEMA)
    op.create_index('idx_cid10_data', 'condicao_cronica', ['cid10', 'data_diagnostico'], unique=False, schema=SCHEMA)
    
    # Create estadiamento table
    op.create_table(
        'estadiamento',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condicao_cronica_id', sa.Integer(), nullable=False),
        sa.Column('sistema_classificacao', sa.String(50), nullable=False),
        sa.Column('estagio', sa.String(20), nullable=False),
        sa.Column('data_classificacao', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('criterios', sa.JSON(), nullable=True),
        sa.Column('exames_suporte', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['condicao_cronica_id'], [f'{SCHEMA}.condicao_cronica.id']),
        sa.PrimaryKeyConstraint('id'),
        schema=SCHEMA
    )
    op.create_index('ix_estadiamento_condicao_cronica_id', 'estadiamento', ['condicao_cronica_id'], unique=False, schema=SCHEMA)
    op.create_index('idx_condicao_data', 'estadiamento', ['condicao_cronica_id', 'data_classificacao'], unique=False, schema=SCHEMA)
    
    # Create plano_cuidado table
    op.create_table(
        'plano_cuidado',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condicao_cronica_id', sa.Integer(), nullable=False),
        sa.Column('data_inicio', sa.Date(), nullable=False),
        sa.Column('data_revisao', sa.Date(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='ATIVO'),
        sa.Column('objetivos', sa.JSON(), nullable=False),
        sa.Column('intervencoes', sa.JSON(), nullable=False),
        sa.Column('medicamentos', sa.JSON(), nullable=False),
        sa.Column('educacao_saude', sa.JSON(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['condicao_cronica_id'], [f'{SCHEMA}.condicao_cronica.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('condicao_cronica_id'),
        schema=SCHEMA
    )
    op.create_index('ix_plano_cuidado_condicao_cronica_id', 'plano_cuidado', ['condicao_cronica_id'], unique=False, schema=SCHEMA)
    
    # Create acompanhamento table
    op.create_table(
        'acompanhamento',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paciente_cpf_hash', sa.String(64), nullable=False),
        sa.Column('condicao_cronica_id', sa.Integer(), nullable=False),
        sa.Column('data_acompanhamento', sa.DateTime(), nullable=False),
        sa.Column('medico_id', sa.String(50), nullable=False),
        sa.Column('local_consulta', sa.String(100), nullable=True),
        sa.Column('pressao_arterial', sa.String(20), nullable=True),
        sa.Column('peso_kg', sa.Float(), nullable=True),
        sa.Column('glicemia', sa.Float(), nullable=True),
        sa.Column('temperatura', sa.Float(), nullable=True),
        sa.Column('adesao_medicamentos', sa.String(20), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('medicamentos_vigentes', sa.JSON(), nullable=True),
        sa.Column('proxima_consulta', sa.Date(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['condicao_cronica_id'], [f'{SCHEMA}.condicao_cronica.id']),
        sa.PrimaryKeyConstraint('id'),
        schema=SCHEMA
    )
    op.create_index('ix_acompanhamento_paciente_cpf_hash', 'acompanhamento', ['paciente_cpf_hash'], unique=False, schema=SCHEMA)
    op.create_index('ix_acompanhamento_condicao_cronica_id', 'acompanhamento', ['condicao_cronica_id'], unique=False, schema=SCHEMA)
    op.create_index('ix_acompanhamento_data_acompanhamento', 'acompanhamento', ['data_acompanhamento'], unique=False, schema=SCHEMA)
    op.create_index('idx_paciente_data', 'acompanhamento', ['paciente_cpf_hash', 'data_acompanhamento'], unique=False, schema=SCHEMA)
    op.create_index('idx_condicao_data_acomp', 'acompanhamento', ['condicao_cronica_id', 'data_acompanhamento'], unique=False, schema=SCHEMA)
    
    # Create alerta table
    op.create_table(
        'alerta',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paciente_cpf_hash', sa.String(64), nullable=False),
        sa.Column('condicao_cronica_id', sa.Integer(), nullable=False),
        sa.Column('tipo_alerta', sa.String(50), nullable=False),
        sa.Column('severidade', sa.String(20), nullable=False),
        sa.Column('descricao', sa.String(256), nullable=False),
        sa.Column('dados_alerta', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='NOVO'),
        sa.Column('data_criacao', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('data_resolvido', sa.DateTime(), nullable=True),
        sa.Column('medico_atribuido', sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(['condicao_cronica_id'], [f'{SCHEMA}.condicao_cronica.id']),
        sa.PrimaryKeyConstraint('id'),
        schema=SCHEMA
    )
    op.create_index('ix_alerta_paciente_cpf_hash', 'alerta', ['paciente_cpf_hash'], unique=False, schema=SCHEMA)
    op.create_index('ix_alerta_condicao_cronica_id', 'alerta', ['condicao_cronica_id'], unique=False, schema=SCHEMA)
    op.create_index('ix_alerta_tipo_alerta', 'alerta', ['tipo_alerta'], unique=False, schema=SCHEMA)
    op.create_index('ix_alerta_severidade', 'alerta', ['severidade'], unique=False, schema=SCHEMA)
    op.create_index('ix_alerta_status', 'alerta', ['status'], unique=False, schema=SCHEMA)
    op.create_index('ix_alerta_data_criacao', 'alerta', ['data_criacao'], unique=False, schema=SCHEMA)
    op.create_index('idx_paciente_severidade', 'alerta', ['paciente_cpf_hash', 'severidade'], unique=False, schema=SCHEMA)
    op.create_index('idx_status_data', 'alerta', ['status', 'data_criacao'], unique=False, schema=SCHEMA)


def downgrade() -> None:
    """Drop oswaldo tables from oswaldo schema."""
    op.drop_index('idx_status_data', table_name='alerta', schema=SCHEMA)
    op.drop_index('idx_paciente_severidade', table_name='alerta', schema=SCHEMA)
    op.drop_index('ix_alerta_data_criacao', table_name='alerta', schema=SCHEMA)
    op.drop_index('ix_alerta_status', table_name='alerta', schema=SCHEMA)
    op.drop_index('ix_alerta_severidade', table_name='alerta', schema=SCHEMA)
    op.drop_index('ix_alerta_tipo_alerta', table_name='alerta', schema=SCHEMA)
    op.drop_index('ix_alerta_condicao_cronica_id', table_name='alerta', schema=SCHEMA)
    op.drop_index('ix_alerta_paciente_cpf_hash', table_name='alerta', schema=SCHEMA)
    op.drop_table('alerta', schema=SCHEMA)
    
    op.drop_index('idx_condicao_data_acomp', table_name='acompanhamento', schema=SCHEMA)
    op.drop_index('idx_paciente_data', table_name='acompanhamento', schema=SCHEMA)
    op.drop_index('ix_acompanhamento_data_acompanhamento', table_name='acompanhamento', schema=SCHEMA)
    op.drop_index('ix_acompanhamento_condicao_cronica_id', table_name='acompanhamento', schema=SCHEMA)
    op.drop_index('ix_acompanhamento_paciente_cpf_hash', table_name='acompanhamento', schema=SCHEMA)
    op.drop_table('acompanhamento', schema=SCHEMA)
    
    op.drop_index('ix_plano_cuidado_condicao_cronica_id', table_name='plano_cuidado', schema=SCHEMA)
    op.drop_table('plano_cuidado', schema=SCHEMA)
    
    op.drop_index('idx_condicao_data', table_name='estadiamento', schema=SCHEMA)
    op.drop_index('ix_estadiamento_condicao_cronica_id', table_name='estadiamento', schema=SCHEMA)
    op.drop_table('estadiamento', schema=SCHEMA)
    
    op.drop_index('idx_cid10_data', table_name='condicao_cronica', schema=SCHEMA)
    op.drop_index('idx_paciente_status', table_name='condicao_cronica', schema=SCHEMA)
    op.drop_index('ix_condicao_cronica_criado_em', table_name='condicao_cronica', schema=SCHEMA)
    op.drop_index('ix_condicao_cronica_status', table_name='condicao_cronica', schema=SCHEMA)
    op.drop_index('ix_condicao_cronica_cid10', table_name='condicao_cronica', schema=SCHEMA)
    op.drop_index('ix_condicao_cronica_paciente_cpf_hash', table_name='condicao_cronica', schema=SCHEMA)
    op.drop_table('condicao_cronica', schema=SCHEMA)

