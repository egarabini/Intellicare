# Oswaldo - Sistema Clínico de Monitoramento Inteligente

## 📋 Visão Geral

**Oswaldo** é um microserviço de processamento inteligente de eventos clínicos para pacientes com condições crônicas. Desenvolvido como parte da plataforma **IntelliCare**, o Oswaldo automatiza:

✅ **Reclassificação de Condições** - Atualiza o estágio de doenças com novos exames  
✅ **Geração de Alertas** - Detecta piora progressiva e descontrole  
✅ **Planos de Acompanhamento** - Recomenda frequência e parâmetros monitorados  

## 🏥 Suporte Clínico

### Condições Crônicas Monitoradas

| Condição | CID10 | Protocolos |
|----------|-------|-----------|
| Diabetes Mellitus II | E11 | ADA 2024 Standards |
| Hipertensão Arterial | I10 | SBC 2023 Guidelines |
| Doença Renal Crônica | N18 | KDIGO Classification |

### Parâmetros Clínicos Monitorados

- **Glicemia**: jejum, casual, HbA1c (mg/dL, %)
- **Pressão Arterial**: sistólica/diastólica (mmHg)
- **Creatinina**: sérica (mg/dL) → TFG estimado
- **Lipídios**: colesterol total, LDL, HDL (mg/dL)
- **Peso/IMC**: variação percentual

## 🚀 Início Rápido

### 1. Instalação

```bash
# Clone e configure
cd intellicare-oswaldo
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Configure banco de dados
export DATABASE_URL="sqlite:///oswaldo.db"
```

### 2. Testes

```bash
# Execute testes principais
pytest tests/test_day6_*.py -v

# Com cobertura
pytest tests/test_day6_*.py --cov=src/oswaldo --cov-report=html

# Resultado esperado: 114 testes PASSING, ~24% cobertura
```

### 3. Execução

```bash
# Via Python direto
python src/oswaldo/api/main.py

# Ou com uvicorn
uvicorn src.oswaldo.api.main:app --reload --port 8002
```

## 🔌 API Endpoints

### 1. Processar Novo Exame

```bash
curl -X POST http://localhost:8002/api/v1/oswaldo/exames/processar \
  -H "Content-Type: application/json" \
  -d '{
    "paciente_cpf_hash": "abc123xyz",
    "data_coleta": "2026-02-14T10:30:00Z",
    "tipo_exame": "glicemia",
    "valor": 280,
    "unidade": "mg/dL",
    "valor_referencia": "70-100",
    "laboratorio": "Lab Central"
  }'
```

**Resposta (Sucesso)**:
```json
{
  "sucesso": true,
  "mensagem": "Exame processado com sucesso: MAL_CONTROLADO",
  "condicao_id": 42,
  "estadiamento_criado": true,
  "alerta_gerado": true,
  "alerta_id": 157
}
```

### 2. Gerar Plano de Acompanhamento

```bash
curl -X POST http://localhost:8002/api/v1/oswaldo/acompanhamentos/gerar \
  -H "Content-Type: application/json" \
  -d '{
    "condicao_cronica_id": 42,
    "cid10": "E11",
    "diagnostico": "Diabetes Mellitus Tipo 2",
    "nivel_alerta": "ALTO",
    "score_controle": 0.6,
    "parametro_principal": "glicemia",
    "valor_atual": 280,
    "valor_objetivo": 200,
    "medicacoes_atuais": ["Metformina 2g/dia"],
    "aderencia_medicacao": 0.8
  }'
```

### 3. Avaliar Progresso de Objetivo

```bash
curl -X POST http://localhost:8002/api/v1/oswaldo/alertas/avaliar \
  -H "Content-Type: application/json" \
  -d '{
    "objetivo_descricao": "Glicemia em jejum < 130 mg/dL",
    "parametro": "glicemia_jejum",
    "valor_atual": 145,
    "valor_objetivo": 130,
    "unidade": "mg/dL",
    "dados_historicos": [145, 142, 140, 138],
    "dias_desde_inicio": 30
  }'
```

## 🧪 Testes e Cobertura

### Arquitetura de Testes

```
tests/
├── test_day6_e2e_integration.py      (8 testes, E2E pipeline validator)
├── test_day6_plano_cuidado.py        (34 testes, PlanoCuidadoService)
├── test_day6_alerta_service.py       (29 testes, AlertaService)
├── test_day6_acompanhamento_service.py (43 testes, AcompanhamentoService)
├── test_day7_coverage_expansion.py   (7 testes, coverage improvements)
└── conftest.py                        (shared fixtures)
```

### Resultados

```
📊 TOTALIZADORES:
- Tests: 121 PASSING (114 Day 6 + 7 Day 7)
- Coverage: 24% (focus: core services)
  - acompanhamento_service.py: 96%
  - plano_cuidado_service.py: 99%
  - alerta_service.py: 84%
- Performance: Todos < 100ms
```

### Executar Testes Específicos

```bash
# Apenas E2E integration
pytest tests/test_day6_e2e_integration.py -v

# Apenas um serviço
pytestests/test_day6_plano_cuidado.py -v

# Com detalhes de falha
pytest tests/test_day6_*.py -v --tb=short
```

## 🏗️ Arquitetura

### Estrutura de Código

```
src/oswaldo/
├── api/
│   ├── main.py                 (FastAPI app)
│   └── endpoints/              (rotas REST)
├── services/
│   ├── plano_cuidado_service.py      (criação de planos)
│   ├── alerta_service.py              (geração de alertas)
│   ├── acompanhamento_service.py      (planejamento follow-up)
│   └── ...
├── models/                     (SQLAlchemy models)
├── schemas/                    (Pydantic validation)
└── integrations/               (event handlers, RabbitMQ)
```

## 📊 Algoritmos Clínicos

### 1. Classificação de Diabete (ADA 2024)

```
HbA1c < 7.0%        → BEM_CONTROLADO (A0)
7.0% - 8.0%         → MODERADO (A1)
8.0% - 9.0%         → MAL_CONTROLADO (A2)
≥ 9.0%              → CRITICO (A3)
```

### 2. Classificação de HAS (SBC 2023)

```
Sistólica < 120 E Diastólica < 80    → CONTROLADO
140-159 OU 90-99                     → ESTÁGIO 1
160-179 OU 100-109                   → ESTÁGIO 2
≥ 180 OU ≥ 110                       → CRISE HIPERTENSIVA
```

### 3. Classificação de DRC (KDIGO)

```
TFG ≥ 90                  → G1 (Normal/Alta)
TFG 60-89                 → G2 (Levemente reduzida)
TFG 45-59                 → G3a (Moderadamente reduzida)
TFG 30-44                 → G3b (Moderadamente reduzida)
TFG 15-29                 → G4 (Severamente reduzida)
TFG < 15                  → G5 (Falência renal)
```

## 🔍 Troubleshooting

### Erro: "Atributo 'paciente_id' não existe"

**Solução**: Usar `event.paciente_cpf_hash` em vez de `event.paciente_id`

### Erro: "KeyError: 'estagio'"

**Solução**: ClassificacaoService retorna campos como `controle_glicemico`, não `estagio`

### Performance Lenta

- Usar índices no banco de dados
- Cache de métodos `@lru_cache`
- Async/await para I/O

---

**Versão**: 0.6.0 (Day 7 Final Polishing)  
**Status**: ✅ Production-Ready (Core Services)
