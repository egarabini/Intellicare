#!/usr/bin/env python3
"""
IntelliCare V3 - Pipeline de ingestao de documentos para pgvector.

Uso:
    python tools/scripts/ingest_docs.py --tenant tenant_dev
    python tools/scripts/ingest_docs.py --tenant tenant_dev --path docs/design-docs
    python tools/scripts/ingest_docs.py --tenant tenant_dev --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
from pathlib import Path
from typing import Generator

import asyncpg
import httpx

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCS_PATH = ROOT / "docs"
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
DEFAULT_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHUNK_SIZE = 200
CHUNK_OVERLAP = 50

DB_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'intellicare')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'intellicare_dev_password')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:5432/"
    f"{os.getenv('POSTGRES_DB', 'intellicare')}"
)


def strip_frontmatter(text: str) -> str:
    return re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, flags=re.DOTALL)


def _extract_title(text: str) -> str:
    match = re.search(r"^#+\s+(.+)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()[:100]
    return " ".join(text.split())[:80] or "Untitled"


def chunk_markdown(text: str, path: str) -> Generator[dict, None, None]:
    """Divide markdown em janelas aproximadas de 512 tokens com overlap de 50."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", strip_frontmatter(text)) if p.strip()]
    units: list[str] = []

    for paragraph in paragraphs:
        words = paragraph.split()
        if len(words) <= CHUNK_SIZE:
            units.append(paragraph)
            continue

        step = max(CHUNK_SIZE - CHUNK_OVERLAP, 1)
        for start in range(0, len(words), step):
            window = words[start : start + CHUNK_SIZE]
            if not window:
                continue
            units.append(" ".join(window))
            if start + CHUNK_SIZE >= len(words):
                break

    if not units:
        return

    current_words: list[str] = []
    chunk_index = 0
    title = _extract_title(units[0])

    for unit in units:
        unit_words = unit.split()
        if current_words and len(current_words) + len(unit_words) > CHUNK_SIZE:
            yield {
                "content": " ".join(current_words),
                "source_path": path,
                "chunk_index": chunk_index,
                "title": title,
            }
            chunk_index += 1
            current_words = current_words[-CHUNK_OVERLAP:]

        current_words.extend(unit_words)

    if current_words:
        yield {
            "content": " ".join(current_words),
            "source_path": path,
            "chunk_index": chunk_index,
            "title": title,
        }


async def get_embedding(text: str, client: httpx.AsyncClient, model: str, base_url: str) -> list[float]:
    response = await client.post(
        f"{base_url}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["embedding"]


async def ensure_table(conn: asyncpg.Connection, schema: str) -> None:
    await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
    await conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    await conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS "{schema}".knowledge_base (
            id          SERIAL PRIMARY KEY,
            title       TEXT NOT NULL,
            content     TEXT NOT NULL,
            source_path TEXT NOT NULL,
            chunk_index INTEGER NOT NULL DEFAULT 0,
            embedding   vector(768),
            metadata    JSONB DEFAULT '{{}}',
            created_at  TIMESTAMPTZ DEFAULT now(),
            updated_at  TIMESTAMPTZ DEFAULT now(),
            UNIQUE (source_path, chunk_index)
        )
        """
    )
    await conn.execute(
        f"""
        CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx_{schema}
        ON "{schema}".knowledge_base
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


async def upsert_chunk(
    conn: asyncpg.Connection,
    schema: str,
    chunk: dict,
    embedding: list[float],
) -> None:
    await conn.execute(
        f"""
        INSERT INTO "{schema}".knowledge_base
            (title, content, source_path, chunk_index, embedding)
        VALUES ($1, $2, $3, $4, $5::vector)
        ON CONFLICT (source_path, chunk_index)
        DO UPDATE SET
            title = EXCLUDED.title,
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding,
            updated_at = now()
        """,
        chunk["title"],
        chunk["content"],
        chunk["source_path"],
        chunk["chunk_index"],
        str(embedding),
    )


def resolve_docs_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    return path


async def ingest(args: argparse.Namespace) -> None:
    docs_path = resolve_docs_path(args.path)
    md_files = sorted(path for path in docs_path.rglob("*.md") if "_templates" not in str(path))

    print(f"Encontrados {len(md_files)} arquivos .md em {docs_path}")

    if args.dry_run:
        for md_file in md_files:
            rel = str(md_file.relative_to(ROOT))
            chunks = list(chunk_markdown(md_file.read_text(encoding="utf-8"), rel))
            print(f"  {rel} -> {len(chunks)} chunks")
        print("\nDry run concluido. Nenhuma insercao realizada.")
        return

    conn = await asyncpg.connect(DB_URL)
    await ensure_table(conn, args.tenant)

    total_chunks = 0
    async with httpx.AsyncClient() as http:
        for md_file in md_files:
            rel = str(md_file.relative_to(ROOT))
            text = md_file.read_text(encoding="utf-8")
            chunks = list(chunk_markdown(text, rel))

            for chunk in chunks:
                embedding = await get_embedding(chunk["content"], http, args.model, args.ollama_url)
                await upsert_chunk(conn, args.tenant, chunk, embedding)
                total_chunks += 1

            print(f"  OK {rel} ({len(chunks)} chunks)")

    await conn.close()
    print(f"\nIngestao concluida: {len(md_files)} arquivos, {total_chunks} chunks.")


def main() -> None:
    parser = argparse.ArgumentParser(description="IntelliCare - ingestao de docs para pgvector")
    parser.add_argument("--tenant", default="tenant_dev", help="Schema de destino")
    parser.add_argument("--path", default=str(DEFAULT_DOCS_PATH.relative_to(ROOT)), help="Diretorio a ingerir")
    parser.add_argument("--model", default=DEFAULT_EMBED_MODEL, help="Modelo de embedding OLLAMA")
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help="Endpoint base da API OLLAMA")
    parser.add_argument("--dry-run", action="store_true", help="Listar sem inserir")
    args = parser.parse_args()

    asyncio.run(ingest(args))


if __name__ == "__main__":
    main()
