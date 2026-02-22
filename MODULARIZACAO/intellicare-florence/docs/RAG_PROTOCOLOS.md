# 🤖 RAG - Protocolos Clínicos

**Versão**: 1.0.0  
**Data**: 2026-02-20  
**Sistema**: Florence RAG (Retrieval-Augmented Generation)

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Como Funciona](#como-funciona)
3. [Protocolos Disponíveis](#protocolos-disponíveis)
4. [Como Adicionar Novos Protocolos](#como-adicionar-novos-protocolos)
5. [Formato de Protocolo](#formato-de-protocolo)
6. [Exemplos de Queries](#exemplos-de-queries)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

### O que é RAG?

RAG (Retrieval-Augmented Generation) é um sistema que combina:
- **Retrieval**: Busca semântica em base de conhecimento
- **Augmented**: Enriquece a análise clínica com protocolos relevantes
- **Generation**: Gera recomendações baseadas em evidências

### Por que usar RAG no Florence?

✅ **Suporte Diagnóstico**: Protocolos clínicos baseados em evidências  
✅ **Busca Semântica**: Encontra protocolos relevantes por contexto, não apenas palavras-chave  
✅ **Auto-Query**: Gera queries automaticamente baseadas na análise clínica  
✅ **Escalável**: Fácil adicionar novos protocolos sem alterar código  
✅ **Auditável**: Rastreabilidade das recomendações

### Arquitetura RAG

```
┌─────────────────┐
│ Análise Clínica │
│  (Labs + Corr)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Auto-Query     │
│  Generation     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Semantic Search │
│   (ChromaDB)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Protocolos    │
│   Relevantes    │
└─────────────────┘
```

---

## ⚙️ Como Funciona

### 1. Indexação (Offline)

```python
from florence.engine.rag.indexer import ProtocolIndexer

# Criar indexer
indexer = ProtocolIndexer(
    chroma_persist_dir="./data/chroma",
    collection_name="clinical_protocols"
)

# Indexar protocolos
indexer.index_protocols_from_directory(
    protocols_dir="./florence/engine/rag/data/protocols"
)
```

**Processo**:
1. Lê arquivos Markdown dos protocolos
2. Extrai metadados (título, especialidade, versão, data)
3. Divide em chunks (500 tokens, overlap de 50)
4. Gera embeddings (OpenAI ou local)
5. Armazena no ChromaDB

### 2. Retrieval (Online)

```python
from florence.engine.rag.retriever import ProtocolRetriever

# Criar retriever
retriever = ProtocolRetriever(
    chroma_persist_dir="./data/chroma",
    collection_name="clinical_protocols"
)

# Buscar protocolos
results = retriever.retrieve(
    query="Como manejar diabetes tipo 2?",
    top_k=3
)
```

**Processo**:
1. Recebe query (customizada ou auto-gerada)
2. Gera embedding da query
3. Busca semântica no ChromaDB (cosine similarity)
4. Retorna top-k protocolos mais relevantes

### 3. Auto-Query Generation

Florence gera queries automaticamente baseadas em:

**Correlações detectadas**:
```
"metabolic_syndrome" → "síndrome metabólica"
"iron_deficiency_anemia" → "anemia ferropriva"
```

**Exames anormais** (top 3 mais críticos):
```
glucose_fasting: 180 (HIGH) → "glucose fasting HIGH"
hba1c: 8.5 (HIGH) → "hba1c HIGH"
```

**Query final**:
```
"Como interpretar e manejar: síndrome metabólica, glucose fasting HIGH, hba1c HIGH"
```

---

## 📚 Protocolos Disponíveis

Florence possui **10 protocolos clínicos** indexados:

### 1. Anemia
- **Especialidade**: Hematologia
- **Versão**: 1.0
- **Data**: 2024-01-15
- **Tamanho**: 4.785 caracteres
- **Chunks**: 3
- **Conteúdo**:
  - Indicações
  - Exames necessários (hemograma, ferritina, B12, folato)
  - Interpretação de resultados
  - Conduta clínica

### 2. Anticoagulação
- **Especialidade**: Hematologia/Cardiologia
- **Versão**: 1.0
- **Data**: 2024-01-15
- **Tamanho**: 9.628 caracteres
- **Chunks**: 4
- **Conteúdo**:
  - Indicações (FA, TEV, próteses valvares)
  - Exames necessários (INR, TP, TTPa, função renal)
  - Interpretação de resultados (tabelas de INR)
  - Monitoramento (varfarina vs DOACs)

### 3. Diabetes Tipo 2
- **Especialidade**: Endocrinologia
- **Versão**: 1.0
- **Data**: 2024-01-15
- **Tamanho**: 3.260 caracteres
- **Chunks**: 2
- **Conteúdo**:
  - Indicações
  - Exames necessários (glicemia, HbA1c, lipidograma)
  - Interpretação de resultados
  - Metas terapêuticas

### 4. Dislipidemia
- **Especialidade**: Cardiologia/Endocrinologia
- **Versão**: 1.0
- **Data**: 2024-01-15
- **Tamanho**: 7.526 caracteres
- **Chunks**: 3
- **Conteúdo**:
  - Indicações
  - Exames necessários (lipidograma completo)
  - Interpretação de resultados (tabelas de risco)
  - Metas terapêuticas por risco cardiovascular

### 5. Exames Periódicos
- **Especialidade**: Medicina Preventiva
- **Versão**: 1.0
- **Data**: 2024-01-15
- **Tamanho**: 8.787 caracteres
- **Chunks**: 4
- **Conteúdo**:
  - Indicações por faixa etária
  - Exames necessários (check-up completo)
  - Interpretação de resultados
  - Periodicidade recomendada

### 6. Hepatopatia
- **Especialidade**: Hepatologia/Gastroenterologia
- **Versão**: 1.0
- **Data**: 2024-01-15
- **Tamanho**: 5.509 caracteres
- **Chunks**: 3
- **Conteúdo**:
  - Indicações
  - Exames necessários (TGO, TGP, GGT, bilirrubinas, albumina)
  - Interpretação de resultados
  - Classificação de gravidade (Child-Pugh, MELD)

### 7. Hipertensão Arterial
- **Especialidade**: Cardiologia
- **Versão**: 1.0
- **Data**: 2024-01-15
- **Tamanho**: 3.984 caracteres
- **Chunks**: 2
- **Conteúdo**:
  - Indicações
  - Exames necessários (função renal, eletrólitos, ECG)
  - Interpretação de resultados
  - Avaliação de lesão de órgão-alvo

### 8. Hipotireoidismo
- **Especialidade**: Endocrinologia
- **Versão**: 1.0
- **Data**: 2024-01-15
- **Tamanho**: 4.012 caracteres
- **Chunks**: 2
- **Conteúdo**:
  - Indicações
  - Exames necessários (TSH, T4 livre, anti-TPO)
  - Interpretação de resultados
  - Conduta terapêutica

### 9. Insuficiência Renal
- **Especialidade**: Nefrologia
- **Versão**: 1.0
- **Data**: 2024-01-15
- **Tamanho**: 5.201 caracteres
- **Chunks**: 3
- **Conteúdo**:
  - Indicações
  - Exames necessários (creatinina, ureia, TFG, eletrólitos)
  - Interpretação de resultados
  - Estadiamento (G1-G5)

### 10. Síndrome Metabólica
- **Especialidade**: Endocrinologia/Cardiologia
- **Versão**: 1.0
- **Data**: 2024-01-15
- **Tamanho**: 4.906 caracteres
- **Chunks**: 3
- **Conteúdo**:
  - Indicações
  - Exames necessários (glicemia, lipidograma, circunferência abdominal)
  - Interpretação de resultados
  - Critérios diagnósticos (NCEP ATP III)

---

## ➕ Como Adicionar Novos Protocolos

### Passo 1: Criar Arquivo Markdown

Crie um arquivo `.md` em `florence/engine/rag/data/protocols/`:

```bash
touch florence/engine/rag/data/protocols/novo_protocolo.md
```

### Passo 2: Seguir Formato Padrão

Veja seção [Formato de Protocolo](#formato-de-protocolo) abaixo.

### Passo 3: Indexar Protocolo

```bash
python scripts/index_protocols.py
```

Ou via código:

```python
from florence.engine.rag.indexer import ProtocolIndexer

indexer = ProtocolIndexer()
indexer.index_protocols_from_directory(
    "./florence/engine/rag/data/protocols"
)
```

### Passo 4: Validar

```bash
python scripts/validate_protocols.py
```

---

## 📝 Formato de Protocolo

### Estrutura Obrigatória

Todo protocolo DEVE ter:

1. **Metadados** (no topo do arquivo)
2. **Título** (# H1)
3. **Seções obrigatórias**:
   - Indicações
   - Exames Necessários
   - Interpretação de Resultados
   - Conduta Clínica

### Template Completo

```markdown
---
title: "Nome do Protocolo"
specialty: "Especialidade Médica"
version: "1.0"
date: "2024-01-15"
source: "Sociedade Brasileira de..."
---

# Nome do Protocolo

## Indicações

Quando solicitar este protocolo:
- Indicação 1
- Indicação 2
- Indicação 3

## Exames Necessários

### Avaliação Inicial

| Exame | Finalidade | Frequência |
|-------|------------|------------|
| Exame 1 | Diagnóstico | Inicial |
| Exame 2 | Monitoramento | Mensal |

### Exames Complementares

- Exame complementar 1
- Exame complementar 2

## Interpretação de Resultados

### Exame 1

| Valor | Interpretação | Conduta |
|-------|---------------|---------|
| < 100 | Normal | Manter acompanhamento |
| 100-125 | Borderline | Repetir em 3 meses |
| > 125 | Anormal | Investigar causa |

### Exame 2

**Normal**: Descrição do resultado normal
**Alterado**: Descrição do resultado alterado
**Crítico**: Descrição do resultado crítico

## Conduta Clínica

### Tratamento Não-Farmacológico

1. Medida 1
2. Medida 2
3. Medida 3

### Tratamento Farmacológico

**Primeira linha**:
- Medicamento 1: dose, via, frequência
- Medicamento 2: dose, via, frequência

**Segunda linha**:
- Medicamento 3: dose, via, frequência

### Monitoramento

- Parâmetro 1: frequência
- Parâmetro 2: frequência
- Parâmetro 3: frequência

## Critérios de Encaminhamento

Encaminhar ao especialista se:
- Critério 1
- Critério 2
- Critério 3

## Referências

1. Referência bibliográfica 1
2. Referência bibliográfica 2
3. Referência bibliográfica 3
```

### Boas Práticas

✅ **Use tabelas** para dados estruturados
✅ **Use listas** para enumerações
✅ **Use negrito** para destacar informações importantes
✅ **Use seções** (##) para organizar conteúdo
✅ **Inclua valores de referência** sempre que possível
✅ **Cite fontes** confiáveis (sociedades médicas, guidelines)
✅ **Mantenha linguagem clara** e objetiva
✅ **Evite jargões** desnecessários

❌ **Não use** imagens (não são indexadas)
❌ **Não use** HTML (use Markdown puro)
❌ **Não use** links externos (podem quebrar)
❌ **Não copie** conteúdo protegido por direitos autorais

---

## 🔍 Exemplos de Queries

### Query 1: Diabetes

**Input**:
```json
{
  "results": {
    "glucose_fasting": 180.0,
    "hba1c": 8.5
  }
}
```

**Auto-Query Gerada**:
```
"Como interpretar e manejar: diabetes pattern, glucose fasting HIGH, hba1c HIGH"
```

**Protocolos Retornados**:
1. Diabetes Tipo 2 (score: 0.95)
2. Síndrome Metabólica (score: 0.78)
3. Exames Periódicos (score: 0.65)

---

### Query 2: Anemia

**Input**:
```json
{
  "results": {
    "hemoglobin": 9.5,
    "hematocrit": 28.0,
    "mcv": 72.0,
    "ferritin": 8.0
  }
}
```

**Auto-Query Gerada**:
```
"Como interpretar e manejar: iron deficiency anemia, hemoglobin LOW, ferritin LOW"
```

**Protocolos Retornados**:
1. Anemia (score: 0.98)
2. Exames Periódicos (score: 0.62)

---

### Query 3: Insuficiência Renal

**Input**:
```json
{
  "results": {
    "creatinine": 3.5,
    "urea": 120.0,
    "potassium": 5.8
  }
}
```

**Auto-Query Gerada**:
```
"Como interpretar e manejar: renal dysfunction, creatinine HIGH, urea HIGH"
```

**Protocolos Retornados**:
1. Insuficiência Renal (score: 0.96)
2. Hipertensão Arterial (score: 0.71)
3. Diabetes Tipo 2 (score: 0.68)

---

### Query 4: Síndrome Metabólica

**Input**:
```json
{
  "results": {
    "glucose_fasting": 180.0,
    "triglycerides": 250.0,
    "hdl": 35.0,
    "systolic_bp": 145.0
  }
}
```

**Auto-Query Gerada**:
```
"Como interpretar e manejar: metabolic syndrome, glucose fasting HIGH, triglycerides HIGH, hdl LOW"
```

**Protocolos Retornados**:
1. Síndrome Metabólica (score: 0.97)
2. Diabetes Tipo 2 (score: 0.89)
3. Dislipidemia (score: 0.85)
4. Hipertensão Arterial (score: 0.76)

---

### Query 5: Customizada

**Input**:
```json
{
  "results": {...},
  "query": "Quais exames solicitar para rastreamento de diabetes em paciente obeso?"
}
```

**Protocolos Retornados**:
1. Diabetes Tipo 2 (score: 0.92)
2. Síndrome Metabólica (score: 0.88)
3. Exames Periódicos (score: 0.81)

---

## 🔧 Troubleshooting

### Problema 1: Protocolos não encontrados

**Erro**: `No protocols found in collection`

**Causas**:
- Protocolos não foram indexados
- ChromaDB não está acessível
- Collection name incorreto

**Solução**:
```bash
# Verificar se protocolos existem
ls florence/engine/rag/data/protocols/

# Re-indexar
python scripts/index_protocols.py

# Verificar ChromaDB
ls data/chroma/
```

---

### Problema 2: Scores muito baixos

**Sintoma**: Todos os protocolos retornam score < 0.5

**Causas**:
- Query muito genérica
- Embeddings de baixa qualidade
- Protocolos não cobrem o tema

**Solução**:
1. Usar queries mais específicas
2. Adicionar protocolos relevantes
3. Verificar modelo de embeddings

---

### Problema 3: Protocolo não aparece nos resultados

**Sintoma**: Protocolo existe mas não é retornado

**Causas**:
- Protocolo não foi indexado
- Conteúdo não é relevante para a query
- top_k muito baixo

**Solução**:
```bash
# Verificar se protocolo foi indexado
curl http://localhost:8002/api/v1/rag/protocols

# Aumentar top_k
{
  "query": "...",
  "top_k": 10  # Aumentar de 3 para 10
}

# Re-indexar protocolo específico
python scripts/index_protocols.py --file protocolo.md
```

---

### Problema 4: Performance lenta

**Sintoma**: Queries RAG demorando > 1s

**Causas**:
- ChromaDB não otimizado
- Muitos chunks indexados
- Modelo de embeddings lento

**Solução**:
1. Reduzir tamanho dos chunks
2. Usar modelo de embeddings mais rápido
3. Implementar cache de queries frequentes

---

### Problema 5: Erro ao indexar

**Erro**: `Failed to index protocol: invalid_protocol.md`

**Causas**:
- Formato Markdown inválido
- Metadados faltando
- Seções obrigatórias ausentes

**Solução**:
```bash
# Validar protocolo
python scripts/validate_protocols.py --file invalid_protocol.md

# Ver erros específicos
python scripts/validate_protocols.py --verbose
```

---

## 📊 Estatísticas

### Protocolos Indexados

- **Total**: 10 protocolos
- **Total de chunks**: 30 chunks
- **Tamanho médio**: 5.760 caracteres/protocolo
- **Chunks por protocolo**: 3.0 (média)

### Especialidades Cobertas

- Cardiologia: 3 protocolos
- Endocrinologia: 4 protocolos
- Hematologia: 2 protocolos
- Nefrologia: 1 protocolo
- Hepatologia: 1 protocolo
- Medicina Preventiva: 1 protocolo

### Performance

- **Indexação**: ~2s para 10 protocolos
- **Query**: < 500ms (p95)
- **Precisão**: > 0.85 (score médio top-1)

---

## 🚀 Roadmap

### Próximas Funcionalidades

- [ ] Suporte a múltiplos idiomas
- [ ] Versionamento de protocolos
- [ ] Feedback loop (relevância)
- [ ] Cache de queries frequentes
- [ ] Integração com LLM para resumos
- [ ] Exportação de protocolos (PDF)

### Novos Protocolos Planejados

- [ ] Osteoporose
- [ ] Doença Renal Crônica (DRC)
- [ ] Insuficiência Cardíaca
- [ ] DPOC (Doença Pulmonar Obstrutiva Crônica)
- [ ] Artrite Reumatoide
- [ ] Lúpus Eritematoso Sistêmico
- [ ] Doença Celíaca
- [ ] Hepatite C
- [ ] HIV/AIDS
- [ ] Tuberculose

---

## 📞 Suporte

**Documentação**: `docs/`
**Guia de Uso**: `docs/GUIA_USO_FLORENCE.md`
**API Reference**: `docs/API_REFERENCE.md`
**Scripts**: `scripts/`

---

**Versão**: 1.0.0
**Última Atualização**: 2026-02-20
**Autor**: Equipe IntelliCare


