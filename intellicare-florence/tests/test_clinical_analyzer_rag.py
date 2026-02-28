"""Testes para integração RAG com ClinicalAnalyzer."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from florence.engine.clinical_analyzer import ClinicalAnalyzer
from florence.engine.correlations.detector import CorrelationDetector
from florence.engine.models import ClinicalSignificance
from florence.engine.reference_ranges.loader import ReferenceRangeLoader
from florence.engine.trend_detector import TrendDetector


@pytest.fixture
def mock_rag_retriever():
    """Mock do RAG retriever."""
    retriever = Mock()
    
    # Mock de RAGResult
    mock_result = Mock()
    mock_result.protocol_id = "diabetes_tipo2"
    mock_result.title = "Manejo de Diabetes Mellitus Tipo 2"
    mock_result.content = "Protocolo de manejo de diabetes..."
    mock_result.score = 0.95
    mock_result.metadata = {
        "specialty": "Endocrinologia",
        "version": "1.0",
    }
    
    retriever.retrieve.return_value = [mock_result]
    
    return retriever


@pytest.fixture
def analyzer_with_rag(mock_rag_retriever):
    """Analyzer com RAG configurado."""
    ref_loader = ReferenceRangeLoader("florence/engine/reference_ranges/data")
    ref_loader.load_all()
    
    corr_detector = CorrelationDetector("florence/engine/correlations/data")
    corr_detector.load_all()
    
    trend_detector = TrendDetector(min_data_points=3)
    
    return ClinicalAnalyzer(
        ref_loader,
        corr_detector,
        trend_detector,
        rag_retriever=mock_rag_retriever,
    )


class TestClinicalAnalyzerRAG:
    """Testes de integração RAG."""

    def test_analyze_with_rag_custom_query(self, analyzer_with_rag, mock_rag_retriever):
        """Testa análise com query customizada."""
        result = analyzer_with_rag.analyze_with_rag(
            patient_id="p-1",
            lab_results={"glucose_fasting": 180.0},
            query="Como manejar diabetes tipo 2?",
            top_k=3,
        )

        # Verificar que RAG foi chamado
        mock_rag_retriever.retrieve.assert_called_once()
        call_args = mock_rag_retriever.retrieve.call_args
        assert call_args[1]["query"] == "Como manejar diabetes tipo 2?"
        assert call_args[1]["top_k"] == 3

        # Verificar resultado
        assert result.patient_id == "p-1"
        assert len(result.relevant_protocols) == 1
        assert result.relevant_protocols[0].title == "Manejo de Diabetes Mellitus Tipo 2"
        assert result.rag_query == "Como manejar diabetes tipo 2?"
        assert result.rag_execution_time_ms is not None

    def test_analyze_with_rag_auto_query(self, analyzer_with_rag, mock_rag_retriever):
        """Testa análise com query auto-gerada."""
        result = analyzer_with_rag.analyze_with_rag(
            patient_id="p-1",
            lab_results={"creatinine": 5.0, "urea": 120.0},
        )

        # Verificar que RAG foi chamado
        mock_rag_retriever.retrieve.assert_called_once()
        call_args = mock_rag_retriever.retrieve.call_args
        
        # Query deve conter informações sobre os exames anormais
        query = call_args[1]["query"]
        assert "creatinina" in query.lower() or "creatinine" in query.lower()

        # Verificar resultado
        assert result.patient_id == "p-1"
        assert len(result.relevant_protocols) == 1
        assert result.rag_query is not None

    def test_analyze_with_rag_no_retriever(self):
        """Testa análise sem RAG retriever configurado."""
        ref_loader = ReferenceRangeLoader("florence/engine/reference_ranges/data")
        ref_loader.load_all()
        
        corr_detector = CorrelationDetector("florence/engine/correlations/data")
        corr_detector.load_all()
        
        analyzer = ClinicalAnalyzer(ref_loader, corr_detector)
        
        result = analyzer.analyze_with_rag(
            patient_id="p-1",
            lab_results={"glucose_fasting": 180.0},
        )

        # Deve retornar análise sem protocolos
        assert result.patient_id == "p-1"
        assert len(result.relevant_protocols) == 0
        assert result.rag_query is None
        assert result.rag_execution_time_ms is None

    def test_analyze_with_rag_correlation_query(self, analyzer_with_rag, mock_rag_retriever):
        """Testa query auto-gerada com correlações detectadas."""
        result = analyzer_with_rag.analyze_with_rag(
            patient_id="p-1",
            lab_results={
                "creatinine": 3.5,
                "urea": 100.0,
                "potassium": 5.8,
            },
        )

        # Verificar que RAG foi chamado
        mock_rag_retriever.retrieve.assert_called_once()
        call_args = mock_rag_retriever.retrieve.call_args
        
        # Query deve conter informações sobre correlação renal
        query = call_args[1]["query"]
        assert query is not None
        assert len(query) > 0

    def test_analyze_with_rag_to_dict(self, analyzer_with_rag):
        """Testa serialização para dict."""
        result = analyzer_with_rag.analyze_with_rag(
            patient_id="p-1",
            lab_results={"glucose_fasting": 180.0},
        )

        result_dict = result.to_dict()

        # Verificar campos básicos
        assert result_dict["patient_id"] == "p-1"
        assert "interpretations" in result_dict
        assert "correlations" in result_dict
        assert "summary" in result_dict

        # Verificar campos RAG
        assert "relevant_protocols" in result_dict
        assert "rag_query" in result_dict
        assert "rag_execution_time_ms" in result_dict
        assert len(result_dict["relevant_protocols"]) == 1
        assert result_dict["relevant_protocols"][0]["title"] == "Manejo de Diabetes Mellitus Tipo 2"

