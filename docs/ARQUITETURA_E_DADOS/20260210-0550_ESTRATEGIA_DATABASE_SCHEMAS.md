# Estratégia de Database Schemas - INTELLICARE

> **Data de Decisão:** 2026-02-10  
> **Decisão:** Usar PostgreSQL Schemas distintos para cada módulo  
> **Status:** ✅ APROVADO E IMPLEMENTADO  
> **Responsável:** Arquitetura INTELLICARE

---

## 📋 Índice

1. [Contexto e Motivação](#contexto-e-motivação)
2. [Decisão Arquitetural](#decisão-arquitetural)
3. [Arquitetura Implementada](#arquitetura-implementada)
4. [Vantagens](#vantagens)
5. [Regras de Ouro](#regras-de-ouro)
6. [Implementação por Módulo](#implementação-por-módulo)
7. [Padrões de Integração](#padrões-de-integração)
8. [Segurança e Permissões](#segurança-e-permissões)
9. [Backup e Restore](#backup-e-restore)
10. [Monitoramento](#monitoramento)
11. [Migração e Versionamento](#migração-e-versionamento)
12. [Próximos Passos](#próximos-passos)

---

## 🎯 Contexto e Motivação

### Problema

O INTELLICARE está sendo modularizado em uma **arquitetura LEGO**, onde cada módulo:
- Deve funcionar de forma **independente**
- Pode ser **vendido separadamente**
- Deve ter **deploy independente**
- Precisa de **isolamento lógico**

### Questão Arquitetural

**Como organizar o banco de dados para suportar múltiplos módulos independentes?**

**Opções avaliadas:**
1. ❌ **Database por módulo** - Complexidade operacional, custo
2. ❌ **Tabelas com prefixo** - Poluição do namespace, sem isolamento real
3. ✅ **Schema por módulo** - Isolamento lógico, flexibilidade, custo-benefício

---

## 🏗️ Decisão Arquitetural

### Decisão

**Usar PostgreSQL Schemas distintos para cada módulo, mantendo todos em um único database.**

### Justificativa

| Critério | Avaliação |
|----------|-----------|
| **Isolamento Lógico** | ✅ Excelente - Namespaces separados |
| **Segurança** | ✅ Excelente - Permissões granulares por schema |
| **Backup/Restore** | ✅ Excelente - Seletivo por módulo |
| **Custo Operacional** | ✅ Baixo - Um único database |
| **Complexidade** | ✅ Baixa - Nativo do PostgreSQL |
| **Venda Modular** | ✅ Excelente - Schemas = Módulos |
| **Performance** | ✅ Excelente - Sem overhead |

---

## 🏛️ Arquitetura Implementada

### Database Única com Múltiplos Schemas

```
┌─────────────────────────────────────────────────────────┐
│  IntellicareDB (161.97.141.186:5432)                   │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  intellicare_core                              │    │
│  │  ├── users                                     │    │
│  │  ├── organizations                             │    │
│  │  ├── roles                                     │    │
│  │  ├── permissions                               │    │
│  │  └── audit_logs                                │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  intellicare_donabedian                        │    │
│  │  ├── pillars                                   │    │
│  │  ├── indicators                                │    │
│  │  ├── indicator_pillars                         │    │
│  │  └── measurements                              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  intellicare_oswaldo                           │    │
│  │  ├── patients                                  │    │
│  │  ├── appointments                              │    │
│  │  ├── medical_records                           │    │
│  │  └── prescriptions                             │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  intellicare_financeiro (futuro)               │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  intellicare_estoque (futuro)                  │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Exemplo de Queries

```sql
-- Acessar tabelas com schema prefix
SELECT * FROM intellicare_donabedian.pillars;
SELECT * FROM intellicare_oswaldo.patients;
SELECT * FROM intellicare_core.users;

-- Listar todos os schemas
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name LIKE 'intellicare_%';

-- Listar tabelas de um schema
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'intellicare_donabedian';
```

---

## ✅ Vantagens

### 1. Isolamento Lógico

**Cada módulo tem seu próprio namespace:**
```sql
-- Sem conflitos de nomes
intellicare_donabedian.indicators
intellicare_oswaldo.indicators  -- Pode existir!
```

**Benefícios:**
- ✅ Separação clara de responsabilidades
- ✅ Evita conflitos de nomes de tabelas
- ✅ Facilita entender "quem é dono do quê"
- ✅ Código mais legível e manutenível

### 2. Segurança Granular

**Permissões por schema:**
```sql
-- Serviço Donabedian só acessa seu schema
GRANT ALL ON SCHEMA intellicare_donabedian TO donabedian_service;
GRANT USAGE ON SCHEMA intellicare_donabedian TO donabedian_service;
GRANT ALL ON ALL TABLES IN SCHEMA intellicare_donabedian TO donabedian_service;

-- Core pode ler Donabedian (para dashboards)
GRANT USAGE ON SCHEMA intellicare_donabedian TO core_service;
GRANT SELECT ON ALL TABLES IN SCHEMA intellicare_donabedian TO core_service;

-- Oswaldo não acessa Donabedian
-- (sem permissões = sem acesso)
```

**Benefícios:**
- ✅ Princípio do menor privilégio
- ✅ Auditoria mais fácil
- ✅ Reduz superfície de ataque
- ✅ Compliance (LGPD, HIPAA)

### 3. Backup e Restore Seletivo

**Backup por módulo:**
```bash
# Backup apenas do módulo Donabedian
pg_dump -h 161.97.141.186 -U admin_intellicare \
        -n intellicare_donabedian \
        IntellicareDB > donabedian_backup_20260210.sql

# Backup apenas do módulo Oswaldo
pg_dump -h 161.97.141.186 -U admin_intellicare \
        -n intellicare_oswaldo \
        IntellicareDB > oswaldo_backup_20260210.sql

# Backup de todos os módulos
pg_dump -h 161.97.141.186 -U admin_intellicare \
        -n 'intellicare_*' \
        IntellicareDB > intellicare_full_backup_20260210.sql
```

**Restore seletivo:**
```bash
# Restore apenas do Donabedian
psql -h 161.97.141.186 -U admin_intellicare \
     IntellicareDB < donabedian_backup_20260210.sql
```

**Benefícios:**
- ✅ Backups modulares (menor tempo)
- ✅ Restore seletivo (menor downtime)
- ✅ Testes de disaster recovery por módulo
- ✅ Economia de espaço

### 4. Versionamento Independente

**Cada módulo gerencia suas migrations:**
```
intellicare-donabedian/
└── migrations/
    └── versions/
        └── 001_create_initial_tables.py  (v1.0.0)

intellicare-oswaldo/
└── migrations/
    └── versions/
        └── 001_create_patient_tables.py  (v2.3.1)

intellicare-core/
└── migrations/
    └── versions/
        └── 001_create_auth_tables.py     (v3.0.0)
```

**Benefícios:**
- ✅ Deploy independente de cada módulo
- ✅ Rollback sem afetar outros módulos
- ✅ Versionamento semântico por módulo
- ✅ Testes isolados

### 5. Venda Modular

**Schemas só existem se módulo estiver ativo:**

| Cliente | Módulos Comprados | Schemas Criados |
|---------|-------------------|-----------------|
| Cliente A | Core + Donabedian | `intellicare_core`, `intellicare_donabedian` |
| Cliente B | Core + Oswaldo + Donabedian | `intellicare_core`, `intellicare_oswaldo`, `intellicare_donabedian` |
| Cliente C | Apenas Core | `intellicare_core` |

**Benefícios:**
- ✅ Licenciamento mais claro
- ✅ Demonstrações focadas
- ✅ Upsell facilitado (adicionar schemas)
- ✅ Downsell facilitado (remover schemas)

### 6. Monitoramento e Performance

**Métricas por módulo:**
```sql
-- Tamanho de cada módulo
SELECT 
    schemaname as module,
    pg_size_pretty(sum(pg_total_relation_size(schemaname||'.'||tablename))::bigint) as size
FROM pg_tables
WHERE schemaname LIKE 'intellicare_%'
GROUP BY schemaname
ORDER BY sum(pg_total_relation_size(schemaname||'.'||tablename)) DESC;

-- Número de tabelas por módulo
SELECT schemaname, COUNT(*) as table_count
FROM pg_tables
WHERE schemaname LIKE 'intellicare_%'
GROUP BY schemaname;

-- Queries mais lentas por módulo
SELECT 
    schemaname,
    query,
    mean_exec_time,
    calls
FROM pg_stat_statements pss
JOIN pg_tables pt ON pss.query LIKE '%'||pt.tablename||'%'
WHERE schemaname LIKE 'intellicare_%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Benefícios:**
- ✅ Identificar módulos "pesados"
- ✅ Otimização focada
- ✅ Alertas por módulo
- ✅ SLA por módulo

---

## 🚫 Regras de Ouro

### Regra 1: Cada Módulo = 1 Schema

**✅ FAZER:**
```python
# intellicare-donabedian/src/donabedian/config.py
class Settings(BaseSettings):
    database_schema: str = "intellicare_donabedian"

# intellicare-oswaldo/src/oswaldo/config.py
class Settings(BaseSettings):
    database_schema: str = "intellicare_oswaldo"
```

**❌ NÃO FAZER:**
```python
# Múltiplos módulos no mesmo schema
database_schema: str = "public"  # ❌ ERRADO!
```

### Regra 2: NÃO Usar Foreign Keys Entre Schemas

**❌ NÃO FAZER:**
```sql
-- Cria acoplamento entre módulos
ALTER TABLE intellicare_oswaldo.patient_indicators
ADD CONSTRAINT fk_indicator 
FOREIGN KEY (indicator_id) 
REFERENCES intellicare_donabedian.indicators(id);
```

**✅ FAZER:**
```python
# Integração via API REST
# intellicare-oswaldo chama API do donabedian
async def get_indicator(indicator_id: int):
    response = await httpx.get(
        f"http://donabedian-api:8000/api/v1/indicators/{indicator_id}"
    )
    return response.json()
```

**Por quê?**
- ✅ Mantém desacoplamento (arquitetura LEGO)
- ✅ Facilita venda modular
- ✅ Permite deploy independente
- ✅ Evita dependências circulares

### Regra 3: Integração via API, Não via FK

**Padrão de Integração:**
```
┌─────────────────┐         HTTP/REST        ┌─────────────────┐
│  Oswaldo API    │ ───────────────────────> │ Donabedian API  │
│  (Port 8002)    │                          │  (Port 8003)    │
└─────────────────┘                          └─────────────────┘
        │                                             │
        │                                             │
        v                                             v
┌─────────────────┐                          ┌─────────────────┐
│ oswaldo schema  │                          │donabedian schema│
└─────────────────┘                          └─────────────────┘
```

### Regra 4: Core Pode Ter Views Read-Only

**✅ PERMITIDO:**
```sql
-- Core cria views para dashboards consolidados
CREATE VIEW intellicare_core.all_quality_indicators AS
SELECT 
    'donabedian' as source_module,
    id,
    name,
    target_value
FROM intellicare_donabedian.indicators;

-- Core pode fazer JOINs read-only
CREATE VIEW intellicare_core.patient_quality_summary AS
SELECT 
    p.id as patient_id,
    p.name as patient_name,
    i.name as indicator_name,
    m.value as measurement_value
FROM intellicare_oswaldo.patients p
LEFT JOIN intellicare_oswaldo.patient_measurements pm ON pm.patient_id = p.id
LEFT JOIN intellicare_donabedian.measurements m ON m.id = pm.measurement_id
LEFT JOIN intellicare_donabedian.indicators i ON i.id = m.indicator_id;
```

**Benefícios:**
- ✅ Dashboards consolidados
- ✅ Relatórios cross-module
- ✅ Sem acoplamento (apenas leitura)

### Regra 5: Cada Módulo Gerencia Suas Migrations

**Estrutura:**
```
intellicare-donabedian/
├── alembic.ini
└── migrations/
    ├── env.py
    └── versions/
        └── 001_create_initial_tables.py

intellicare-oswaldo/
├── alembic.ini
└── migrations/
    ├── env.py
    └── versions/
        └── 001_create_patient_tables.py
```

**Comandos independentes:**
```bash
# Donabedian
cd intellicare-donabedian
alembic upgrade head

# Oswaldo
cd intellicare-oswaldo
alembic upgrade head
```

---

## 🔧 Implementação por Módulo

### Template de Implementação

Cada módulo deve seguir este padrão:

#### 1. **Configuração (`config.py`)**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    intellicare_database_url: str = (
        "postgresql+asyncpg://admin_intellicare:PASSWORD@161.97.141.186:5432/IntellicareDB"
    )

    # Schema do módulo (IMPORTANTE!)
    database_schema: str = "intellicare_NOME_DO_MODULO"

    # Module Info
    module_name: str = "intellicare-NOME_DO_MODULO"
    module_version: str = "1.0.0"

settings = Settings()
```

#### 2. **Models (`models/__init__.py`)**

```python
from sqlalchemy.orm import DeclarativeBase
from NOME_DO_MODULO.config import settings

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    # Define schema for all tables in this module
    __table_args__ = {"schema": settings.database_schema}
```

#### 3. **Migration Inicial**

```python
"""create_initial_tables

Revision ID: 001
Revises:
Create Date: 2026-02-10
"""

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # 1. Criar schema
    op.execute("CREATE SCHEMA IF NOT EXISTS intellicare_NOME_DO_MODULO")

    # 2. Criar tabelas no schema
    op.create_table(
        'tabela_exemplo',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        schema='intellicare_NOME_DO_MODULO'
    )

    # 3. Criar indexes no schema
    op.create_index(
        'ix_tabela_exemplo_name',
        'tabela_exemplo',
        ['name'],
        schema='intellicare_NOME_DO_MODULO'
    )

def downgrade() -> None:
    # 1. Dropar indexes
    op.drop_index('ix_tabela_exemplo_name', table_name='tabela_exemplo', schema='intellicare_NOME_DO_MODULO')

    # 2. Dropar tabelas
    op.drop_table('tabela_exemplo', schema='intellicare_NOME_DO_MODULO')

    # 3. Dropar schema
    op.execute("DROP SCHEMA IF EXISTS intellicare_NOME_DO_MODULO CASCADE")
```

---

## 📚 Referências

- [PostgreSQL Schemas Documentation](https://www.postgresql.org/docs/current/ddl-schemas.html)
- [Multi-tenancy with PostgreSQL Schemas](https://www.citusdata.com/blog/2017/03/09/multi-tenant-sharding-tutorial/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)

---

## 📞 Contato

**Dúvidas sobre esta estratégia?**
- Arquitetura: arquitetura@intellicare.health
- DevOps: devops@intellicare.health
- Documentação: docs@intellicare.health

---

**Última Atualização:** 2026-02-10
**Versão do Documento:** 1.0.0
**Status:** ✅ APROVADO E EM PRODUÇÃO

