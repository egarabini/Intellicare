"""
Florence Database Migrations
=============================

Database schema initialization para Florence.
Usa Alembic para versionamento de schema.

Migrations criadas para:
1. PacienteAnonimizado (anonimização LGPD)
2. PacienteHashMapping (mapeamento CPF hash)
3. AcessoHashMapping (auditoria de acessos)
4. Exame (dados de exames)
"""

import os
from alembic import op
import sqlalchemy as sa


def upgrade():
    """
    Migração UP: Criar tabelas iniciais.
    
    Executar com: alembic upgrade head
    """
    
    # ========================================================================
    # Tabela 1: paciente_anonimizado
    # ========================================================================
    op.create_table(
        'paciente_anonimizado',
        
        sa.Column('paciente_id_hash', sa.String(64), primary_key=True, nullable=False),
        sa.Column('nome_truncado', sa.String(50), nullable=True),  # "João S."
        sa.Column('data_nascimento_mes_ano', sa.String(10), nullable=True),  # "01/1980"
        sa.Column('sexo', sa.String(1), nullable=True),  # M, F
        sa.Column('altura_cm', sa.Float, nullable=True),
        sa.Column('peso_kg', sa.Float, nullable=True),
        
        sa.Column('criado_em', sa.DateTime, server_default=sa.func.now()),
        sa.Column('atualizado_em', sa.DateTime, onupdate=sa.func.now()),
        
        # Index para lookup rápido
        sa.Index('ix_paciente_anonimizado_hash', 'paciente_id_hash'),
        sa.Index('ix_paciente_anonimizado_data_nasc', 'data_nascimento_mes_ano'),
    )
    
    # ========================================================================
    # Tabela 2: paciente_hash_mapping
    # ========================================================================
    op.create_table(
        'paciente_hash_mapping',
        
        sa.Column('cpf_hash', sa.String(64), primary_key=True, nullable=False),
        sa.Column('cpf_aes256_encrypted', sa.String(256), nullable=False),  # Fernet
        sa.Column('paciente_id_hash', sa.String(64), nullable=False),
        
        sa.Column('acessado_contador', sa.Integer, default=0),
        sa.Column('acessado_em', sa.DateTime, nullable=True),
        sa.Column('is_deleted', sa.Boolean, default=False),  # Soft delete
        sa.Column('deletado_em', sa.DateTime, nullable=True),
        
        sa.Column('criado_em', sa.DateTime, server_default=sa.func.now()),
        sa.Column('atualizado_em', sa.DateTime, onupdate=sa.func.now()),
        
        # Índices
        sa.Index('ix_paciente_hash_mapping_cpf', 'cpf_hash'),
        sa.Index('ix_paciente_hash_mapping_paciente_id', 'paciente_id_hash'),
        sa.Index('ix_paciente_hash_mapping_deleted', 'is_deleted'),
        
        # Constraint: não ter duplicatas
        sa.UniqueConstraint('cpf_hash', name='uq_cpf_hash'),
    )
    
    # ========================================================================
    # Tabela 3: acesso_hash_mapping (Auditoria LGPD)
    # ========================================================================
    op.create_table(
        'acesso_hash_mapping',
        
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('cpf_hash', sa.String(64), nullable=False),
        
        sa.Column('usuario_id', sa.String(50), nullable=False),
        sa.Column('usuario_ip', sa.String(45), nullable=True),  # IPv4 ou IPv6
        sa.Column('usuario_user_agent', sa.String(512), nullable=True),
        
        sa.Column('accessed_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('motivo_acesso', sa.String(100), nullable=False),  # VALIDACAO, VISUALIZACAO, EXPORTACAO
        sa.Column('sucesso', sa.Boolean, default=True),
        sa.Column('erro_msg', sa.String(256), nullable=True),
        
        # Índices para auditoria rápida
        sa.Index('ix_acesso_hash_mapping_cpf', 'cpf_hash'),
        sa.Index('ix_acesso_hash_mapping_usuario', 'usuario_id'),
        sa.Index('ix_acesso_hash_mapping_data', 'accessed_at'),
        sa.Index('ix_acesso_hash_mapping_motivo', 'motivo_acesso'),
        sa.Index('ix_acesso_hash_mapping_sucesso', 'sucesso'),
        
        # Constraint: FK para paciente_hash_mapping
        sa.ForeignKeyConstraint(['cpf_hash'], ['paciente_hash_mapping.cpf_hash']),
    )
    
    # ========================================================================
    # Tabela 4: exame
    # ========================================================================
    op.create_table(
        'exame',
        
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),  # UUID
        sa.Column('paciente_id_hash', sa.String(64), nullable=False),
        
        sa.Column('tipo_exame', sa.String(50), nullable=False),  # hemograma, lipidograma, etc
        sa.Column('data_exame', sa.DateTime, nullable=False),
        sa.Column('resultado_json', sa.JSON, nullable=True),  # Armazenar resultado completo
        
        sa.Column('validado', sa.Boolean, nullable=True),  # Resultado da validação
        sa.Column('validacao_msg', sa.String(256), nullable=True),  # Mensagem de validação
        
        sa.Column('criado_em', sa.DateTime, server_default=sa.func.now()),
        sa.Column('atualizado_em', sa.DateTime, onupdate=sa.func.now()),
        
        # Índices
        sa.Index('ix_exame_paciente', 'paciente_id_hash'),
        sa.Index('ix_exame_tipo', 'tipo_exame'),
        sa.Index('ix_exame_data', 'data_exame'),
        sa.Index('ix_exame_validado', 'validado'),
        
        # Constraint: FK para paciente_anonimizado
        sa.ForeignKeyConstraint(['paciente_id_hash'], ['paciente_anonimizado.paciente_id_hash']),
    )
    
    # ========================================================================
    # Criar views úteis para queries comuns
    # ========================================================================
    
    # View: Auditoria última 30 dias
    op.execute("""
    CREATE VIEW vw_auditoria_30dias AS
    SELECT 
        a.accessed_at,
        a.usuario_id,
        COUNT(*) as acessos
    FROM acesso_hash_mapping a
    WHERE a.accessed_at > NOW() - INTERVAL '30 days'
    GROUP BY a.accessed_at, a.usuario_id
    ORDER BY a.accessed_at DESC;
    """)
    
    # View: Taxa de sucesso por tipo
    op.execute("""
    CREATE VIEW vw_taxa_sucesso AS
    SELECT 
        e.tipo_exame,
        COUNT(*) as total,
        SUM(CASE WHEN e.validado = true THEN 1 ELSE 0 END) as sucesso,
        ROUND(100.0 * SUM(CASE WHEN e.validado = true THEN 1 ELSE 0 END) / COUNT(*), 2) as taxa_sucesso_pct
    FROM exame e
    GROUP BY e.tipo_exame;
    """)
    
    print("✅ Migration UP: Tabelas Florence criadas com sucesso")


def downgrade():
    """
    Migração DOWN: Remover tabelas.
    
    Executar com: alembic downgrade -1
    (ou alembic downgrade base para remover tudo)
    """
    
    # Remover views
    op.execute("DROP VIEW IF EXISTS vw_taxa_sucesso;")
    op.execute("DROP VIEW IF EXISTS vw_auditoria_30dias;")
    
    # Remover tabelas (ordem importa - respeitar FKs)
    op.drop_table('exame')
    op.drop_table('acesso_hash_mapping')
    op.drop_table('paciente_hash_mapping')
    op.drop_table('paciente_anonimizado')
    
    print("✅ Migration DOWN: Tabelas Florence removidas")


# ============================================================================
# Script para executar migrations (run_migrations.py)
# ============================================================================

"""
# Uso:
# 1. Iniciar alembic (uma vez):
#    cd intellicare-florence
#    alembic init alembic
#
# 2. Configurar alembic.ini com DB URL:
#    sqlalchemy.url = driver://user:password@localhost/dbname
#
# 3. Criar migration a partir deste arquivo:
#    alembic revision --autogenerate -m "Create Florence tables"
#
# 4. Executar migration:
#    alembic upgrade head
#
# 5. Verificar status:
#    alembic current
#    alembic history --verbose

# Para desenvolvimento rápido:
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.florence.models.anonymization import Base

# Conectar e criar tabelas
engine = create_engine("postgresql://florence:password@localhost/intellicare_florence")
Base.metadata.create_all(engine)
print("✅ Tabelas criadas via SQLAlchemy")
"""
