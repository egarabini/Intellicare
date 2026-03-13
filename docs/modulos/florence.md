---
tipo: nota-modulo
modulo: florence
porto: 8001
fase: 3
sprint: "3.x"
status: pendente
dem_principal: DEM-009
score_v2: "1/10"
tags: [fase-3, florence, rag, protocolos, vector]
---

# Módulo: florence

**Responsabilidade:** Pipeline RAG completo — ingestão de documentos, busca semântica (pgvector) e gestão da base de conhecimento por tenant. V2: score 1/10. V3: reconstruída como módulo `vector`.

---

## Distinção em relação ao módulo `cuidado`

| `cuidado` | `florence` (vector) |
|-----------|---------------------|
| Fluxo clínico (o que fazer com o protocolo) | Pipeline de dados (ingestão, chunking, embedding, busca) |
| Interface para o profissional | Infraestrutura RAG para qualquer módulo consumir |
| Consome resultados da busca | Produz e mantém os chunks na knowledge_base |

Florence/vector é o **pipeline de dados**. Cuidado é o **fluxo clínico**.

---

## Propósito

Gerencia o ciclo completo de documentos na base de conhecimento: upload → chunking → embedding (OLLAMA nomic-embed-text) → upsert em `knowledge_base` (pgvector). Provê busca semântica e watcher automático de novos arquivos.

---

## Endpoints Principais

| Método | Rota | Descrição | Role |
|--------|------|-----------|------|
| GET | `/vector/health` | Health check | any |
| POST | `/vector/ingest` | Upload e ingestão de documento (PDF, MD, TXT) | autenticado |
| GET | `/vector/search` | Busca semântica na knowledge_base | autenticado |
| DELETE | `/vector/documents/{source_path}` | Remove documento e seus chunks | `TENANT_GESTOR` |
| GET | `/vector/stats` | Estatísticas (doc_count, chunk_count) | autenticado |

---

## Tabelas (schema `tenant_{slug}`)

| Tabela | Descrição |
|--------|-----------|
| `knowledge_base` | Chunks indexados (`title`, `content`, `source_path`, `chunk_index`, `embedding vector(768)`) |
| `ingest_log` | Log de ingestão (`source_path`, `chunk_count`, `status`, `error_message`) |

### Índices relevantes

- HNSW em `embedding` (`vector_cosine_ops`, m=16, ef_construction=64)
- `uq_kb_source_chunk` — UNIQUE (`source_path`, `chunk_index`) para upsert idempotente

---

## Componentes Internos

| Componente | Localização | Papel |
|------------|-------------|-------|
| `chunking.py` | `intellicare_core/vector/` | Divide texto em chunks (512 tokens, overlap 64) |
| `embeddings.py` | `intellicare_core/vector/` | Embedding via OLLAMA com batch e retry |
| `search.py` | `intellicare_core/vector/` | `semantic_search()` — busca por similaridade coseno |
| `IngestService` | `modules/vector/` | Pipeline completo: extract → chunk → embed → upsert |
| `watcher.py` | `modules/vector/` | APScheduler: varre `tools/data/docs/` a cada 5 min |

---

## Roles Autorizados

- **Qualquer autenticado** — ingest, search, stats
- **`TENANT_GESTOR`** — delete de documentos

---

## Stack e Dependências

- FastAPI (APIRouter com prefix `/vector`)
- OLLAMA `nomic-embed-text` (embedding dim 768)
- pgvector (extensão PostgreSQL)
- APScheduler (watcher de arquivos)
- pdfplumber (extração de texto de PDF)
- [[decisoes/ADR-003-rag-slm-pgvector]]
- intellicare-core/vector/ (DEM-003)

---

## DEMs relacionadas

- **DEM-009**: Pipeline RAG completo (chunking, embeddings, ingest, watcher, search)
- **DEM-013**: Cuidado backend (consome busca semântica)
- **DEM-010**: SLM OLLAMA (consome chunks para geração)
