---
dem: DEM-009
titulo: Pipeline RAG — Especificação Técnica
tipo: TECNICA
status: aprovado
criado: 2026-03-13
---

# DEM-009 · 02 — Especificação Técnica

## Estrutura

```
intellicare_core/
└── vector/
    ├── __init__.py
    ├── embeddings.py        # get_embedding(), batch_embed()
    ├── search.py            # semantic_search() — evolução de DEM-003
    └── chunking.py          # chunk_text(), chunk_pdf()

modules/
└── vector/
    ├── __init__.py
    ├── main.py              # class Module(BaseModule)
    ├── router.py            # /vector/* endpoints
    ├── schemas.py
    ├── ingest_service.py    # IngestService
    └── watcher.py           # APScheduler file watcher

db/
└── platform_migrations/
    └── 003_ingest_log.sql   # tabela de log de ingest (por schema de tenant)
```

> **Nota**: `intellicare_core/vector/` é a camada de acesso de dados (baixo nível).
> `modules/vector/` é o módulo de aplicação com API e serviço.
> Esta separação respeita a ADR-002 (MODULE ≠ SERVICE) e as regras de layer do DEM-003.

---

## BLOCO 1 — `db/tenant_migrations/002_ingest_log.sql`

Executado no schema de cada tenant (junto com as migrations de tenant do DEM-005).

```sql
-- Adicionado ao schema tenant_{slug} durante provisionamento

CREATE TABLE IF NOT EXISTS ingest_log (
    id              BIGSERIAL   PRIMARY KEY,
    source_path     TEXT        NOT NULL,
    chunk_count     INTEGER     NOT NULL DEFAULT 0,
    status          TEXT        NOT NULL DEFAULT 'ok' CHECK (status IN ('ok','error')),
    error_message   TEXT,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ingest_log_path ON ingest_log (source_path, ingested_at DESC);

-- Adicionar chunk_index à knowledge_base para upsert idempotente
ALTER TABLE knowledge_base
    ADD COLUMN IF NOT EXISTS chunk_index INTEGER NOT NULL DEFAULT 0;

-- Constraint para upsert idempotente
ALTER TABLE knowledge_base
    DROP CONSTRAINT IF EXISTS uq_kb_source_chunk;
ALTER TABLE knowledge_base
    ADD CONSTRAINT uq_kb_source_chunk UNIQUE (source_path, chunk_index);
```

---

## BLOCO 2 — `intellicare_core/vector/chunking.py`

```python
"""Chunking de texto para o pipeline RAG."""
from __future__ import annotations

import re
from typing import Iterator
from dataclasses import dataclass


@dataclass
class Chunk:
    index: int
    text: str
    char_start: int
    char_end: int


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
    separator: str = "\n\n",
) -> list[Chunk]:
    """
    Divide texto em chunks de `chunk_size` tokens (aproximado por palavras × 1.3).
    Preserva parágrafos: tenta quebrar em `separator` antes de cortar no meio.

    Args:
        text: texto completo
        chunk_size: tokens por chunk (aprox.: palavras × 1.3)
        overlap: tokens de sobreposição entre chunks consecutivos
        separator: separador preferencial de parágrafos
    """
    # Normalizar quebras de linha
    text = re.sub(r'\r\n', '\n', text).strip()
    paragraphs = text.split(separator)

    chunks: list[Chunk] = []
    current_words: list[str] = []
    current_char_start = 0
    chunk_idx = 0

    # Convertemos tokens ≈ palavras × 1.3 (estimativa segura)
    word_limit = int(chunk_size / 1.3)
    word_overlap = int(overlap / 1.3)

    for para in paragraphs:
        words = para.split()
        for word in words:
            current_words.append(word)
            if len(current_words) >= word_limit:
                chunk_text_str = " ".join(current_words)
                chunks.append(Chunk(
                    index=chunk_idx,
                    text=chunk_text_str,
                    char_start=current_char_start,
                    char_end=current_char_start + len(chunk_text_str),
                ))
                chunk_idx += 1
                current_char_start += len(chunk_text_str) + 1
                # Overlap: manter últimas `word_overlap` palavras
                current_words = current_words[-word_overlap:] if word_overlap > 0 else []

    # Chunk final
    if current_words:
        chunk_text_str = " ".join(current_words)
        chunks.append(Chunk(
            index=chunk_idx,
            text=chunk_text_str,
            char_start=current_char_start,
            char_end=current_char_start + len(chunk_text_str),
        ))

    return chunks


def chunk_pdf(pdf_path: str) -> list[Chunk]:
    """Extrai texto de PDF e aplica chunking."""
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError("pdfplumber não instalado. Execute: pip install pdfplumber")

    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            full_text += text + "\n\n"

    return chunk_text(full_text.strip())
```

---

## BLOCO 3 — `intellicare_core/vector/embeddings.py` (atualizado)

```python
"""Embeddings via OLLAMA — versão de produção com batch e retry."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Sequence

import httpx

OLLAMA_URL  = os.getenv("OLLAMA_URL",   "http://ollama:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL",  "nomic-embed-text")
EMBED_DIM   = 768
BATCH_SIZE  = 32
MAX_RETRIES = 3

logger = logging.getLogger("intellicare.vector.embeddings")


async def get_embedding(text: str) -> list[float]:
    """Gera embedding para um único texto."""
    results = await batch_embed([text])
    return results[0]


async def batch_embed(texts: Sequence[str]) -> list[list[float]]:
    """
    Gera embeddings para múltiplos textos em batches de BATCH_SIZE.
    Retry automático com backoff exponencial.
    """
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    tasks = [
                        client.post(
                            f"{OLLAMA_URL}/api/embeddings",
                            json={"model": EMBED_MODEL, "prompt": t},
                        )
                        for t in batch
                    ]
                    responses = await asyncio.gather(*tasks)

                embeddings = []
                for resp in responses:
                    resp.raise_for_status()
                    emb = resp.json()["embedding"]
                    if len(emb) != EMBED_DIM:
                        raise ValueError(f"Embedding dim inesperada: {len(emb)} (esperado {EMBED_DIM})")
                    embeddings.append(emb)

                all_embeddings.extend(embeddings)
                break  # sucesso, sair do retry loop

            except Exception as exc:
                if attempt == MAX_RETRIES:
                    raise RuntimeError(f"Falha ao gerar embeddings após {MAX_RETRIES} tentativas: {exc}")
                wait = 2 ** attempt
                logger.warning("Embedding falhou (tentativa %d/%d), aguardando %ds: %s",
                               attempt, MAX_RETRIES, wait, exc)
                await asyncio.sleep(wait)

    return all_embeddings
```

---

## BLOCO 4 — `modules/vector/ingest_service.py`

```python
"""IngestService — pipeline completo de ingestão de documentos."""
from __future__ import annotations

import logging
import time
from pathlib import Path

from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session
from intellicare_core.vector.chunking import chunk_text, chunk_pdf
from intellicare_core.vector.embeddings import batch_embed

logger = logging.getLogger("intellicare.vector.ingest")


class IngestService:

    async def ingest_file(
        self,
        file_path: str,
        ctx: TenantContext,
        source_label: str | None = None,
    ) -> dict:
        """
        Ingere um arquivo (PDF, MD, TXT) na knowledge_base do tenant.
        Idempotente: re-ingerir o mesmo arquivo substitui os chunks anteriores.

        Returns:
            {"source_path": ..., "chunk_count": N, "duration_ms": ...}
        """
        source_path = source_label or file_path
        path = Path(file_path)
        t0 = time.monotonic()

        # 1. Extrair texto
        if path.suffix.lower() == ".pdf":
            chunks = chunk_pdf(file_path)
        else:
            text_content = path.read_text(encoding="utf-8", errors="replace")
            chunks = chunk_text(text_content)

        if not chunks:
            logger.warning("Arquivo '%s' não gerou chunks. Ignorado.", file_path)
            return {"source_path": source_path, "chunk_count": 0, "duration_ms": 0}

        logger.info("Arquivo '%s': %d chunks gerados", file_path, len(chunks))

        # 2. Embeddings em batch
        texts = [c.text for c in chunks]
        embeddings = await batch_embed(texts)

        # 3. Upsert na knowledge_base
        async with tenant_session(ctx) as db:
            # Deletar chunks antigos do mesmo source_path
            await db.execute(
                text("DELETE FROM knowledge_base WHERE source_path = :sp"),
                {"sp": source_path},
            )

            # Inserir novos chunks
            for chunk, emb in zip(chunks, embeddings):
                emb_str = f"[{','.join(str(x) for x in emb)}]"
                await db.execute(
                    text("""
                        INSERT INTO knowledge_base
                            (title, content, source_path, chunk_index, embedding)
                        VALUES
                            (:title, :content, :source_path, :chunk_index, :embedding::vector)
                        ON CONFLICT (source_path, chunk_index)
                        DO UPDATE SET
                            content   = EXCLUDED.content,
                            embedding = EXCLUDED.embedding
                    """),
                    {
                        "title":       path.stem,
                        "content":     chunk.text,
                        "source_path": source_path,
                        "chunk_index": chunk.index,
                        "embedding":   emb_str,
                    },
                )

            # Registrar ingest_log
            chunk_count = len(chunks)
            await db.execute(
                text("""
                    INSERT INTO ingest_log (source_path, chunk_count, status)
                    VALUES (:sp, :cc, 'ok')
                """),
                {"sp": source_path, "cc": chunk_count},
            )

        duration_ms = int((time.monotonic() - t0) * 1000)
        logger.info("Ingest '%s' concluído: %d chunks em %dms", source_path, chunk_count, duration_ms)

        return {
            "source_path": source_path,
            "chunk_count": chunk_count,
            "duration_ms": duration_ms,
        }

    async def delete_document(self, source_path: str, ctx: TenantContext) -> int:
        """Remove todos os chunks de um documento. Retorna qtd removida."""
        async with tenant_session(ctx) as db:
            result = await db.execute(
                text("DELETE FROM knowledge_base WHERE source_path = :sp RETURNING id"),
                {"sp": source_path},
            )
            deleted = len(result.fetchall())
        logger.info("Deletados %d chunks de '%s' do tenant '%s'", deleted, source_path, ctx.tenant_id)
        return deleted

    async def get_stats(self, ctx: TenantContext) -> dict:
        async with tenant_session(ctx) as db:
            stats = (await db.execute(text("""
                SELECT
                    COUNT(DISTINCT source_path) AS doc_count,
                    COUNT(*)                    AS chunk_count,
                    MAX(created_at)             AS last_ingested_at
                FROM knowledge_base
            """))).mappings().first()
        return dict(stats) if stats else {"doc_count": 0, "chunk_count": 0, "last_ingested_at": None}
```

---

## BLOCO 5 — `modules/vector/router.py`

```python
"""Vector Router — API de ingest e search."""
from __future__ import annotations

import os
import tempfile
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from intellicare_core.auth.jwt import require_role, get_current_tenant
from intellicare_core.contracts.base import TenantContext
from intellicare_core.vector.search import semantic_search
from .ingest_service import IngestService
from .schemas import IngestResponse, SearchResponse, VectorStats

router = APIRouter(prefix="/vector", tags=["vector"])
_ingest = IngestService()

GestorOrAdmin = Annotated[
    TenantContext,
    Depends(lambda ctx=Depends(get_current_tenant): ctx)  # qualquer autenticado
]


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "module": "vector", "version": "1.0.0"}


@router.post("/ingest", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    ctx: GestorOrAdmin = Depends(get_current_tenant),
) -> dict:
    """Upload e ingestão de documento na knowledge_base do tenant."""
    if file.content_type not in (
        "application/pdf",
        "text/plain",
        "text/markdown",
        "text/x-markdown",
    ):
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de arquivo não suportado: {file.content_type}",
        )

    # Salvar temporariamente
    suffix = "." + (file.filename or "doc.txt").rsplit(".", 1)[-1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = await _ingest.ingest_file(
            file_path=tmp_path,
            ctx=ctx,
            source_label=file.filename or "unknown",
        )
    finally:
        os.unlink(tmp_path)

    return result


@router.get("/search", response_model=list[SearchResponse])
async def search(
    q: str = Query(..., min_length=2, description="Query de busca semântica"),
    limit: int = Query(default=5, ge=1, le=20),
    min_similarity: float = Query(default=0.5, ge=0.0, le=1.0),
    ctx: GestorOrAdmin = Depends(get_current_tenant),
) -> list[dict]:
    results = await semantic_search(
        query=q,
        ctx=ctx,
        limit=limit,
        min_similarity=min_similarity,
    )
    return results


@router.delete("/documents/{source_path:path}")
async def delete_document(
    source_path: str,
    ctx: Annotated[TenantContext, Depends(require_role("TENANT_GESTOR"))],
) -> dict:
    deleted = await _ingest.delete_document(source_path, ctx)
    return {"deleted_chunks": deleted, "source_path": source_path}


@router.get("/stats", response_model=VectorStats)
async def get_stats(ctx: GestorOrAdmin = Depends(get_current_tenant)) -> dict:
    return await _ingest.get_stats(ctx)
```

---

## BLOCO 6 — `modules/vector/schemas.py`

```python
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class IngestResponse(BaseModel):
    source_path: str
    chunk_count: int
    duration_ms: int


class SearchResponse(BaseModel):
    id: int
    title: str
    content: str
    source_path: str
    similarity: float


class VectorStats(BaseModel):
    doc_count: int
    chunk_count: int
    last_ingested_at: Optional[datetime]
```

---

## BLOCO 7 — `modules/vector/watcher.py`

```python
"""
watcher.py — Monitora pasta tools/data/docs/ e ingerere novos arquivos.
Executado como job APScheduler a cada 5 minutos.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from intellicare_core.contracts.base import TenantContext
from .ingest_service import IngestService

logger = logging.getLogger("intellicare.vector.watcher")

WATCH_BASE = Path(os.getenv("DOCS_WATCH_DIR", "tools/data/docs"))
SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt"}

# Cache de arquivos já ingeridos (source_path → mtime)
_ingested: dict[str, float] = {}


async def scan_and_ingest() -> None:
    """Varre WATCH_BASE/{tenant_slug}/ e ingerere arquivos novos ou modificados."""
    if not WATCH_BASE.exists():
        return

    svc = IngestService()

    for tenant_dir in WATCH_BASE.iterdir():
        if not tenant_dir.is_dir():
            continue
        slug = tenant_dir.name

        # TenantContext sintético para o watcher (role PLATFORM_ADMIN)
        ctx = TenantContext.from_slug(
            slug=slug,
            user_id="watcher-system",
            roles=["PLATFORM_ADMIN"],
        )

        for file in tenant_dir.rglob("*"):
            if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            key = str(file)
            mtime = file.stat().st_mtime

            if _ingested.get(key) == mtime:
                continue  # não modificado

            try:
                result = await svc.ingest_file(str(file), ctx, source_label=str(file.relative_to(WATCH_BASE)))
                _ingested[key] = mtime
                logger.info("Watcher: '%s' ingerido (%d chunks)", key, result["chunk_count"])
            except Exception as exc:
                logger.error("Watcher: falha ao ingerir '%s': %s", key, exc)


def start_watcher() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scan_and_ingest,
        IntervalTrigger(minutes=5),
        id="vector_watcher",
        name="RAG Document Watcher",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Vector watcher iniciado (intervalo: 5min, pasta: %s)", WATCH_BASE)
    return scheduler
```

---

## BLOCO 8 — `modules/vector/main.py`

```python
from fastapi import APIRouter
from intellicare_core.contracts.base import BaseModule, HealthResponse
from .router import router as vec_router


class Module(BaseModule):
    @property
    def name(self) -> str:
        return "vector"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_router(self) -> APIRouter:
        return vec_router

    async def health(self) -> HealthResponse:
        return HealthResponse(status="healthy", module=self.name, version=self.version)
```

---

## BLOCO 9 — Commit

```bash
git add intellicare_core/vector/ \
        modules/vector/ \
        db/tenant_migrations/002_ingest_log.sql \
        docs/demandas/DEM-009_PGVECTOR_RAG/

git commit -m "DEM-009: Pipeline RAG completo - chunking, embeddings batch, ingest API, watcher, search"
git push origin main
```

---

## Critérios de Aceite (técnicos)

| # | Critério | Verificação |
|---|---|---|
| AC-1 | POST `/vector/ingest` com PDF → chunks em `knowledge_base` | `SELECT COUNT(*) FROM tenant_dev.knowledge_base` |
| AC-2 | Re-ingestão do mesmo PDF → contagem não dobra | Ingerir 2× → mesmo `chunk_count` |
| AC-3 | GET `/vector/search?q=hipertensao` → similarity > 0.5 | Response `similarity` field |
| AC-4 | Isolamento: busca de tenant_a não retorna docs de tenant_b | `test_isolation.py` |
| AC-5 | DELETE `/vector/documents/{path}` → `deleted_chunks > 0` | Response `deleted_chunks` |
| AC-6 | GET `/vector/stats` → `doc_count` e `chunk_count` corretos | Conferir com SELECT |
| AC-7 | Latência p95 < 300ms | `pytest tests/perf/ -k search` |
| AC-8 | Watcher: arquivo novo em `tools/data/docs/dev/` → ingerido em < 5min | Aguardar ciclo |
| AC-9 | 50 páginas de PDF → ingest < 60s | Testar com PDF real |
