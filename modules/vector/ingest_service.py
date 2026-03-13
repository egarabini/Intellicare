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
