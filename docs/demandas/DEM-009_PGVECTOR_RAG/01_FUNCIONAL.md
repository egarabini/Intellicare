---
dem: DEM-009
titulo: Pipeline RAG — pgvector + OLLAMA (ingest, search, rerank)
tipo: FUNCIONAL
status: aprovado
criado: 2026-03-13
dependencias: [DEM-002, DEM-003, DEM-008]
---

# DEM-009 · 01 — Especificação Funcional

## Contexto e Motivação

A ADR-003 define o triad RAG+SLM+pgvector como o coração inteligente do IntelliCare.
A DEM-002 provisionou a infraestrutura (pgvector extensão, tabela `knowledge_base`, índice HNSW).
A DEM-003 criou a função `semantic_search()` no módulo `vector/`.

Esta demanda completa o **pipeline RAG completo** de produção:

1. **Ingest**: chunking inteligente de PDFs/Markdown + geração de embeddings + upsert idempotente
2. **Search**: busca semântica com filtro por similaridade mínima e reranking
3. **API de ingest**: endpoint autenticado para upload de documentos por tenant
4. **Watcher**: monitora pasta `docs/tenant_{slug}/` e ingerere automaticamente novos arquivos
5. **Métricas**: latência de search, taxa de hit, tamanho da base por tenant

O pipeline é **multi-tenant por design**: cada tenant tem sua própria `knowledge_base` no schema
`tenant_{slug}` — documentos de um tenant jamais aparecem na busca de outro.

## Escopo

### Incluído

- **Chunking**: texto em chunks de 512 tokens, overlap 64, preservando parágrafos
- **Embeddings**: via OLLAMA `nomic-embed-text` (768 dims), com retry e batch de 32
- **Upsert idempotente**: `ON CONFLICT (source_path, chunk_index) DO UPDATE`
- **API de ingest**: POST `/vector/ingest` (upload de arquivo ou URL de doc)
- **Search API**: GET `/vector/search?q=...&limit=5&min_similarity=0.5`
- **Watcher de pasta**: APScheduler escaneia `tools/data/docs/` a cada 5 minutos
- **Métricas básicas**: GET `/vector/stats` por tenant (count docs, última ingestão)
- **Delete de documento**: DELETE `/vector/documents/{source_path}` — remove chunks do tenant

### Excluído

- SLM (OLLAMA geração de resposta) → DEM-010
- Interface de upload do gestor → DEM-013 (Gestor Frontend Fase 3)
- OCR de imagens em PDF → Fase 3

## Atores

| Ator | Ação |
|---|---|
| `TENANT_GESTOR` | Upload de docs, busca, delete, stats — do próprio tenant |
| `CLINICO` | Busca apenas — do próprio tenant |
| `PLATFORM_ADMIN` | Stats globais, forçar re-ingest |

## Fluxo de Ingest

```
Arquivo (PDF/MD/TXT)
  → chunking (512 tok, overlap 64)
  → [chunk₁, chunk₂, ..., chunkₙ]
  → batch embeddings via OLLAMA (32 chunks por chamada)
  → upsert em knowledge_base com source_path + chunk_index
  → registro em ingest_log (tenant, arquivo, chunks, duração)
```

## Fluxo de Search

```
Query string
  → embedding via OLLAMA
  → pgvector cosine search (HNSW)
  → filtro min_similarity
  → opcional: rerank por BM25 (TF-IDF lexical + semântico)
  → retorno top-k com score, title, content, source_path
```

## Critérios de Aceite

| # | Critério |
|---|---|
| AC-1 | POST `/vector/ingest` com PDF → chunks inseridos em `knowledge_base` do tenant |
| AC-2 | Upsert idempotente: re-ingerir mesmo arquivo não duplica chunks |
| AC-3 | GET `/vector/search?q=hipertensao` → top-1 é doc relevante (similarity > 0.5) |
| AC-4 | Busca do tenant A não retorna docs do tenant B |
| AC-5 | DELETE `/vector/documents/{path}` remove todos os chunks do arquivo |
| AC-6 | GET `/vector/stats` retorna `doc_count`, `chunk_count`, `last_ingested_at` |
| AC-7 | Search latência p95 < 300ms (critério ADR-003) |
| AC-8 | Watcher detecta novo arquivo em `tools/data/docs/` e ingerere em < 5min |
| AC-9 | Batch de 32 chunks: 1 arquivo de 50 páginas ingerido em < 60s |

## Não-Funcionais

- Embeddings: dim 768, modelo `nomic-embed-text` via OLLAMA
- Índice HNSW: `m=16, ef_construction=64` (já criado no DEM-002)
- Chunk size: 512 tokens (≈ 400 palavras)
- Chunk overlap: 64 tokens
- Min similarity padrão: 0.5
- Retry em falha de OLLAMA: 3 tentativas com backoff exponencial
