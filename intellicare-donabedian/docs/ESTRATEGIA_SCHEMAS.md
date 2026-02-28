# Estratégia de Schemas PostgreSQL - INTELLICARE

> **Data:** 2026-02-10  
> **Decisão:** Usar schemas distintos para cada módulo  
> **Status:** ✅ APROVADO E IMPLEMENTADO

---

## 🎯 Objetivo

Implementar **isolamento lógico** entre módulos INTELLICARE usando **PostgreSQL schemas**, mantendo todos os módulos no mesmo database (`IntellicareDB`) mas em namespaces separados.

---

## 🏗️ Arquitetura

### Database Única com Múltiplos Schemas

```
IntellicareDB (161.97.141.186:5432)
├── intellicare_core          (usuários, organizações, auth, logs)
├── intellicare_donabedian    (7 pilares, indicadores, medições)
├── intellicare_oswaldo       (pacientes, agendamentos, prontuários)
├── intellicare_financeiro    (futuro)
└── intellicare_estoque       (futuro)
```

### Exemplo de Tabelas

```sql
-- Módulo Donabedian
intellicare_donabedian.pillars
intellicare_donabedian.indicators
intellicare_donabedian.indicator_pillars
intellicare_donabedian.measurements

-- Módulo Oswaldo (futuro)
intellicare_oswaldo.patients
intellicare_oswaldo.appointments
intellicare_oswaldo.medical_records

-- Módulo Core (futuro)
intellicare_core.users
intellicare_core.organizations
intellicare_core.audit_logs
```

---

## ✅ Vantagens

### 1. **Isolamento Lógico**
- Cada módulo tem seu próprio namespace
- Evita conflitos de nomes de tabelas
- Separação clara de responsabilidades

### 2. **Segurança Granular**
```sql
-- Permissões por schema
GRANT ALL ON SCHEMA intellicare_donabedian TO donabedian_service;
GRANT SELECT ON SCHEMA intellicare_donabedian TO intellicare_core;
```

### 3. **Backup/Restore Seletivo**
```bash
# Backup apenas do módulo Donabedian
pg_dump -n intellicare_donabedian IntellicareDB > donabedian_backup.sql
```

### 4. **Versionamento Independente**
- Cada módulo gerencia suas próprias migrations
- Deploy independente
- Rollback sem afetar outros módulos

### 5. **Venda Modular**
- Schemas só existem se módulo estiver ativo
- Licenciamento mais claro
- Demonstrações focadas

### 6. **Monitoramento**
```sql
-- Tamanho por módulo
SELECT schema_name, 
       pg_size_pretty(sum(table_size)::bigint)
FROM (
  SELECT pg_catalog.pg_namespace.nspname as schema_name,
         pg_relation_size(pg_catalog.pg_class.oid) as table_size
  FROM pg_catalog.pg_class
  JOIN pg_catalog.pg_namespace ON relnamespace = pg_catalog.pg_namespace.oid
) t
GROUP BY schema_name;
```

---

## 🚫 Regras de Ouro

### 1. **Cada Módulo = 1 Schema**
```python
# config.py
database_schema: str = "intellicare_donabedian"
```

### 2. **NÃO usar Foreign Keys entre Schemas**
```sql
-- ❌ EVITAR (cria acoplamento)
ALTER TABLE intellicare_oswaldo.patient_indicators
ADD CONSTRAINT fk_indicator 
FOREIGN KEY (indicator_id) 
REFERENCES intellicare_donabedian.indicators(id);

-- ✅ USAR (desacoplamento via API)
-- Integração via API REST, não via FK
```

### 3. **Integração via API, não via FK**
- Módulos se comunicam via HTTP/REST
- Mantém arquitetura LEGO (desacoplada)
- Facilita venda modular

### 4. **Core pode ter Views Read-Only**
```sql
-- Core pode criar views para dashboards consolidados
CREATE VIEW intellicare_core.all_quality_indicators AS
SELECT * FROM intellicare_donabedian.indicators;
```

### 5. **Cada Módulo Gerencia Suas Migrations**
```
migrations/
└── versions/
    └── 20260210_1200_001_create_initial_tables.py
```

---

## 🔧 Implementação no Donabedian

### 1. **Config (`config.py`)**
```python
class Settings(BaseSettings):
    intellicare_database_url: str = (
        "postgresql+asyncpg://admin_intellicare:PASSWORD@161.97.141.186:5432/IntellicareDB"
    )
    database_schema: str = "intellicare_donabedian"
```

### 2. **Models (`models/__init__.py`)**
```python
class Base(DeclarativeBase):
    __table_args__ = {"schema": settings.database_schema}
```

### 3. **Migration**
```python
def upgrade() -> None:
    # Criar schema
    op.execute("CREATE SCHEMA IF NOT EXISTS intellicare_donabedian")
    
    # Criar tabelas no schema
    op.create_table(
        'pillars',
        ...,
        schema='intellicare_donabedian'
    )
```

---

## 📊 Conexão com Database Produção

```
Host: 161.97.141.186
Port: 5432
User: admin_intellicare
Password: Crazy#57LB
Database: IntellicareDB
Schema: intellicare_donabedian
```

---

## 🎯 Próximos Passos

1. ✅ **Donabedian:** Schema implementado
2. ⏳ **Oswaldo:** Implementar `intellicare_oswaldo` schema
3. ⏳ **Core:** Implementar `intellicare_core` schema
4. ⏳ **Documentar:** Padrão de integração entre módulos via API

---

## 📚 Referências

- [PostgreSQL Schemas Documentation](https://www.postgresql.org/docs/current/ddl-schemas.html)
- [Multi-tenancy with PostgreSQL Schemas](https://www.citusdata.com/blog/2017/03/09/multi-tenant-sharding-tutorial/)

