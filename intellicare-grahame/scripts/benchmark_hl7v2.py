#!/usr/bin/env python3
"""HL7v2 Performance Benchmark Script.

Testa a performance do endpoint HL7v2 com diferentes cargas.
Target: 1000+ mensagens por segundo.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
import aiohttp
import argparse


@dataclass
class BenchmarkResult:
    """Resultado de um benchmark."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    duration_seconds: float
    requests_per_second: float
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    errors: Dict[str, int]


# Mensagem HL7v2 de teste (ADT^A04)
SAMPLE_HL7_MESSAGE = """MSH|^~\\&|TASY|HSP|GRAHAME|INTELLICARE|20260225120000||ADT^A04|MSG{msg_id}|P|2.5
EVN|A04|20260225120000
PID|1||{patient_id}^^^HSP^MR||Silva^João^Carlos||19800101|M|||Rua das Flores, 123^^São Paulo^SP^01234-567^BR||11987654321||PT|C|CAT|||123456789||||||BR
PV1|1|I|UTI^101^01^HSP||||123456^Santos^Maria^A^^^Dra.||||||CLI||||V|||||||||||||||||||||||||20260225120000"""


async def send_hl7_message(
    session: aiohttp.ClientSession,
    url: str,
    api_key: str,
    message: str,
    msg_id: int,
) -> tuple[bool, float, str]:
    """Envia uma mensagem HL7v2 e retorna (sucesso, latência_ms, erro).
    
    Args:
        session: aiohttp session
        url: URL do endpoint
        api_key: API Key
        message: Mensagem HL7v2
        msg_id: ID da mensagem
    
    Returns:
        Tuple (sucesso, latência_ms, erro)
    """
    # Substitui placeholders
    msg = message.replace("{msg_id}", str(msg_id).zfill(10))
    msg = msg.replace("{patient_id}", str(10000 + (msg_id % 1000)))
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/x-hl7-v2",
    }
    
    start = time.time()
    try:
        async with session.post(url, data=msg, headers=headers) as response:
            latency_ms = (time.time() - start) * 1000
            
            if response.status == 200:
                return True, latency_ms, ""
            else:
                error = f"HTTP {response.status}"
                return False, latency_ms, error
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        return False, latency_ms, str(e)


async def run_benchmark(
    url: str,
    api_key: str,
    num_requests: int,
    concurrency: int,
    message: str = SAMPLE_HL7_MESSAGE,
) -> BenchmarkResult:
    """Executa benchmark de performance.
    
    Args:
        url: URL do endpoint
        api_key: API Key
        num_requests: Número total de requisições
        concurrency: Número de requisições concorrentes
        message: Mensagem HL7v2 template
    
    Returns:
        BenchmarkResult com estatísticas
    """
    print(f"\n🚀 Iniciando benchmark:")
    print(f"   URL: {url}")
    print(f"   Total de requisições: {num_requests}")
    print(f"   Concorrência: {concurrency}")
    print(f"   Target: 1000+ req/s\n")
    
    # Criar sessão HTTP
    connector = aiohttp.TCPConnector(limit=concurrency)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Criar tasks
        tasks = []
        for i in range(num_requests):
            task = send_hl7_message(session, url, api_key, message, i)
            tasks.append(task)
        
        # Executar com concorrência limitada
        start_time = time.time()
        results = []
        
        # Processar em batches para controlar concorrência
        batch_size = concurrency
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)
            
            # Progress
            progress = (i + len(batch)) / num_requests * 100
            print(f"   Progresso: {progress:.1f}%", end="\r")
        
        duration = time.time() - start_time
    
    # Processar resultados
    successful = sum(1 for success, _, _ in results if success)
    failed = num_requests - successful
    latencies = [latency for _, latency, _ in results]
    errors: Dict[str, int] = {}
    
    for success, _, error in results:
        if not success and error:
            errors[error] = errors.get(error, 0) + 1
    
    # Calcular estatísticas
    latencies_sorted = sorted(latencies)
    
    return BenchmarkResult(
        total_requests=num_requests,
        successful_requests=successful,
        failed_requests=failed,
        duration_seconds=duration,
        requests_per_second=num_requests / duration,
        avg_latency_ms=statistics.mean(latencies),
        min_latency_ms=min(latencies),
        max_latency_ms=max(latencies),
        p50_latency_ms=latencies_sorted[int(len(latencies_sorted) * 0.50)],
        p95_latency_ms=latencies_sorted[int(len(latencies_sorted) * 0.95)],
        p99_latency_ms=latencies_sorted[int(len(latencies_sorted) * 0.99)],
        errors=errors,
    )


def print_results(result: BenchmarkResult) -> None:
    """Imprime resultados do benchmark."""
    print("\n" + "=" * 70)
    print("📊 RESULTADOS DO BENCHMARK")
    print("=" * 70)

    # Throughput
    print(f"\n🚀 Throughput:")
    print(f"   Total de requisições: {result.total_requests}")
    print(f"   Requisições bem-sucedidas: {result.successful_requests}")
    print(f"   Requisições falhadas: {result.failed_requests}")
    print(f"   Taxa de sucesso: {result.successful_requests / result.total_requests * 100:.2f}%")
    print(f"   Duração: {result.duration_seconds:.2f}s")
    print(f"   Requisições/segundo: {result.requests_per_second:.2f} req/s")

    # Target check
    if result.requests_per_second >= 1000:
        print(f"   ✅ TARGET ATINGIDO! (>= 1000 req/s)")
    else:
        print(f"   ⚠️  Abaixo do target (< 1000 req/s)")

    # Latência
    print(f"\n⏱️  Latência:")
    print(f"   Média: {result.avg_latency_ms:.2f}ms")
    print(f"   Mínima: {result.min_latency_ms:.2f}ms")
    print(f"   Máxima: {result.max_latency_ms:.2f}ms")
    print(f"   P50 (mediana): {result.p50_latency_ms:.2f}ms")
    print(f"   P95: {result.p95_latency_ms:.2f}ms")
    print(f"   P99: {result.p99_latency_ms:.2f}ms")

    # Erros
    if result.errors:
        print(f"\n❌ Erros:")
        for error, count in sorted(result.errors.items(), key=lambda x: x[1], reverse=True):
            print(f"   {error}: {count}")

    print("\n" + "=" * 70)


async def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="HL7v2 Performance Benchmark")
    parser.add_argument(
        "--url",
        default="http://localhost:8012/api/v1/hl7v2/adt-a04",
        help="URL do endpoint HL7v2",
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="API Key para autenticação",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=10000,
        help="Número total de requisições (default: 10000)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=100,
        help="Número de requisições concorrentes (default: 100)",
    )

    args = parser.parse_args()

    # Executar benchmark
    result = await run_benchmark(
        url=args.url,
        api_key=args.api_key,
        num_requests=args.requests,
        concurrency=args.concurrency,
    )

    # Imprimir resultados
    print_results(result)

    # Exit code baseado no target
    if result.requests_per_second >= 1000:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)


