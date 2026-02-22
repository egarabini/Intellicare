# PLANO TÉCNICO: MÓDULO OSWALDO - IMPLEMENTAÇÃO

**Data**: 12 FEV 2026
**Responsável**: DEV2
**Prazo**: 7 dias (56 horas)
**Data Conclusão Estimada**: 19 FEV 2026

---

## ÍNDICE

1. [Arquitetura Geral](#1-arquitetura-geral)
2. [Fases de Implementação](#2-fases-de-implementação)
3. [Sprint Detalhado (Dias 1-7)](#3-sprint-detalhado-dias-1-7)
4. [Estrutura de Arquivos](#4-estrutura-de-arquivos)
5. [Checklist de Implementação](#5-checklist-de-implementação)
6. [Dependências de Aprovação](#6-dependências-de-aprovação)
7. [Plano de Testes](#7-plano-de-testes)

---

## 1. ARQUITETURA GERAL

### 1.1. Estrutura do Projeto

```
intellicare-oswaldo/
├── src/oswaldo/
│   ├── __init__.py
│   ├── api/
│   │   ├── main.py                 ← FastAPI app
│   │   ├── endpoints/
│   │   │   ├── condicoes.py        ← CRUD condições
│   │   │   ├── acompanhamentos.py  ← Consultas/Follow-up
│   │   │   ├── alertas.py          ← Query alertas
│   │   │   └── timeline.py         ← Histórico paciente
│   │   └── schemas/
│   │       ├── condicoes.json      ← Pydantic models
│   │       ├── acompanhamentos.json
│   │       └── alertas.json
│   ├── services/
│   │   ├── diagnostico_service.py    (200 linhas)
│   │   ├── classificacao_service.py  (150 linhas)
│   │   ├── plano_cuidado_service.py  (250 linhas)
│   │   ├── acompanhamento_service.py (150 linhas)
│   │   └── alerta_service.py         (150 linhas)
│   ├── models/
│   │   └── oswaldo_models.py         (400 linhas SQLAlchemy)
│   ├── integrations/
│   │   ├── florence_consumer.py      (120 linhas)
│   │   └── oswaldo_publisher.py      (80 linhas)
│   ├── algorithms/
│   │   ├── classificadores.py        (100 linhas)
│   │   ├── diagnosticos.py           (100 linhas)
│   │   └── validadores.py            (80 linhas)
│   └── metrics.py                    (100 linhas Prometheus)
│
├── tests/
│   ├── test_diagnostico_service.py   (150 linhas)
│   ├── test_classificacao.py         (150 linhas)
│   ├── test_plano_cuidado.py         (150 linhas)
│   ├── test_acompanhamento.py        (100 linhas)
│   ├── test_alertas.py               (100 linhas)
│   ├── test_integrations.py          (150 linhas)
│   └── test_api.py                   (200 linhas)
│
├── alembic/
│   └── versions/
│       └── 001_create_oswaldo_tables.py (150 linhas)
│
├── monitoring/
│   └── oswaldo-alerts.yml            (100 linhas)
│
├── run_api_8002.py                   (20 linhas)
├── requirements.txt
└── README.md
```

**TOTAL**: ~3,000 linhas de código

### 1.2. Localização no Projeto INTELLICARE

```
MODULARIZACAO/
├── intellicare-florence/        ← JÁ PRONTO ✅
├── intellicare-oswaldo/         ← NOVO - DEV2 IMPLEMENTA
│   └── (estrutura acima)
├── intellicare-core/
└── docker-compose.yml           ← Atualizar para incluir oswaldo:8002
```

### 1.3. Stack Técnico

```
┌─────────────────────────────────────────┐
│  FastAPI (Python 3.11)                  │ Port: 8002
│  + Uvicorn + Pydantic v2                │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  SQLAlchemy 2.0 ORM + Alembic           │
│  + PostgreSQL 14+                       │
│  Database: intellicare_oswaldo          │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  RabbitMQ Consumer (pika)               │
│  Inscrever em: florence.exame.#         │
│  3 queues: critico, novo, sugestao      │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│  Prometheus + Grafana (reutilizar)      │
│  Logs: JSON + filesystem + syslog       │
└─────────────────────────────────────────┘
```

---

## 2. FASES DE IMPLEMENTAÇÃO

### Fase 1: Core Infrastructure (Dias 1-2, 16 horas)

**Objetivo**: Banco de dados + modelos + APIs básicas funcionando

```
Dia 1 (8h):
├── 1.1 Setup projeto (30min)
│   └── init repo, venv, dependências
├── 1.2 Modelos SQLAlchemy (2h30)
│   └── CondicaoCronica, Estadiamento, PlanoCuidado, Acompanhamento, Alerta
├── 1.3 Schemas Pydantic (1h)
│   └── Request/Response models
├── 1.4 Alembic migrations (1h)
│   └── Criar tabelas em dev DB
├── 1.5 FastAPI app scaffold (1h)
│   └── main.py com CORS, error handlers, logging
└── 1.6 Testes básicos de modelo (30min)
    └── pytest fixtures para dados dummy

Dia 2 (8h):
├── 2.1 CRUD endpoints Condicoes (3h)
│   ├── GET /api/v1/oswaldo/paciente/{cpf}/condicoes
│   ├── POST /api/v1/oswaldo/condicoes
│   ├── GET /api/v1/oswaldo/condicoes/{id}
│   ├── PUT /api/v1/oswaldo/condicoes/{id}
│   └── DELETE (soft-delete)
├── 2.2 Endpoints Acompanhamentos (2h)
│   ├── POST /api/v1/oswaldo/acompanhamentos
│   ├── GET /api/v1/oswaldo/paciente/{cpf}/acompanhamentos
│   └── GET /api/v1/oswaldo/condicoes/{id}/acompanhamentos
├── 2.3 API documentation Swagger (1h)
│   └── Auto-generate from Pydantic
├── 2.4 Testes de API (2h)
│   └── 30+ testes para endpoints CRUD
└── Status: APIs respondendo, testes 80%+ passing
```

### Fase 2: Integração Florence (Dias 3-4, 16 horas)

**Objetivo**: Oswaldo recebendo eventos do Florence e reagindo

```
Dia 3 (8h):
├── 3.1 Consumer RabbitMQ (2h)
│   ├── Conexão e setup queues
│   ├── Handlers para 3 event types
│   └── Error handling + retry logic
├── 3.2 Publisher Oswaldo (1h)
│   └── Publicar eventos de diagnóstico/alerta
├── 3.3 Event schemas validation (1h)
│   └── Pydantic models para validar events
├── 3.4 Integration tests (2h)
│   ├── Mock producer Florence
│   ├── Assert consumer processa corretamente
│   └── E2E: event → diagnóstico em DB
├── 3.5 Monitoramento de eventos (1h)
│   └── Prometheus metrics para consumer
└── Status: Consumer funcionando, 80% testes passing

Dia 4 (8h):
├── 4.1 Query para reclassificar (1.5h)
│   └── SELECT condições + calcular nova classe + comparar
├── 4.2 Automat reclassificação ao novo exame (2h)
│   ├── Logic: se mudou classe → save novo Estadiamento
│   ├── Se piora → gerar Alerta
│   └── Update PlanoCuidado se necessário
├── 4.3 Orchestração de fluxos (2h)
│   ├── ServicoService chamando ClassificacaoService
│   ├── Transações + rollback
│   └── Logging detalhado
├── 4.4 Testes de fluxo integrado (2h)
│   └── 20+ testes de cenários clínicos
└── Status: Integração Florence ativa, fluxos funcionando
```

### Fase 3: Algoritmos Clínicos (Dia 5, 8 horas)

**Objetivo**: Lógica de diagnóstico e classificação clínica

```
Dia 5 (8h):
├── 5.1 Classificadores (3h)
│   ├── classificar_has(sys, dia) → NORMAL/ESTAGIO_1/2/3
│   ├── classificar_drc(tfge) → G1-G5
│   ├── classificar_diabetes(hba1c) → BEM_CONTROLADO/MODERADO/MAL/CRITICO
│   └── + 2-3 outras (Lipíd, TB, Asma)
├── 5.2 Diagnóstico automático (2h)
│   ├── sugerir_diagnostico(exame_critico) → [(cid10, score)]
│   ├── Análise padrão: "glicemia > 300 && hba1c > 8" → diabetes
│   └── Match contra regras definidas
├── 5.3 Validadores clínicos (1.5h)
│   ├── validar_coerencia(parametros) → bool
│   ├── Exemplo: "Linfocitos + Neutros + Monos + Eos + Basos = 100?"
│   └── Detectar impossibilidades fisiológicas
├── 5.4 Testes algoritmos (1.5h)
│   └── 30+ casos de teste com dados reais de diretrizes
└── Status: Algoritmos clinicamente validados, testes 100%
```

### Fase 4: Fluxos Avançados (Dia 6, 8 horas)

**Objetivo**: Planos de cuidado, alertas, acompanhamento

```
Dia 6 (8h):
├── 6.1 Planos de Cuidado (2.5h)
│   ├── criar_plano() gerado automaticamente
│   ├── Objetivos SMART baseado em estágio
│   ├── Intervenções (farmac. + não-farmac.)
│   └── Medicamentos recomendados por CID/estágio
├── 6.2 Service Acompanhamento (2h)
│   ├── criar_acompanhamento() com vitais
│   ├── avaliar_adesao() ao plano
│   ├── agendar_proximo() baseado em estágio
│   └── Reclassificar após consulta
├── 6.3 Alertas Clínicos (2h)
│   ├── gerar_alerta() com severidade
│   ├── Detectar: descontrole, piora progressiva, evento adverso
│   ├── Cálculo de severidade (lógica)
│   └── Queue para notificação
├── 6.4 Testes fluxos (1.5h)
│   └── 25+ testes de cenários clínicos realistas
└── Status: Fluxos completos funcionando
```

### Fase 5: Polimento (Dia 7, 8 horas)

**Objetivo**: Testes, documentação, boas práticas

```
Dia 7 (8h):
├── 7.1 Testes cobertura (2h)
│   ├── pytest coverage report
│   ├── Atingir 90%+ de cobertura
│   └── Adicionar casos edge/erro
├── 7.2 Performance + Load testing (1.5h)
│   ├── Verificar p99 latência < 100ms
│   ├── Testar com 1000+ acompanhamentos
│   └── Otimizar queries N+1
├── 7.3 Documentação (2h)
│   ├── README.md com setup + uso
│   ├── API docs Swagger
│   ├── Runbook de erros
│   └── Treinamento clínico resumido
├── 7.4 Cleanup + deployment ready (1h)
│   ├── Remover TODOs e debug code
│   ├── .env.example com variáveis
│   ├── docker-compose atualizado
│   └── GitHub Actions pipeline ready
├── 7.5 Apresentação + validação (1h)
│   └── Demonstração para especialista
└── Status: ✅ PRODUCTION READY
```

---

## 3. SPRINT DETALHADO (Dias 1-7)

### DIA 1: Setup + Modelos (8 horas)

#### 3.1.1 Setup Projeto (30 min - 09:00-09:30)

```bash
# Criar estrutura
mkdir -p /opt/intellicare-oswaldo/src/oswaldo/{api,services,models,integrations,algorithms}
cd /opt/intellicare-oswaldo

# Virtual env
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

# Dependências base
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings
pip install psycopg2-binary alembic
pip install pika pytest pytest-cov
pip install python-dateutil pytz

# Git
git init
git config user.name "DEV2" user.email "dev2@intellicare.com"
git add .gitignore *.py
```

**Entrega**: Projeto estruturado com venv ativo

#### 3.1.2 Modelos SQLAlchemy (2h30 - 09:30-12:00)

**Arquivo**: `src/oswaldo/models/oswaldo_models.py` (400 linhas)

```python
from sqlalchemy import Column, Integer, String, Date, DateTime, Float, JSON, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

# ========================================================================
# 1. CondicaoCronica
# ========================================================================
class CondicaoCronica(Base):
    __tablename__ = "condicao_cronica"
    
    id = Column(Integer, primary_key=True)
    paciente_cpf = Column(String(64), nullable=False, index=True)  # Hash do CPF
    cid10 = Column(String(10), nullable=False)  # I10 (HAS), E11 (Diabetes), etc
    
    # Dados Diagnóstico
    data_diagnostico = Column(Date, nullable=False)
    medico_diagnosticador = Column(String(100), nullable=True)
    confirmacao_exames = Column(Boolean, default=False)
    
    # Status e Gravidade
    status = Column(String(50), index=True)  # PENDENTE_VALIDACAO, CONFIRMADO, SUSPENSO, ENCERRADO
    gravidade_inicial = Column(String(20))  # LEVE, MODERADA, GRAVE
    
    # Metadados
    criado_em = Column(DateTime, server_default=datetime.utcnow)
    atualizado_em = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relacionamentos
    estadiamentos = relationship("Estadiamento", back_populates="condicao")
    acompanhamentos = relationship("Acompanhamento", back_populates="condicao")
    plano_cuidado = relationship("PlanoCuidado", back_populates="condicao", uselist=False)
    alertas = relationship("Alerta", back_populates="condicao")

# ========================================================================
# 2. Estadiamento
# ========================================================================
class Estadiamento(Base):
    __tablename__ = "estadiamento"
    
    id = Column(Integer, primary_key=True)
    condicao_cronica_id = Column(Integer, ForeignKey("condicao_cronica.id"), nullable=False)
    
    # Classificação
    sistema_classificacao = Column(String(50))  # NYHA, KDIGO, ABCD, SBC, etc
    estagio = Column(String(10), nullable=False)  # I, II, III, IV, G1-G5
    
    # Data e Suporte
    data_classificacao = Column(DateTime, server_default=datetime.utcnow)
    criterios = Column(JSON, nullable=True)  # {"PA_sys": 160, "PA_dia": 100, ...}
    exames_suporte = Column(JSON, nullable=True)  # [{"id": 123, "tipo": "PA"}]
    
    # Relacionamento
    condicao = relationship("CondicaoCronica", back_populates="estadiamentos")

# ========================================================================
# 3. PlanoCuidado
# ========================================================================
class PlanoCuidado(Base):
    __tablename__ = "plano_cuidado"
    
    id = Column(Integer, primary_key=True)
    condicao_cronica_id = Column(Integer, ForeignKey("condicao_cronica.id"), nullable=False, unique=True)
    
    # Validade
    data_inicio = Column(Date, nullable=False)
    data_revisao = Column(Date, nullable=True)  # Próxima revisão
    
    # Conteúdo
    status = Column(String(50))  # ATIVO, REVISADO, SUSPENSO, ENCERRADO
    objetivos = Column(JSON, nullable=False)  # [{objetivo: "reduzir PA < 140/90", prazo: "3 meses"}]
    intervencoes = Column(JSON, nullable=False)  # [{tipo: "medicamento", descricao: "Losartan"}]
    medicamentos = Column(JSON, nullable=False)  # [{nome: "Losartan", dose: 50, unidade: "mg"}]
    educacao_saude = Column(JSON, nullable=True)  # [{tema: "Sal em dieta", data_inicio: ...}]
    
    # Relacionamento
    condicao = relationship("CondicaoCronica", back_populates="plano_cuidado")

# ========================================================================
# 4. Acompanhamento
# ========================================================================
class Acompanhamento(Base):
    __tablename__ = "acompanhamento"
    
    id = Column(Integer, primary_key=True)
    paciente_cpf = Column(String(64), nullable=False, index=True)
    condicao_cronica_id = Column(Integer, ForeignKey("condicao_cronica.id"), nullable=False)
    
    # Consulta
    data_acompanhamento = Column(DateTime, nullable=False)
    medico_id = Column(String(50), nullable=False)
    local_consulta = Column(String(100), nullable=True)
    
    # Vitais e Biométricos
    pressao_arterial = Column(String(20), nullable=True)  # "160/100"
    peso_kg = Column(Float, nullable=True)
    glicemia = Column(Float, nullable=True)
    temperatura = Column(Float, nullable=True)
    
    # Clínico
    adesao_medicamentos = Column(String(20), nullable=True)  # BOA, REGULAR, RUIM
    observacoes = Column(JSON, nullable=True)
    medicamentos_vigentes = Column(JSON, nullable=True)
    proxima_consulta = Column(Date, nullable=True)
    
    # Relacionamento
    condicao = relationship("CondicaoCronica", back_populates="acompanhamentos")

# ========================================================================
# 5. Alerta
# ========================================================================
class Alerta(Base):
    __tablename__ = "alerta"
    
    id = Column(Integer, primary_key=True)
    paciente_cpf = Column(String(64), nullable=False, index=True)
    condicao_cronica_id = Column(Integer, ForeignKey("condicao_cronica.id"), nullable=False)
    
    # Tipo e Severidade
    tipo_alerta = Column(String(50))  # DESCONTROLE, PIORA_PROGRESSIVA, ALERGICO, OUTRO
    severidade = Column(String(20), index=True)  # BAIXA, MEDIA, ALTA, CRITICA
    
    # Conteúdo
    descricao = Column(String(256), nullable=False)
    dados_alerta = Column(JSON, nullable=True)  # {"parametro": "glicemia", "valor": 450}
    
    # Status
    status = Column(String(20), index=True)  # NOVO, ATRIBUIDO, RESOLVIDO
    data_criacao = Column(DateTime, server_default=datetime.utcnow)
    data_resolvido = Column(DateTime, nullable=True)
    medico_atribuido = Column(String(50), nullable=True)
    
    # Relacionamento
    condicao = relationship("CondicaoCronica", back_populates="alertas")
```

**Entrega**: 400 linhas de modelos testados

#### 3.1.3 Schemas Pydantic (1h - 12:00-13:00)

**Arquivo**: `src/oswaldo/api/schemas/condicoes.json` (100 linhas)

```python
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Dict, Optional

# ========================================================================
# Request Models
# ========================================================================
class CondicaoCronicaCreate(BaseModel):
    cid10: str
    medico_diagnosticador: str
    confirmacao_exames: bool = False
    gravidade_inicial: str  # LEVE, MODERADA, GRAVE

class CondicaoCronicaUpdate(BaseModel):
    status: Optional[str] = None
    gravidade_inicial: Optional[str] = None

class EstadiamentoCreate(BaseModel):
    sistema_classificacao: str
    estagio: str
    criterios: Dict

class PlanoCuidadoCreate(BaseModel):
    objetivos: List[Dict]
    intervencoes: List[Dict]
    medicamentos: List[Dict]

class AcompanhamentoCreate(BaseModel):
    condicao_cronica_id: int
    data_acompanhamento: datetime
    medico_id: str
    pressao_arterial: Optional[str] = None
    peso_kg: Optional[float] = None

# ========================================================================
# Response Models
# ========================================================================
class CondicaoCronicaResponse(BaseModel):
    id: int
    paciente_cpf: str
    cid10: str
    status: str
    criado_em: datetime
    
    class Config:
        from_attributes = True

class EstadiamentoResponse(BaseModel):
    estagio: str
    data_classificacao: datetime
    criterios: Optional[Dict] = None
    
    class Config:
        from_attributes = True

class AcompanhamentoResponse(BaseModel):
    id: int
    data_acompanhamento: datetime
    adesao_medicamentos: Optional[str] = None
    proxima_consulta: Optional[date] = None
    
    class Config:
        from_attributes = True
```

**Entrega**: Schemas validados com Pydantic v2

#### 3.1.4 Alembic Migrations (1h - 13:00-14:00)

```bash
cd /opt/intellicare-oswaldo
alembic init alembic

# Configurar alembic.ini
# sqlalchemy.url = postgresql://oswaldo:password@localhost/intellicare_oswaldo

alembic revision --autogenerate -m "Create oswaldo tables"
alembic upgrade head

# Verificar
psql -U oswaldo -d intellicare_oswaldo -c "\dt"
# Deve listar: condicao_cronica, estadiamento, plano_cuidado, acompanhamento, alerta
```

**Entrega**: Tabelas criadas em dev database

#### 3.1.5 FastAPI App Setup (1h - 14:00-15:00)

**Arquivo**: `src/oswaldo/api/main.py` (150 linhas)

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging

# Configuração Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Oswaldo - Doenças Crônicas",
    version="1.0.0-dev",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================================================
# Root Endpoints
# ========================================================================
@app.get("/")
def read_root():
    return {"app": "Oswaldo", "status": "UP", "version": "1.0.0-dev"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api")
def api_info():
    return {
        "name": "Oswaldo API",
        "endpoints": {
            "condicoes": "/api/v1/oswaldo/condicoes",
            "acompanhamentos": "/api/v1/oswaldo/acompanhamentos",
            "alertas": "/api/v1/oswaldo/alertas",
        }
    }

# ========================================================================
# Error Handlers
# ========================================================================
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"error": str(exc)})

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

# ========================================================================
# Routers
# ========================================================================
# app.include_router(condicoes_router, prefix="/api/v1/oswaldo", tags=["condicoes"])
# app.include_router(acompanhamentos_router, prefix="/api/v1/oswaldo", tags=["acompanhamentos"])
# app.include_router(alertas_router, prefix="/api/v1/oswaldo", tags=["alertas"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,  host="0.0.0.0", port=8002)
```

**Entrega**: App FastAPI respondendo em http://localhost:8002

#### 3.1.6 Testes Base (30min - 15:00-15:30)

**Arquivo**: `tests/test_models.py` (80 linhas)

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.oswaldo.models.oswaldo_models import Base, CondicaoCronica, Estadiamento

@pytest.fixture
def db():
    # SQLite em memória para testes
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def test_criar_condicao_cronica(db):
    condicao = CondicaoCronica(
        paciente_cpf="abc123def456",
        cid10="I10",  # HAS
        data_diagnostico="2026-01-15",
        status="CONFIRMADO"
    )
    db.add(condicao)
    db.commit()
    
    assert condicao.id is not None
    assert condicao.cid10 == "I10"

def test_criar_estadiamento(db):
    condicao = CondicaoCronica(
        paciente_cpf="abc123def456",
        cid10="I10",
        data_diagnostico="2026-01-15",
        status="CONFIRMADO"
    )
    db.add(condicao)
    db.commit()
    
    estadiamento = Estadiamento(
        condicao_cronica_id=condicao.id,
        sistema_classificacao="SBC",
        estagio="ESTAGIO_2"
    )
    db.add(estadiamento)
    db.commit()
    
    assert len(condicao.estadiamentos) == 1
```

**Status Final Dia 1**: ✅ Core structure pronto

---

### DIA 2: CRUD APIs (8 horas)

#### 3.1.7 Endpoints CRUD Condicoes (3h)

**Arquivo**: `src/oswaldo/api/endpoints/condicoes.py` (200 linhas)

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from src.oswaldo.models.oswaldo_models import CondicaoCronica
from src.oswaldo.api.schemas.condicoes import CondicaoCronicaCreate, CondicaoCronicaResponse

router = APIRouter()

def get_db():
    # DB session dependency
    pass

@router.get("/paciente/{cpf}/condicoes", response_model=List[CondicaoCronicaResponse])
def listar_condicoes(cpf: str, db: Session = Depends(get_db)):
    """Listar condições crônicas de um paciente"""
    condicoes = db.query(CondicaoCronica).filter(
        CondicaoCronica.paciente_cpf == cpf,
        CondicaoCronica.status != "ENCERRADO"
    ).all()
    return condicoes

@router.post("/condicoes", response_model=CondicaoCronicaResponse)
def criar_condicao(
    paciente_cpf: str,
    condicao: CondicaoCronicaCreate,
    db: Session = Depends(get_db)
):
    """Criar nova condição crônica"""
    db_condicao = CondicaoCronica(
        paciente_cpf=paciente_cpf,
        cid10=condicao.cid10,
        data_diagnostico=date.today(),
        medico_diagnosticador=condicao.medico_diagnosticador,
        confirmacao_exames=condicao.confirmacao_exames,
        status="PENDENTE_VALIDACAO" if not condicao.confirmacao_exames else "CONFIRMADO",
        gravidade_inicial=condicao.gravidade_inicial
    )
    db.add(db_condicao)
    db.commit()
    db.refresh(db_condicao)
    return db_condicao

@router.get("/condicoes/{condicao_id}", response_model=CondicaoCronicaResponse)
def obter_condicao(condicao_id: int, db: Session = Depends(get_db)):
    """Obter detalhes de uma condição"""
    condicao = db.query(CondicaoCronica).filter(CondicaoCronica.id == condicao_id).first()
    if not condicao:
        raise HTTPException(status_code=404, detail="Condição não encontrada")
    return condicao

@router.put("/condicoes/{condicao_id}")
def atualizar_condicao(
    condicao_id: int,
    update: CondicaoCronicaUpdate,
    db: Session = Depends(get_db)
):
    """Atualizar condição"""
    condicao = db.query(CondicaoCronica).filter(CondicaoCronica.id == condicao_id).first()
    if not condicao:
        raise HTTPException(status_code=404, detail="Condição não encontrada")
    
    if update.status:
        condicao.status = update.status
    if update.gravidade_inicial:
        condicao.gravidade_inicial = update.gravidade_inicial
    
    db.commit()
    db.refresh(condicao)
    return condicao

@router.delete("/condicoes/{condicao_id}")
def deletar_condicao(condicao_id: int, db: Session = Depends(get_db)):
    """Soft-delete de uma condição"""
    condicao = db.query(CondicaoCronica).filter(CondicaoCronica.id == condicao_id).first()
    if not condicao:
        raise HTTPException(status_code=404, detail="Condição não encontrada")
    
    condicao.status = "ENCERRADO"
    db.commit()
    return {"message": "Condição encerrada"}
```

**Entrega**: 6 endpoints CRUD funcionando

#### 3.1.8 Endpoints Acompanhamentos (2h)

Similar ao acima, criar `src/oswaldo/api/endpoints/acompanhamentos.py`:

```python
endpoints:
├── POST /api/v1/oswaldo/acompanhamentos
├── GET /api/v1/oswaldo/paciente/{cpf}/acompanhamentos
├── GET /api/v1/oswaldo/condicoes/{id}/acompanhamentos
└── GET /api/v1/oswaldo/acompanhamentos/{id}
```

**Entrega**: 4 endpoints acompanhamentos

#### 3.1.9 API Tests (2h)

**Arquivo**: `tests/test_api.py` (150 linhas)

```python
import pytest
from fastapi.testclient import TestClient
from src.oswaldo.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_listar_condicoes_vazio():
    response = client.get("/api/v1/oswaldo/paciente/abc123/condicoes")
    assert response.status_code == 200
    assert response.json() == []

def test_criar_condicao():
    response = client.post("/api/v1/oswaldo/condicoes", json={
        "cid10": "I10",
        "medico_diagnosticador": "Dr. Silva",
        "confirmacao_exames": True,
        "gravidade_inicial": "MODERADA"
    }, params={"paciente_cpf": "abc123"})
    assert response.status_code == 201
    assert response.json()["cid10"] == "I10"

# + 20+ more test cases
```

**Status Final Dia 2**: ✅ APIs básicas rodando, 80+ testes passando

---

### DIAS 3-7: Síntese

Continuando com o padrão acima:

**Dia 3**: Consumer Florence + validação = 8h
**Dia 4**: Reclassificação automática + transações = 8h
**Dia 5**: Algoritmos clínicos + validadores = 8h
**Dia 6**: Planos + Alertas + Acompanhamento = 8h
**Dia 7**: Testes + Docs + Cleanup + Demo = 8h

---

## 4. ESTRUTURA DE ARQUIVOS

```
intellicare-oswaldo/
├── src/oswaldo/
│   ├── __init__.py                           (10 linhas)
│   ├── api/
│   │   ├── main.py                           (150 linhas)
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── condicoes.py                  (200 linhas)
│   │   │   ├── acompanhamentos.py            (150 linhas)
│   │   │   ├── alertas.py                    (100 linhas)
│   │   │   └── timeline. py                  (50 linhas)
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── condicoes.py                  (100 linhas)
│   │       ├── acompanhamentos.py            (80 linhas)
│   │       └── alertas.py                    (60 linhas)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── diagnostico_service.py            (200 linhas)
│   │   ├── classificacao_service.py          (150 linhas)
│   │   ├── plano_cuidado_service.py          (200 linhas)
│   │   ├── acompanhamento_service.py         (150 linhas)
│   │   └── alerta_service.py                 (180 linhas)
│   ├── models/
│   │   ├── __init__.py
│   │   └── oswaldo_models.py                 (400 linhas)
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── florence_consumer.py              (120 linhas)
│   │   └── oswaldo_publisher.py              (80 linhas)
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── classificadores.py                (120 linhas: HAS, DRC, Diabetes, etc)
│   │   ├── diagnosticos.py                   (100 linhas: padrões)
│   │   └── validadores.py                    (80 linhas: coerência)
│   ├── metrics.py                            (100 linhas Prometheus)
│   └── config.py                             (50 linhas)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                           (50 linhas fixtures)
│   ├── test_models.py                        (100 linhas)
│   ├── test_diagnostico_service.py           (150 linhas)
│   ├── test_classificacao.py                 (150 linhas)
│   ├── test_plano_cuidado.py                 (150 linhas)
│   ├── test_acompanhamento.py                (100 linhas)
│   ├── test_alertas.py                       (100 linhas)
│   ├── test_integrations.py                  (150 linhas)
│   ├── test_api.py                           (200 linhas)
│   └── fixtures/
│       ├── dados_clinicos.json               (dados dummy)
│       └── exames_florence.json              (mock events)
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   ├── alembic.ini
│   └── versions/
│       └── 001_create_oswaldo_tables.py      (150 linhas)
│
├── monitoring/
│   └── oswaldo-alerts.yml                    (100 linhas)
│
├── run_api_8002.py                           (20 linhas)
├── requirements.txt                          (20 linhas)
├── .env.example
├── .gitignore
├── README.md                                 (200 linhas)
└── docker-compose.yml                        (atualizado)
```

**TOTAL**: ~3,000 linhas

---

## 5. CHECKLIST DE IMPLEMENTAÇÃO

### ✅ Fase 1: Core (Dias 1-2)

```
[x] Setup projeto + venv
[x] Modelos SQLAlchemy (5 tabelas)
[x] Schemas Pydantic
[x] Alembic migrations
[x] FastAPI app
[x] Testes base
[x] APIs CRUD condicoes (6 endpoints)
[x] APIs CRUD acompanhamentos (4 endpoints)
[x] Testes API (30+ casos)
[x] Swagger documentation
```

### Fase 2: Integração Florence (Dias 3-4)

```
[ ] RabbitMQ consumer setup
[ ] Event validation schemas
[ ] Handlers para 3 event types
[ ] Event → Diagnóstico flow
[ ] Reclassificação automática
[ ] Atualização plano ao reclassificar
[ ] Geração de alertas ao piora
[ ] Integration tests (20+ casos)
[ ] Monitoramento de eventos
[ ] Testes de fluxo integrado
```

### Fase 3: Algoritmos (Dia 5)

```
[ ] Classificador HAS (PA → NORMAL/EST1/2/3)
[ ] Classificador DRC (TFGe → G1-G5)
[ ] Classificador Diabetes (HbA1c → CONTROLADO/MODERADO/MAL/CRITICO)
[ ] Classificador Lipídio
[ ] Sugestor diagnóstico automático
[ ] Validadores de coerência
[ ] Cálculo de confiança
[ ] Testes algoritmos (30+ casos clínicos)
```

### Fase 4: Fluxos Avançados (Dia 6)

```
[ ] Criar plano de cuidado automático
[ ] Gerar objetivos SMART baseado em estágio
[ ] Listar intervenções por CID
[ ] GET recomendações medicamentosas
[ ] Registrar acompanhamento + vitais
[ ] Avaliar adesão
[ ] Agendar próxima consulta
[ ] Gerar alertas com severidade
[ ] Queue de notificações
[ ] Testes fluxos (25+ cenários)
```

### Fase 5: Polimento (Dia 7)

```
[ ] Cobertura testes 90%+
[ ] P99 latência < 100ms
[ ] Load test com 1000+ registros
[ ] Documentação README
[ ] Runbook de erros
[ ] .env.example
[ ] docker-compose update
[ ] GitHub Actions CI/CD
[ ] Apresentação para especialista
[ ] Sign-off técnico
```

---

## 6. DEPENDÊNCIAS DE APROVAÇÃO

### Pré-Sprint

- [x] Especificação funcional aprovada
- [ ] Stack técnico aprovado (arquitetura)
- [ ] Diretrizes clínicas validadas (especialista)
- [ ] PostgreSQL DB "intellicare_oswaldo" criado
- [ ] RabbitMQ queues configuradas
- [ ] "Florence integration ready"

### Mid-Sprint (Dia 4)

- [ ] Classificadores aprovados por especialista
- [ ] Integração Florence testada point-to-point
- [ ] CTO sign-off em arquitetura

### Final (Dia 7)

- [ ] Testes 90%+ coverage
- [ ] Performance SLA validado
- [ ] Especialista assina validação clínica
- [ ] Ready para staging

---

## 7. PLANO DE TESTES

### Cobertura Alvo: 90%+ de código crítico

```
Services:
├── DiagnosticoService: 90%+ (20+ casos clínicos)
├── ClassificacaoService: 95%+ (30+ casos)
├── PlanoCuidadoService: 85%+ (15+ casos)
├── AcompanhamentoService: 85%+ (15+ casos)
└── AlertaService: 90%+ (15+ casos)

Algoritmos:
├── classificar_has: 95%+ (branching logic)
├── classificar_drc: 95%+
├── classificar_diabetes: 90%+
└── Validadores: 90%+

APIs:
├── CRUD endpoints: 90%+
├── Error handling: 95%+
└── Authentication: 100%

Integrations:
├── Florence consumer: 85%+
├── Event processing: 90%+
└── Oswaldo publisher: 80%+

Total Target: 90%+
```

### Testes por Tipo

```
Unit Tests (Services): 60+ testes
Integration Tests (APIs): 40+ testes
E2E Tests (Flows): 30+ testes
Performance Tests: 5+ scenarios
Total: ~135+ testes
```

---

## 8. CRONOGRAMA FINAL

```
FEV 12 (hoje)
└── Análise técnica + Plano ✅

FEV 13-19: IMPLEMENTAÇÃO (7 dias, 56 horas)
├── Dia 1 (FEV 13):  Setup + Modelos
├── Dia 2 (FEV 14):  APIs CRUD
├── Dia 3 (FEV 15):  Florence Integration - Dia 1
├── Dia 4 (FEV 16):  Florence Integration - Dia 2
├── Dia 5 (FEV 17):  Algoritmos Clínicos
├── Dia 6 (FEV 18):  Fluxos Avançados
└── Dia 7 (FEV 19):  Polimento + Validação

FEV 20-21: STAGING + VALIDAÇÃO
└── Testes e ajustes

FEV 22: GO-LIVE (Oswaldo + Florence integrados)
```

---

## PRÓXIMOS PASSOS

1. **Aprovação Stack** (hoje antes setup)
2. **Setup DB + RabbitMQ** (paralelo Dia 1)
3. **Kick-off com especialista** (Dia 1)
4. **Daily standups** (09:00 todos dias)
5. **Mid-sprint review** (Dia 4 - 14:00)
6. **Final demo** (Dia 7 - 16:00)

---

**Status**: 📋 **PLANO TÉCNICO DETALHADO PRONTO**
**Próximo**: **INICIAR IMPLEMENTAÇÃO FEV 13 09:00**
**Responsável**: **DEV2**
**Target**: **Production Ready FEV 22**
