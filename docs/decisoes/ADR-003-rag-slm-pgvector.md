---
tipo: adr
id: ADR-003
titulo: Tríade RAG+SLM+pgvector como core de IA clínica
status: aprovado
data: 2026-03-13
decidido_por: Eduardo (Arquiteto)
tags: [ia, rag, slm, pgvector, arquitetura, cuidado]
---

# ADR-003 — Tríade RAG+SLM+pgvector

## Decisão

A inteligência clínica do IntelliCare V3 é construída sobre três componentes
que rodam **localmente**, sem hops de rede externos:

1. **pgvector** — extensão do PostgreSQL. Embeddings ficam na mesma tabela
   dos dados clínicos do tenant. Sem banco vetorial externo.

2. **SLM local via OLLAMA** — modelo leve (Qwen2.5-7B ou similar).
   Inferência em ~100-300ms, sem chamada para API externa.

3. **RAG pipeline** — busca semântica (`ORDER BY embedding <=> $1 LIMIT 5`)
   + síntese via SLM. **Latência alvo: <300ms total.**

## Contexto

Stack V2: WANDA → LangGraph → FLORENCE → Flowise → OLLAMA → Pinecone.
4-5 hops de rede por consulta. Latência >2s. Inaceitável para uso clínico
(janela de atenção do profissional: <30 segundos).

## Por que funciona aqui

| Componente | Vantagem |
|-----------|---------|
| pgvector dentro do PostgreSQL | Sem serviço extra; embeddings no mesmo `pg_dump` que os dados clínicos |
| Índice HNSW por tenant | Busca sub-linear mesmo com 100k+ protocolos por tenant |
| SLM local (OLLAMA) | Zero latência de rede; modelo ajustável sem custo por token |
| Schema por tenant | Isolamento nativo; cada tenant tem seus próprios embeddings |

## Fluxo de referência

```python
# Etapa 1 — Gerar embedding da consulta: ~10ms
query_embedding = await ollama_embed(query, model="nomic-embed-text")

# Etapa 2 — Busca semântica pgvector: ~5ms
results = await db.execute(f"""
    SELECT title, content, program,
           1 - (embedding <=> :emb) AS similarity
    FROM {tenant_schema}.protocols
    ORDER BY embedding <=> :emb
    LIMIT 5
""", {"emb": query_embedding})

# Etapa 3 — Síntese SLM local: ~200ms
context = "\n---\n".join(r.content for r in results)
response = await ollama_generate(
    model="qwen2.5:7b",
    prompt=f"Baseado nos protocolos abaixo, responda: {query}\n\n{context}"
)
# Total: ~215ms
```

## Schema pgvector (dentro do schema do tenant)

```sql
CREATE TABLE tenant_{slug}.protocols (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    program     TEXT,                   -- 'drc', 'diabetes', 'has', 'cancer'
    source      TEXT,
    embedding   vector(384) NOT NULL,   -- pgvector
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- Índice HNSW para busca sub-linear
CREATE INDEX ON tenant_{slug}.protocols
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

## Pipeline de ingestão

```
docs/references/*.md
  + docs/modulos/*.md
  + protocolos clínicos (SBEM, MS, CFM)
        ↓
tools/scripts/ingest_docs.py
  → chunking (512 tokens, 50 tokens overlap)
  → embedding via OLLAMA (nomic-embed-text)
  → INSERT INTO tenant_{slug}.protocols
```

## Consequências

- Toda inferência roda localmente — zero custo por token, zero dependência de API externa
- Dados clínicos nunca saem do servidor (LGPD compliance by design)
- Modelo SLM é substituível sem alterar código (troca via env `SLM_MODEL`)
- Embeddings vivem no mesmo `pg_dump` que os dados clínicos — backup unificado
- Requer servidor com RAM suficiente para OLLAMA (~4GB para modelos 3B)
- Qualidade de resposta limitada pelo modelo local (trade-off vs. GPT-4/Claude)

## Alternativas rejeitadas

| Alternativa | Por que foi descartada |
|-------------|----------------------|
| **APIs externas (OpenAI, Anthropic)** | Dados clínicos sensíveis (LGPD) não podem trafegar para servidores externos. Custo por token imprevisível. Latência de rede adicional (~500ms+). Dependência de disponibilidade de terceiros. |
| **Banco vetorial dedicado (Pinecone, Milvus, Qdrant)** | Serviço extra para operar. Dados ficam separados do PostgreSQL — backup e restore mais complexos. pgvector é suficiente para o volume esperado (<1M chunks por tenant). |
| **LangChain/LangGraph como orquestrador** | V2 usava LangGraph. Adicionava 4-5 hops de rede por consulta (>2s latência). Abstração desnecessária quando o pipeline é linear (embed → search → generate). |
| **Fine-tuning de modelo próprio** | Custo de treinamento e manutenção. RAG com modelo genérico + contexto de protocolos é suficiente e atualizável em tempo real (re-ingestão). |

## Implementação

- DEM-002: `CREATE EXTENSION vector`, docker-compose com OLLAMA
- DEM-002: `tools/scripts/ingest_docs.py` (pipeline de ingestão)
- DEM-003: `packages/intellicare-core/vector/` (helpers de embedding)
- DEM-013: módulo `cuidado` com busca semântica e síntese
- DEM-014: programas de saúde indexados (DRC, Diabetes, HAS, Câncer)
