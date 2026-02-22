"""Script para testar consultas RAG."""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from florence.engine.rag.models import RAGQuery
from florence.engine.rag.retriever import ProtocolRetriever


def main() -> None:
    """Testa consultas RAG."""
    chroma_dir = Path(__file__).parent.parent / "data" / "chroma"

    print("🔍 Testando consultas RAG...")
    print(f"💾 Diretório ChromaDB: {chroma_dir}")
    print()

    # Criar retriever
    retriever = ProtocolRetriever(
        chroma_persist_dir=str(chroma_dir),
        collection_name="clinical_protocols",
    )

    # Queries de teste
    test_queries = [
        "Como manejar paciente com creatinina elevada?",
        "Qual a meta de HbA1c para diabéticos?",
        "Como tratar hipertensão em diabéticos?",
        "Quando indicar estatina?",
        "Como investigar anemia?",
    ]

    for i, query_text in enumerate(test_queries, 1):
        print(f"{'=' * 80}")
        print(f"Query {i}: {query_text}")
        print(f"{'=' * 80}")
        print()

        # Criar query
        query = RAGQuery(query=query_text, top_k=3)

        # Executar query
        response = retriever.query(query)

        # Mostrar resultados
        print(f"⏱️  Tempo de execução: {response.execution_time_ms:.2f}ms")
        print(f"📊 Total de resultados: {response.total_results}")
        print()

        for j, result in enumerate(response.results, 1):
            print(f"  Resultado {j}:")
            print(f"    📄 Título: {result.title}")
            print(f"    🏥 Especialidade: {result.metadata.get('specialty', 'N/A')}")
            print(f"    ⭐ Score: {result.score:.3f}")
            print(f"    📝 Conteúdo (preview):")
            # Mostrar primeiras 200 caracteres
            preview = result.content[:200].replace("\n", " ")
            print(f"       {preview}...")
            print()

        print()


if __name__ == "__main__":
    main()

