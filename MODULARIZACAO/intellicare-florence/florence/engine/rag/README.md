# RAG - Retrieval-Augmented Generation para Protocolos Clínicos

Sistema de busca semântica de protocolos clínicos usando RAG (Retrieval-Augmented Generation).

---

## 📚 Visão Geral

O módulo RAG permite:
- **Indexar** protocolos clínicos em formato Markdown
- **Buscar** protocolos relevantes usando busca semântica
- **Recuperar** informações contextuais para análise clínica

---

## 🏗️ Arquitetura

```
florence/engine/rag/
├── __init__.py           # Exports principais
├── models.py             # Modelos de dados (Protocol, RAGQuery, RAGResult)
├── indexer.py            # Indexador de protocolos
├── retriever.py          # Retriever de protocolos
└── data/
    └── protocols/        # Protocolos clínicos (.md)
        ├── diabetes_tipo2.md
        ├── hipertensao_arterial.md
        ├── insuficiencia_renal.md
        └── ...
```

---

## 🚀 Uso Rápido

### 1. Indexar Protocolos

```python
from florence.engine.rag.indexer import ProtocolIndexer

# Criar indexer
indexer = ProtocolIndexer(
    protocols_dir="florence/engine/rag/data/protocols",
    chroma_persist_dir="./data/chroma",
)

# Indexar todos os protocolos
results = indexer.index_all_protocols()
print(f"Indexados: {len(results)} protocolos")

# Ver estatísticas
stats = indexer.get_stats()
print(f"Total de chunks: {stats['total_chunks']}")
```

### 2. Buscar Protocolos

```python
from florence.engine.rag.retriever import ProtocolRetriever
from florence.engine.rag.models import RAGQuery

# Criar retriever
retriever = ProtocolRetriever(
    chroma_persist_dir="./data/chroma",
)

# Buscar protocolos
query = RAGQuery(
    query="Como manejar paciente com creatinina elevada?",
    top_k=3,
)

response = retriever.query(query)

for result in response.results:
    print(f"Título: {result.title}")
    print(f"Score: {result.score:.3f}")
    print(f"Conteúdo: {result.content[:200]}...")
```

### 3. Buscar por Especialidade

```python
results = retriever.search_by_specialty(
    specialty="Cardiologia",
    top_k=5,
)
```

---

## 📋 Protocolos Disponíveis

| Protocolo | Especialidade | Descrição |
|-----------|---------------|-----------|
| `diabetes_tipo2.md` | Endocrinologia | Manejo de DM2 |
| `hipertensao_arterial.md` | Cardiologia | Manejo de HAS |
| `insuficiencia_renal.md` | Nefrologia | IRC estadiamento |
| `dislipidemia.md` | Cardiologia/Endocrinologia | Manejo de colesterol |
| `anemia.md` | Hematologia | Investigação e tratamento |
| `hepatopatia.md` | Hepatologia/Gastro | Lesão hepática |
| `hipotireoidismo.md` | Endocrinologia | Disfunção tireoidiana |
| `sindrome_metabolica.md` | Endocrinologia/Cardio | Critérios e manejo |
| `anticoagulacao.md` | Hematologia/Cardio | Manejo de INR |
| `exames_periodicos.md` | Medicina Preventiva | Rastreamento |

---

## 🔧 Configuração

### Dependências

```toml
langchain = "^0.1.0"
langchain-openai = "^0.0.5"
langchain-community = "^0.0.20"
chromadb = "^0.4.22"
tiktoken = "^0.5.2"
```

### Instalação

```bash
cd MODULARIZACAO/intellicare-florence
poetry install
```

---

## 📝 Formato de Protocolo

Cada protocolo deve seguir este formato Markdown:

```markdown
# [Nome do Protocolo]

**Especialidade**: [Especialidade]  
**Versão**: 1.0  
**Data**: 2026-02-15  
**Fonte**: [Referência científica]

## Indicações

[Quando usar este protocolo]

## Critérios Diagnósticos

[Critérios clínicos e laboratoriais]

## Exames Necessários

[Lista de exames]

## Interpretação de Resultados

[Como interpretar]

## Conduta

[Ações recomendadas]

## Critérios de Encaminhamento

[Quando referenciar]

## Referências

[Bibliografia]
```

---

## 🧪 Testes

```bash
# Executar testes do RAG
pytest tests/test_rag_indexer.py -v
pytest tests/test_rag_retriever.py -v

# Com cobertura
pytest tests/test_rag_*.py --cov=florence.engine.rag
```

---

## 📊 Performance

- **Indexação**: ~10 protocolos em < 5 segundos
- **Busca**: < 200ms (p95)
- **Chunks**: ~15 chunks por protocolo (média)

---

## 🔍 Exemplos de Queries

```python
# Query 1: Manejo de IRC
query = "Como manejar paciente com creatinina elevada?"

# Query 2: Metas de controle
query = "Qual a meta de HbA1c para diabéticos?"

# Query 3: Tratamento
query = "Como tratar hipertensão em diabéticos?"

# Query 4: Indicações
query = "Quando indicar estatina?"

# Query 5: Investigação
query = "Como investigar anemia?"
```

---

## 📚 Referências

- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [RAG Pattern](https://arxiv.org/abs/2005.11401)


