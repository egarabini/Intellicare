---
tipo: nota-modulo
modulo: cuidado
porto: 8004
fase: 3
sprint: "3.3"
status: pendente
dem_principal: DEM-013
tags: [fase-3, cuidado, rag, slm, pgvector]
---

# Módulo: cuidado

**Responsabilidade:** Cuidado clínico base com busca semântica de protocolos (RAG+SLM).

---

## O que entrega

- Consulta de protocolos clínicos via busca semântica (pgvector)
- Síntese de resposta contextualizada via SLM local (OLLAMA)
- Programas de saúde: DRC, Diabetes, HAS, Câncer
- **Latência alvo: <300ms por consulta**

## Tabela principal (pgvector)

```sql
tenant_{slug}.protocols (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    program     TEXT,           -- 'drc', 'diabetes', 'has', 'cancer'
    source      TEXT,
    embedding   vector(384),    -- pgvector (nomic-embed-text)
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON tenant_{slug}.protocols
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

## Fluxo de consulta

```
Profissional pergunta
    ↓
Embedding da pergunta via OLLAMA (~10ms)
    ↓
SELECT FROM protocols ORDER BY embedding <=> $1 LIMIT 5  (~5ms)
    ↓
SLM sintetiza resposta com os 5 chunks (~200ms)
    ↓
Resposta fundamentada com fonte rastreável
```

## Dependências

- [[decisoes/ADR-003-rag-slm-pgvector]]
- pgvector ativo (DEM-002)
- SLM OLLAMA configurado (DEM-002)
- intellicare-core/vector/ helpers (DEM-003)

## DEMs relacionadas

- DEM-013: Cuidado backend (busca semântica + síntese)
- DEM-014: Programas de saúde indexados (DRC, Diabetes, HAS, Câncer)
- DEM-015: Frontend clínico MVP
