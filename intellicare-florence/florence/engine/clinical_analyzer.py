"""Clinical Analyzer — motor principal de analise clinica."""

import logging
import time
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from florence.engine.correlations.detector import CorrelationDetector
from florence.engine.lab_interpreter import LabInterpreter
from florence.engine.models import (
    ClinicalAnalysis,
    ClinicalAnalysisWithRAG,
    ClinicalSignificance,
    CorrelationFinding,
    LabInterpretation,
    TrendAnalysis,
)
from florence.engine.reference_ranges.loader import ReferenceRangeLoader
from florence.engine.trend_detector import TrendDetector

if TYPE_CHECKING:
    from florence.engine.rag.retriever import ProtocolRetriever

logger = logging.getLogger(__name__)


class ClinicalAnalyzer:
    """Motor principal de analise clinica do Florence."""

    def __init__(
        self,
        ref_loader: ReferenceRangeLoader,
        corr_detector: CorrelationDetector,
        trend_detector: TrendDetector | None = None,
        rag_retriever: "ProtocolRetriever | None" = None,
        min_trend_points: int = 3,
    ) -> None:
        self._interpreter = LabInterpreter(ref_loader)
        self._correlator = corr_detector
        self._trend_detector = trend_detector or TrendDetector(min_data_points=min_trend_points)
        self._ref_loader = ref_loader
        self._rag = rag_retriever

    def analyze_labs(
        self,
        patient_id: str,
        lab_results: dict[str, float],
        timestamp: datetime | None = None,
    ) -> ClinicalAnalysis:
        """Analisa um conjunto de resultados laboratoriais."""
        ts = timestamp or datetime.now(timezone.utc)

        # 1. Interpretar cada exame
        interpretations = self._interpreter.interpret_batch(lab_results, ts)

        # 2. Detectar correlacoes
        correlations = self._correlator.detect(lab_results)

        # 3. Classificar significancia geral
        significance = self._overall_significance(interpretations, correlations)

        # 4. Gerar sumario
        summary = self._generate_summary(interpretations, correlations, significance)

        return ClinicalAnalysis(
            patient_id=patient_id,
            interpretations=interpretations,
            trends=[],
            correlations=correlations,
            summary=summary,
            significance=significance,
            timestamp=ts,
        )

    def analyze_with_trends(
        self,
        patient_id: str,
        lab_results: dict[str, float],
        historical: dict[str, list[tuple[datetime, float]]],
        timestamp: datetime | None = None,
    ) -> ClinicalAnalysis:
        """Analisa resultados com historico de tendencias."""
        ts = timestamp or datetime.now(timezone.utc)

        # 1. Interpretar exames
        interpretations = self._interpreter.interpret_batch(lab_results, ts)

        # 2. Detectar correlacoes
        correlations = self._correlator.detect(lab_results)

        # 3. Analisar tendencias
        trends = self._analyze_trends(historical)

        # 4. Classificar significancia
        significance = self._overall_significance(interpretations, correlations)

        # 5. Gerar sumario
        summary = self._generate_summary(interpretations, correlations, significance)

        return ClinicalAnalysis(
            patient_id=patient_id,
            interpretations=interpretations,
            trends=trends,
            correlations=correlations,
            summary=summary,
            significance=significance,
            timestamp=ts,
        )

    def interpret_single(
        self, lab_id: str, value: float, timestamp: datetime | None = None
    ) -> LabInterpretation | None:
        """Interpreta um unico exame."""
        return self._interpreter.interpret(lab_id, value, timestamp)

    def _analyze_trends(
        self, historical: dict[str, list[tuple[datetime, float]]]
    ) -> list[TrendAnalysis]:
        """Analisa tendencias para cada lab com historico."""
        trends = []
        for lab_id, data_points in historical.items():
            if not data_points:
                continue
            ref = self._ref_loader.get(lab_id)
            lab_name = ref.name if ref else lab_id
            timestamps = [dp[0] for dp in data_points]
            values = [dp[1] for dp in data_points]
            trend = self._trend_detector.analyze(lab_id, lab_name, values, timestamps)
            trends.append(trend)
        return trends

    def _overall_significance(
        self,
        interpretations: list[LabInterpretation],
        correlations: list[CorrelationFinding],
    ) -> ClinicalSignificance:
        """Determina a significancia clinica geral."""
        levels = [i.significance for i in interpretations]
        levels.extend(c.significance for c in correlations)

        if not levels:
            return ClinicalSignificance.ROUTINE

        priority = {
            ClinicalSignificance.CRITICAL: 4,
            ClinicalSignificance.URGENT: 3,
            ClinicalSignificance.ATTENTION: 2,
            ClinicalSignificance.ROUTINE: 1,
        }
        return max(levels, key=lambda x: priority.get(x, 0))

    def _generate_summary(
        self,
        interpretations: list[LabInterpretation],
        correlations: list[CorrelationFinding],
        significance: ClinicalSignificance,
    ) -> str:
        """Gera sumario textual da analise."""
        total = len(interpretations)
        abnormal = [i for i in interpretations if i.significance != ClinicalSignificance.ROUTINE]

        parts = [f"Analise de {total} exames laboratoriais."]

        if not abnormal:
            parts.append("Todos os resultados dentro da normalidade.")
        else:
            parts.append(f"{len(abnormal)} resultado(s) fora da referencia.")
            for interp in abnormal:
                parts.append(f"  - {interp.message}")

        if correlations:
            parts.append(f"{len(correlations)} padrao(oes) clinico(s) detectado(s):")
            for corr in correlations:
                parts.append(f"  - {corr.pattern_name}: {corr.message}")

        sig_labels = {
            ClinicalSignificance.ROUTINE: "Rotina",
            ClinicalSignificance.ATTENTION: "Atencao",
            ClinicalSignificance.URGENT: "Urgente",
            ClinicalSignificance.CRITICAL: "Critico",
        }
        parts.append(f"Significancia clinica geral: {sig_labels.get(significance, 'N/A')}")

        return "\n".join(parts)

    def analyze_with_rag(
        self,
        patient_id: str,
        lab_results: dict[str, float],
        query: str | None = None,
        timestamp: datetime | None = None,
        top_k: int = 3,
    ) -> ClinicalAnalysisWithRAG:
        """
        Analisa resultados laboratoriais com consulta a protocolos clínicos via RAG.

        Args:
            patient_id: ID do paciente
            lab_results: Dicionário de resultados laboratoriais
            query: Query customizada para RAG (opcional)
            timestamp: Timestamp da análise
            top_k: Número de protocolos a retornar

        Returns:
            ClinicalAnalysisWithRAG com análise + protocolos relevantes
        """
        # 1. Análise clínica normal
        analysis = self.analyze_labs(patient_id, lab_results, timestamp)

        # 2. Se RAG não está disponível, retornar análise sem protocolos
        if not self._rag:
            logger.warning("RAG retriever não configurado. Retornando análise sem protocolos.")
            return ClinicalAnalysisWithRAG(
                patient_id=analysis.patient_id,
                interpretations=analysis.interpretations,
                trends=analysis.trends,
                correlations=analysis.correlations,
                summary=analysis.summary,
                significance=analysis.significance,
                timestamp=analysis.timestamp,
                metadata=analysis.metadata,
                relevant_protocols=[],
                rag_query=None,
                rag_execution_time_ms=None,
            )

        # 3. Gerar query para RAG
        start_time = time.time()

        if query:
            # Usar query customizada
            rag_query = query
        else:
            # Auto-gerar query baseada na análise
            rag_query = self._generate_rag_query(analysis)

        # 4. Buscar protocolos relevantes
        try:
            protocols = self._rag.retrieve(query=rag_query, top_k=top_k)
            execution_time_ms = (time.time() - start_time) * 1000

            logger.info(
                f"RAG query executada em {execution_time_ms:.2f}ms. "
                f"Encontrados {len(protocols)} protocolos."
            )
        except Exception as e:
            logger.error(f"Erro ao executar RAG query: {e}")
            protocols = []
            execution_time_ms = (time.time() - start_time) * 1000

        # 5. Retornar análise com protocolos
        return ClinicalAnalysisWithRAG(
            patient_id=analysis.patient_id,
            interpretations=analysis.interpretations,
            trends=analysis.trends,
            correlations=analysis.correlations,
            summary=analysis.summary,
            significance=analysis.significance,
            timestamp=analysis.timestamp,
            metadata=analysis.metadata,
            relevant_protocols=protocols,
            rag_query=rag_query,
            rag_execution_time_ms=execution_time_ms,
        )

    def _generate_rag_query(self, analysis: ClinicalAnalysis) -> str:
        """
        Gera query automática para RAG baseada na análise clínica.

        Args:
            analysis: Análise clínica

        Returns:
            Query string para RAG
        """
        query_parts = []

        # 1. Adicionar correlações detectadas
        if analysis.correlations:
            for corr in analysis.correlations:
                query_parts.append(corr.pattern_name.replace("_", " "))

        # 2. Adicionar exames anormais
        abnormal_labs = [
            interp for interp in analysis.interpretations
            if interp.significance != ClinicalSignificance.ROUTINE
        ]

        if abnormal_labs:
            # Pegar os 3 exames mais críticos
            sorted_labs = sorted(
                abnormal_labs,
                key=lambda x: {
                    ClinicalSignificance.CRITICAL: 4,
                    ClinicalSignificance.URGENT: 3,
                    ClinicalSignificance.ATTENTION: 2,
                    ClinicalSignificance.ROUTINE: 1,
                }.get(x.significance, 0),
                reverse=True,
            )[:3]

            for lab in sorted_labs:
                query_parts.append(f"{lab.lab_name} {lab.level.value}")

        # 3. Se não houver nada específico, fazer query genérica
        if not query_parts:
            query_parts.append("exames laboratoriais de rotina")

        # 4. Montar query final
        query = "Como interpretar e manejar: " + ", ".join(query_parts)

        logger.debug(f"Query RAG auto-gerada: {query}")

        return query
