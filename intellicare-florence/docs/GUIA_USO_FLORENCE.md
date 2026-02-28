# 📘 Guia de Uso - Florence (Análise Clínica)

**Versão**: 1.0.0  
**Data**: 2026-02-20  
**Módulo**: Florence - Clinical Analysis Module

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Instalação e Setup](#instalação-e-setup)
3. [Como Usar](#como-usar)
4. [Interpretação de Resultados](#interpretação-de-resultados)
5. [RAG - Consulta a Protocolos](#rag---consulta-a-protocolos)
6. [Exemplos Práticos](#exemplos-práticos)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

---

## 🎯 Visão Geral

### O que é o Florence?

Florence é o módulo de **Análise Clínica** do ecossistema IntelliCare. Ele interpreta resultados laboratoriais, detecta correlações clínicas, identifica tendências e fornece suporte diagnóstico baseado em protocolos clínicos via RAG (Retrieval-Augmented Generation).

### Principais Funcionalidades

✅ **Interpretação de Exames Laboratoriais**
- 27 tipos de exames suportados
- 6 painéis clínicos (Hemograma, Metabólico, Lipídico, Hepático, Renal, Tireoidiano)
- Classificação automática (normal, borderline, anormal)

✅ **Detecção de Correlações Clínicas**
- 8 padrões clínicos detectados automaticamente
- Síndrome metabólica, anemia ferropriva, disfunção renal, etc.

✅ **Análise de Tendências**
- Detecção de tendências em séries temporais
- Regressão linear para prever evolução
- Alertas de piora ou melhora

✅ **RAG - Protocolos Clínicos**
- 10 protocolos clínicos indexados
- Busca semântica por contexto clínico
- Auto-geração de queries baseada em análise

✅ **Conformidade LGPD**
- Anonimização automática de dados sensíveis
- Logs auditáveis
- Controle de acesso

### Arquitetura

```
Florence
├── Engine (Core)
│   ├── Lab Interpreter (27 exames)
│   ├── Correlation Detector (8 padrões)
│   ├── Trend Detector (séries temporais)
│   └── RAG System (protocolos clínicos)
├── API (FastAPI)
│   ├── 7 endpoints core
│   └── 3 endpoints RAG
└── Data
    ├── Reference Ranges (YAML)
    └── Clinical Protocols (Markdown)
```

---

## 🚀 Instalação e Setup

### Pré-requisitos

- Python 3.11+
- pip ou poetry
- intellicare-core SDK

### Instalação

#### Opção 1: Com Poetry (Recomendado)

```bash
cd intellicare-florence
poetry install
```

#### Opção 2: Com pip

```bash
cd intellicare-florence
pip install -e .
```

### Configuração

#### 1. Variáveis de Ambiente

Crie um arquivo `.env`:

```bash
# Configuração do Módulo
MODULE_NAME=florence
MODULE_PORT=8002
MODULE_HOST=0.0.0.0

# Feature Flags
ENABLE_RAG=true
ENABLE_DIAGNOSTIC_SUPPORT=true

# RAG Configuration
RAG_CHROMA_DIR=./data/chroma
RAG_PROTOCOLS_DIR=./florence/engine/rag/data/protocols
RAG_TOP_K_DEFAULT=3

# LGPD
ENABLE_ANONYMIZATION=true
```

#### 2. Inicializar RAG (Opcional)

Se você habilitou RAG, indexe os protocolos:

```bash
python scripts/index_protocols.py
```

### Executar o Servidor

```bash
# Com uvicorn
uvicorn florence.api.app:app --host 0.0.0.0 --port 8002 --reload

# Ou com o script
python -m florence.api.app
```

### Verificar Saúde

```bash
curl http://localhost:8002/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "module": "florence",
  "version": "1.0.0",
  "timestamp": "2026-02-20T10:00:00Z"
}
```

---

## 💡 Como Usar

Florence oferece **3 métodos principais** de análise:

### Método 1: Interpretação Simples

**Endpoint**: `POST /api/v1/interpret`

**Quando usar**: Quando você quer apenas interpretar exames sem análise avançada.

**Exemplo**:
```python
import requests

response = requests.post(
    "http://localhost:8002/api/v1/interpret",
    json={
        "patient_id": "PAT-001",
        "results": {
            "glucose_fasting": 180.0,
            "hba1c": 8.5
        }
    }
)

data = response.json()
print(data["interpretations"])
```

### Método 2: Análise Completa (com Correlações)

**Endpoint**: `POST /api/v1/analyze`

**Quando usar**: Quando você quer detectar correlações e padrões clínicos.

**Exemplo**:
```python
response = requests.post(
    "http://localhost:8002/api/v1/analyze",
    json={
        "patient_id": "PAT-002",
        "results": {
            "glucose_fasting": 180.0,
            "hba1c": 8.5,
            "triglycerides": 250.0,
            "hdl": 35.0,
            "systolic_bp": 145.0
        }
    }
)

data = response.json()
print(data["correlations"])  # Detecta síndrome metabólica
```

### Método 3: Análise com RAG (Protocolos Clínicos)

**Endpoint**: `POST /api/v1/analyze-with-rag`

**Quando usar**: Quando você quer recomendações baseadas em protocolos clínicos.

**Exemplo**:
```python
response = requests.post(
    "http://localhost:8002/api/v1/analyze-with-rag",
    json={
        "patient_id": "PAT-003",
        "results": {
            "glucose_fasting": 180.0,
            "hba1c": 8.5
        },
        "query": "Como manejar diabetes tipo 2?",  # Opcional
        "top_k": 3
    }
)

data = response.json()
print(data["relevant_protocols"])  # Protocolos relevantes
```

---

## 📊 Interpretação de Resultados

### Estrutura da Resposta

Todas as análises retornam uma estrutura similar:

```json
{
  "patient_id": "PAT-001",
  "timestamp": "2026-02-20T10:00:00Z",
  "interpretations": [...],
  "correlations": [...],
  "summary": {...},
  "relevant_protocols": [...]  // Apenas com RAG
}
```

### Campos Principais

#### 1. `interpretations`

Lista de interpretações de cada exame:

```json
{
  "lab_id": "glucose_fasting",
  "value": 180.0,
  "unit": "mg/dL",
  "reference_range": {"min": 70.0, "max": 100.0},
  "status": "HIGH",
  "severity": "MODERATE",
  "clinical_significance": "Hiperglicemia de jejum..."
}
```

**Status possíveis**:
- `NORMAL`: Dentro da faixa de referência
- `BORDERLINE`: Próximo ao limite
- `LOW`: Abaixo do normal
- `HIGH`: Acima do normal
- `CRITICAL_LOW`: Criticamente baixo
- `CRITICAL_HIGH`: Criticamente alto

#### 2. `correlations`

Padrões clínicos detectados:

```json
{
  "pattern_name": "metabolic_syndrome",
  "confidence": 0.85,
  "involved_labs": ["glucose_fasting", "triglycerides", "hdl"],
  "clinical_interpretation": "Síndrome metabólica detectada..."
}
```

**Padrões detectados**:
- `metabolic_syndrome`: Síndrome metabólica
- `iron_deficiency_anemia`: Anemia ferropriva
- `renal_dysfunction`: Disfunção renal
- `liver_dysfunction`: Disfunção hepática
- `hypothyroidism`: Hipotireoidismo
- `hyperthyroidism`: Hipertireoidismo
- `dyslipidemia`: Dislipidemia
- `diabetes_pattern`: Padrão diabético

#### 3. `summary`

Resumo executivo da análise:

```json
{
  "total_labs": 5,
  "abnormal_count": 3,
  "critical_count": 0,
  "correlations_detected": 1,
  "overall_status": "ATTENTION_NEEDED"
}
```

---

## 🔍 RAG - Consulta a Protocolos

### O que é RAG?

RAG (Retrieval-Augmented Generation) é um sistema que busca protocolos clínicos relevantes baseado no contexto da análise.

### Como Funciona?

1. **Análise Clínica**: Florence analisa os exames
2. **Geração de Query**: Cria uma query baseada nos achados
3. **Busca Semântica**: Busca protocolos relevantes no ChromaDB
4. **Retorno**: Retorna os top-k protocolos mais relevantes

### Protocolos Disponíveis

Florence possui **10 protocolos clínicos** indexados:

1. **Anemia** (Hematologia)
2. **Anticoagulação** (Hematologia/Cardiologia)
3. **Diabetes Tipo 2** (Endocrinologia)
4. **Dislipidemia** (Cardiologia/Endocrinologia)
5. **Exames Periódicos** (Medicina Preventiva)
6. **Hepatopatia** (Hepatologia/Gastroenterologia)
7. **Hipertensão Arterial** (Cardiologia)
8. **Hipotireoidismo** (Endocrinologia)
9. **Insuficiência Renal** (Nefrologia)
10. **Síndrome Metabólica** (Endocrinologia/Cardiologia)

### Usando RAG

#### Opção 1: Query Customizada

```python
response = requests.post(
    "http://localhost:8002/api/v1/analyze-with-rag",
    json={
        "patient_id": "PAT-001",
        "results": {"creatinine": 3.5, "urea": 120.0},
        "query": "Como manejar insuficiência renal crônica?",
        "top_k": 3
    }
)
```

#### Opção 2: Auto-Query (Recomendado)

Florence gera automaticamente a query baseada nos achados:

```python
response = requests.post(
    "http://localhost:8002/api/v1/analyze-with-rag",
    json={
        "patient_id": "PAT-001",
        "results": {"creatinine": 3.5, "urea": 120.0}
        # Sem campo "query" - Florence gera automaticamente
    }
)
```

#### Opção 3: Query Direta ao RAG

```python
response = requests.post(
    "http://localhost:8002/api/v1/rag/query",
    json={
        "query": "Quais exames solicitar para diabetes?",
        "top_k": 3
    }
)
```

---

## 📚 Exemplos Práticos

### Exemplo 1: Paciente com Diabetes

```python
import requests

# Dados do paciente
patient_data = {
    "patient_id": "PAT-DIABETES-001",
    "results": {
        "glucose_fasting": 180.0,
        "hba1c": 8.5,
        "triglycerides": 250.0,
        "hdl": 35.0
    }
}

# Análise com RAG
response = requests.post(
    "http://localhost:8002/api/v1/analyze-with-rag",
    json=patient_data
)

data = response.json()

# Exibir interpretações
print("=== INTERPRETAÇÕES ===")
for interp in data["interpretations"]:
    print(f"{interp['lab_id']}: {interp['value']} {interp['unit']} - {interp['status']}")

# Exibir correlações
print("\n=== CORRELAÇÕES ===")
for corr in data["correlations"]:
    print(f"- {corr['pattern_name']} (confiança: {corr['confidence']:.2f})")

# Exibir protocolos relevantes
print("\n=== PROTOCOLOS RELEVANTES ===")
for protocol in data["relevant_protocols"]:
    print(f"- {protocol['title']} (score: {protocol['score']:.2f})")
```

### Exemplo 2: Paciente com Anemia

```python
patient_data = {
    "patient_id": "PAT-ANEMIA-001",
    "results": {
        "hemoglobin": 9.5,
        "hematocrit": 28.0,
        "mcv": 72.0,
        "ferritin": 8.0
    }
}

response = requests.post(
    "http://localhost:8002/api/v1/analyze-with-rag",
    json=patient_data
)

data = response.json()

# Florence detectará "iron_deficiency_anemia" e buscará protocolo de anemia
```

### Exemplo 3: Análise de Tendências

```python
# Histórico de glicemia
history = [
    {"timestamp": "2026-01-01T00:00:00Z", "results": {"glucose_fasting": 110.0}},
    {"timestamp": "2026-01-15T00:00:00Z", "results": {"glucose_fasting": 130.0}},
    {"timestamp": "2026-02-01T00:00:00Z", "results": {"glucose_fasting": 150.0}},
    {"timestamp": "2026-02-15T00:00:00Z", "results": {"glucose_fasting": 170.0}},
]

response = requests.post(
    "http://localhost:8002/api/v1/analyze-trends",
    json={
        "patient_id": "PAT-TREND-001",
        "history": history
    }
)

data = response.json()

# Exibir tendências
for trend in data["trends"]:
    print(f"{trend['lab_id']}: {trend['direction']} (slope: {trend['slope']:.2f})")
```

### Exemplo 4: Listar Recursos Disponíveis

```python
response = requests.get("http://localhost:8002/api/v1/resources")
data = response.json()

print("=== EXAMES SUPORTADOS ===")
for lab in data["supported_labs"]:
    print(f"- {lab['id']}: {lab['name']} ({lab['unit']})")

print("\n=== PAINÉIS DISPONÍVEIS ===")
for panel in data["panels"]:
    print(f"- {panel['name']}: {len(panel['labs'])} exames")
```

### Exemplo 5: Listar Protocolos RAG

```python
response = requests.get("http://localhost:8002/api/v1/rag/protocols")
data = response.json()

print("=== PROTOCOLOS CLÍNICOS ===")
for protocol in data["protocols"]:
    print(f"- {protocol['title']} ({protocol['specialty']})")
```

---

## 🔧 Troubleshooting

### Problema 1: Servidor não inicia

**Erro**: `ModuleNotFoundError: No module named 'florence'`

**Solução**:
```bash
# Reinstalar o módulo
pip install -e .
# ou
poetry install
```

### Problema 2: RAG não funciona

**Erro**: `ModuleNotFoundError: No module named 'chromadb'`

**Solução**:
```bash
# Instalar dependências RAG
pip install chromadb tiktoken langchain
```

### Problema 3: Protocolos não encontrados

**Erro**: `No protocols found`

**Solução**:
```bash
# Indexar protocolos
python scripts/index_protocols.py
```

### Problema 4: Exame não reconhecido

**Erro**: `Lab ID 'xyz' not found`

**Solução**:
```python
# Listar exames suportados
response = requests.get("http://localhost:8002/api/v1/resources")
print(response.json()["supported_labs"])
```

### Problema 5: Performance lenta

**Sintoma**: Análises demorando > 1s

**Solução**:
1. Desabilitar RAG se não estiver usando: `ENABLE_RAG=false`
2. Reduzir `top_k` nas queries RAG
3. Verificar logs de performance

---

## ❓ FAQ

### 1. Quantos exames o Florence suporta?

Florence suporta **27 tipos de exames** distribuídos em 6 painéis clínicos.

### 2. O RAG é obrigatório?

Não. RAG é opcional e pode ser desabilitado via `ENABLE_RAG=false`.

### 3. Como adicionar novos protocolos?

Veja a documentação em `docs/RAG_PROTOCOLOS.md`.

### 4. Florence substitui um médico?

**NÃO**. Florence é uma ferramenta de **suporte diagnóstico**. Todas as decisões clínicas devem ser tomadas por profissionais de saúde qualificados.

### 5. Os dados são anonimizados?

Sim, se `ENABLE_ANONYMIZATION=true`. Florence remove automaticamente dados sensíveis dos logs.

### 6. Qual a performance esperada?

- Interpretação simples: < 200ms (p95)
- Análise completa: < 300ms (p95)
- Análise com RAG: < 500ms (p95)

### 7. Florence é compatível com FHIR?

Sim. Florence usa FHIR R4 para comunicação com outros módulos do IntelliCare.

### 8. Como reportar bugs?

Abra uma issue no repositório ou contate a equipe de desenvolvimento.

---

## 📞 Suporte

**Documentação**: `docs/`
**API Reference**: `docs/API_REFERENCE.md`
**Protocolos RAG**: `docs/RAG_PROTOCOLOS.md`
**Testes**: `tests/`

---

**Versão**: 1.0.0
**Última Atualização**: 2026-02-20
**Autor**: Equipe IntelliCare


