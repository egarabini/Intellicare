"""
Florence Performance Testing Suite
===================================

Testes de performance e benchmarks para validadores Florence.

Requisitos de SLA:
- Latência p99: < 100ms por validação
- Throughput: > 1000 exames/hora
- Taxa de erros: < 0.1%
"""

import time
import random
import pytest
from typing import Dict, Callable, List
from dataclasses import dataclass

# Importar validators
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.clinical_validation import ClinicaAlgorithmValidator


@dataclass
class BenchmarkResult:
    """Resultado de benchmark"""
    validator_type: str
    num_iterations: int
    total_time_ms: float
    mean_time_ms: float
    p50_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    throughput_per_hour: float


class HemogramaDataGenerator:
    """Gera dados válidos/inválidos de hemograma"""
    
    @staticmethod
    def valid_hemograma():
        """Hemograma válido"""
        return {
            "hemoglobina": random.uniform(13.5, 17.5),
            "hematocrito": random.uniform(40, 52),
            "gb": random.uniform(4.5, 11.0),
            "neutrofilos": random.uniform(45, 75),
            "linfocitos": random.uniform(15, 40),
            "monocitos": random.uniform(2, 8),
            "eosinofilos": random.uniform(0, 5),
            "basofilos": random.uniform(0, 2),
        }
    
    @staticmethod
    def invalid_hemograma():
        """Hemograma invalidox (Ht muito baixo)"""
        return {
            "hemoglobina": 14.5,
            "hematocrito": 30.0,  # Inválido: esperado ~42.5
            "gb": 7.0,
            "neutrofilos": 60,
            "linfocitos": 25,
            "monocitos": 5,
            "eosinofilos": 2,
            "basofilos": 1,
        }


class LipidogramaDataGenerator:
    """Gera dados de lipidograma"""
    
    @staticmethod
    def valid_lipidograma():
        """Lipidograma válido (Friedewald ok)"""
        colesterol = random.uniform(150, 220)
        hdl = random.uniform(35, 55)
        triglicerideos = random.uniform(50, 150)
        # LDL via Friedewald: (Colesterol - HDL - Triglicerídeos/5)
        ldl = colesterol - hdl - (triglicerideos / 5)
        return {
            "colesterol_total": colesterol,
            "hdl": hdl,
            "ldl": ldl,
            "triglicerideos": triglicerideos,
        }
    
    @staticmethod
    def invalid_lipidograma():
        """Lipidograma inválido"""
        return {
            "colesterol_total": 300,
            "hdl": 20,
            "ldl": 350,  # Muito alto
            "triglicerideos": 500,
        }


class GlicemiaDataGenerator:
    """Gera dados de glicemia"""
    
    @staticmethod
    def valid_glicemia(context="jejum"):
        """Glicemia válida"""
        if context == "jejum":
            return {"glicemia": random.uniform(70, 100)}
        elif context == "pos_prandial":
            return {"glicemia": random.uniform(100, 140)}
        else:  # aleatório
            return {"glicemia": random.uniform(80, 130)}
    
    @staticmethod
    def critical_glicemia():
        """Glicemia crítica"""
        return {"glicemia": 350}


class PerformanceTestSuite:
    """Suite de testes de performance"""
    
    def __init__(self, num_iterations: int = 1000):
        self.num_iterations = num_iterations
        self.validator = ClinicaAlgorithmValidator()
        self.results: List[BenchmarkResult] = []
    
    def benchmark_validator(
        self,
        validator_func: Callable,
        data_generator: Callable,
        validator_name: str,
        **validator_kwargs
    ) -> BenchmarkResult:
        """
        Benchmark de um validador específico.
        
        Args:
            validator_func: Função do validator
            data_generator: Função que gera dados de teste
            validator_name: Nome do validator
            **validator_kwargs: Argumentos extras para validator
            
        Returns:
            BenchmarkResult com estatísticas
        """
        times = []
        
        for _ in range(self.num_iterations):
            data = data_generator()
            
            start = time.perf_counter()
            validator_func(data, **validator_kwargs)
            end = time.perf_counter()
            
            times.append((end - start) * 1000)  # Converter para ms
        
        # Calcular estatísticas
        times_sorted = sorted(times)
        total_time_ms = sum(times)
        mean_time = total_time_ms / len(times)
        
        p50_idx = int(len(times) * 0.50)
        p95_idx = int(len(times) * 0.95)
        p99_idx = int(len(times) * 0.99)
        
        result = BenchmarkResult(
            validator_type=validator_name,
            num_iterations=self.num_iterations,
            total_time_ms=total_time_ms,
            mean_time_ms=mean_time,
            p50_time_ms=times_sorted[p50_idx],
            p95_time_ms=times_sorted[p95_idx],
            p99_time_ms=times_sorted[p99_idx],
            throughput_per_hour=(3600000 / mean_time),  # ops/hour
        )
        
        self.results.append(result)
        return result
    
    def run_all_benchmarks(self) -> Dict[str, BenchmarkResult]:
        """Executa benchmarks para todos os validators"""
        
        results = {}
        
        # Hemograma
        print(f"\n[BENCHMARK] Hemograma ({self.num_iterations} iterações)...")
        results['hemograma'] = self.benchmark_validator(
            self.validator.validar_hemograma,
            HemogramaDataGenerator.valid_hemograma,
            "hemograma",
            sexo="M"
        )
        
        # Lipidograma
        print(f"[BENCHMARK] Lipidograma ({self.num_iterations} iterações)...")
        results['lipidograma'] = self.benchmark_validator(
            self.validator.validar_lipidograma,
            LipidogramaDataGenerator.valid_lipidograma,
            "lipidograma",
        )
        
        # Glicemia (jejum)
        print(f"[BENCHMARK] Glicemia ({self.num_iterations} iterações)...")
        results['glicemia'] = self.benchmark_validator(
            self.validator.validar_glicemia,
            GlicemiaDataGenerator.valid_glicemia,
            "glicemia",
            tipo="jejum"
        )
        
        return results
    
    def print_report(self):
        """Imprime relatório de performance"""
        
        print("\n" + "="*80)
        print("RELATÓRIO DE PERFORMANCE - FLORENCE VALIDATORS")
        print("="*80)
        
        for result in self.results:
            print(f"\n{result.validator_type.upper()}")
            print("-" * 80)
            print(f"  Iterações:              {result.num_iterations:,}")
            print(f"  Tempo Total:            {result.total_time_ms:,.2f} ms")
            print(f"  Média:                  {result.mean_time_ms:.4f} ms")
            print(f"  p50:                    {result.p50_time_ms:.4f} ms")
            print(f"  p95:                    {result.p95_time_ms:.4f} ms")
            print(f"  p99:                    {result.p99_time_ms:.4f} ms ← SLA TARGET <100ms")
            print(f"  Throughput:             {result.throughput_per_hour:,.0f} exames/hora")
            
            # Validação SLA
            if result.p99_time_ms < 100:
                print(f"  ✅ SLA ATENDIDO (p99 < 100ms)")
            else:
                print(f"  ❌ SLA NÃO ATENDIDO (p99 >= 100ms)")
        
        # Resumo geral
        print("\n" + "="*80)
        print("RESUMO")
        print("="*80)
        
        all_p99 = [r.p99_time_ms for r in self.results]
        all_throughput = [r.throughput_per_hour for r in self.results]
        
        print(f"P99 máximo:               {max(all_p99):.4f} ms")
        print(f"Throughput mínimo:        {min(all_throughput):,.0f} exames/hora")
        
        if all(p99 < 100 for p99 in all_p99):
            print(f"\n✅ TODOS OS VALIDADORES ATENDEM SLA")
        else:
            print(f"\n❌ ALGUNS VALIDADORES NÃO ATENDEM SLA")


# Testes pytest
class TestPerformanceSLA:
    @pytest.fixture
    def suite(self):
        return PerformanceTestSuite(num_iterations=1000)
    
    def test_hemograma_p99_latency(self, suite):
        """P99 latência < 100ms"""
        result = suite.benchmark_validator(
            suite.validator.validar_hemograma,
            HemogramaDataGenerator.valid_hemograma,
            "hemograma",
            sexo="M"
        )
        assert result.p99_time_ms < 100, f"P99 {result.p99_time_ms:.4f}ms > 100ms"
    
    def test_lipidograma_p99_latency(self, suite):
        """P99 latência < 100ms"""
        result = suite.benchmark_validator(
            suite.validator.validar_lipidograma,
            LipidogramaDataGenerator.valid_lipidograma,
            "lipidograma",
        )
        assert result.p99_time_ms < 100, f"P99 {result.p99_time_ms:.4f}ms > 100ms"
    
    def test_glicemia_p99_latency(self, suite):
        """P99 latência < 100ms"""
        result = suite.benchmark_validator(
            suite.validator.validar_glicemia,
            GlicemiaDataGenerator.valid_glicemia,
            "glicemia",
            tipo="jejum"
        )
        assert result.p99_time_ms < 100, f"P99 {result.p99_time_ms:.4f}ms > 100ms"
    
    def test_hemograma_throughput(self, suite):
        """Throughput > 1000 exames/hora"""
        result = suite.benchmark_validator(
            suite.validator.validar_hemograma,
            HemogramaDataGenerator.valid_hemograma,
            "hemograma",
            sexo="M"
        )
        assert result.throughput_per_hour > 1000, \
            f"Throughput {result.throughput_per_hour:.0f}/h < 1000/h"


class TestClinicalAnalyzerPerformance:
    """Testes de performance do ClinicalAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Analyzer configurado."""
        from florence.engine.clinical_analyzer import ClinicalAnalyzer
        from florence.engine.correlations.detector import CorrelationDetector
        from florence.engine.reference_ranges.loader import ReferenceRangeLoader
        from florence.engine.trend_detector import TrendDetector

        ref_loader = ReferenceRangeLoader("florence/engine/reference_ranges/data")
        ref_loader.load_all()

        corr_detector = CorrelationDetector("florence/engine/correlations/data")
        corr_detector.load_all()

        return ClinicalAnalyzer(ref_loader, corr_detector, TrendDetector())

    def test_analyze_labs_performance(self, analyzer):
        """Performance de análise de exames."""
        times = []

        for i in range(100):
            start = time.perf_counter()
            analyzer.analyze_labs(
                patient_id=f"perf-{i}",
                lab_results={
                    "glucose_fasting": 100.0 + i,
                    "hba1c": 5.5 + (i * 0.01),
                    "creatinine": 1.0 + (i * 0.01),
                },
            )
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        # Estatísticas
        times_sorted = sorted(times)
        p50 = times_sorted[int(len(times) * 0.50)]
        p95 = times_sorted[int(len(times) * 0.95)]
        p99 = times_sorted[int(len(times) * 0.99)]

        print(f"\nAnalyze Labs Performance:")
        print(f"  p50: {p50:.2f}ms")
        print(f"  p95: {p95:.2f}ms")
        print(f"  p99: {p99:.2f}ms")

        # SLA: p95 < 100ms
        assert p95 < 100, f"p95 {p95:.2f}ms > 100ms"

    def test_correlation_detection_performance(self, analyzer):
        """Performance de detecção de correlações."""
        times = []

        for i in range(100):
            start = time.perf_counter()
            analyzer.analyze_labs(
                patient_id=f"corr-perf-{i}",
                lab_results={
                    "creatinine": 3.5,
                    "urea": 120.0,
                    "potassium": 5.8,
                },
            )
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        times_sorted = sorted(times)
        p95 = times_sorted[int(len(times) * 0.95)]

        print(f"\nCorrelation Detection Performance:")
        print(f"  p95: {p95:.2f}ms")

        # SLA: p95 < 150ms (mais complexo)
        assert p95 < 150, f"p95 {p95:.2f}ms > 150ms"

    def test_batch_processing_throughput(self, analyzer):
        """Throughput de processamento em lote."""
        num_patients = 1000

        start = time.perf_counter()
        for i in range(num_patients):
            analyzer.analyze_labs(
                patient_id=f"batch-{i}",
                lab_results={"glucose_fasting": 100.0 + (i % 100)},
            )
        elapsed = time.perf_counter() - start

        throughput = num_patients / elapsed
        print(f"\nBatch Processing:")
        print(f"  {num_patients} patients in {elapsed:.2f}s")
        print(f"  Throughput: {throughput:.0f} patients/s")

        # SLA: > 100 patients/s
        assert throughput > 100, f"Throughput {throughput:.0f}/s < 100/s"


class TestRAGPerformance:
    """Testes de performance do RAG."""

    def test_rag_query_performance(self):
        """Performance de query RAG."""
        pytest.skip("RAG não habilitado por padrão")

    def test_rag_indexing_performance(self):
        """Performance de indexação RAG."""
        pytest.skip("RAG não habilitado por padrão")


if __name__ == "__main__":
    # Executar benchmarks
    suite = PerformanceTestSuite(num_iterations=1000)
    suite.run_all_benchmarks()
    suite.print_report()

    print("\n\nPara executar testes pytest:")
    print("  pytest tests/test_performance.py -v -s")
