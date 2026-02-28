#!/usr/bin/env python3
"""Test HL7v2 endpoint with real messages from Brazilian hospitals.

Testa o endpoint HL7v2 com mensagens reais de hospitais brasileiros
para validar compatibilidade com diferentes sistemas (TASY, MV, etc.).
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import requests
from tabulate import tabulate


@dataclass
class TestResult:
    """Resultado de um teste de mensagem."""
    system: str
    filename: str
    message_type: str
    success: bool
    http_status: int
    response_time_ms: float
    error_message: str = ""
    patient_id: str = ""
    encounter_id: str = ""


def find_hl7_files(base_dir: Path, system: str = None) -> List[tuple[str, Path]]:
    """Encontra todos os arquivos .hl7 no diretório.
    
    Args:
        base_dir: Diretório base
        system: Sistema específico (tasy, mv, etc.) ou None para todos
    
    Returns:
        Lista de tuplas (sistema, caminho_arquivo)
    """
    files = []
    
    if system:
        # Apenas um sistema
        system_dir = base_dir / system
        if system_dir.exists():
            for file in system_dir.glob("*.hl7"):
                files.append((system, file))
    else:
        # Todos os sistemas
        for system_dir in base_dir.iterdir():
            if system_dir.is_dir():
                system_name = system_dir.name
                for file in system_dir.glob("*.hl7"):
                    files.append((system_name, file))
    
    return sorted(files)


def extract_message_type(message: str) -> str:
    """Extrai o tipo de mensagem do MSH."""
    try:
        msh_line = message.split('\n')[0]
        fields = msh_line.split('|')
        if len(fields) > 8:
            return fields[8]  # MSH-9
        return "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def test_message(
    url: str,
    api_key: str,
    system: str,
    filepath: Path,
    verbose: bool = False,
) -> TestResult:
    """Testa uma mensagem HL7v2.
    
    Args:
        url: URL do endpoint
        api_key: API Key
        system: Nome do sistema
        filepath: Caminho do arquivo
        verbose: Modo verbose
    
    Returns:
        TestResult
    """
    # Ler mensagem
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            message = f.read()
    except UnicodeDecodeError:
        # Tentar ISO-8859-1
        with open(filepath, 'r', encoding='iso-8859-1') as f:
            message = f.read()
    
    message_type = extract_message_type(message)
    
    if verbose:
        print(f"\n📄 Testando: {system}/{filepath.name}")
        print(f"   Tipo: {message_type}")
        print(f"   Tamanho: {len(message)} bytes")
    
    # Enviar requisição
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/x-hl7-v2",
    }
    
    start = time.time()
    try:
        response = requests.post(url, data=message, headers=headers, timeout=30)
        response_time_ms = (time.time() - start) * 1000
        
        if response.status_code == 200:
            # Sucesso
            if verbose:
                print(f"   ✅ Sucesso ({response_time_ms:.0f}ms)")
            
            return TestResult(
                system=system,
                filename=filepath.name,
                message_type=message_type,
                success=True,
                http_status=200,
                response_time_ms=response_time_ms,
            )
        else:
            # Falha
            error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
            
            if verbose:
                print(f"   ❌ Falha: {error_msg}")
            
            return TestResult(
                system=system,
                filename=filepath.name,
                message_type=message_type,
                success=False,
                http_status=response.status_code,
                response_time_ms=response_time_ms,
                error_message=error_msg,
            )
    
    except Exception as e:
        response_time_ms = (time.time() - start) * 1000
        error_msg = str(e)
        
        if verbose:
            print(f"   ❌ Erro: {error_msg}")
        
        return TestResult(
            system=system,
            filename=filepath.name,
            message_type=message_type,
            success=False,
            http_status=0,
            response_time_ms=response_time_ms,
            error_message=error_msg,
        )


def print_summary(results: List[TestResult]) -> None:
    """Imprime resumo dos testes."""
    print("\n" + "=" * 80)
    print("📊 RESUMO DOS TESTES - MENSAGENS REAIS")
    print("=" * 80)

    # Estatísticas gerais
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful
    success_rate = (successful / total * 100) if total > 0 else 0

    avg_time = sum(r.response_time_ms for r in results) / total if total > 0 else 0

    print(f"\n🚀 Geral:")
    print(f"   Total de mensagens: {total}")
    print(f"   Sucesso: {successful}")
    print(f"   Falha: {failed}")
    print(f"   Taxa de sucesso: {success_rate:.2f}%")
    print(f"   Tempo médio: {avg_time:.2f}ms")

    # Target check
    if success_rate >= 95:
        print(f"   ✅ TARGET ATINGIDO! (>= 95%)")
    else:
        print(f"   ⚠️  Abaixo do target (< 95%)")

    # Por sistema
    systems = {}
    for r in results:
        if r.system not in systems:
            systems[r.system] = {"total": 0, "success": 0, "failed": 0}
        systems[r.system]["total"] += 1
        if r.success:
            systems[r.system]["success"] += 1
        else:
            systems[r.system]["failed"] += 1

    print(f"\n📊 Por Sistema:")
    table_data = []
    for system, stats in sorted(systems.items()):
        rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
        status = "✅" if rate >= 95 else "⚠️"
        table_data.append([
            status,
            system.upper(),
            stats["total"],
            stats["success"],
            stats["failed"],
            f"{rate:.1f}%"
        ])

    print(tabulate(
        table_data,
        headers=["", "Sistema", "Total", "Sucesso", "Falha", "Taxa"],
        tablefmt="simple"
    ))

    # Falhas
    failures = [r for r in results if not r.success]
    if failures:
        print(f"\n❌ Falhas ({len(failures)}):")
        for r in failures:
            print(f"   {r.system}/{r.filename}: {r.error_message[:80]}")

    print("\n" + "=" * 80)


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Test HL7v2 endpoint with real messages from Brazilian hospitals"
    )
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
        "--system",
        choices=["tasy", "mv", "wareline", "pixeon", "agfa"],
        help="Testar apenas um sistema específico",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Modo verbose",
    )
    parser.add_argument(
        "--output",
        help="Arquivo de saída para relatório (Markdown)",
    )

    args = parser.parse_args()

    # Encontrar arquivos
    base_dir = Path(__file__).parent.parent / "test_data" / "real_messages"

    if not base_dir.exists():
        print(f"❌ Erro: Diretório não encontrado: {base_dir}")
        return 1

    files = find_hl7_files(base_dir, args.system)

    if not files:
        print(f"❌ Erro: Nenhum arquivo .hl7 encontrado")
        return 1

    print(f"\n🚀 Testando {len(files)} mensagens reais de hospitais brasileiros")
    print(f"   URL: {args.url}")
    print(f"   Sistema: {args.system or 'TODOS'}")

    # Executar testes
    results = []
    for system, filepath in files:
        result = test_message(
            url=args.url,
            api_key=args.api_key,
            system=system,
            filepath=filepath,
            verbose=args.verbose,
        )
        results.append(result)

    # Imprimir resumo
    print_summary(results)

    # Salvar relatório
    if args.output:
        save_report(results, args.output)
        print(f"\n📄 Relatório salvo em: {args.output}")

    # Exit code baseado no target
    success_rate = (sum(1 for r in results if r.success) / len(results) * 100)
    return 0 if success_rate >= 95 else 1


def save_report(results: List[TestResult], output_file: str) -> None:
    """Salva relatório em Markdown."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Relatório de Testes - Mensagens Reais\n\n")
        f.write(f"**Data:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Resumo
        total = len(results)
        successful = sum(1 for r in results if r.success)
        success_rate = (successful / total * 100) if total > 0 else 0

        f.write("## Resumo\n\n")
        f.write(f"- **Total:** {total} mensagens\n")
        f.write(f"- **Sucesso:** {successful}\n")
        f.write(f"- **Falha:** {total - successful}\n")
        f.write(f"- **Taxa de Sucesso:** {success_rate:.2f}%\n\n")

        # Detalhes
        f.write("## Detalhes\n\n")
        f.write("| Sistema | Arquivo | Tipo | Status | Tempo (ms) | Erro |\n")
        f.write("|---------|---------|------|--------|------------|------|\n")

        for r in results:
            status = "✅" if r.success else "❌"
            error = r.error_message[:50] if r.error_message else ""
            f.write(f"| {r.system} | {r.filename} | {r.message_type} | {status} | {r.response_time_ms:.0f} | {error} |\n")


if __name__ == "__main__":
    sys.exit(main())


