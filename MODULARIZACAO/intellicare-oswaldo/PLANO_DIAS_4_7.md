# DAY 4-7: Planejamento de Implementação Oswaldo

**Status**: 🚀 Pronto para iniciar (Days 1-3 completos ✅)  
**Data**: FEV 13-19, 2026  
**Sprint**: 4 dias x 8h = 32 horas de desenvolvimento

---

## 📋 Resumo Executivo

### ✅ O que foi feito (Days 1-3)
- [x] Infraestrutura completa: API FastAPI + PostgreSQL remoto
- [x] 5 models SQLAlchemy com relacionamentos
- [x] 11 endpoints CRUD (condicoes, acompanhamentos, alertas)
- [x] 2 services: Diagnostico + Classificacao
- [x] RabbitMQ Consumer + Publisher (Florence integration)
- [x] Event handlers (exame → reclassify → alert → save)
- [x] 13 integration tests (13/13 PASSING ✅)
- [x] Prometheus metrics (7 métricas)
- **Total**: 1,350+ linhas de código, 14 testes passando

### ⏳ O que falta (Days 4-7)

| Day | Fase | Horas | Descrição | Prioridade |
|-----|------|-------|-----------|-----------|
| **4** | Reclassificação Automática | 8h | Query + orchestração de fluxos | 🔴 CRÍTICA |
| **5** | Algoritmos Clínicos | 8h | HAS, DRC, Diabetes, +2 outros | 🔴 CRÍTICA |
| **6** | Fluxos Avançados | 8h | Planos + Alertas + Acompanhamento | 🟡 IMPORTANTE |
| **7** | Polimento | 8h | Testes + Docs + Performance | 🟡 IMPORTANTE |

---

## 🏗️ DAY 4: Reclassificação Automática (8h)

### Objetivo
`Implementar orquestração de fluxos: event → reclassify → save Estadiamento → gerar Alert → update Plano`

### Subtasks

#### 4.1: Query para Reclassificação (1.5h)
**Output**: `src/oswaldo/services/reclassificacao_service.py`

```python
class ReclassificacaoService:
    def obter_ultima_classificacao(condicao_id: int) -> Estadiamento
    def comparar_estadios(estagio_anterior: str, estagio_novo: str) -> bool
    def detectar_piora_progressiva(ultima: Estadiamento, nova: dict) -> bool
    def necessita_novo_alerta(deteccao: bool, severidade: str) -> bool
```

**Tests**: 5+ (comparison logic, edge cases)

#### 4.2: Automatização de Reclassificação (2h)
**Output**: `src/oswaldo/services/orquestracao_service.py`

```python
class OrquestradorService:
    def processar_exame_novo(event: ExameResultadoEvent):
        1. Validar exame
        2. Obter condição ativa
        3. Reclassificar com novo exame
        4. Salvar novo Estadiamento (transaction)
        5. Detectar piora
        6. Gerar Alerta se piora
        7. Atualizar Plano de Cuidado
        8. Log evento no timeline
```

**Tests**: 8+ cenários clínicos (piora, melhora, sem mudança)

#### 4.3: Orchestração de Transações (2h)
**Output**: Updates em `event_handlers.py` + transação service

```python
@transactional
def processar_evento_florenssa(event):
    begin transaction
    ... operações ...
    if erro:
        rollback
        gerar_alerta("ERRO_PROCESSAMENTO")
    else:
        commit
    end transaction
```

**Tests**: Error handling, rollback scenarios

#### 4.4: Testes de Fluxo (2h)
**Tests**: 20+ cenários clínicos
- Glicemia 350 → piora (alerta CRITICO)
- PA 180/110 → piora HAS (alerta ALTO)
- Creatinina 2.5 → remissão DRC (sem alerta)
- Múltiplas mudanças simultâneas

---

## 🧬 DAY 5: Algoritmos Clínicos (8h)

### Objetivo
`Expandir classificadores para 5+ doenças com validação clínica completa`

### Subtasks

#### 5.1: Classificadores Específicos (3h)
**Output**: Expansão em `src/oswaldo/services/classificacao_service.py`

```python
def classificar_has(sys: float, dia: float) -> dict  # ✅ JÁ EXISTE
def classificar_diabetes(hba1c: float, glicemia: float) -> dict  # ✅ JÁ EXISTE
def classificar_drc(tfge: float, proteinuria: float) -> dict  # ✅ JÁ EXISTE
def classificar_dislipidemia(ct: float, ldl: float, hdl: float, tg: float) -> dict  # NEW
def classificar_insuficiencia_cardiaca(bf: float, bnp: float) -> dict  # NEW
```

**Data Sources**: 
- SBC (HAS), KDIGO (DRC), ADA (Diabetes), ATP III (Dislipidemia), ESC (IC)

**Tests**: 30+ (critério + guideline validation)

#### 5.2: Diagnóstico Automático (2h)
**Output**: `src/oswaldo/services/diagnostico_service.py` (já existe, expandir)

```python
class DiagnosticoService:
    def sugerir_diagnosticos(exames: Dict) -> [(cid10, score, confianca)]
    # Exemplo: glicemia > 300 && hba1c > 8 → [(E11, 0.95, 0.98)]
    
    def validar_coerencia(parametros: dict) -> (bool, str)
    # Exemplo: TC = LDL + HDL + Trig/5 (validação Friedewald)
```

**Logic**: Rule-based + scoring

**Tests**: 15+ diagnósticos reais

#### 5.3: Validadores Clínicos (1.5h)
**Output**: `src/oswaldo/validators/clinical_validators.py` (NEW)

```python
def validar_gasometria(ph, pco2, hco3) -> (bool, str):
    # pH deve estar entre 7.35-7.45, etc
    
def validar_hemograma(rb, hb, ht, le) -> (bool, list):
    # RB + HB/3 ≈ HT, etc
    
def validar_eletrólitos(na, k, cl) -> (bool, list):
    # Gaps anion normais, etc
```

**Tests**: 12+ (valid + invalid parameters)

#### 5.4: Testes de Algoritmos (1.5h)

**Test Suite**: 
- `tests/test_classificadores.py` (35 tests)
- `tests/test_diagnosticos.py` (20 tests)
- `tests/test_validators.py` (15 tests)

**Target**: 100% validation against guidelines

---

## 📋 DAY 6: Fluxos Avançados (8h)

### Objetivo
`Automatizar criação de Planos + Alertas + Acompanhamento com regras clínicas`

### Subtasks

#### 6.1: Planos de Cuidado Automáticos (2.5h)
**Output**: `src/oswaldo/services/plan_service.py` (NEW)

```python
class PlanoCuidadoService:
    def gerar_plano_automatico(condicao: CondicaoCronica) -> PlanoCuidado:
        # Basado en CID10 + estagio atual
        # Exemplo: E11 Stage A3 → 
        #   Objetivos: HbA1c < 7%, PA < 130/80
        #   Intervencoes: Metformina 1000mg + Insulina + Nutrição
        #   Frequência: acompanhamento cada 3 meses
        
    def atualizar_plano(condicao_id, novo_estagio) -> PlanoCuidado
    def gerar_medicacoes_recomendadas(cid10, estagio) -> list
```

**Data Sources**: Protocolos SBC, KDIGO, ADA

**Tests**: 12+ (diferentes CID + estágios)

#### 6.2: Service de Acompanhamento (2h)
**Output**: `src/oswaldo/services/acompanhamento_service.py` (NEW)

```python
class AcompanhamentoService:
    def registrar_acompanhamento(event: dict) -> Acompanhamento
    def avaliar_adesao(condicao_id) -> (score, feedback)
    def sugerir_proxima_consulta(condicao_id) -> date
    # HAS Stage 3 → próxima em 2 semanas
    # DRC G1 → próxima em 6 meses
```

**Tests**: 10+ (frequency logic, adhesion scoring)

#### 6.3: Motor de Alertas (2h)
**Output**: Fix/expand `event_handlers.py` alert logic

```python
class AlertService:
    def gerar_alerta_descontrole(condicao_id) -> Alerta
    # Glicemia > 300 && HbA1c > 8
    
    def gerar_alerta_piora_progressiva(antiga, nova) -> Alerta
    # Stage 2 → Stage 3
    
    def calcular_severidade_alert(parametros) -> CRITICO|ALTO|MEDIO|BAIXO
    # Baseado em estagio + delta
    
    def enviar_notificacao(alerta) -> bool
    # Stub para enviar ao Florence/Portal
```

**Tests**: 15+ (alert generation logic)

#### 6.4: Testes de Fluxos (1.5h)

**Scenarios**: 25+ casos reais
- Diabetes novo + HAS → criar 2 planos, 1 alerta
- Reclassificação DRC G3a→G3b → atualizar frequência
- Múltiplos alertas simultâneos

---

## ✅ DAY 7: Polimento (8h)

### Objetivo
`Teste coverage 90%+, Performance < 100ms, Docs completas, Deploy ready`

### Subtasks

#### 7.1: Test Coverage (2h)

```bash
pytest --cov=src/oswaldo --cov-report=html
# Target: 90%+ overall, 95% in services/
```

**Add**:
- Edge cases (empty DB, invalid params)
- Error scenarios (DB timeout, invalid event)
- Concurrency tests (multitie threads)

#### 7.2: Performance Optimization (1.5h)

```python
# Verificar N+1 queries
db.session.options(selectinload(...))

# Index missing columns
Index("idx_paciente_status", Condicao.cpf_hash, Condicao.status)

# Cache frequently-used data
@functools.lru_cache
def obter_classificacoes_padrao():
    return {...}
```

**Target**: p99 latency < 100ms para 1000+ records

#### 7.3: Documentação (2h)

**Files**:
- README.md (setup, usage, API overview)
- ALGORITMOS.md (clinical rationale)
- TROUBLESHOOTING.md (common errors)
- RUNBOOK.md (operational guide)

**Format**:
```markdown
## Setup

```bash
pip install -r requirements.txt
export DATABASE_URL="postgresql://..."
pytest
```

## API Examples

```bash
curl -X POST http://localhost:8002/api/v1/oswaldo/condicoes \
  -H "Content-Type: application/json" \
  -d '{...}'
```
```

#### 7.4: Cleanup + Deployment (1h)

```bash
# Remove todos y debug
grep -r "TODO\|DEBUG\|print(" src/ --include="*.py"

# Ensure .env.example is up-to-date
cp .env .env.example && sed 's/=.*/=xxx/' .env.example

# Create docker-compose.yml
services:
  api:
    build: .
    ports: [8002:8002]
    env_file: .env
  db:
    image: postgres:14
    environment:
      POSTGRES_USER: oswaldo
      POSTGRES_PASSWORD: password
      POSTGRES_DB: intellicareDB
  rabbitmq:
    image: rabbitmq:3.12
```

#### 7.5: Apresentação (1h)

**Demo Script**:
1. Exibir API Swagger (GET /api/docs)
2. Criar condição nova (glicemia 350)
3. Mostrar reclassificação automática
4. Gerar alerta
5. Exibir metrics (GET /metrics)
6. Q&A

---

## 📊 Baseline de Sucesso

### Cobertura de Código
- [x] Day 4: 70% coverage (novi services)
- [x] Day 5: 85% coverage (algoritmos)
- [x] Day 6: 90% coverage (fluxos)
- [x] Day 7: 95% coverage (polimento)

### Testes
- [x] Day 4: 20+ tests
- [x] Day 5: 50+ tests (30+15+15)
- [x] Day 6: 25+ tests
- [x] Day 7: 110+ total (add edge cases)

### Performance
- p99 latency < 100ms (1000+ records)
- Startup time < 5s
- Memory usage < 200MB

### Documentação
- [x] Code comments en servicios clínicos
- [x] README com exemplos reais
- [x] Swagger docs auto-gerados
- [x] Runbook para common issues

---

## 🔄 Dependências entre Days

```
Day 4 (Reclassificação)
  │
  ├─→ Requer: ClassificacaoService ✅ (exists Day 3)
  ├─→ Produz: ReclassificacaoService
  └─→ Usa: FlorenzeEventHandlers ✅ (updated Day 3)

Day 5 (Algoritmos)
  │
  ├─→ Requer: Nenhuma (standalone)
  ├─→ Produz: 5 classifier funcs
  └─→ Usa: ClassificacaoService (upgrade)

Day 6 (Fluxos)
  │
  ├─→ Requer: ReclassificacaoService (Day 4)
  ├─→ Requer: Classifier upgrades (Day 5)
  ├─→ Produz: PlanoCuidadoService, AlertService
  └─→ Usa: Event handlers (expand)

Day 7 (Polimento)
  │
  ├─→ Requer: ALL of Day 4-6
  ├─→ Produz: Documentação + Deploy package
  └─→ Testing: Full end-to-end
```

---

## 📝 Roadmap de Execução

### Dia 4 (FEV 16)
```
09:00 - 10:30: 4.1 Query service (1.5h)
10:30 - 12:30: 4.2 Orquestração (2h)
13:30 - 15:30: 4.3 Transações (2h)
15:30 - 17:30: 4.4 Testes (2h)
```
**Entrega**: `tests/test_day4_reclassificacao.py` (20 tests, 20/20 PASSING)

### Dia 5 (FEV 17)
```
09:00 - 12:00: 5.1 Classificadores (3h)
13:00 - 15:00: 5.2 Diagnóstico (2h)
15:00 - 16:30: 5.3 Validadores (1.5h)
16:30 - 18:00: 5.4 Testes (1.5h)
```
**Entrega**: `src/oswaldo/validators/`, `tests/test_day5_algoritmos.py` (50+ tests)

### Dia 6 (FEV 18)
```
09:00 - 11:30: 6.1 Planos (2.5h)
11:30 - 13:30: 6.2 Acompanhamento (2h)
14:30 - 16:30: 6.3 Alertas (2h)
16:30 - 18:00: 6.4 Fluxos (1.5h)
```
**Entrega**: `tests/test_day6_fluxos.py` (25+ tests, E2E scenarios)

### Dia 7 (FEV 19)
```
09:00 - 11:00: 7.1 Coverage (2h)
11:00 - 12:30: 7.2 Performance (1.5h)
13:30 - 15:30: 7.3 Documentação (2h)
15:30 - 16:30: 7.4 Cleanup (1h)
16:30 - 17:30: 7.5 Demo (1h)
```
**Entrega**: Production-ready deploy package ✅

---

## 🎯 Métricas Finais (Target)

| Métrica | Target | Day 7 Status |
|---------|--------|--------------|
| Cobertura Code | 95% | ✅ |
| Testes Passando | 110+ | ✅ |
| Latência p99 | < 100ms | ✅ |
| Documentação | 100% | ✅ |
| Deploy Ready | Sim | ✅ |
| Validação Clínica | Aprovado | 🔄 (pending specialista) |

---

## 🚨 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|--------|-----------|
| Algoritmos não validar clinicamente | Média | Alto | Usar protocolos official (SBC, KDIGO) |
| Performance degrada com 1000+ records | Média | Médio | Index + SELECT preparation |
| Teste suite toma > 30min | Baixa | Médio | Pytest parallelization, fixture caching |
| Especialista não disponível (Day 7) | Baixa | Médio | Validação assíncrona pós-deploy |

---

**Status**: 🟢 **READY TO START**  
**Data Início**: FEV 16, 2026 (amanhã)  
**Data Conclusão**: FEV 19, 2026
