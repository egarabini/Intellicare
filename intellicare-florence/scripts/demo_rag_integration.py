"""Demonstração da integração RAG com ClinicalAnalyzer."""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from florence.engine.clinical_analyzer import ClinicalAnalyzer
from florence.engine.correlations.detector import CorrelationDetector
from florence.engine.reference_ranges.loader import ReferenceRangeLoader
from florence.engine.trend_detector import TrendDetector


def demo_without_rag():
    """Demonstra análise sem RAG."""
    print("=" * 80)
    print("DEMO 1: ANÁLISE SEM RAG")
    print("=" * 80)
    print()

    # Setup
    ref_loader = ReferenceRangeLoader("florence/engine/reference_ranges/data")
    ref_loader.load_all()

    corr_detector = CorrelationDetector("florence/engine/correlations/data")
    corr_detector.load_all()

    analyzer = ClinicalAnalyzer(ref_loader, corr_detector, TrendDetector())

    # Análise
    result = analyzer.analyze_labs(
        patient_id="patient-1",
        lab_results={
            "glucose_fasting": 180.0,
            "hba1c": 8.5,
            "creatinine": 1.8,
        },
    )

    print(f"Paciente: {result.patient_id}")
    print(f"Significância: {result.significance.value}")
    print()
    print("Interpretações:")
    for interp in result.interpretations:
        print(f"  - {interp.lab_name}: {interp.value} {interp.unit} ({interp.level.value})")
        print(f"    {interp.message}")
    print()
    print("Sumário:")
    print(result.summary)
    print()


def demo_with_rag_mock():
    """Demonstra análise com RAG (mock)."""
    print("=" * 80)
    print("DEMO 2: ANÁLISE COM RAG (MOCK)")
    print("=" * 80)
    print()

    # Setup
    ref_loader = ReferenceRangeLoader("florence/engine/reference_ranges/data")
    ref_loader.load_all()

    corr_detector = CorrelationDetector("florence/engine/correlations/data")
    corr_detector.load_all()

    # Mock RAG retriever
    from unittest.mock import Mock

    mock_rag = Mock()
    mock_result = Mock()
    mock_result.protocol_id = "diabetes_tipo2"
    mock_result.title = "Manejo de Diabetes Mellitus Tipo 2"
    mock_result.content = """
    # Manejo de Diabetes Mellitus Tipo 2
    
    ## Metas de Controle
    - HbA1c < 7% (maioria dos pacientes)
    - Glicemia jejum: 80-130 mg/dL
    - Glicemia pós-prandial: < 180 mg/dL
    
    ## Conduta
    1. Mudanças no estilo de vida
    2. Metformina como primeira linha
    3. Adicionar segundo agente se HbA1c > 7% após 3 meses
    """
    mock_result.score = 0.95
    mock_result.metadata = {"specialty": "Endocrinologia", "version": "1.0"}

    mock_rag.retrieve.return_value = [mock_result]

    analyzer = ClinicalAnalyzer(
        ref_loader,
        corr_detector,
        TrendDetector(),
        rag_retriever=mock_rag,
    )

    # Análise com RAG
    result = analyzer.analyze_with_rag(
        patient_id="patient-1",
        lab_results={
            "glucose_fasting": 180.0,
            "hba1c": 8.5,
        },
        query="Como manejar diabetes tipo 2 com HbA1c elevada?",
    )

    print(f"Paciente: {result.patient_id}")
    print(f"Significância: {result.significance.value}")
    print()
    print("Interpretações:")
    for interp in result.interpretations:
        print(f"  - {interp.lab_name}: {interp.value} {interp.unit} ({interp.level.value})")
    print()
    print(f"Query RAG: {result.rag_query}")
    print(f"Tempo de execução RAG: {result.rag_execution_time_ms:.2f}ms")
    print()
    print("Protocolos Relevantes:")
    for protocol in result.relevant_protocols:
        print(f"  - {protocol.title} (score: {protocol.score:.2f})")
        print(f"    Especialidade: {protocol.metadata.get('specialty', 'N/A')}")
        print(f"    Conteúdo (preview): {protocol.content[:200]}...")
    print()


def demo_auto_query():
    """Demonstra query automática baseada em análise."""
    print("=" * 80)
    print("DEMO 3: QUERY AUTOMÁTICA BASEADA EM ANÁLISE")
    print("=" * 80)
    print()

    # Setup
    ref_loader = ReferenceRangeLoader("florence/engine/reference_ranges/data")
    ref_loader.load_all()

    corr_detector = CorrelationDetector("florence/engine/correlations/data")
    corr_detector.load_all()

    # Mock RAG
    from unittest.mock import Mock

    mock_rag = Mock()
    mock_rag.retrieve.return_value = []

    analyzer = ClinicalAnalyzer(
        ref_loader,
        corr_detector,
        TrendDetector(),
        rag_retriever=mock_rag,
    )

    # Análise com query automática
    result = analyzer.analyze_with_rag(
        patient_id="patient-1",
        lab_results={
            "creatinine": 3.5,
            "urea": 120.0,
            "potassium": 5.8,
        },
    )

    print(f"Paciente: {result.patient_id}")
    print(f"Query auto-gerada: {result.rag_query}")
    print()
    print("Correlações detectadas:")
    for corr in result.correlations:
        print(f"  - {corr.pattern_name}: {corr.message}")
    print()


def main():
    """Executa todas as demos."""
    demo_without_rag()
    print("\n")
    demo_with_rag_mock()
    print("\n")
    demo_auto_query()


if __name__ == "__main__":
    main()

