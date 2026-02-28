# ESPECIFICAÇÃO TÉCNICA - Separação Operacional/Analítico

**Data**: 2026-02-11  
**Status**: 🟢 Especificação Técnica Completa  
**Versão**: v1.0  
**Stack**: Python 3.11+ | PostgreSQL 15+ | Redis 7+ | FastAPI  

---

## 📋 Índice

1. [Arquitetura Técnica](#arquitetura-técnica)
2. [Stack de Tecnologia](#stack-de-tecnologia)
3. [Schema Database](#schema-database)
4. [Padrões de Código](#padrões-de-código)
5. [Event Publishing](#event-publishing)
6. [Consolidation Service](#consolidation-service)
7. [Row-Level Security](#row-level-security)
8. [Monitoramento](#monitoramento)
9. [Migração e Versionamento](#migração-e-versionamento)
10. [Exemplos de Código](#exemplos-de-código)

---

## 🏗️ Arquitetura Técnica

### Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                  APLICAÇÕES (FastAPI)                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ oswaldo      │ │ florence     │ │ donabedian   │ ...          │
│  │ :8501        │ │ :8502        │ │ :8503        │             │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘             │
├─────────┴──────────────────┴────────────────┴───────────────────┤
│              intellicare-core (Shared Library)                   │
│  ├─ OperationalDataLayer (SQLAlchemy ORM models)                 │
│  ├─ AnalyticsDataLayer (read-only, denormalized)                 │
│  ├─ EventPublisher (Redis Stream abstraction)                    │
│  ├─ ProvenanceTracker (auditoria padrão FHIR)                    │
│  ├─ RLSEnforcer (Row-Level Security policies)                    │
│  └─ DataIntegrityValidator (checks de separação)                 │
├─────────────────────────────────────────────────────────────────┤
│                   PostgreSQL (Database)                          │
│  ├─ intellicare_core (usuarios, org, configuracao)               │
│  ├─ {modulo}_operacional (transacional, write)                   │
│  └─ {modulo}_analitico (eventual, read-only)                     │
├─────────────────────────────────────────────────────────────────┤
│                   Redis (Message Broker)                         │
│  ├─ Streams: {modulo}:events:{entity}                            │
│  ├─ DLQ: {modulo}:dlq                                            │
│  └─ Checkpoint: consolidation:{modulo}:checkpoint               │
├─────────────────────────────────────────────────────────────────┤
│            Consolidation Service (Standalone Service)            │
│  ├─ ConsolidationOrchestrator                                    │
│  ├─ EventProcessor                                               │
│  ├─ AggregationEngine                                            │
│  └─ HealthMonitor                                                │
└─────────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados (Sequência)

```
1. [Aplicação Escreve]
   │
   ├─→ FastAPI endpoint: POST /patients
   │
   ├─→ Valida usando Pydantic schema
   │
   ├─→ OperationalDataAccess.create(entity_class, data)
   │     │
   │     ├─→ SQLAlchemy ORM
   │     │
   │     └─→ PostgreSQL {modulo}_operacional
   │           INSERT INTO pacientes (...)
   │           TRANSACTION (ACID)
   │           ← Trigger: published_event()
   │
   ├─→ Redis Streams: {modulo}:events:pacientes
   │     {
   │       "event_id": "uuid",
   │       "operation": "CREATE",
   │       "entity_id": "patient-123",
   │       "timestamp": "2026-02-11T10:00:00Z",
   │       "actor": "user-abc",
   │       "data": {...}
   │     }
   │
   └─→ Response: 201 Created (instantâneo)

2. [Consolidation Service Consome]
   │
   ├─→ ConsolidationListener (background task)
   │     Crons: 0 2 * * * (2:00 AM UTC)
   │
   ├─→ Redis.xread(group='consolidators', streams={modulo}:events)
   │
   ├─→ Para cada evento:
   │     │
   │     ├─ Lê dado em {modulo}_operacional
   │     │
   │     ├─ Aplica transformação (denormalization rules)
   │     │
   │     ├─ Insere em {modulo}_analitico (eventual)
   │     │
   │     └─ Registra em audit_trail
   │
   └─→ Publica métrica (Prometheus)
```

---

## 💻 Stack de Tecnologia

### Backend

| Componente | Versão | Propósito |
|-----------|--------|----------|
| Python | 3.11+ | Linguagem base |
| FastAPI | 0.100+ | Web framework |
| SQLAlchemy | 2.0+ | ORM e query builder |
| Pydantic | 2.0+ | Validação de schemas |
| Alembic | 1.12+ | Migrações de BD |
| psycopg2-binary | 2.9+ | Driver PostgreSQL |
| redis | 5.0+ | Cliente Redis |
| prometheus-client | 0.18+ | Métricas |

### Database

| Componente | Versão | Propósito |
|-----------|--------|----------|
| PostgreSQL | 15+ | Armazenamento principal |
| pg_stat_statements | built-in | Monitoramento de queries |
| pgAudit | 1.7+ | Plugin de auditoria |

### Message Broker

| Componente | Versão | Propósito |
|-----------|--------|----------|
| Redis | 7+ | Streams, cache, sessions |

### Observabilidade

| Componente | Versão | Propósito |
|-----------|--------|----------|
| Prometheus | 2.45+ | Coleta de métricas |
| Grafana | 10+ | Visualização |
| Loki/ELK | latest | Logs agregados |

---

## 📊 Schema Database

### Criação de Schemas

```sql
-- Criar schemas (per module: oswaldo, florence, etc.)
CREATE SCHEMA IF NOT EXISTS oswaldo_operacional;
CREATE SCHEMA IF NOT EXISTS oswaldo_analitico;

-- Grant permissões base
GRANT USAGE ON SCHEMA oswaldo_operacional TO intellicare_app_role;
GRANT USAGE ON SCHEMA oswaldo_analitico TO intellicare_analytics_role;

-- Tabelas operacionais (transacionais)
CREATE TABLE oswaldo_operacional.pacientes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nome VARCHAR(255) NOT NULL,
  cpf VARCHAR(14) UNIQUE,
  email VARCHAR(255),
  data_nascimento DATE,
  status VARCHAR DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo', 'coordenando')),
  
  -- Auditoria
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  created_by UUID NOT NULL REFERENCES intellicare_core.usuarios(id),
  updated_by UUID NOT NULL REFERENCES intellicare_core.usuarios(id),
  
  -- Versionamento Otimista
  rowversion INT NOT NULL DEFAULT 1,
  
  -- Constraint de exclusão
  valid_from TIMESTAMP DEFAULT NOW(),
  valid_to TIMESTAMP,
  
  CONSTRAINT check_dates CHECK (valid_to IS NULL OR valid_to > valid_from)
);

-- Índices operacionais (performance de write)
CREATE INDEX idx_pacientes_status ON oswaldo_operacional.pacientes(status);
CREATE INDEX idx_pacientes_created_by ON oswaldo_operacional.pacientes(created_by);

-- Tabela de Auditoria Operacional
CREATE TABLE oswaldo_operacional.audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- O QUÊ
  entity_type VARCHAR NOT NULL,  -- 'paciente', 'tarefa', etc.
  entity_id UUID NOT NULL,
  operation VARCHAR NOT NULL,    -- 'CREATE', 'UPDATE', 'DELETE'
  
  -- ANTES E DEPOIS
  old_values JSONB,              -- NULL se CREATE
  new_values JSONB,              -- NULL se DELETE
  
  -- QUEM E QUANDO
  actor_id UUID NOT NULL REFERENCES intellicare_core.usuarios(id),
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  request_id VARCHAR,            -- trace id do request
  
  -- PROVENANCE (FHIR Provenance Model)
  provenance JSONB NOT NULL DEFAULT jsonb_build_object(
    'entity', 'unknown',
    'agent', jsonb_build_object('type', 'Person'),
    'activity', 'unknown',
    'recorded', 'now()'
  ),
  
  CONSTRAINT check_operation CHECK (operation IN ('CREATE', 'UPDATE', 'DELETE'))
);

CREATE INDEX idx_audit_log_entity ON oswaldo_operacional.audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_timestamp ON oswaldo_operacional.audit_log(timestamp DESC);

-- Tabelas Analíticas (denormalizadas, histórico)
CREATE TABLE oswaldo_analitico.pacientes_hist (
  -- ID do paciente (não PK, pode ter múltiplos registros por período)
  paciente_id UUID NOT NULL,
  
  -- Dimensões temporais (para particionamento)
  ano_mes INT NOT NULL,  -- YYYYMM
  
  -- Dados desnormalizados para análise
  nome VARCHAR(255),
  data_nascimento DATE,
  
  -- Métricas agregadas
  status_durante_periodo VARCHAR,
  dias_em_status INT,
  numero_mudancas_status INT,
  
  -- Dimensão de coordenação
  coordenador_id UUID,
  coordenador_nome VARCHAR,
  
  -- Timestamps
  data_primeiro_evento DATE,
  data_ultimo_evento DATE,
  replicated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  
  -- Rastreabilidade
  provenance JSONB,  -- {source: 'oswaldo_operacional', pipeline_version: 'v1.0'}
  
  PRIMARY KEY (paciente_id, ano_mes)
);

-- Índice para queries de BI
CREATE INDEX idx_pacientes_hist_periodo ON oswaldo_analitico.pacientes_hist(ano_mes DESC);
CREATE INDEX idx_pacientes_hist_coordenador ON oswaldo_analitico.pacientes_hist(coordenador_id);

-- Tabela de Rastreamento de Consolidação
CREATE TABLE oswaldo_analitico.consolidation_meta (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  schema_name VARCHAR NOT NULL UNIQUE,  -- 'oswaldo_operacional'
  last_consolidated TIMESTAMP,
  last_event_id VARCHAR,  -- Redis stream ID
  
  -- Estatísticas da última consolidação
  events_processed INT,
  events_failed INT,
  duration_seconds FLOAT,
  
  status VARCHAR CHECK (status IN ('success', 'warning', 'error', 'running')),
  error_message TEXT,
  
  next_scheduled TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de Trilha de Auditoria Analítica
CREATE TABLE oswaldo_analitico.replication_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  source_schema VARCHAR NOT NULL,             -- 'oswaldo_operacional'
  operation VARCHAR NOT NULL,                  -- 'CREATE', 'UPDATE'
  entity_id UUID NOT NULL,
  entity_type VARCHAR NOT NULL,
  
  -- Rastreabilidade do evento
  source_event_id VARCHAR,                     -- Redis stream ID
  consumed_at TIMESTAMP NOT NULL DEFAULT NOW(),
  
  -- Quem replicou
  replicated_by VARCHAR,                       -- job name
  replicated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  
  -- Metadados
  provenance JSONB
);

CREATE INDEX idx_replication_audit_source ON oswaldo_analitico.replication_audit(source_schema, consumed_at DESC);
```

### Row-Level Security (RLS) Policies

```sql
-- Ativar RLS nas tabelas operacionais
ALTER TABLE oswaldo_operacional.pacientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE oswaldo_operacional.audit_log ENABLE ROW LEVEL SECURITY;

-- Policy para operacional: apenas seu próprio usuário/org pode ver
CREATE POLICY pacientes_operational_access ON oswaldo_operacional.pacientes
  USING (
    created_by = current_user_id()  -- função custom que pega do JWT
    OR created_by IN (
      SELECT user_id FROM intellicare_core.user_org_roles 
      WHERE org_id = current_user_org()
    )
  );

-- Policy para analítico: analytics_role pode read-only
ALTER TABLE oswaldo_analitico.pacientes_hist ENABLE ROW LEVEL SECURITY;

CREATE POLICY pacientes_analytics_read ON oswaldo_analitico.pacientes_hist
  USING (current_user_role() = 'analytics')
  WITH CHECK (FALSE);  -- Nega UPDATE/DELETE

-- Proteção: rejeitar escrita em analítico a qualquer usuário
CREATE POLICY pacientes_analytics_no_write ON oswaldo_analitico.pacientes_hist
  AS PERMISSIVE
  FOR UPDATE, DELETE
  USING (FALSE);
```

### Triggers para Event Publishing

```sql
-- Trigger que publica evento no Redis quando paciente é criado/atualizado
CREATE OR REPLACE FUNCTION oswaldo_operacional.publish_paciente_event()
RETURNS TRIGGER AS $$
DECLARE
  event_data JSONB;
  event_type VARCHAR;
BEGIN
  -- Determina tipo de evento
  event_type := CASE TG_OP
    WHEN 'INSERT' THEN 'paciente:created'
    WHEN 'UPDATE' THEN 'paciente:updated'
    WHEN 'DELETE' THEN 'paciente:deleted'
  END;
  
  -- Constrói payload do evento
  event_data := jsonb_build_object(
    'event_id', gen_random_uuid()::text,
    'event_type', event_type,
    'entity_id', COALESCE(NEW.id, OLD.id),
    'timestamp', to_jsonb(NOW()),
    'actor_id', COALESCE(NEW.updated_by, OLD.updated_by),
    'operation', TG_OP,
    'old_values', CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
    'new_values', CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END
  );
  
  -- Publica em Redis (chamada via pg_http ou via app trigger)
  -- SELECT pg_notify('oswaldo_events', event_data::text);
  
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER paciente_event_trigger
AFTER INSERT OR UPDATE OR DELETE ON oswaldo_operacional.pacientes
FOR EACH ROW
EXECUTE FUNCTION oswaldo_operacional.publish_paciente_event();

-- Trigger para registrar em audit_log
CREATE OR REPLACE FUNCTION oswaldo_operacional.log_paciente_audit()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO oswaldo_operacional.audit_log (
    entity_type, entity_id, operation,
    old_values, new_values,
    actor_id, request_id, provenance
  ) VALUES (
    'paciente',
    COALESCE(NEW.id, OLD.id),
    TG_OP,
    CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
    CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END,
    COALESCE(NEW.updated_by, OLD.updated_by),
    current_setting('application.request_id', true),
    jsonb_build_object(
      'actor', COALESCE(NEW.updated_by, OLD.updated_by),
      'operation', TG_OP,
      'timestamp', NOW(),
      'table', 'pacientes'
    )
  );
  
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER paciente_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON oswaldo_operacional.pacientes
FOR EACH ROW
EXECUTE FUNCTION oswaldo_operacional.log_paciente_audit();
```

---

## 🐍 Padrões de Código

### 1. Camada de Acesso a Dados (DAO)

```python
# intellicare_core/data_access/operational_dao.py

from typing import TypeVar, Generic, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Entity class

class OperationalDataAccess(Generic[T]):
    """
    DAO para operações em esquemas {modulo}_operacional.
    Garante que:
    - Apenas escrita em _operacional
    - Leitura com controle de acesso
    - Eventos são publicados automaticamente
    """
    
    def __init__(self, session: Session, entity_class: type[T], schema: str):
        """
        Args:
            session: SQLAlchemy session
            entity_class: ORM model class (e.g., Paciente)
            schema: 'oswaldo_operacional'
        """
        self.session = session
        self.entity_class = entity_class
        self.schema = schema
        self._validate_schema(schema)
    
    def _validate_schema(self, schema: str):
        """Valida que schema é operacional, nunca analítico."""
        if 'analitico' in schema:
            raise ValueError(f"OperationalDataAccess nunca acessa {schema}")
    
    def create(self, entity_data: dict, actor_id: str) -> T:
        """
        Cria entidade em esquema operacional.
        
        Args:
            entity_data: dicionário com dados
            actor_id: ID do usuário criando
        
        Returns:
            Entidade criada
        
        Raises:
            ValidationError, IntegrityError
        """
        try:
            entity = self.entity_class(**entity_data, created_by=actor_id, updated_by=actor_id)
            self.session.add(entity)
            self.session.flush()  # Garante ID antes de commit
            
            logger.info(f"Created {self.entity_class.__name__} {entity.id} by {actor_id}")
            return entity
            
        except IntegrityError as e:
            logger.error(f"Integrity error creating {self.entity_class.__name__}: {e}")
            self.session.rollback()
            raise
    
    def update(self, entity_id: str, updates: dict, actor_id: str) -> T:
        """
        Atualiza entidade.
        
        Args:
            entity_id: ID da entidade
            updates: campos a atualizar
            actor_id: ID do usuário atualizando
        
        Returns:
            Entidade atualizada
        """
        entity = self.session.get(self.entity_class, entity_id)
        if not entity:
            raise ValueError(f"{self.entity_class.__name__} {entity_id} not found")
        
        # Incrementa rowversion para otimistic locking
        entity.rowversion += 1
        entity.updated_by = actor_id
        entity.updated_at = datetime.utcnow()
        
        for key, value in updates.items():
            setattr(entity, key, value)
        
        self.session.flush()
        logger.info(f"Updated {self.entity_class.__name__} {entity_id} by {actor_id}")
        return entity
    
    def read(self, entity_id: str) -> Optional[T]:
        """Lê entidade com RLS aplicado."""
        return self.session.get(self.entity_class, entity_id)
    
    def list(self, filters: dict = None) -> List[T]:
        """Lista entidades com RLS aplicado."""
        query = select(self.entity_class)
        if filters:
            for key, value in filters.items():
                query = query.where(getattr(self.entity_class, key) == value)
        return self.session.execute(query).scalars().all()
    
    def delete(self, entity_id: str, actor_id: str) -> bool:
        """Delete lógico (soft delete)."""
        entity = self.session.get(self.entity_class, entity_id)
        if not entity:
            return False
        
        entity.valid_to = datetime.utcnow()
        entity.updated_by = actor_id
        self.session.flush()
        return True


# Uso em FastAPI
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

app = FastAPI()

@app.post("/patients", status_code=201)
async def create_patient(
    data: PacienteSchema,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cria paciente em oswaldo_operacional."""
    dao = OperationalDataAccess(
        session=session,
        entity_class=Paciente,
        schema='oswaldo_operacional'
    )
    
    paciente = dao.create(
        entity_data=data.dict(),
        actor_id=current_user.id
    )
    
    session.commit()  # Trigger publica evento em Redis
    return paciente
```

### 2. Event Publisher (Redis)

```python
# intellicare_core/events/event_publisher.py

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
    """
    Publica eventos de mudanças operacionais em Redis Streams.
    
    Padrão:
      Stream: {schema}:events:{entity_type}
      Exemplo: oswaldo_operacional:events:pacientes
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def publish(
        self,
        schema: str,
        entity_type: str,
        entity_id: str,
        operation: EventOperation,
        actor_id: str,
        old_values: dict = None,
        new_values: dict = None,
        metadata: dict = None
    ) -> str:
        """
        Publica evento.
        
        Args:
            schema: 'oswaldo_operacional'
            entity_type: 'paciente', 'tarefa'
            entity_id: UUID da entidade
            operation: CREATE, UPDATE, DELETE
            actor_id: Quem fez a mudança
            old_values: Valores antes (NULL se CREATE)
            new_values: Valores depois (NULL se DELETE)
            metadata: Dados adicionais
        
        Returns:
            Event ID (stream message ID)
        """
        stream_key = f"{schema}:events:{entity_type}"
        
        event = {
            "event_id": str(uuid4()),
            "schema": schema,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "operation": operation.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "actor_id": str(actor_id),
            "old_values": json.dumps(old_values) if old_values else None,
            "new_values": json.dumps(new_values) if new_values else None,
            "metadata": json.dumps(metadata) if metadata else None
        }
        
        # XADD publica em stream
        message_id = self.redis.xadd(stream_key, event)
        
        logging.info(f"Published event {event['event_id']} to {stream_key}")
        return message_id.decode() if isinstance(message_id, bytes) else message_id


# Integração com trigger do PostgreSQL (via application code)
publisher = EventPublisher(redis_client)

def publish_on_db_change(entity_class_name, entity_id, operation, old_values, new_values, actor_id):
    """Callback chamado após commit de transação."""
    publisher.publish(
        schema='oswaldo_operacional',
        entity_type=entity_class_name.lower() + 's',  # paciente → pacientes
        entity_id=entity_id,
        operation=EventOperation[operation],
        actor_id=actor_id,
        old_values=old_values,
        new_values=new_values
    )
```

### 3. Consolidation Service

```python
# consolidation_service/consolidator.py

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import redis
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class DataConsolidator:
    """
    Consome eventos de {modulo}_operacional e replica em {modulo}_analitico.
    
    Garantias:
    - Idempotência: Se rodado 2x, mesmo resultado
    - Unidirecionalidade: Apenas lê operacional, escreve analítico
    - Rastreabilidade: Cada replicação registra provenance
    """
    
    def __init__(self, redis_client: redis.Redis, db_session: Session, schema: str):
        self.redis = redis_client
        self.db = db_session
        self.schema = schema
        self.consumer_group = f"consolidators-{schema}"
        self._ensure_consumer_group()
    
    def _ensure_consumer_group(self):
        """Cria consumer group se não existir."""
        stream_key = f"{self.schema}:events:*"
        try:
            self.redis.xgroup_create(stream_key, self.consumer_group, id='0', mkstream=True)
        except redis.ResponseError:
            pass  # Grupo já existe
    
    def consolidate_batch(self, batch_size: int = 100) -> Dict[str, any]:
        """
        Consolida até `batch_size` eventos.
        
        Returns:
            {
              'events_processed': int,
              'events_failed': int,
              'duration_seconds': float,
              'status': 'success' | 'warning' | 'error'
            }
        """
        start_time = datetime.utcnow()
        events_processed = 0
        events_failed = 0
        failed_event_ids = []
        
        try:
            # Lê eventos do Redis
            stream_key = f"{self.schema}:events:*"
            events = self.redis.xreadgroup(
                self.consumer_group,
                self.consumer_group,
                {stream_key: '>'},  # '>' = novos eventos desde última leitura
                count=batch_size,
                block=0
            )
            
            for stream, messages in events or []:
                for message_id, event_data in messages:
                    try:
                        self._process_event(event_data)
                        self.redis.xack(stream, self.consumer_group, message_id)
                        events_processed += 1
                    except Exception as e:
                        logger.error(f"Failed to process event {message_id}: {e}")
                        events_failed += 1
                        failed_event_ids.append(message_id)
                        self._move_to_dlq(stream, message_id, event_data, str(e))
        
        except Exception as e:
            logger.error(f"Consolidation batch failed: {e}")
            status = 'error'
        else:
            status = 'warning' if events_failed > 0 else 'success'
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Registra meta de consolidação
        self._record_consolidation_meta(events_processed, events_failed, duration, status)
        
        return {
            'events_processed': events_processed,
            'events_failed': events_failed,
            'failed_event_ids': failed_event_ids,
            'duration_seconds': duration,
            'status': status
        }
    
    def _process_event(self, event_data: Dict):
        """Processa um evento individual."""
        entity_type = event_data.get(b'entity_type', b'').decode()
        entity_id = event_data.get(b'entity_id', b'').decode()
        operation = event_data.get(b'operation', b'').decode()
        new_values = event_data.get(b'new_values', b'{}').decode()
        
        # Replica em tabela histórica desnormalizada
        if operation == 'CREATE' or operation == 'UPDATE':
            self._replicate_to_hist_table(entity_type, entity_id, json.loads(new_values), event_data.get(b'event_id'))
        
        # Registra em audit trail
        self._record_replication_audit(entity_type, entity_id, operation, event_data)
    
    def _replicate_to_hist_table(self, entity_type: str, entity_id: str, values: dict, event_id: bytes):
        """Replica para tabela histórica desnormalizada."""
        table_name = f"{self.schema.replace('_operacional', '')}_analitico.{entity_type}_hist"
        
        # Insere/atualiza registro histórico
        query = text(f"""
            INSERT INTO {table_name} (
              {entity_type.rstrip('s')}_id,
              ano_mes,
              ...campos desnormalizados...,
              replicated_at,
              provenance
            ) VALUES (
              :entity_id,
              :ano_mes,
              ...,
              NOW(),
              :provenance
            )
            ON CONFLICT ({entity_type.rstrip('s')}_id, ano_mes) 
            DO UPDATE SET ...
        """)
        
        self.db.execute(query, {
            'entity_id': entity_id,
            'ano_mes': datetime.utcnow().strftime('%Y%m'),
            'provenance': json.dumps({
                'source': self.schema,
                'event_id': event_id.decode() if isinstance(event_id, bytes) else event_id,
                'pipeline_version': 'v1.0'
            })
        })
    
    def _record_consolidation_meta(self, processed, failed, duration, status):
        """Registra metadados da consolidação."""
        query = text(f"""
            UPDATE {self.schema.replace('_operacional', '')}_analitico.consolidation_meta
            SET
              last_consolidated = NOW(),
              events_processed = :processed,
              events_failed = :failed,
              duration_seconds = :duration,
              status = :status,
              next_scheduled = NOW() + INTERVAL '24 HOURS'
            WHERE schema_name = :schema
        """)
        
        self.db.execute(query, {
            'processed': processed,
            'failed': failed,
            'duration': duration,
            'status': status,
            'schema': self.schema
        })
        self.db.commit()
    
    def _move_to_dlq(self, stream, message_id, event_data, error):
        """Move evento falhado para Dead Letter Queue."""
        dlq_key = f"{self.schema}:dlq"
        self.redis.xadd(dlq_key, {
            'original_stream': stream.decode() if isinstance(stream, bytes) else stream,
            'original_message_id': message_id.decode() if isinstance(message_id, bytes) else message_id,
            'error': error,
            'failed_at': datetime.utcnow().isoformat(),
            'event_data': json.dumps({k.decode(): v.decode() if isinstance(v, bytes) else v for k, v in event_data.items()})
        })
```

---

## 📡 Event Publishing

### Padrão de Streamming

```
Redis Streams:

{modulo}_operacional:events:{entity_type}
  └─ Message: {event_id}-{seq}
      ├─ entity_id: "uuid-123"
      ├─ operation: "CREATE|UPDATE|DELETE"
      ├─ timestamp: "2026-02-11T10:00:00Z"
      ├─ actor_id: "user-abc"
      ├─ old_values: "{...}"
      ├─ new_values: "{...}"
      └─ metadata: "{...}"

Consumer Group: "consolidators-oswaldo"
  ├─ XREADGROUP (consome novos eventos)
  ├─ Processa 1 evento
  ├─ XACK (confirma consumo)
  └─ Retry na fila ainda não confirmada

Dead Letter Queue:

{modulo}:dlq
  └─ Message com evento que falhou
      ├─ original_stream
      ├─ original_message_id
      ├─ error: "Foreign key constraint..."
      └─ failed_at
```

---

## 🔒 Row-Level Security

Implementação no PostgreSQL:

1. **Objetos de Segurança**
   - `intellicare_app_role` - aplicação operacional
   - `intellicare_analytics_role` - analytics/BI
   - `intellicare_consolidation_role` - job de consolidação

2. **Policies**
   - Operacional: `app_role` pode READ/WRITE `_operacional`
   - Operacional: `app_role` é REJEITADO em `_analitico`
   - Analítico: `analytics_role` pode READ `_analitico`
   - Analítico: `analytics_role` é REJEITADO `UPDATE/DELETE`

3. **Verificação em App**
   ```python
   @app.post("/data")
   async def write_data(session: Session):
       # Sempre checa se DAO é do schema correto
       if 'analitico' in dao.schema:
           raise SecurityError("Cannot write to analytics schema")
   ```

---

## 📊 Monitoramento

### Métricas Prometheus

```python
from prometheus_client import Counter, Gauge, Histogram

# Eventos publicados
events_published = Counter(
    'events_published_total',
    'Total events published',
    ['schema', 'entity_type', 'operation']
)

# Eventos consolidados
events_consolidated = Counter(
    'events_consolidated_total',
    'Total events consolidated',
    ['schema', 'status']  # status = 'success', 'failed'
)

# Atraso de replicação
replication_lag = Gauge(
    'replication_lag_seconds',
    'Seconds behind production',
    ['schema']
)

# Duração de consolidação
consolidation_duration = Histogram(
    'consolidation_duration_seconds',
    'Consolidation job duration',
    ['schema']
)

# Violações de segurança
security_violations = Counter(
    'security_violations_total',
    'Attempts to violate schema separation',
    ['schema', 'type']  # type = 'write_to_analytics', 'cross_schema_join'
)
```

### Dashboards Grafana

```json
{
  "dashboard": {
    "title": "Separation Operacional/Analítico",
    "panels": [
      {
        "title": "Replication Lag by Module",
        "targets": [
          {
            "expr": "replication_lag_seconds"
          }
        ]
      },
      {
        "title": "Events Published vs Consolidated",
        "targets": [
          {
            "expr": "rate(events_published_total[5m])"
          },
          {
            "expr": "rate(events_consolidated_total[5m])"
          }
        ]
      },
      {
        "title": "Security Violations",
        "targets": [
          {
            "expr": "rate(security_violations_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### Alertas

```yaml
# prometheus-rules.yaml

groups:
  - name: separation_alerts
    rules:
      - alert: HighReplicationLag
        expr: replication_lag_seconds > 3600
        for: 5m
        annotations:
          summary: "Replication lag > 1 hour for {{ $labels.schema }}"
      
      - alert: ConsolidationJobFailed
        expr: events_consolidated{status="failed"} > 0
        for: 1m
        annotations:
          summary: "Consolidation failed for {{ $labels.schema }}"
      
      - alert: SecurityViolationDetected
        expr: rate(security_violations_total[1m]) > 0
        annotations:
          summary: "Unauthorized access attempt detected"
          severity: "critical"
```

---

## 🔄 Migração e Versionamento

### Alembic Migrations

```bash
# Criar migration
alembic revision --autogenerate -m "Add operational_analytic schemas"

# Migration file: alembic/versions/xxxxx_add_operational_analytic_schemas.py
def upgrade():
    # Criar schemas operacionais
    op.execute("CREATE SCHEMA oswaldo_operacional")
    op.execute("CREATE SCHEMA oswaldo_analitico")
    
    # Criar tabelas operacionais
    op.create_table(
        'pacientes',
        sa.Column('id', sa.UUID, primary_key=True),
        sa.Column('nome', sa.String(255), nullable=False),
        ...
        schema='oswaldo_operacional'
    )
    
    # Criar tabelas analíticas
    op.create_table(
        'pacientes_hist',
        sa.Column('paciente_id', sa.UUID),
        sa.Column('ano_mes', sa.Integer),
        ...
        schema='oswaldo_analitico'
    )

def downgrade():
    op.drop_schema('oswaldo_analitico')
    op.drop_schema('oswaldo_operacional')
```

---

## 💡 Exemplos de Código

### Exemplo 1: Criar Paciente (Operacional)

```python
from fastapi import FastAPI
from sqlalchemy.orm import Session
from intellicare_core.data_access import OperationalDataAccess
from intellicare_core.events import EventPublisher

@app.post("/patients")
async def create_patient(
    data: PacienteCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # DAO para operacional
    dao = OperationalDataAccess[Paciente](
        session=session,
        entity_class=Paciente,
        schema='oswaldo_operacional'
    )
    
    # Cria entidade
    paciente = dao.create(data.dict(), actor_id=current_user.id)
    
    # Commit: triggers PostgreSQL:
    # 1. Registra em audit_log
    # 2. Publica evento em Redis
    session.commit()
    
    return paciente
```

### Exemplo 2: Consolidar Dados (Analítico)

```python
import asyncio
from consolidation_service import DataConsolidator

async def consolidation_job():
    """Rodada diária de consolidação."""
    async with get_redis_client() as redis:
        async with get_session() as session:
            consolidator = DataConsolidator(
                redis_client=redis,
                db_session=session,
                schema='oswaldo_operacional'
            )
            
            result = consolidator.consolidate_batch(batch_size=1000)
            
            print(f"Processed {result['events_processed']} events")
            print(f"Failed {result['events_failed']} events")
            print(f"Duration: {result['duration_seconds']}s")

# Agendador
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    consolidation_job,
    'cron',
    hour=2,
    minute=0,
    id='consolidation_oswaldo'  # 2:00 AM UTC
)
scheduler.start()
```

### Exemplo 3: Consultar Histórico (Analítico)

```python
# BI Tool ou Data Scientist

@app.get("/analytics/patients-history")
async def get_patient_history(
    period: str,  # YYYYMM
    session: Session = Depends(get_db),
    current_user: User = Depends(auth_analytics_role)
):
    """Consulta histórico - NUNCA toca operacional."""
    query = select(PacientesHist).where(
        PacientesHist.ano_mes == int(period)
    ).order_by(PacientesHist.replicated_at.desc())
    
    return session.execute(query).scalars().all()
```

---

**Próximo Passo**: Leia `PLANO_PASSO_A_PASSO.md` para cronograma.
