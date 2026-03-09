# STEPS DE IMPLEMENTAÇÃO - Separação Operacional/Analítico

**Data Criação**: 2026-02-11  
**Formato**: Passos executáveis, command-line ready  
**Público**: Desenvolvedores implementando a feature  

---

## 📋 Índice

1. [Fase 1 - Steps: Fundação](#fase-1---steps-fundação)
2. [Fase 2 - Steps: Core](#fase-2---steps-core)
3. [Fase 3 - Steps: Consolidação](#fase-3---steps-consolidação)
4. [Fase 4 - Steps: Deploy](#fase-4---steps-deploy)

---

## 🔧 FASE 1 - Steps: Fundação

### STEP 1.1: Criar estrutura de intellicare-core

```bash
#!/bin/bash
# Script: setup_phase1_structure.sh

# Criar diretório
mkdir -p intellicare-core/src/intellicare_core
mkdir -p intellicare-core/{tests,alembic/versions,docs}

# Estrutura de código
mkdir -p intellicare-core/src/intellicare_core/{data_access,events,security,monitoring,config,schemas}

# Criar __init__.py files
touch intellicare-core/src/intellicare_core/__init__.py
touch intellicare-core/src/intellicare_core/data_access/__init__.py
touch intellicare-core/src/intellicare_core/events/__init__.py
touch intellicare-core/src/intellicare_core/security/__init__.py
touch intellicare-core/src/intellicare_core/monitoring/__init__.py
touch intellicare-core/src/intellicare_core/config/__init__.py
touch intellicare-core/src/intellicare_core/schemas/__init__.py

echo "✅ Estrutura criada em intellicare-core/"
tree intellicare-core/ -L 3
```

**Executar**:
```bash
bash setup_phase1_structure.sh
```

---

### STEP 1.2: Implementar BaseDAO

**Arquivo**: `intellicare-core/src/intellicare_core/data_access/base.py`

```python
from typing import TypeVar, Generic, Optional, List, Dict, Any
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy import select

T = TypeVar('T')

class BaseDAO(ABC, Generic[T]):
    """Base DAO abstrato com CRUD genérico."""
    
    def __init__(self, session: Session, entity_class: type[T]):
        self.session = session
        self.entity_class = entity_class
    
    @abstractmethod
    def create(self, entity_data: Dict[str, Any]) -> T:
        """Criar entidade."""
        pass
    
    @abstractmethod
    def read(self, entity_id: str) -> Optional[T]:
        """Ler entidade."""
        pass
    
    def list(self, skip: int = 0, limit: int = 100, filters: Dict = None) -> List[T]:
        """Listar entidades."""
        query = select(self.entity_class)
        if filters:
            for key, value in filters.items():
                query = query.where(getattr(self.entity_class, key) == value)
        return self.session.execute(
            query.offset(skip).limit(limit)
        ).scalars().all()
    
    @abstractmethod
    def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[T]:
        """Atualizar entidade."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Deletar entidade."""
        pass
```

**Testes**: `intellicare-core/tests/test_base_dao.py`

```python
import pytest
from unittest.mock import MagicMock
from intellicare_core.data_access.base import BaseDAO

def test_list_with_filters():
    """Testa listagem com filtros."""
    session = MagicMock()
    dao = ConcreteDAO(session, MockEntity)
    result = dao.list(filters={'status': 'ativo'})
    assert isinstance(result, list)
```

**Executar**:
```bash
cd intellicare-core
pytest tests/test_base_dao.py -v
```

---

### STEP 1.3: Implementar OperationalDataAccess

**Arquivo**: `intellicare-core/src/intellicare_core/data_access/operational.py`

```python
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from .base import BaseDAO, T

class OperationalDataAccess(BaseDAO[T]):
    """DAO para esquemas _operacional."""
    
    def __init__(self, session, entity_class, schema: str):
        super().__init__(session, entity_class)
        self.schema = schema
        self._validate_schema()
    
    def _validate_schema(self):
        """Garante que schema é operacional."""
        if 'analitico' in self.schema:
            raise ValueError(f"OperationalDataAccess não usa {self.schema}")
    
    def create(self, entity_data):
        """Criar entidade em operacional."""
        try:
            entity = self.entity_class(**entity_data)
            self.session.add(entity)
            self.session.flush()
            return entity
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Erro ao criar: {e}")
    
    def read(self, entity_id: str):
        """Ler entidade."""
        return self.session.query(self.entity_class).get(entity_id)
    
    def update(self, entity_id: str, updates):
        """Atualizar entidade."""
        entity = self.read(entity_id)
        if not entity:
            raise ValueError(f"Entidade {entity_id} não encontrada")
        
        for key, value in updates.items():
            setattr(entity, key, value)
        
        entity.updated_at = datetime.utcnow()
        self.session.flush()
        return entity
    
    def delete(self, entity_id: str) -> bool:
        """Delete lógico."""
        entity = self.read(entity_id)
        if not entity:
            return False
        entity.valid_to = datetime.utcnow()
        self.session.flush()
        return True
```

**Testes**:
```bash
pytest tests/test_operational_dao.py -v --cov
```

---

### STEP 1.4: Implementar AnalyticsDataAccess

**Arquivo**: `intellicare-core/src/intellicare_core/data_access/analytics.py`

```python
from sqlalchemy import select
from .base import BaseDAO, T

class AnalyticsDataAccess(BaseDAO[T]):
    """DAO read-only para esquemas _analitico."""
    
    def __init__(self, session, entity_class, schema: str):
        super().__init__(session, entity_class)
        self.schema = schema
        self._validate_schema()
    
    def _validate_schema(self):
        """Garante que schema é analítico."""
        if 'analitico' not in self.schema:
            raise ValueError(f"AnalyticsDataAccess só usa _analitico, recebeu: {self.schema}")
    
    def create(self, entity_data):
        raise PermissionError("AnalyticsDataAccess é read-only")
    
    def update(self, entity_id: str, updates):
        raise PermissionError("AnalyticsDataAccess é read-only")
    
    def delete(self, entity_id: str):
        raise PermissionError("AnalyticsDataAccess é read-only")
    
    def read(self, entity_id: str):
        """Ler entidade (único método permitido)."""
        return self.session.query(self.entity_class).get(entity_id)
    
    def list(self, skip=0, limit=100, filters=None):
        """Listar entidades."""
        return super().list(skip, limit, filters)
    
    def aggregate(self, group_by: str, agg_func: str, field: str):
        """Agregação customizada."""
        # Implementar funções de agregação
        pass
```

**Testes**:
```bash
pytest tests/test_analytics_dao.py::test_read_only_enforcement -v
```

---

### STEP 1.5: Implementar EventPublisher

**Arquivo**: `intellicare-core/src/intellicare_core/events/publisher.py`

```python
import json
from datetime import datetime
from uuid import uuid4
import redis
from enum import Enum

class EventOperation(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class EventPublisher:
    """Publica eventos em Redis Streams."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def publish(self, schema: str, entity_type: str, entity_id: str,
                operation: str, actor_id: str, 
                old_values: dict = None, new_values: dict = None) -> str:
        """
        Publica evento em Redis.
        
        Stream: {schema}:events:{entity_type}
        """
        stream_key = f"{schema}:events:{entity_type}"
        
        event = {
            "event_id": str(uuid4()),
            "schema": schema,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "actor_id": str(actor_id),
            "old_values": json.dumps(old_values) if old_values else "",
            "new_values": json.dumps(new_values) if new_values else ""
        }
        
        message_id = self.redis.xadd(stream_key, event)
        return message_id.decode() if isinstance(message_id, bytes) else message_id
```

**Testes**:
```bash
pytest tests/test_event_publisher.py -v
```

---

### STEP 1.6: Criar migration inicial

**Arquivo**: `intellicare-core/alembic/versions/001_initial_schemas.py`

```python
\"\"\"Initial core schemas.\"\"\"
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None

def upgrade():
    # Criar schema core
    op.execute("CREATE SCHEMA IF NOT EXISTS intellicare_core")
    
    # Tabela de usuários
    op.create_table(
        'usuarios',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True),
        sa.Column('nome', sa.String(255)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        schema='intellicare_core'
    )
    
    # Tabela de organizações
    op.create_table(
        'organizacoes',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('nome', sa.String(255)),
        sa.Column('cnpj', sa.String(14), unique=True),
        schema='intellicare_core'
    )

def downgrade():
    op.drop_table('organizacoes', schema='intellicare_core')
    op.drop_table('usuarios', schema='intellicare_core')
    op.execute("DROP SCHEMA IF EXISTS intellicare_core")
```

**Executar**:
```bash
cd intellicare-core
alembic upgrade head
```

---

### STEP 1.7: Configurar PostgreSQL roles

**Script**: `intellicare-core/scripts/setup_postgres_roles.sql`

```sql
-- Conectar como superuser: psql -U postgres -d intellicare_db

-- Criar roles
CREATE ROLE intellicare_app_role NOLOGIN;
CREATE ROLE intellicare_analytics_role NOLOGIN;
CREATE ROLE intellicare_consolidation_role NOLOGIN;

-- Permissões base
GRANT CONNECT ON DATABASE intellicare_db TO intellicare_app_role;
GRANT CONNECT ON DATABASE intellicare_db TO intellicare_analytics_role;
GRANT CONNECT ON DATABASE intellicare_db TO intellicare_consolidation_role;

-- Usage em schemas
GRANT USAGE ON SCHEMA intellicare_core 
  TO intellicare_app_role, intellicare_analytics_role, intellicare_consolidation_role;

-- SELECT permissões em core
GRANT SELECT ON ALL TABLES IN SCHEMA intellicare_core 
  TO intellicare_app_role, intellicare_analytics_role, intellicare_consolidation_role;

echo "✅ Roles criados"
```

**Executar**:
```bash
psql -U postgres -d intellicare_db -f intellicare-core/scripts/setup_postgres_roles.sql
```

---

### STEP 1.8: Configurar Redis

**Script**: `intellicare-core/scripts/setup_redis.sh`

```bash
#!/bin/bash
# Configurar Redis Streams e Consumer Groups

# Connect to Redis
redis-cli << EOF

# Verificar que Redis está rodando
PING

# Criar streams iniciais (com dados dummy)
XADD oswaldo_operacional:events:pacientes * entity_id "dummy" operation "INIT"
XADD florence_operacional:events:cuidado * entity_id "dummy" operation "INIT"

# Criar consumer groups
XGROUP CREATE oswaldo_operacional:events:pacientes consolidators-oswaldo 0 MKSTREAM
XGROUP CREATE florence_operacional:events:cuidado consolidators-florence 0 MKSTREAM

# Verificar
XINFO STREAM oswaldo_operacional:events:pacientes

# Configurar persistence
BGSAVE

EOF

echo "✅ Redis configurado"
```

**Executar**:
```bash
redis-server --daemonize yes
bash intellicare-core/scripts/setup_redis.sh
redis-cli PING  # Verify
```

---

### STEP 1.9: Testes integrados Fase 1

**Script**: `test_phase1.sh`

```bash
#!/bin/bash
# Testes de Fase 1

echo "🧪 Executando testes de Fase 1..."

cd intellicare-core

# Tests
pytest tests/ -v --cov=src/intellicare_core --cov-report=html

# Coverage report
echo "📊 Coverage report gerado em htmlcov/index.html"

# Lint
flake8 src/ --max-line-length=120

# Type checking
mypy src/intellicare_core --ignore-missing-imports

echo "✅ Todos os testes passaram!"
```

**Executar**:
```bash
bash test_phase1.sh
```

---

## 🔄 FASE 2 - Steps: Core

### STEP 2.1: Analisar módulos

**Script**: `analyze_modules.py`

```python
#!/usr/bin/env python3
\"\"\"Analisa estrutura de BD de cada módulo.\"\"\"

import sqlalchemy as sa
from sqlalchemy import inspect

MODULES = [
    'oswaldo', 'florence', 'donabedian', 'zilda',
    'geralda', 'comunicacao', 'auth', 'portal', 'wanda'
]

for module in MODULES:
    print(f"\n📊 Módulo: {module}")
    print("=" * 50)
    
    # Conectar ao BD
    engine = sa.create_engine(f"postgresql://user:pass@localhost/{module}_db")
    inspector = inspect(engine)
    
    # Listar tabelas
    tables = inspector.get_table_names()
    print(f"Tabelas: {len(tables)}")
    
    for table in tables:
        columns = inspector.get_columns(table)
        print(f"  - {table} ({len(columns)} colunas)")
    
    # Sugerir separação
    suggest_operational_analytic_split(module, tables)

def suggest_operational_analytic_split(module, tables):
    \"\"\"Sugere quais tabelas são operacional vs analítico.\"\"\"
    
    operational = [t for t in tables if not any(x in t for x in ['hist', 'agg', 'report'])]
    analytic = [t for t in tables if any(x in t for x in ['hist', 'agg', 'report'])]
    
    print(f"\n  💾 Operational ({len(operational)}):")
    for t in operational:
        print(f"    - {t}")
    
    print(f"\n  📈 Analytic ({len(analytic)}):")
    for t in analytic:
        print(f"    - {t}")
```

**Executar**:
```bash
python analyze_modules.py > modules_analysis.txt
cat modules_analysis.txt
```

---

### STEP 2.2: Migrar módulo (exemplo: oswaldo)

**Script**: `migrate_module_oswaldo.sh`

```bash
#!/bin/bash
# Migrar oswaldo para separação operacional/analítico

MODULE="oswaldo"
DB="${MODULE}_db"

echo "🔄 Migrando módulo $MODULE..."

# 1. Criar schemas
psql -U intellicare -d $DB << EOF
CREATE SCHEMA IF NOT EXISTS ${MODULE}_operacional;
CREATE SCHEMA IF NOT EXISTS ${MODULE}_analitico;
ALTER SCHEMA ${MODULE}_operacional OWNER TO intellicare_app_role;
ALTER SCHEMA ${MODULE}_analitico OWNER TO intellicare_analytics_role;
EOF

# 2. Mover tabelas existentes para operacional
psql -U intellicare -d $DB << EOF
-- Tabelas operacionais
ALTER TABLE IF EXISTS pacientes SET SCHEMA ${MODULE}_operacional;
ALTER TABLE IF EXISTS monitoramento SET SCHEMA ${MODULE}_operacional;
ALTER TABLE IF EXISTS alertas SET SCHEMA ${MODULE}_operacional;
EOF

# 3. Criar tabelas analíticas (desnormalizadas)
psql -U intellicare -d $DB << EOF
CREATE TABLE ${MODULE}_analitico.pacientes_hist (
  paciente_id UUID NOT NULL,
  ano_mes INT NOT NULL,
  nome VARCHAR,
  status VARCHAR,
  dias_em_status INT,
  replicated_at TIMESTAMP DEFAULT NOW(),
  provenance JSONB,
  PRIMARY KEY (paciente_id, ano_mes)
);

CREATE TABLE ${MODULE}_analitico.monitoramento_diario (
  paciente_id UUID NOT NULL,
  data DATE NOT NULL,
  metricas JSONB,
  replicated_at TIMESTAMP,
  PRIMARY KEY (paciente_id, data)
);

CREATE INDEX idx_${MODULE}_hist_period ON ${MODULE}_analitico.pacientes_hist(ano_mes DESC);
EOF

# 4. Aplicar RLS policies
psql -U intellicare -d $DB << EOF
ALTER TABLE ${MODULE}_analitico.pacientes_hist ENABLE ROW LEVEL SECURITY;

CREATE POLICY no_write_analytic ON ${MODULE}_analitico.pacientes_hist
  AS PERMISSIVE FOR UPDATE, DELETE USING (FALSE);

CREATE POLICY read_only_analytics ON ${MODULE}_analitico.pacientes_hist
  AS RESTRICTIVE FOR SELECT USING (TRUE)
  FOR DELETE USING (FALSE)
  FOR UPDATE USING (FALSE);
EOF

echo "✅ Módulo $MODULE migrado!"
```

**Executar**:
```bash
bash migrate_module_oswaldo.sh
psql -U intellicare -d oswaldo_db -c "\dn+"  # Verificar schemas
```

---

### STEP 2.3-2.10: Repetir para outros módulos

```bash
# Para cada módulo
for module in florence donabedian zilda geralda comunicacao auth portal wanda; do
  bash migrate_module.sh $module
done
```

---

## ⚙️ FASE 3 - Steps: Consolidação

### STEP 3.1: Criar serviço de consolidação

**Arquivo**: `consolidation-service/src/consolidation_service/consolidator.py`

```python
import redis
from sqlalchemy.orm import Session
from typing import Dict

class DataConsolidator:
    """Consolida eventos de operacional para analítico."""
    
    def __init__(self, redis_client: redis.Redis, db: Session, schema: str):
        self.redis = redis_client
        self.db = db
        self.schema = schema
    
    def consolidate_batch(self, batch_size: int = 100) -> Dict:
        """Processa batch de eventos."""
        events_processed = 0
        events_failed = 0
        
        try:
            # Ler eventos do Redis
            stream_key = f"{self.schema}:events:*"
            events = self.redis.xreadgroup(
                f"consolidators-{self.schema}",
                f"consolidators-{self.schema}",
                {stream_key: '>'},
                count=batch_size
            )
            
            for stream, messages in (events or []):
                for msg_id, event_data in messages:
                    try:
                        self._process_event(event_data)
                        self.redis.xack(stream, f"consolidators-{self.schema}", msg_id)
                        events_processed += 1
                    except Exception as e:
                        events_failed += 1
                        self._move_to_dlq(msg_id, event_data, str(e))
        
        except Exception as e:
            print(f"❌ Erro: {e}")
            return {'status': 'error', 'error': str(e)}
        
        return {
            'status': 'success' if events_failed == 0 else 'warning',
            'events_processed': events_processed,
            'events_failed': events_failed
        }
    
    def _process_event(self, event_data: Dict):
        """Processa um evento individual."""
        entity_type = event_data[b'entity_type'].decode()
        entity_id = event_data[b'entity_id'].decode()
        
        # Replica em tabela analítica
        table_name = f"{self.schema.replace('_operacional', '')}_analitico.{entity_type}_hist"
        
        # Implementar inserção/update
        # self.db.execute(...)
```

**Testes**:
```bash
pytest consolidation-service/tests/ -v
```

---

### STEP 3.2: Agendar consolidação

**Arquivo**: `consolidation-service/src/consolidation_service/scheduler.py`

```python
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

def schedule_consolidation():
    scheduler = BackgroundScheduler()
    
    # Consolidar diariamente às 2:00 AM UTC
    scheduler.add_job(
        run_consolidation,
        'cron',
        hour=2,
        minute=0,
        id='daily_consolidation'
    )
    
    scheduler.start()
    print("✅ Schedular iniciado")

def run_consolidation():
    print(f"🔄 Consolidação iniciada em {datetime.utcnow()}")
    # Chamar consolidator.consolidate_batch()
    print(f"✅ Consolidação concluída")
```

---

### STEP 3.3: Monitoramento

**Arquivo**: `consolidation-service/src/consolidation_service/metrics.py`

```python
from prometheus_client import Counter, Gauge, Histogram

events_consolidated = Counter(
    'events_consolidated_total',
    'Total events consolidated',
    ['schema', 'status']
)

replication_lag = Gauge(
    'replication_lag_seconds',
    'Lag em segundos',
    ['schema']
)

consolidation_duration = Histogram(
    'consolidation_duration_seconds',
    'Duração da consolidação',
    ['schema']
)
```

---

## ✅ FASE 4 - Steps: Deploy

### STEP 4.1: Build Docker

```bash
# intellicare-core
cd intellicare-core
docker build -t intellicare-core:v1 .
docker push intellicare-core:v1

# consolidation-service
cd consolidation-service
docker build -t consolidation-service:v1 .
docker push consolidation-service:v1
```

---

### STEP 4.2: Deploy em staging

```bash
docker-compose -f docker-compose.staging.yml up -d

# Validar
curl http://localhost:8000/api/v1/health
```

---

### STEP 4.3: Run tests em staging

```bash
pytest tests/e2e/ -v --environment=staging
```

---

### STEP 4.4: Deploy progressivo em produção

```bash
# Phase 1: Canary (10%)
docker service update --image consolidation-service:v1 \
  --replicas 1 consolidation_prod

# Phase 2: Ramp (50%)
docker service update --replicas 5 consolidation_prod

# Phase 3: Full (100%)
docker service update --replicas 10 consolidation_prod
```

---

## ✨ Próximos passos

1. ✅ Fase 1 - Fundação (17 dias)
2. ▶️ Fase 2 - Core (21 dias)
3. ▶️ Fase 3 - Consolidação (15 dias)
4. ▶️ Fase 4 - Deploy (10 dias)

**Total**: ~63 dias

Comece com STEP 1.1!
