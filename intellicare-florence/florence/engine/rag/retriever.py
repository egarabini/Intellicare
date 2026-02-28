"""Retriever de protocolos clínicos para RAG."""

import time
from typing import Any

import chromadb
from chromadb.config import Settings

from florence.engine.rag.models import RAGQuery, RAGQueryResponse, RAGResult


class ProtocolRetriever:
    """Retriever de protocolos clínicos."""

    def __init__(
        self,
        chroma_persist_dir: str = "./data/chroma",
        collection_name: str = "clinical_protocols",
    ) -> None:
        """
        Inicializa o retriever.

        Args:
            chroma_persist_dir: Diretório de persistência do ChromaDB
            collection_name: Nome da coleção ChromaDB
        """
        self.chroma_persist_dir = chroma_persist_dir
        self.collection_name = collection_name

        # Inicializar ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )

        # Obter coleção
        try:
            self.collection = self.chroma_client.get_collection(
                name=self.collection_name
            )
        except Exception:
            # Coleção não existe, criar vazia
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Clinical protocols for RAG"},
            )

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[RAGResult]:
        """
        Busca protocolos relevantes.

        Args:
            query: Texto da consulta
            top_k: Número de resultados
            filters: Filtros de metadados (ex: {"specialty": "Cardiologia"})

        Returns:
            Lista de RAGResult ordenada por relevância
        """
        # Preparar filtros ChromaDB
        where_filter = None
        if filters:
            where_filter = filters

        # Buscar no ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter,
        )

        # Converter para RAGResult
        rag_results: list[RAGResult] = []

        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                # Calcular score (ChromaDB retorna distância, converter para similaridade)
                distance = results["distances"][0][i] if results["distances"] else 0.0
                score = 1.0 / (1.0 + distance)  # Converter distância em score 0-1

                metadata = results["metadatas"][0][i] if results["metadatas"] else {}

                rag_results.append(
                    RAGResult(
                        protocol_id=metadata.get("title", "Unknown"),
                        title=metadata.get("title", "Unknown"),
                        content=results["documents"][0][i],
                        score=score,
                        metadata=metadata,
                    )
                )

        return rag_results

    def query(self, rag_query: RAGQuery) -> RAGQueryResponse:
        """
        Executa query RAG completa.

        Args:
            rag_query: RAGQuery object

        Returns:
            RAGQueryResponse com resultados e metadados
        """
        start_time = time.time()

        # Buscar resultados
        results = self.retrieve(
            query=rag_query.query,
            top_k=rag_query.top_k,
            filters=rag_query.filters,
        )

        execution_time_ms = (time.time() - start_time) * 1000

        return RAGQueryResponse(
            query=rag_query.query,
            results=results,
            total_results=len(results),
            execution_time_ms=execution_time_ms,
        )

    def get_protocol_by_id(self, protocol_id: str) -> list[RAGResult]:
        """
        Busca protocolo específico por ID.

        Args:
            protocol_id: ID do protocolo

        Returns:
            Lista de chunks do protocolo
        """
        results = self.collection.get(
            where={"title": protocol_id}
        )

        rag_results: list[RAGResult] = []

        if results["documents"]:
            for i in range(len(results["documents"])):
                metadata = results["metadatas"][i] if results["metadatas"] else {}

                rag_results.append(
                    RAGResult(
                        protocol_id=protocol_id,
                        title=metadata.get("title", protocol_id),
                        content=results["documents"][i],
                        score=1.0,  # Score máximo para busca exata
                        metadata=metadata,
                    )
                )

        return rag_results

    def search_by_specialty(
        self, specialty: str, top_k: int = 5
    ) -> list[RAGResult]:
        """
        Busca protocolos por especialidade.

        Args:
            specialty: Nome da especialidade
            top_k: Número de resultados

        Returns:
            Lista de RAGResult
        """
        return self.retrieve(
            query=specialty,
            top_k=top_k,
            filters={"specialty": specialty},
        )

