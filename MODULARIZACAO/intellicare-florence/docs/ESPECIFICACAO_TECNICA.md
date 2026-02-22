# intellicare-florence — Especificacao Tecnica

## 1. Estrutura

```
intellicare-florence/
├── florence/
│   ├── __init__.py
│   ├── config.py               # FlorenceConfig extends BaseConfig
│   ├── api/                    # FastAPI REST
│   │   ├── app.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── info.py
│   │       ├── analyze.py      # POST /api/v1/analyze (analise clinica)
│   │       └── interpret.py    # POST /api/v1/interpret (exames)
│   ├── engine/
│   │   ├── clinical_analyzer.py  # Motor principal de analise
│   │   ├── lab_interpreter.py    # Interpretacao de laboratoriais
│   │   ├── trend_detector.py     # Deteccao de tendencias
│   │   └── rag/
│   │       ├── retriever.py      # RAG retriever (protocolos clinicos)
│   │       ├── indexer.py        # Indexador de documentos
│   │       └── protocols/        # Base de protocolos clinicos
│   ├── ui/                     # Streamlit
│   │   └── main.py
│   └── subagent/               # Para Wanda
│       └── florence_subagent.py
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## 2. Dependencias Especificas

```
# Alem do intellicare-core:
langchain>=0.3.0           # RAG
langchain-anthropic>=0.3.0 # LLM
chromadb>=0.5.0            # Vector store para RAG
sentence-transformers      # Embeddings locais
```

## 3. Maturidade Atual

- Skeleton existente no monolito (1/10)
- Maior parte e novo desenvolvimento
- Prioridade ALTA apos Oswaldo funcionar isolado
