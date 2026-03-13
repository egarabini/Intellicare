---
tipo: referencia
tecnologia: pgvector
versao: "0.7+"
tags: [referencia, pgvector, postgres, vector, embedding, rag]
---

# pgvector — Referência Rápida

> Extensão PostgreSQL para busca por similaridade vetorial. Core do RAG no IntelliCare.

---

## Setup

```sql
-- Habilitar extensão (uma vez por banco)
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Tipo `vector`

```sql
-- Coluna de embedding com dimensão fixa
embedding vector(768)   -- nomic-embed-text usa dim 768
```

---

## Tabela de chunks (IntelliCare)

```sql
CREATE TABLE tenant_{slug}.knowledge_base (
    id           SERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    content      TEXT NOT NULL,
    source_path  TEXT NOT NULL,
    chunk_index  INTEGER NOT NULL,
    embedding    vector(768) NOT NULL,
    metadata     JSONB DEFAULT '{}',
    created_at   TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT uq_kb_source_chunk UNIQUE (source_path, chunk_index)
);
```

---

## Índices

### HNSW (recomendado para produção)

```sql
CREATE INDEX idx_kb_embedding ON tenant_{slug}.knowledge_base
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `m` | 16 | Conexões por nó (mais = mais preciso, mais memória) |
| `ef_construction` | 64 | Qualidade na construção (mais = mais lento para insert) |

### IVFFlat (alternativa para datasets grandes)

```sql
CREATE INDEX ON knowledge_base
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

---

## Operadores de distância

| Operador | Tipo | Uso |
|----------|------|-----|
| `<=>` | Distância coseno | `ORDER BY embedding <=> $1` (padrão IntelliCare) |
| `<->` | Distância L2 (euclidiana) | `ORDER BY embedding <-> $1` |
| `<#>` | Produto interno negativo | `ORDER BY embedding <#> $1` |

---

## Busca semântica

```sql
-- Top 5 chunks mais similares
SELECT
    title,
    content,
    source_path,
    1 - (embedding <=> :query_embedding) AS similarity
FROM tenant_{slug}.knowledge_base
WHERE 1 - (embedding <=> :query_embedding) > 0.5  -- min_similarity
ORDER BY embedding <=> :query_embedding
LIMIT 5;
```

### Em Python (SQLAlchemy)

```python
from sqlalchemy import text

async def semantic_search(session, query_embedding, limit=5, min_sim=0.5):
    result = await session.execute(
        text("""
            SELECT title, content, source_path,
                   1 - (embedding <=> :emb) AS similarity
            FROM knowledge_base
            WHERE 1 - (embedding <=> :emb) > :min_sim
            ORDER BY embedding <=> :emb
            LIMIT :limit
        """),
        {"emb": str(query_embedding), "min_sim": min_sim, "limit": limit}
    )
    return result.mappings().all()
```

---

## Upsert idempotente

```sql
INSERT INTO knowledge_base (title, content, source_path, chunk_index, embedding)
VALUES (:title, :content, :path, :idx, :emb)
ON CONFLICT (source_path, chunk_index)
DO UPDATE SET
    title = EXCLUDED.title,
    content = EXCLUDED.content,
    embedding = EXCLUDED.embedding;
```

---

## Performance tips

- **Batch inserts**: inserir chunks em lotes de 32-64 para reduzir overhead de transação
- **ef_search** em runtime: `SET hnsw.ef_search = 100;` (default 40, mais = mais preciso)
- **Vacuum**: `VACUUM ANALYZE knowledge_base;` após ingestão em massa
- **Dimensão**: 768 (nomic-embed-text) é ótimo para recall vs. custo de armazenamento

---

## Links úteis

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [HNSW vs IVFFlat](https://github.com/pgvector/pgvector#indexing)
- [pgvector + SQLAlchemy](https://github.com/pgvector/pgvector-python)

