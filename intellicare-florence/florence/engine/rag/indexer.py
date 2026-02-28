"""Indexador de protocolos clínicos para RAG."""

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import chromadb
import tiktoken
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from florence.engine.rag.models import Protocol, ProtocolChunk


class ProtocolIndexer:
    """Indexador de protocolos clínicos."""

    def __init__(
        self,
        protocols_dir: str | Path,
        chroma_persist_dir: str | Path = "./data/chroma",
        collection_name: str = "clinical_protocols",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        """
        Inicializa o indexador.

        Args:
            protocols_dir: Diretório com protocolos Markdown
            chroma_persist_dir: Diretório de persistência do ChromaDB
            collection_name: Nome da coleção ChromaDB
            chunk_size: Tamanho do chunk em tokens
            chunk_overlap: Sobreposição entre chunks
        """
        self.protocols_dir = Path(protocols_dir)
        self.chroma_persist_dir = Path(chroma_persist_dir)
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Inicializar ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )

        # Criar ou obter coleção
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Clinical protocols for RAG"},
        )

        # Tokenizer para contagem de tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def load_protocol_from_file(self, file_path: Path) -> Protocol:
        """
        Carrega protocolo de arquivo Markdown.

        Args:
            file_path: Caminho do arquivo .md

        Returns:
            Protocol object
        """
        content = file_path.read_text(encoding="utf-8")

        # Extrair metadados do cabeçalho
        metadata = self._extract_metadata(content)

        # ID baseado no nome do arquivo
        protocol_id = file_path.stem

        return Protocol(
            id=protocol_id,
            title=metadata.get("title", file_path.stem.replace("_", " ").title()),
            specialty=metadata.get("specialty", "Geral"),
            version=metadata.get("version", "1.0"),
            date=metadata.get("date", datetime.now()),
            source=metadata.get("source", ""),
            content=content,
            metadata=metadata,
        )

    def _extract_metadata(self, content: str) -> dict[str, Any]:
        """Extrai metadados do cabeçalho Markdown."""
        metadata: dict[str, Any] = {}

        # Extrair título (primeira linha com #)
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # Extrair especialidade
        specialty_match = re.search(
            r"\*\*Especialidade\*\*:\s*(.+)$", content, re.MULTILINE
        )
        if specialty_match:
            metadata["specialty"] = specialty_match.group(1).strip()

        # Extrair versão
        version_match = re.search(r"\*\*Versão\*\*:\s*(.+)$", content, re.MULTILINE)
        if version_match:
            metadata["version"] = version_match.group(1).strip()

        # Extrair data
        date_match = re.search(r"\*\*Data\*\*:\s*(.+)$", content, re.MULTILINE)
        if date_match:
            date_str = date_match.group(1).strip()
            try:
                metadata["date"] = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                metadata["date"] = datetime.now()

        # Extrair fonte
        source_match = re.search(r"\*\*Fonte\*\*:\s*(.+)$", content, re.MULTILINE)
        if source_match:
            metadata["source"] = source_match.group(1).strip()

        return metadata

    def chunk_document(self, protocol: Protocol) -> list[ProtocolChunk]:
        """
        Divide protocolo em chunks.

        Args:
            protocol: Protocol object

        Returns:
            Lista de ProtocolChunk
        """
        # Usar RecursiveCharacterTextSplitter do LangChain
        # Converter chunk_size de tokens para caracteres (aproximadamente)
        char_chunk_size = self.chunk_size * 4  # ~4 chars por token
        char_overlap = self.chunk_overlap * 4

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=char_chunk_size,
            chunk_overlap=char_overlap,
            length_function=len,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
        )

        chunks_text = text_splitter.split_text(protocol.content)

        # Criar ProtocolChunk objects
        chunks: list[ProtocolChunk] = []
        for i, chunk_text in enumerate(chunks_text):
            chunk_id = self._generate_chunk_id(protocol.id, i)
            chunks.append(
                ProtocolChunk(
                    protocol_id=protocol.id,
                    chunk_id=chunk_id,
                    content=chunk_text,
                    metadata={
                        "title": protocol.title,
                        "specialty": protocol.specialty,
                        "version": protocol.version,
                        "chunk_index": i,
                        "total_chunks": len(chunks_text),
                    },
                )
            )

        return chunks

    def _generate_chunk_id(self, protocol_id: str, chunk_index: int) -> str:
        """Gera ID único para chunk."""
        return f"{protocol_id}_chunk_{chunk_index:03d}"

    def index_protocol(self, protocol: Protocol) -> int:
        """
        Indexa um protocolo no ChromaDB.

        Args:
            protocol: Protocol object

        Returns:
            Número de chunks indexados
        """
        # Dividir em chunks
        chunks = self.chunk_document(protocol)

        if not chunks:
            return 0

        # Preparar dados para ChromaDB
        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        # Adicionar ao ChromaDB (usa embeddings padrão do ChromaDB)
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        return len(chunks)

    def index_all_protocols(self) -> dict[str, int]:
        """
        Indexa todos os protocolos do diretório.

        Returns:
            Dict com protocol_id -> número de chunks
        """
        results: dict[str, int] = {}

        # Buscar todos arquivos .md
        protocol_files = list(self.protocols_dir.glob("*.md"))

        for file_path in protocol_files:
            try:
                protocol = self.load_protocol_from_file(file_path)
                num_chunks = self.index_protocol(protocol)
                results[protocol.id] = num_chunks
            except Exception as e:
                print(f"Erro ao indexar {file_path.name}: {e}")
                results[file_path.stem] = 0

        return results

    def list_indexed_protocols(self) -> list[dict[str, Any]]:
        """
        Lista protocolos indexados.

        Returns:
            Lista de dicts com informações dos protocolos
        """
        # Obter todos os documentos
        all_data = self.collection.get()

        # Agrupar por protocol_id
        protocols_map: dict[str, dict[str, Any]] = {}

        if all_data["metadatas"]:
            for metadata in all_data["metadatas"]:
                protocol_id = metadata.get("title", "Unknown")
                if protocol_id not in protocols_map:
                    protocols_map[protocol_id] = {
                        "title": metadata.get("title", "Unknown"),
                        "specialty": metadata.get("specialty", "Unknown"),
                        "version": metadata.get("version", "1.0"),
                        "num_chunks": 0,
                    }
                protocols_map[protocol_id]["num_chunks"] += 1

        return list(protocols_map.values())

    def delete_protocol(self, protocol_id: str) -> bool:
        """
        Remove protocolo do índice.

        Args:
            protocol_id: ID do protocolo

        Returns:
            True se removido com sucesso
        """
        try:
            # Buscar todos os chunks do protocolo
            results = self.collection.get(
                where={"title": protocol_id}  # Filtrar por metadata
            )

            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                return True

            return False
        except Exception:
            return False

    def clear_index(self) -> None:
        """Remove todos os protocolos do índice."""
        # Deletar e recriar coleção
        self.chroma_client.delete_collection(name=self.collection_name)
        self.collection = self.chroma_client.create_collection(
            name=self.collection_name,
            metadata={"description": "Clinical protocols for RAG"},
        )

    def get_stats(self) -> dict[str, Any]:
        """
        Retorna estatísticas do índice.

        Returns:
            Dict com estatísticas
        """
        all_data = self.collection.get()
        total_chunks = len(all_data["ids"]) if all_data["ids"] else 0

        protocols = self.list_indexed_protocols()
        total_protocols = len(protocols)

        return {
            "total_protocols": total_protocols,
            "total_chunks": total_chunks,
            "avg_chunks_per_protocol": (
                total_chunks / total_protocols if total_protocols > 0 else 0
            ),
            "collection_name": self.collection_name,
            "protocols": protocols,
        }

