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
