# ESPECIFICAÇÃO TÉCNICA: SEPARAÇÃO OPERACIONAL/ANALÍTICO

## 📌 ID: DEV1-TEC-002
## 📅 Data: 12/02/2026
## 👤 Responsável Técnico: DEV1
## 📄 Baseado em: DEV1-FUNC-002
## ⏱️ Estimativa Técnica: 40 horas (5 dias úteis)
## ✅ Status: NÃO INICIADO

---

## 1. ANÁLISE TÉCNICA

### 1.1. Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA APLICAÇÃO                          │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  Apps            │         │  Apps            │          │
│  │  Operacionais    │         │  Analíticas      │          │
│  │  (Florence,      │         │  (BI, Reports,   │          │
│  │   Oswaldo, etc)  │         │   Dashboards)    │          │
│  └────────┬─────────┘         └────────┬─────────┘          │
└───────────┼────────────────────────────┼────────────────────┘
            │                            │
            │ READ/WRITE                 │ READ ONLY
            │ (Transacional)             │ (Analítico)
            ▼                            ▼
┌─────────────────────┐      ┌─────────────────────┐
│  PostgreSQL         │      │  PostgreSQL         │
│  OPERACIONAL        │      │  ANALÍTICO          │
│                     │      │                     │
│  - Dados vivos      │      │  - Dados históricos │
│  - Transações       │      │  - Agregados        │
│  - OLTP             │      │  - OLAP             │
│  - Identificados    │      │  - Anonimizados     │
└──────────┬──────────┘      └──────────▲──────────┘
           │                            │
           │         PIPELINE ETL       │
           └────────────────────────────┘
                  (Unidirecional)
                  (Nightly Batch)
```

### 1.2. Tecnologias Utilizadas

**Bancos de Dados**:
- `PostgreSQL 15+` - Ambos os domínios
- `pg_partman` - Particionamento automático (analítico)
- `TimescaleDB` - Time-series optimization (analítico)
- `pgcrypto` - Anonimização/pseudonimização

**Pipeline ETL**:
- `Apache Airflow` - Orquestração de workflows
- `dbt (Data Build Tool)` - Transformações SQL
- `Debezium` - Change Data Capture (CDC)
- `Apache Kafka` - Streaming (near-real-time)

**Monitoramento**:
- `Prometheus` - Métricas
- `Grafana` - Dashboards
- `pgBadger` - Análise de logs PostgreSQL
- `DataDog` - APM e alertas

**Segurança**:
- `HashiCorp Vault` - Gestão de secrets
- `pgAudit` - Auditoria PostgreSQL
- `Row Level Security (RLS)` - Controle granular

### 1.3. Design Patterns Aplicados

1. **CQRS (Command Query Responsibility Segregation)**
   - Justificativa: Separação natural entre operacional (commands) e analítico (queries)

2. **Event Sourcing** (parcial)
   - Justificativa: CDC captura eventos de mudança para pipeline

3. **Data Lake Pattern**
   - Justificativa: Analítico como repositório central de dados históricos

4. **Strangler Fig Pattern**
   - Justificativa: Migração gradual sem big bang

5. **Circuit Breaker**
   - Justificativa: Proteção do operacional contra falhas do pipeline

---

## 2. DESIGN DETALHADO

### 2.1. Estrutura de Bancos de Dados

#### 2.1.1. PostgreSQL Operacional

```sql
-- Database: intellicare_operacional
-- Purpose: Dados transacionais em tempo real
-- Retention: 7 anos (LGPD)
-- Backup: Diário + WAL continuous

-- Configurações otimizadas para OLTP
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '10MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';

-- Schemas por módulo
CREATE SCHEMA florence;    -- Análise clínica
CREATE SCHEMA oswaldo;     -- Doenças crônicas
CREATE SCHEMA wanda;       -- Orquestração
CREATE SCHEMA geralda;     -- Acompanhamento
CREATE SCHEMA zilda;       -- CNES/territorial
CREATE SCHEMA donabedian;  -- Qualidade

-- Metadados de domínio
CREATE TABLE _metadata.table_domain (
    schema_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    domain TEXT NOT NULL CHECK (domain IN ('operational', 'analytical')),
    pii_level TEXT CHECK (pii_level IN ('none', 'low', 'medium', 'high')),
    retention_days INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (schema_name, table_name)
);

-- Exemplo: Tabela operacional
CREATE TABLE florence.exames (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL,
    tipo_exame VARCHAR(100) NOT NULL,
    resultado JSONB,
    data_realizacao TIMESTAMPTZ NOT NULL,
    medico_solicitante VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pendente',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Registrar metadados
INSERT INTO _metadata.table_domain VALUES
('florence', 'exames', 'operational', 'high', 2555);  -- 7 anos
```

#### 2.1.2. PostgreSQL Analítico

```sql
-- Database: intellicare_analitico
-- Purpose: Dados históricos e agregados
-- Retention: Indefinido (dados anonimizados)
-- Backup: Semanal + incremental

-- Configurações otimizadas para OLAP
ALTER SYSTEM SET shared_buffers = '8GB';
ALTER SYSTEM SET effective_cache_size = '24GB';
ALTER SYSTEM SET maintenance_work_mem = '2GB';
ALTER SYSTEM SET work_mem = '50MB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;

-- Extension para time-series
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Schemas por domínio
CREATE SCHEMA florence_analytics;
CREATE SCHEMA oswaldo_analytics;
CREATE SCHEMA wanda_analytics;
CREATE SCHEMA geralda_analytics;
CREATE SCHEMA aggregates;  -- Agregados cross-módulo

-- Exemplo: Tabela analítica (anonimizada)
CREATE TABLE florence_analytics.exames_anon (
    id BIGSERIAL PRIMARY KEY,
    paciente_hash VARCHAR(64) NOT NULL,  -- SHA-256 do ID
    tipo_exame VARCHAR(100) NOT NULL,
    resultado_categoria VARCHAR(50),     -- Categorizado, não bruto
    data_realizacao DATE,                -- Apenas data, sem hora
    faixa_etaria VARCHAR(20),            -- Ex: "40-50"
    regiao_geografica VARCHAR(50),       -- Agregado por região
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Converter para hypertable (TimescaleDB)
SELECT create_hypertable(
    'florence_analytics.exames_anon',
    'data_realizacao',
    chunk_time_interval => INTERVAL '1 month'
);

-- Índices otimizados para análise
CREATE INDEX idx_exames_tipo_data 
ON florence_analytics.exames_anon (tipo_exame, data_realizacao DESC);

CREATE INDEX idx_exames_regiao_data 
ON florence_analytics.exames_anon (regiao_geografica, data_realizacao DESC);

-- Tabela de agregados diários
CREATE TABLE aggregates.exames_diarios (
    data DATE PRIMARY KEY,
    tipo_exame VARCHAR(100),
    regiao VARCHAR(50),
    total_exames INTEGER,
    media_resultado NUMERIC(10,2),
    percentil_95 NUMERIC(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.2. Pipeline ETL com Apache Airflow

#### 2.2.1. Estrutura do Projeto

```
intellicare-etl/
├── dags/
│   ├── florence_operational_to_analytical.py
│   ├── oswaldo_operational_to_analytical.py
│   ├── wanda_operational_to_analytical.py
│   └── aggregates_daily.py
├── plugins/
│   ├── anonymization.py
│   ├── validation.py
│   └── monitoring.py
├── sql/
│   ├── extract/
│   │   ├── florence_exames.sql
│   │   └── oswaldo_evolucoes.sql
│   ├── transform/
│   │   ├── anonymize_exames.sql
│   │   └── aggregate_exames.sql
│   └── load/
│       └── upsert_exames_anon.sql
├── config/
│   ├── connections.yaml
│   └── pipeline_config.yaml
└── tests/
    ├── test_anonymization.py
    └── test_pipeline.py
```

#### 2.2.2. DAG Principal (Airflow)

```python
# dags/florence_operational_to_analytical.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import hashlib

default_args = {
    'owner': 'intellicare-etl',
    'depends_on_past': True,
    'start_date': datetime(2026, 2, 1),
    'email': ['etl-alerts@intellicare.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'florence_operational_to_analytical',
    default_args=default_args,
    description='Pipeline diário: Florence Operacional → Analítico',
    schedule_interval='0 2 * * *',  # 2h da manhã
    catchup=False,
    max_active_runs=1,
    tags=['florence', 'etl', 'daily']
)

# Task 1: Extrair dados incrementais
extract_task = PostgresOperator(
    task_id='extract_exames_incremental',
    postgres_conn_id='intellicare_operacional',
    sql='sql/extract/florence_exames.sql',
    params={
        'start_date': '{{ ds }}',
        'end_date': '{{ tomorrow_ds }}'
    },
    dag=dag
)

# Task 2: Anonimizar dados
def anonymize_data(**context):
    """
    Anonimiza dados sensíveis:
    - Hash de IDs
    - Generalização de datas
    - Categorização de valores
    """
    from plugins.anonymization import anonymize_patient_data
    
    operational_hook = PostgresHook(postgres_conn_id='intellicare_operacional')
    analytical_hook = PostgresHook(postgres_conn_id='intellicare_analitico')
    
    # Buscar dados do staging
    records = operational_hook.get_records("""
        SELECT id, paciente_id, tipo_exame, resultado, 
               data_realizacao, medico_solicitante
        FROM _staging.exames_to_process
        WHERE processed = FALSE
    """)
    
    anonymized_records = []
    for record in records:
        anon_record = anonymize_patient_data(record)
        anonymized_records.append(anon_record)
    
    # Inserir no analítico
    analytical_hook.insert_rows(
        table='florence_analytics.exames_anon',
        rows=anonymized_records,
        target_fields=['paciente_hash', 'tipo_exame', 'resultado_categoria',
                      'data_realizacao', 'faixa_etaria', 'regiao_geografica']
    )
    
    # Marcar como processado
    operational_hook.run("""
        UPDATE _staging.exames_to_process 
        SET processed = TRUE, processed_at = NOW()
        WHERE processed = FALSE
    """)

anonymize_task = PythonOperator(
    task_id='anonymize_exames',
    python_callable=anonymize_data,
    provide_context=True,
    dag=dag
)

# Task 3: Validar qualidade dos dados
validate_task = PostgresOperator(
    task_id='validate_data_quality',
    postgres_conn_id='intellicare_analitico',
    sql="""
        -- Verificar completeness
        SELECT 
            COUNT(*) as total_records,
            COUNT(paciente_hash) as with_patient,
            COUNT(tipo_exame) as with_type,
            COUNT(data_realizacao) as with_date,
            (COUNT(paciente_hash)::FLOAT / COUNT(*)) * 100 as completeness_pct
        FROM florence_analytics.exames_anon
        WHERE DATE(created_at) = '{{ ds }}';
        
        -- Alertar se completeness < 99%
        DO $$
        DECLARE
            completeness NUMERIC;
        BEGIN
            SELECT (COUNT(paciente_hash)::FLOAT / COUNT(*)) * 100
            INTO completeness
            FROM florence_analytics.exames_anon
            WHERE DATE(created_at) = CURRENT_DATE;
            
            IF completeness < 99 THEN
                RAISE EXCEPTION 'Data quality check failed: completeness = %', completeness;
            END IF;
        END $$;
    """,
    dag=dag
)

# Task 4: Gerar agregados
aggregate_task = PostgresOperator(
    task_id='generate_daily_aggregates',
    postgres_conn_id='intellicare_analitico',
    sql='sql/transform/aggregate_exames.sql',
    params={'date': '{{ ds }}'},
    dag=dag
)

# Task 5: Atualizar métricas de monitoramento
def update_metrics(**context):
    """Atualiza métricas Prometheus"""
    from prometheus_client import Gauge, push_to_gateway
    
    analytical_hook = PostgresHook(postgres_conn_id='intellicare_analitico')
    
    # Contar registros processados
    result = analytical_hook.get_first("""
        SELECT COUNT(*) 
        FROM florence_analytics.exames_anon
        WHERE DATE(created_at) = %s
    """, parameters=(context['ds'],))
    
    records_processed = Gauge('etl_records_processed', 'Records processed today')
    records_processed.set(result[0])
    
    push_to_gateway('localhost:9091', job='florence_etl', registry=...)

metrics_task = PythonOperator(
    task_id='update_monitoring_metrics',
    python_callable=update_metrics,
    provide_context=True,
    dag=dag
)

# Definir dependências
extract_task >> anonymize_task >> validate_task >> aggregate_task >> metrics_task
```

### 2.3. Funções de Anonimização

```python
# plugins/anonymization.py
import hashlib
from datetime import datetime
from typing import Dict, Any

def anonymize_patient_data(record: tuple) -> Dict[str, Any]:
    """
    Anonimiza dados de paciente seguindo LGPD
    
    Técnicas:
    - Hashing: IDs → SHA-256
    - Generalização: Data completa → Apenas data
    - Categorização: Valores numéricos → Faixas
    - Supressão: Dados muito específicos
    """
    id, paciente_id, tipo_exame, resultado, data_realizacao, medico = record
    
    # Hash do ID do paciente (irreversível)
    paciente_hash = hashlib.sha256(
        f"{paciente_id}:salt_secreto".encode()
    ).hexdigest()
    
    # Generalizar data (remover hora)
    data_apenas = data_realizacao.date() if data_realizacao else None
    
    # Categorizar resultado (exemplo para glicemia)
    resultado_categoria = categorize_resultado(tipo_exame, resultado)
    
    # Calcular faixa etária (assumindo que temos data de nascimento)
    faixa_etaria = calculate_age_range(paciente_id)
    
    # Generalizar região geográfica
    regiao = get_patient_region(paciente_id)
    
    return {
        'paciente_hash': paciente_hash,
        'tipo_exame': tipo_exame,
        'resultado_categoria': resultado_categoria,
        'data_realizacao': data_apenas,
        'faixa_etaria': faixa_etaria,
        'regiao_geografica': regiao
    }

def categorize_resultado(tipo_exame: str, resultado: dict) -> str:
    """
    Categoriza resultados numéricos em faixas
    
    Exemplo: Glicemia
    - < 70: Hipoglicemia
    - 70-99: Normal
    - 100-125: Pré-diabetes
    - > 125: Diabetes
    """
    if tipo_exame == 'glicemia':
        valor = resultado.get('valor', 0)
        if valor < 70:
            return 'hipoglicemia'
        elif valor < 100:
            return 'normal'
        elif valor < 126:
            return 'pre_diabetes'
        else:
            return 'diabetes'
    
    # Outros tipos de exame...
    return 'unknown'

def calculate_age_range(paciente_id: int) -> str:
    """
    Calcula faixa etária do paciente
    
    Faixas: 0-18, 19-30, 31-40, 41-50, 51-60, 61-70, 71+
    """
    # Buscar data de nascimento (cache ou DB)
    birth_date = get_patient_birth_date(paciente_id)
    
    if not birth_date:
        return 'unknown'
    
    age = (datetime.now().date() - birth_date).days // 365
    
    if age <= 18:
        return '0-18'
    elif age <= 30:
        return '19-30'
    elif age <= 40:
        return '31-40'
    elif age <= 50:
        return '41-50'
    elif age <= 60:
        return '51-60'
    elif age <= 70:
        return '61-70'
    else:
        return '71+'

def get_patient_region(paciente_id: int) -> str:
    """
    Obtém região geográfica do paciente (generalizada)
    
    Níveis de generalização:
    - Cidade → Região metropolitana
    - Bairro → Zona (Norte, Sul, Leste, Oeste)
    """
    # Buscar endereço (cache ou DB)
    address = get_patient_address(paciente_id)
    
    if not address:
        return 'unknown'
    
    # Mapear cidade → região
    city_to_region = {
        'São Paulo': 'SP-Capital',
        'Guarulhos': 'SP-Grande-SP',
        'Campinas': 'SP-Interior',
        # ...
    }
    
    return city_to_region.get(address['city'], 'unknown')
```

### 2.4. Middleware de Validação de Domínio

```python
# src/intellicare_core/middleware/domain_validator.py
from fastapi import Request, HTTPException
from typing import Callable
import re
import logging

logger = logging.getLogger(__name__)

class DomainValidationMiddleware:
    """
    Middleware que valida se a aplicação está acessando
    o domínio correto (operacional vs analítico)
    """
    
    def __init__(self, app_domain: str):
        """
        Args:
            app_domain: 'operational' ou 'analytical'
        """
        self.app_domain = app_domain
        self.operational_tables = self._load_operational_tables()
        self.analytical_tables = self._load_analytical_tables()
    
    async def __call__(self, request: Request, call_next: Callable):
        # Interceptar queries SQL (se possível)
        # Alternativa: validar no nível do ORM
        
        response = await call_next(request)
        return response
    
    def validate_query(self, query: str) -> bool:
        """
        Valida se o query está acessando o domínio correto
        
        Regras:
        - App operacional: pode acessar apenas tabelas operacionais
        - App analítico: pode acessar apenas tabelas analíticas
        """
        # Extrair tabelas do query
        tables = self._extract_tables_from_query(query)
        
        for table in tables:
            if self.app_domain == 'operational':
                if table in self.analytical_tables:
                    logger.error(
                        f"VIOLATION: Operational app accessing analytical table: {table}"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Access denied: {table} is analytical data"
                    )
            
            elif self.app_domain == 'analytical':
                if table in self.operational_tables:
                    logger.error(
                        f"VIOLATION: Analytical app accessing operational table: {table}"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Access denied: {table} is operational data"
                    )
        
        return True
    
    def _extract_tables_from_query(self, query: str) -> list:
        """Extrai nomes de tabelas de um query SQL"""
        # Regex simplificado (melhorar com parser SQL real)
        pattern = r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z0-9_]*)'
        matches = re.findall(pattern, query, re.IGNORECASE)
        return matches
    
    def _load_operational_tables(self) -> set:
        """Carrega lista de tabelas operacionais do metadados"""
        # Buscar do banco _metadata.table_domain
        return {
            'florence.exames',
            'oswaldo.evolucoes',
            'wanda.decisoes',
            # ...
        }
    
    def _load_analytical_tables(self) -> set:
        """Carrega lista de tabelas analíticas do metadados"""
        return {
            'florence_analytics.exames_anon',
            'oswaldo_analytics.evolucoes_anon',
            'aggregates.exames_diarios',
            # ...
        }
```

---

## 3. CONFIGURAÇÃO DE CONEXÕES

### 3.1. SQLAlchemy (Python)

```python
# src/intellicare_core/database/connections.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    # Operacional
    OPERATIONAL_DB_HOST: str = "localhost"
    OPERATIONAL_DB_PORT: int = 5432
    OPERATIONAL_DB_NAME: str = "intellicare_operacional"
    OPERATIONAL_DB_USER: str
    OPERATIONAL_DB_PASSWORD: str
    
    # Analítico
    ANALYTICAL_DB_HOST: str = "localhost"
    ANALYTICAL_DB_PORT: int = 5433  # Porta diferente
    ANALYTICAL_DB_NAME: str = "intellicare_analitico"
    ANALYTICAL_DB_USER: str
    ANALYTICAL_DB_PASSWORD: str
    
    class Config:
        env_file = ".env.database"

settings = DatabaseSettings()

# Engine operacional (OLTP)
operational_engine = create_engine(
    f"postgresql://{settings.OPERATIONAL_DB_USER}:{settings.OPERATIONAL_DB_PASSWORD}"
    f"@{settings.OPERATIONAL_DB_HOST}:{settings.OPERATIONAL_DB_PORT}"
    f"/{settings.OPERATIONAL_DB_NAME}",
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=False
)

# Engine analítico (OLAP)
analytical_engine = create_engine(
    f"postgresql://{settings.ANALYTICAL_DB_USER}:{settings.ANALYTICAL_DB_PASSWORD}"
    f"@{settings.ANALYTICAL_DB_HOST}:{settings.ANALYTICAL_DB_PORT}"
    f"/{settings.ANALYTICAL_DB_NAME}",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False
)

# Sessions
OperationalSession = sessionmaker(bind=operational_engine)
AnalyticalSession = sessionmaker(bind=analytical_engine)

# FastAPI Dependencies
async def get_operational_db():
    """Dependency para acesso ao banco operacional"""
    db = OperationalSession()
    try:
        yield db
    finally:
        db.close()

async def get_analytical_db():
    """Dependency para acesso ao banco analítico"""
    db = AnalyticalSession()
    try:
        yield db
    finally:
        db.close()
```

### 3.2. Uso em Endpoints FastAPI

```python
# src/florence/api/routes/exames.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connections import get_operational_db, get_analytical_db

router = APIRouter()

# Endpoint operacional (transacional)
@router.post("/exames")
async def criar_exame(
    exame_data: ExameCreate,
    db: Session = Depends(get_operational_db)  # ← Banco operacional
):
    """
    Cria novo exame (operação transacional)
    
    **Domínio**: Operacional
    **Banco**: intellicare_operacional
    """
    exame = Exame(**exame_data.dict())
    db.add(exame)
    db.commit()
    return exame

# Endpoint analítico (consulta)
@router.get("/exames/estatisticas")
async def estatisticas_exames(
    tipo_exame: str,
    data_inicio: date,
    data_fim: date,
    db: Session = Depends(get_analytical_db)  # ← Banco analítico
):
    """
    Retorna estatísticas de exames (dados agregados)
    
    **Domínio**: Analítico
    **Banco**: intellicare_analitico
    """
    result = db.execute("""
        SELECT 
            data_realizacao,
            COUNT(*) as total,
            AVG(CASE resultado_categoria 
                WHEN 'normal' THEN 1 
                ELSE 0 
            END) as pct_normal
        FROM florence_analytics.exames_anon
        WHERE tipo_exame = :tipo
          AND data_realizacao BETWEEN :inicio AND :fim
        GROUP BY data_realizacao
        ORDER BY data_realizacao
    """, {
        'tipo': tipo_exame,
        'inicio': data_inicio,
        'fim': data_fim
    })
    
    return [dict(row) for row in result]
```

---

## 4. MONITORAMENTO E ALERTAS

### 4.1. Métricas Prometheus

```python
# src/intellicare_core/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Métricas de acesso por domínio
operational_queries = Counter(
    'intellicare_operational_queries_total',
    'Total queries no banco operacional',
    ['module', 'table']
)

analytical_queries = Counter(
    'intellicare_analytical_queries_total',
    'Total queries no banco analítico',
    ['module', 'table']
)

# Violações de domínio
domain_violations = Counter(
    'intellicare_domain_violations_total',
    'Total de violações de acesso entre domínios',
    ['app_domain', 'accessed_domain', 'table']
)

# Latência de queries
query_latency = Histogram(
    'intellicare_query_duration_seconds',
    'Latência de queries',
    ['domain', 'operation']
)

# Pipeline ETL
etl_records_processed = Gauge(
    'intellicare_etl_records_processed',
    'Registros processados no ETL',
    ['module', 'date']
)

etl_duration = Histogram(
    'intellicare_etl_duration_seconds',
    'Duração do pipeline ETL',
    ['module', 'stage']
)

etl_failures = Counter(
    'intellicare_etl_failures_total',
    'Falhas no pipeline ETL',
    ['module', 'stage', 'error_type']
)
```

### 4.2. Dashboard Grafana

```yaml
# grafana/dashboards/domain_separation.json
{
  "dashboard": {
    "title": "IntelliCare - Separação Operacional/Analítico",
    "panels": [
      {
        "title": "Queries por Domínio",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(intellicare_operational_queries_total[5m])",
            "legendFormat": "Operacional - {{module}}"
          },
          {
            "expr": "rate(intellicare_analytical_queries_total[5m])",
            "legendFormat": "Analítico - {{module}}"
          }
        ]
      },
      {
        "title": "Violações de Domínio",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(intellicare_domain_violations_total)",
            "legendFormat": "Total Violações"
          }
        ],
        "thresholds": [
          {"value": 0, "color": "green"},
          {"value": 1, "color": "red"}
        ]
      },
      {
        "title": "Latência de Queries (p95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(intellicare_query_duration_seconds_bucket{domain=\"operational\"}[5m]))",
            "legendFormat": "Operacional p95"
          },
          {
            "expr": "histogram_quantile(0.95, rate(intellicare_query_duration_seconds_bucket{domain=\"analytical\"}[5m]))",
            "legendFormat": "Analítico p95"
          }
        ]
      },
      {
        "title": "Pipeline ETL - Status",
        "type": "table",
        "targets": [
          {
            "expr": "intellicare_etl_records_processed",
            "format": "table"
          }
        ]
      }
    ]
  }
}
```

---

## 5. TESTES

### 5.1. Testes de Validação de Domínio

```python
# tests/test_domain_validation.py
import pytest
from fastapi.testclient import TestClient
from src.florence.api.main import app

client = TestClient(app)

def test_operational_endpoint_uses_operational_db():
    """Verifica que endpoint operacional usa banco operacional"""
    response = client.post("/exames", json={
        "paciente_id": 123,
        "tipo_exame": "glicemia",
        "resultado": {"valor": 95}
    })
    
    assert response.status_code == 201
    # Verificar que foi no banco operacional (via logs ou metrics)

def test_analytical_endpoint_uses_analytical_db():
    """Verifica que endpoint analítico usa banco analítico"""
    response = client.get("/exames/estatisticas", params={
        "tipo_exame": "glicemia",
        "data_inicio": "2026-01-01",
        "data_fim": "2026-01-31"
    })
    
    assert response.status_code == 200
    # Verificar que foi no banco analítico

def test_operational_app_cannot_access_analytical_data():
    """Verifica que app operacional não acessa dados analíticos"""
    # Tentar forçar acesso a tabela analítica
    with pytest.raises(HTTPException) as exc_info:
        # Simular query direto
        db.execute("SELECT * FROM florence_analytics.exames_anon")
    
    assert exc_info.value.status_code == 403
    assert "analytical data" in exc_info.value.detail

def test_analytical_app_cannot_access_operational_data():
    """Verifica que app analítico não acessa dados operacionais"""
    with pytest.raises(HTTPException) as exc_info:
        db.execute("SELECT * FROM florence.exames")
    
    assert exc_info.value.status_code == 403
    assert "operational data" in exc_info.value.detail
```

### 5.2. Testes de Anonimização

```python
# tests/test_anonymization.py
import pytest
from plugins.anonymization import anonymize_patient_data
from datetime import datetime

def test_patient_id_is_hashed():
    """Verifica que ID do paciente é hasheado"""
    record = (1, 12345, 'glicemia', {'valor': 95}, datetime.now(), 'Dr. Silva')
    
    result = anonymize_patient_data(record)
    
    assert 'paciente_hash' in result
    assert result['paciente_hash'] != '12345'
    assert len(result['paciente_hash']) == 64  # SHA-256

def test_date_is_generalized():
    """Verifica que data/hora é generalizada para apenas data"""
    record = (1, 12345, 'glicemia', {'valor': 95}, 
              datetime(2026, 2, 12, 14, 30, 0), 'Dr. Silva')
    
    result = anonymize_patient_data(record)
    
    assert result['data_realizacao'].hour == 0
    assert result['data_realizacao'].minute == 0

def test_resultado_is_categorized():
    """Verifica que resultado numérico é categorizado"""
    record = (1, 12345, 'glicemia', {'valor': 95}, datetime.now(), 'Dr. Silva')
    
    result = anonymize_patient_data(record)
    
    assert result['resultado_categoria'] == 'normal'
    assert 'valor' not in result  # Valor bruto não deve estar presente

def test_anonymization_is_deterministic():
    """Verifica que anonimização é determinística (mesmo input = mesmo output)"""
    record = (1, 12345, 'glicemia', {'valor': 95}, datetime.now(), 'Dr. Silva')
    
    result1 = anonymize_patient_data(record)
    result2 = anonymize_patient_data(record)
    
    assert result1['paciente_hash'] == result2['paciente_hash']
```

### 5.3. Testes de Pipeline ETL

```python
# tests/test_etl_pipeline.py
import pytest
from airflow.models import DagBag

def test_dag_loads_without_errors():
    """Verifica que DAG carrega sem erros"""
    dag_bag = DagBag(dag_folder='dags/', include_examples=False)
    
    assert len(dag_bag.import_errors) == 0

def test_florence_dag_has_correct_tasks():
    """Verifica que DAG do Florence tem todas as tasks"""
    dag_bag = DagBag(dag_folder='dags/')
    dag = dag_bag.get_dag('florence_operational_to_analytical')
    
    expected_tasks = [
        'extract_exames_incremental',
        'anonymize_exames',
        'validate_data_quality',
        'generate_daily_aggregates',
        'update_monitoring_metrics'
    ]
    
    actual_tasks = [task.task_id for task in dag.tasks]
    
    assert set(expected_tasks) == set(actual_tasks)

def test_dag_dependencies_are_correct():
    """Verifica que dependências entre tasks estão corretas"""
    dag_bag = DagBag(dag_folder='dags/')
    dag = dag_bag.get_dag('florence_operational_to_analytical')
    
    extract_task = dag.get_task('extract_exames_incremental')
    anonymize_task = dag.get_task('anonymize_exames')
    
    assert anonymize_task in extract_task.downstream_list
```

---

## 6. PLANO DE IMPLEMENTAÇÃO

### 6.1. Fase 1: Infraestrutura (1 semana)

**Dia 1-2: Setup de Bancos**
- [ ] Criar banco `intellicare_operacional`
- [ ] Criar banco `intellicare_analitico`
- [ ] Configurar TimescaleDB no analítico
- [ ] Criar schemas por módulo
- [ ] Configurar backup/restore

**Dia 3-4: Migração de Dados**
- [ ] Identificar tabelas operacionais vs analíticas
- [ ] Criar tabela de metadados `_metadata.table_domain`
- [ ] Migrar dados existentes
- [ ] Validar integridade

**Dia 5: Configuração de Conexões**
- [ ] Configurar SQLAlchemy engines
- [ ] Criar dependencies FastAPI
- [ ] Testar conexões
- [ ] Documentar

### 6.2. Fase 2: Pipeline ETL (1 semana)

**Dia 6-7: Setup Airflow**
- [ ] Instalar Apache Airflow
- [ ] Configurar conexões
- [ ] Criar estrutura de projeto
- [ ] Testar DAG básico

**Dia 8-9: Implementar DAGs**
- [ ] DAG Florence
- [ ] DAG Oswaldo
- [ ] DAG Wanda
- [ ] DAG Geralda

**Dia 10: Anonimização**
- [ ] Implementar funções de anonimização
- [ ] Testar com dados reais
- [ ] Validar conformidade LGPD

### 6.3. Fase 3: Validação e Monitoramento (3 dias)

**Dia 11: Middleware de Validação**
- [ ] Implementar DomainValidationMiddleware
- [ ] Integrar em todos os módulos
- [ ] Testar violações

**Dia 12: Monitoramento**
- [ ] Configurar métricas Prometheus
- [ ] Criar dashboards Grafana
- [ ] Configurar alertas

**Dia 13: Testes e Documentação**
- [ ] Testes de integração
- [ ] Testes de performance
- [ ] Documentação completa

---

## 7. RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Pipeline ETL lento (> 4h) | Média | Alto | Otimizar queries, paralelizar, usar CDC |
| Dados anonimizados reidentificáveis | Baixa | Crítico | Auditoria por especialista LGPD, testes |
| Performance operacional degradada | Média | Alto | Monitoramento contínuo, circuit breaker |
| Falha no pipeline | Média | Médio | Retry automático, alertas, rollback |

---

## 8. PRÓXIMOS PASSOS

1. **Aprovação desta especificação técnica**
2. **Setup de infraestrutura** (bancos separados)
3. **Implementação do pipeline ETL**
4. **Testes e validação**
5. **Go-live faseado por módulo**

---

## 9. APROVAÇÕES

- [ ] **Aprovação Técnica (DEV1)**: _________________ Data: __/__/____
- [ ] **Aprovação Arquiteto de Dados**: _________________ Data: __/__/____
- [ ] **Aprovação DPO (LGPD)**: _________________ Data: __/__/____
- [ ] **Aprovação Product Owner**: _________________ Data: __/__/____

---

**STATUS**: 📄 ESPECIFICAÇÃO TÉCNICA PRONTA PARA REVISÃO

**Última Atualização**: 12/02/2026  
**Versão**: 1.0  
**Autor**: DEV1

