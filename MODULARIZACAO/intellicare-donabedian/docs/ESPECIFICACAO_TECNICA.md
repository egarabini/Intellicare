# intellicare-donabedian v1.0.0 — Especificacao Tecnica

> **Autor:** DEV1 (Claude Agent)
> **Data:** 2026-02-10
> **Status:** APROVADO COM AJUSTES (aplicados)

## Histórico de Revisões

**v1.1 - 2026-02-10 - Ajustes pós-revisão:**
1. ✅ Adicionado campo `weight` em `IndicatorPillar` (permite pesos diferentes por pilar)
2. ✅ Variável de ambiente renomeada: `DATABASE_URL` → `INTELLICARE_DATABASE_URL` (padrão IntelliCare)
3. ✅ Healthcheck adicionado no PostgreSQL com `depends_on: condition: service_healthy`
4. ✅ Removido `version: '3.8'` do docker-compose (não mais necessário)

**v1.0 - 2026-02-10 - Versão inicial:**
- Especificação técnica completa submetida para revisão

---

## 1. Stack Tecnologico

### 1.1 Linguagens e Frameworks

| Componente | Tecnologia | Versão | Justificativa |
|------------|------------|--------|---------------|
| **Backend API** | Python | 3.11+ | Conforme requisito, ecossistema rico para saúde |
| **Framework API** | FastAPI | 0.109+ | Performance, async, OpenAPI automático, type hints |
| **Dashboard** | Streamlit | 1.30+ | Conforme requisito, prototipagem rápida |
| **ORM** | SQLAlchemy | 2.0+ | Conforme requisito, async support, type-safe |
| **Validação** | Pydantic | 2.5+ | Integração nativa com FastAPI, validação robusta |

### 1.2 Banco de Dados

| Componente | Tecnologia | Versão | Justificativa |
|------------|------------|--------|---------------|
| **SGBD** | PostgreSQL | 15+ | Conforme requisito, JSONB para flexibilidade |
| **Migrations** | Alembic | 1.13+ | Padrão com SQLAlchemy, versionamento de schema |

### 1.3 Visualização de Dados

| Componente | Tecnologia | Versão | Justificativa |
|------------|------------|--------|---------------|
| **Gráficos** | Plotly | 5.18+ | Interativo, radar chart nativo, integra com Streamlit |
| **Tabelas** | Pandas | 2.1+ | Manipulação de séries temporais, agregações |

### 1.4 Testes e Qualidade

| Componente | Tecnologia | Versão | Justificativa |
|------------|------------|--------|---------------|
| **Framework Testes** | pytest | 7.4+ | Padrão Python, fixtures poderosos |
| **Cobertura** | pytest-cov | 4.1+ | Relatórios de cobertura >= 80% |
| **Async Tests** | pytest-asyncio | 0.23+ | Testes de endpoints FastAPI async |
| **Linting** | ruff | 0.1+ | Conforme requisito, rápido, substitui flake8+black |
| **Type Checking** | mypy | 1.8+ | Conforme requisito (strict mode) |

### 1.5 Infraestrutura

| Componente | Tecnologia | Versão | Justificativa |
|------------|------------|--------|---------------|
| **Containerização** | Docker | 24+ | Conforme requisito, isolamento |
| **Orquestração** | Docker Compose | 2.23+ | Conforme requisito, multi-container |
| **Gerenciador Deps** | Poetry | 1.7+ | Lock file determinístico, melhor que pip |

---

## 2. Arquitetura de Dados

### 2.1 Os 7 Pilares de Donabedian (CORRETO)

Conforme framework original de Avedis Donabedian (1990):

1. **Eficácia (Efficacy)** - O cuidado funciona em condições ideais?
2. **Efetividade (Effectiveness)** - O cuidado funciona na prática?
3. **Eficiência (Efficiency)** - Usa bem os recursos?
4. **Otimidade (Optimality)** - O custo-benefício é adequado?
5. **Aceitabilidade (Acceptability)** - O paciente aceita e adere?
6. **Legitimidade (Legitimacy)** - Atende expectativas da sociedade?
7. **Equidade (Equity)** - O acesso é justo para todos?

**Referência:** https://blogdaqualidade.com.br/saude-os-7-pilares-da-qualidade-de-avedis-donabedian/

### 2.2 Modelo Entidade-Relacionamento

4 tabelas principais:

**Pillar** (7 registros fixos)
- id (PK)
- name (efficacy, effectiveness, efficiency, optimality, acceptability, legitimacy, equity)
- description
- display_order

**Indicator** (indicadores de qualidade)
- id (PK)
- name
- description
- formula
- unit
- target_value
- target_operator (>=, <=, ==)
- triad_dimension (structure, process, outcome)
- created_at
- updated_at

**IndicatorPillar** (N:N associativa)
- id (PK)
- indicator_id (FK)
- pillar_id (FK)
- weight (float, default 1.0) - peso do indicador neste pilar

**Measurement** (medições temporais)
- id (PK)
- indicator_id (FK)
- value
- period_start
- period_end
- period_type (monthly, quarterly, semiannual, annual)
- status (green, yellow, red) - calculado automaticamente
- created_at

### 2.3 Justificativa do Modelo

**Pillar (Tabela de Referência):**
- 7 registros fixos (os 7 pilares de Donabedian 1990)
- Seed data inicial, raramente muda
- Permite extensão futura se necessário

**Indicator:**
- Representa cada indicador de qualidade
- `triad_dimension`: qual dimensão da tríade (Estrutura/Processo/Resultado)
- `target_operator`: como comparar com meta (>=, <=, ==)
- Relacionamento N:N com Pillar (um indicador pode pertencer a múltiplos pilares)

**IndicatorPillar:**
- Tabela associativa para N:N
- Campo `weight` permite que um indicador tenha importância diferente em cada pilar
- **Exemplo:** "Taxa de Infecção Hospitalar" pode ter:
  - weight = 1.0 em Eficácia (impacto direto)
  - weight = 0.5 em Efetividade (impacto indireto)
- Isso permite cálculo de scores mais refinado por pilar

**Measurement:**
- Medições ao longo do tempo
- `status` calculado automaticamente comparando `value` com `indicator.target_value`
- Permite análise temporal (trends)

---

## 3. API REST - Endpoints

Todos os endpoints seguem padrão IntelliCare: **/api/v1/**

### 3.1 Health & Info
- GET /api/v1/health → Status do módulo
- GET /api/v1/info → Nome, versão, capabilities

### 3.2 Indicators
- GET /api/v1/indicators → Lista todos indicadores
- GET /api/v1/indicators/{id} → Detalhe de um indicador
- POST /api/v1/indicators → Cadastrar novo indicador
- PUT /api/v1/indicators/{id} → Atualizar indicador
- DELETE /api/v1/indicators/{id} → Remover indicador

### 3.3 Measurements
- POST /api/v1/measurements → Registrar medição
- GET /api/v1/measurements?indicator_id={id}&period_start={date}&period_end={date} → Listar medições

### 3.4 Dashboard & Assessment
- GET /api/v1/dashboard → Dados consolidados (tríade + pilares + alertas)
- POST /api/v1/assess → Avaliação completa de qualidade
- GET /api/v1/trends/{indicator_id} → Tendência temporal de um indicador

---

## 4. Estrutura de Diretórios

`
intellicare-donabedian/
├── src/
│   └── donabedian/
│       ├── api/                    # FastAPI
│       │   ├── main.py
│       │   ├── dependencies.py
│       │   └── routes/
│       │       ├── health.py
│       │       ├── indicators.py
│       │       ├── measurements.py
│       │       └── dashboard.py
│       ├── dashboard/              # Streamlit
│       │   ├── app.py
│       │   └── components/
│       │       ├── triad.py
│       │       ├── pillars.py
│       │       └── timeline.py
│       ├── models/                 # SQLAlchemy
│       │   ├── pillar.py
│       │   ├── indicator.py
│       │   └── measurement.py
│       ├── schemas/                # Pydantic
│       │   ├── pillar.py
│       │   ├── indicator.py
│       │   ├── measurement.py
│       │   └── dashboard.py
│       ├── services/               # Business logic
│       │   ├── calculator.py       # Score calculation
│       │   ├── assessor.py         # Quality assessment
│       │   └── trend_analyzer.py
│       ├── database/
│       │   ├── session.py
│       │   └── seed.py
│       └── config.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── migrations/                     # Alembic
├── data/seed/
│   ├── pillars.json
│   ├── indicators.json
│   └── measurements.json
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.dashboard
│   └── docker-compose.yml
├── pyproject.toml
├── ruff.toml
├── mypy.ini
└── pytest.ini
`

---

## 5. Docker Configuration

### 5.1 docker-compose.yml

```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: donabedian
      POSTGRES_USER: donabedian
      POSTGRES_PASSWORD: donabedian_dev
    ports:
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U donabedian"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    ports:
      - "8003:8000"
    environment:
      INTELLICARE_DATABASE_URL: postgresql://donabedian:donabedian_dev@db:5432/donabedian
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn donabedian.api.main:app --host 0.0.0.0 --port 8000 --reload

  dashboard:
    build:
      context: .
      dockerfile: docker/Dockerfile.dashboard
    ports:
      - "8503:8501"
    environment:
      API_URL: http://api:8000
    depends_on:
      - api
    command: streamlit run src/donabedian/dashboard/app.py --server.port=8501 --server.address=0.0.0.0

volumes:
  postgres_data:
```

---

## 6. Estratégia de Testes

### 6.1 Cobertura Mínima: 80%

### 6.2 Tipos de Teste

**Unit Tests:**
- 	est_calculator.py - Cálculo de scores
- 	est_assessor.py - Lógica de avaliação
- 	est_trend_analyzer.py - Análise temporal

**Integration Tests:**
- 	est_api_indicators.py - CRUD de indicadores
- 	est_api_measurements.py - CRUD de medições
- 	est_api_dashboard.py - Endpoints de dashboard

**E2E Tests:**
- 	est_full_workflow.py - Fluxo completo: cadastrar indicador → registrar medições → visualizar dashboard

---

## 7. Seed Data

### 7.1 Pillars (7 registros)

`json
[
  {"name": "efficacy", "description": "Eficácia - O cuidado funciona em condições ideais?", "display_order": 1},
  {"name": "effectiveness", "description": "Efetividade - O cuidado funciona na prática?", "display_order": 2},
  {"name": "efficiency", "description": "Eficiência - Usa bem os recursos?", "display_order": 3},
  {"name": "optimality", "description": "Otimidade - O custo-benefício é adequado?", "display_order": 4},
  {"name": "acceptability", "description": "Aceitabilidade - O paciente aceita e adere?", "display_order": 5},
  {"name": "legitimacy", "description": "Legitimidade - Atende expectativas da sociedade?", "display_order": 6},
  {"name": "equity", "description": "Equidade - O acesso é justo para todos?", "display_order": 7}
]
`

### 7.2 Indicators (15 mínimo)

Exemplos:
- Taxa de infecção hospitalar (Resultado, Eficácia+Efetividade)
- Taxa de mortalidade geral (Resultado, Eficácia)
- Taxa de reinternação 30d (Resultado, Efetividade)
- Tempo médio de permanência (Processo, Eficiência)
- Taxa de ocupação de leitos (Estrutura, Eficiência)
- Satisfação do paciente (Resultado, Aceitabilidade)
- Adesão ao checklist cirúrgico (Processo, Eficácia)
- Profissionais por leito (Estrutura, Otimidade)
- Protocolos atualizados (Estrutura, Legitimidade)
- Taxa de cesárea (Processo, Efetividade)
- Tempo porta-balão IAM (Processo, Eficácia)
- Cobertura vacinal (Processo, Legitimidade+Equidade)
- Taxa de abandono de tratamento (Resultado, Aceitabilidade)
- Giro de leitos (Processo, Eficiência)
- Equipamentos calibrados (Estrutura, Eficácia)

### 7.3 Measurements

12 meses de dados para cada indicador (simulando 2025).

---

## 8. Cronograma de Implementação

| Fase | Componente | Estimativa |
|------|-----------|-----------|
| 1 | Setup inicial (Poetry, Docker, estrutura) | 2h |
| 2 | Models SQLAlchemy + Migrations | 3h |
| 3 | Schemas Pydantic | 2h |
| 4 | API Routes (CRUD básico) | 4h |
| 5 | Services (Calculator, Assessor) | 4h |
| 6 | Seed Data | 2h |
| 7 | Dashboard Streamlit (básico) | 4h |
| 8 | Dashboard Components (radar, timeline) | 4h |
| 9 | Testes (unit + integration) | 6h |
| 10 | Docker final + README | 2h |
| **TOTAL** | | **33h** (~4-5 dias) |

---

## 9. Próximos Passos

1. ✅ Especificação Técnica completa (este documento)
2. ⏳ Aguardar revisão e aprovação
3. 🚀 Iniciar implementação seguindo cronograma
4. 📝 Registrar progresso em steps/STEP-001.md
5. ✅ Validar contra critérios de aceite da spec funcional

---

**FIM DA ESPECIFICAÇÃO TÉCNICA v1.0.0**
