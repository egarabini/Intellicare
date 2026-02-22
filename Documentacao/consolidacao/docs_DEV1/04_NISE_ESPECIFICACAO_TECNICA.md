# ESPECIFICAÇÃO TÉCNICA: MÓDULO NISE - TREINAMENTO ASSISTIDO

## ID: DEV1-NISE-TEC-001
## Versão: 1.0
## Data: 26/02/2026
## Responsável: DEV1
## Status: AGUARDANDO APROVAÇÃO

---

## 1. VISÃO GERAL

### 1.1. Objetivo
Implementar ambiente de **treinamento assistido** com simulação FHIR realista para capacitação de profissionais de saúde no uso do sistema INTELLICARE.

### 1.2. Escopo Técnico
- **Fase 1 (MVP)**: Infraestrutura + APIs FHIR básicas (4 semanas)
- **Fase 2 (Avançado)**: Sistema de treinamento + Integrações (4 semanas)
- **Total**: 8 semanas (~60 horas)

### 1.3. Princípios Arquiteturais
1. ✅ **Isolamento total** de produção (schema dedicado)
2. ✅ **Conformidade FHIR R4** (padrão internacional)
3. ✅ **Dados sintéticos realistas** (Brasil-específicos)
4. ✅ **Performance** (<100ms P99)
5. ✅ **Escalabilidade** (múltiplos usuários simultâneos)

---

## 2. ARQUITETURA TÉCNICA

### 2.1. Diagrama de Componentes
```
┌─────────────────────────────────────────────────────────┐
│                   MÓDULO NISE                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   FastAPI    │  │ fhir.resources│  │   pgvector   │ │
│  │  (API FHIR)  │  │  (Validação)  │  │     (RAG)    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                  │                  │         │
│         └──────────────────┴──────────────────┘         │
│                          │                              │
│  ┌───────────────────────────────────────────────────┐ │
│  │      PostgreSQL (nise_training schema)            │ │
│  │  - patients (5k)                                  │ │
│  │  - observations (20k)                             │ │
│  │  - practitioners (1k)                             │ │
│  │  - encounters (500)                               │ │
│  │  - scenarios (100)                                │ │
│  └───────────────────────────────────────────────────┘ │
│                          │                              │
│  ┌───────────────────────────────────────────────────┐ │
│  │           Integrações Externas                    │ │
│  │  - Ollama (RAG suporte)                           │ │
│  │  - n8n (Automação)                                │ │
│  │  - Módulos INTELLICARE (Florence, Oswaldo, etc)   │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2. Stack Tecnológica

| Componente | Tecnologia | Versão | Justificativa |
|------------|------------|--------|---------------|
| API Framework | FastAPI | 0.109+ | Performance, async, OpenAPI |
| FHIR Library | fhir.resources | 7.1+ | Validação FHIR R4 completa |
| Database | PostgreSQL | 15+ | Já existe, JSONB, performance |
| Vector DB | pgvector | 0.5+ | RAG para treinamento |
| ORM | psycopg | 3.1+ | Async, performance |
| Container | Docker | 24+ | Isolamento, portabilidade |
| LLM Engine | Ollama | Latest | LLMs locais, privacidade |
| RAG/Chatbot | Flowise | Latest | RAG + Chatbots + LLM Workflows |
| CI/CD | Dagger | Latest | Deployment + Versionamento |

---

## 3. MODELO DE DADOS

### 3.1. Schema PostgreSQL
```sql
-- Schema dedicado (isolamento total)
CREATE SCHEMA IF NOT EXISTS nise_training;

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Tabela: Pacientes
CREATE TABLE nise_training.patients (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR(64) UNIQUE NOT NULL,
    cpf VARCHAR(11) UNIQUE,
    cns VARCHAR(15) UNIQUE,
    name_given VARCHAR(100) NOT NULL,
    name_family VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    gender VARCHAR(20) NOT NULL,
    municipality_code VARCHAR(7),
    municipality_name VARCHAR(100),
    data JSONB NOT NULL,  -- FHIR Patient completo
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabela: Observações (RELs)
CREATE TABLE nise_training.observations (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR(64) UNIQUE NOT NULL,
    patient_fhir_id VARCHAR(64) REFERENCES nise_training.patients(fhir_id),
    code_loinc VARCHAR(20) NOT NULL,
    code_display VARCHAR(200),
    value_quantity NUMERIC(10,2),
    value_unit VARCHAR(50),
    effective_datetime TIMESTAMP NOT NULL,
    data JSONB NOT NULL,  -- FHIR Observation completo
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela: Profissionais
CREATE TABLE nise_training.practitioners (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR(64) UNIQUE NOT NULL,
    cpf VARCHAR(11) UNIQUE,
    cns VARCHAR(15) UNIQUE,
    name_given VARCHAR(100) NOT NULL,
    name_family VARCHAR(100) NOT NULL,
    specialty VARCHAR(100),
    crm VARCHAR(20),
    data JSONB NOT NULL,  -- FHIR Practitioner completo
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela: Consultas
CREATE TABLE nise_training.encounters (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR(64) UNIQUE NOT NULL,
    patient_fhir_id VARCHAR(64) REFERENCES nise_training.patients(fhir_id),
    practitioner_fhir_id VARCHAR(64) REFERENCES nise_training.practitioners(fhir_id),
    encounter_type VARCHAR(50) NOT NULL,
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP,
    data JSONB NOT NULL,  -- FHIR Encounter completo
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela: Cenários Clínicos
CREATE TABLE nise_training.scenarios (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty VARCHAR(20) NOT NULL,  -- basic, intermediate, advanced
    module VARCHAR(50) NOT NULL,  -- florence, oswaldo, geralda, wanda
    patient_fhir_id VARCHAR(64) REFERENCES nise_training.patients(fhir_id),
    expected_actions JSONB NOT NULL,  -- Ações esperadas
    evaluation_criteria JSONB NOT NULL,  -- Critérios de avaliação
    embedding vector(1536),  -- Para RAG
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela: Sessões de Treinamento
CREATE TABLE nise_training.training_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL,
    scenario_id INTEGER REFERENCES nise_training.scenarios(id),
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP,
    actions_taken JSONB,  -- Ações realizadas
    score NUMERIC(5,2),  -- Pontuação (0-100)
    feedback JSONB,  -- Feedback automático
    status VARCHAR(20) DEFAULT 'in_progress'  -- in_progress, completed, abandoned
);

-- Índices para performance
CREATE INDEX idx_patients_fhir_id ON nise_training.patients(fhir_id);
CREATE INDEX idx_patients_cpf ON nise_training.patients(cpf);
CREATE INDEX idx_patients_cns ON nise_training.patients(cns);
CREATE INDEX idx_observations_patient ON nise_training.observations(patient_fhir_id);
CREATE INDEX idx_observations_code ON nise_training.observations(code_loinc);
CREATE INDEX idx_observations_datetime ON nise_training.observations(effective_datetime);
CREATE INDEX idx_encounters_patient ON nise_training.encounters(patient_fhir_id);
CREATE INDEX idx_scenarios_module ON nise_training.scenarios(module);
CREATE INDEX idx_scenarios_difficulty ON nise_training.scenarios(difficulty);
CREATE INDEX idx_training_sessions_user ON nise_training.training_sessions(user_id);
CREATE INDEX idx_training_sessions_scenario ON nise_training.training_sessions(scenario_id);

-- Índice vetorial para RAG
CREATE INDEX idx_scenarios_embedding ON nise_training.scenarios 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## 4. API FHIR

### 4.1. Endpoints Principais (Fase 1)

| Método | Endpoint | Descrição | Status |
|--------|----------|-----------|--------|
| GET | `/fhir/Patient` | Listar pacientes | Fase 1 |
| GET | `/fhir/Patient/{id}` | Buscar paciente | Fase 1 |
| POST | `/fhir/Patient` | Criar paciente | Fase 1 |
| GET | `/fhir/Observation` | Listar observações | Fase 1 |
| GET | `/fhir/Observation/{id}` | Buscar observação | Fase 1 |
| POST | `/fhir/Observation` | Criar observação | Fase 1 |
| GET | `/fhir/Practitioner` | Listar profissionais | Fase 1 |
| GET | `/fhir/Practitioner/{id}` | Buscar profissional | Fase 1 |

### 4.2. Endpoints de Treinamento (Fase 2)

| Método | Endpoint | Descrição | Status |
|--------|----------|-----------|--------|
| GET | `/training/scenarios` | Listar cenários | Fase 2 |
| GET | `/training/scenarios/{id}` | Buscar cenário | Fase 2 |
| POST | `/training/sessions` | Iniciar sessão | Fase 2 |
| PUT | `/training/sessions/{id}/action` | Registrar ação | Fase 2 |
| POST | `/training/sessions/{id}/complete` | Finalizar sessão | Fase 2 |
| GET | `/training/sessions/{id}/feedback` | Obter feedback | Fase 2 |
| GET | `/training/users/{id}/progress` | Progresso usuário | Fase 2 |

---

## 5. GERAÇÃO DE DADOS SINTÉTICOS

### 5.1. Pacientes (5.000)
```python
# Características:
- CPF válido (algoritmo módulo 11)
- CNS válido (algoritmo módulo 11)
- Nomes brasileiros (Faker pt_BR)
- Municípios IBGE reais
- Distribuição demográfica realista:
  - 51% feminino, 49% masculino
  - Pirâmide etária Brasil (IBGE 2023)
  - Municípios proporcionais à população
```

### 5.2. Observações (20.000)
```python
# Características:
- Códigos LOINC oficiais
- ValueSets RNDS/SUS
- Valores dentro de ranges clínicos
- Distribuição temporal realista
- Associação correta com pacientes
```

### 5.3. Cenários Clínicos (100)
```python
# Distribuição:
- 40 cenários básicos (basic)
- 40 cenários intermediários (intermediate)
- 20 cenários avançados (advanced)

# Módulos:
- 25 Florence (Exames laboratoriais)
- 25 Oswaldo (Doenças crônicas)
- 25 Geralda (Acompanhamento)
- 25 Wanda (Orquestração)
```

---

## 6. INTEGRAÇÕES

### 6.1. Com Módulos INTELLICARE
```python
# Florence (Exames):
- Cenários de interpretação de exames
- Solicitação de exames complementares
- Análise de tendências laboratoriais

# Oswaldo (Doenças Crônicas):
- Gestão de HAS, Diabetes, DRC
- Ajuste de medicações
- Monitoramento de metas terapêuticas

# Geralda (Acompanhamento):
- Follow-up de pacientes
- Agendamento de consultas
- Registro de evolução

# Wanda (Orquestração):
- Fluxos completos de atendimento
- Coordenação entre módulos
- Tomada de decisão complexa
```

### 6.2. Com Flowise (RAG + Chatbots)
```python
# Funcionalidades:
1. RAG (Retrieval Augmented Generation):
   - Guidelines clínicas (SBC, KDIGO, ADA)
   - Casos clínicos históricos
   - Protocolos institucionais

2. Chatbots:
   - "Dr. Nise": Suporte durante treinamento
   - Guideline Assistant: Consulta rápida
   - Feedback Generator: Avaliação LLM

3. LLM Workflows:
   - Scenario Evaluation
   - Personalized Feedback
   - Difficulty Adjustment

# Configuração:
- Model: Ollama (Llama2-7B-medical)
- Interface: Web UI (port 3000)
- Storage: PostgreSQL (mesmo banco)
- API: REST endpoints para integração
```

### 6.3. Com Ollama (LLM Engine)
```python
# Funcionalidades:
- LLMs locais (Llama2-7B-medical)
- Inferência privada (sem envio dados externos)
- Suporte a múltiplos modelos
- API REST para integração

# Requisitos:
- CPU: 4 cores (recomendado)
- RAM: 8GB mínimo
- GPU: Opcional (acelera inferência)
```

### 6.4. Com Dagger (CI/CD)
```python
# Funcionalidades:
1. CI/CD Pipelines:
   - Build Flowise containers
   - Deploy Ollama models
   - Run database migrations
   - Deploy FastAPI application

2. Versionamento:
   - Version LLM prompts
   - Version RAG knowledge bases
   - Version training scenarios

3. Deployment:
   - Consistent deployment across environments
   - Rollback capabilities
   - Smoke testing automation

# Configuração:
- Integration: GitHub Actions
- Language: Python SDK
- Execution: Dagger Engine
```

---

## 7. REQUISITOS NÃO-FUNCIONAIS

### 7.1. Performance
- ✅ API: <100ms P99 para endpoints FHIR
- ✅ Busca: <50ms para queries simples
- ✅ RAG: <500ms para busca semântica
- ✅ Concorrência: 50 usuários simultâneos

### 7.2. Segurança
- ✅ Isolamento total de produção (schema dedicado)
- ✅ Dados sintéticos (sem PII real)
- ✅ Autenticação JWT
- ✅ Logs de auditoria

### 7.3. Escalabilidade
- ✅ Horizontal: Docker containers
- ✅ Vertical: PostgreSQL otimizado
- ✅ Cache: Redis (futuro)
- ✅ CDN: Assets estáticos (futuro)

### 7.4. Manutenibilidade
- ✅ Código limpo e documentado
- ✅ Testes automatizados (>80% cobertura)
- ✅ CI/CD pipeline
- ✅ Documentação OpenAPI

---

## 8. ESTRUTURA DE DIRETÓRIOS

```
nise/
├── api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── fhir/
│   │   ├── __init__.py
│   │   ├── patient.py          # Endpoints Patient
│   │   ├── observation.py      # Endpoints Observation
│   │   ├── practitioner.py     # Endpoints Practitioner
│   │   └── encounter.py        # Endpoints Encounter
│   └── training/
│       ├── __init__.py
│       ├── scenarios.py        # Endpoints Scenarios
│       └── sessions.py         # Endpoints Sessions
├── database/
│   ├── __init__.py
│   ├── connection.py           # PostgreSQL connection
│   ├── models.py               # SQLAlchemy models
│   └── migrations/             # Alembic migrations
├── generators/
│   ├── __init__.py
│   ├── patients.py             # Gerador de pacientes
│   ├── observations.py         # Gerador de observações
│   ├── practitioners.py        # Gerador de profissionais
│   └── scenarios.py            # Gerador de cenários
├── integrations/
│   ├── __init__.py
│   ├── ollama.py               # Integração Ollama
│   ├── n8n.py                  # Integração n8n
│   └── modules.py              # Integração módulos INTELLICARE
├── utils/
│   ├── __init__.py
│   ├── validators.py           # CPF, CNS, FHIR
│   ├── fhir_helpers.py         # Helpers FHIR
│   └── brazilian_data.py       # Dados brasileiros (IBGE, etc)
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_generators.py
│   └── test_integrations.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/
│   ├── api_reference.md
│   ├── user_guide.md
│   └── scenarios_catalog.md
├── requirements.txt
└── README.md
```

---

**Documento criado por**: DEV1  
**Data**: 26/02/2026  
**Versão**: 1.0  
**Status**: ✅ AGUARDANDO APROVAÇÃO  
**Próximo passo**: Criar Plano de Implementação

