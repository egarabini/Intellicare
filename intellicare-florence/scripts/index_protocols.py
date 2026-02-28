"""Script para indexar protocolos clínicos."""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from florence.engine.rag.indexer import ProtocolIndexer


def main() -> None:
    """Indexa todos os protocolos."""
    # Diretórios
    protocols_dir = Path(__file__).parent.parent / "florence" / "engine" / "rag" / "data" / "protocols"
    chroma_dir = Path(__file__).parent.parent / "data" / "chroma"

    print("🚀 Iniciando indexação de protocolos clínicos...")
    print(f"📁 Diretório de protocolos: {protocols_dir}")
    print(f"💾 Diretório ChromaDB: {chroma_dir}")
    print()

    # Criar indexer
    indexer = ProtocolIndexer(
        protocols_dir=protocols_dir,
        chroma_persist_dir=chroma_dir,
        collection_name="clinical_protocols",
        chunk_size=500,
        chunk_overlap=50,
    )

    # Limpar índice anterior (opcional)
    print("🗑️  Limpando índice anterior...")
    indexer.clear_index()
    print()

    # Indexar todos os protocolos
    print("📚 Indexando protocolos...")
    results = indexer.index_all_protocols()

    # Mostrar resultados
    print()
    print("✅ Indexação concluída!")
    print()
    print("📊 Resultados:")
    print("-" * 60)

    total_chunks = 0
    for protocol_id, num_chunks in results.items():
        print(f"  • {protocol_id:30s} → {num_chunks:3d} chunks")
        total_chunks += num_chunks

    print("-" * 60)
    print(f"  Total: {len(results)} protocolos, {total_chunks} chunks")
    print()

    # Estatísticas
    stats = indexer.get_stats()
    print("📈 Estatísticas do índice:")
    print(f"  • Total de protocolos: {stats['total_protocols']}")
    print(f"  • Total de chunks: {stats['total_chunks']}")
    print(f"  • Média de chunks/protocolo: {stats['avg_chunks_per_protocol']:.1f}")
    print()

    # Listar protocolos indexados
    print("📋 Protocolos indexados:")
    protocols = indexer.list_indexed_protocols()
    for protocol in protocols:
        print(f"  • {protocol['title']:40s} ({protocol['specialty']:20s}) - {protocol['num_chunks']} chunks")

    print()
    print("✨ Indexação finalizada com sucesso!")


if __name__ == "__main__":
    main()

