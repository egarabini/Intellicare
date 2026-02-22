#!/usr/bin/env python3
"""
IntelliCare - Smoke Tests
Verifica se todos os serviços estão saudáveis e acessíveis após deploy.

Uso:
    python scripts/smoke_tests.py                                    # localhost
    python scripts/smoke_tests.py --url https://staging.example.com  # staging/produção
    python scripts/smoke_tests.py --json report.json                 # salvar JSON
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("❌ Erro: requests não instalado. Execute: pip install requests")
    sys.exit(1)

# Cores para output no terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def colored(text: str, color: str) -> str:
    """Retorna texto colorido para terminal."""
    return f"{color}{text}{Colors.RESET}"

# Configuração dos serviços a serem testados
BACKEND_SERVICES = {
    "florence": {"port": 8001, "name": "Florence - RAG + Protocolos Clínicos"},
    "oswaldo": {"port": 8002, "name": "Oswaldo - Análise Clínica + FHIR"},
    "donabedian": {"port": 8003, "name": "Donabedian - Qualidade + Indicadores"},
    "wanda": {"port": 8004, "name": "Wanda - Orquestração + Workflows"},
    "comunicacao": {"port": 8005, "name": "Comunicacao - Comunicação + Notificações"},
    "geralda": {"port": 8006, "name": "Geralda - Gestão + Administrativo"},
}

FRONTEND_SERVICE = {
    "portal": {"port": 3001, "name": "Portal - Frontend React"},
}

INFRASTRUCTURE_SERVICES = {
    "postgres": {"port": 5432, "name": "PostgreSQL - Database"},
    "redis": {"port": 6379, "name": "Redis - Cache + Events"},
}

def check_http_endpoint(name: str, url: str, timeout: int = 10) -> Dict:
    """Verifica se endpoint HTTP retorna 200 OK."""
    result = {
        "service": name,
        "url": url,
        "status": "unknown",
        "response_time_ms": None,
        "error": None,
    }
    
    try:
        start_time = datetime.now()
        response = requests.get(url, timeout=timeout)
        end_time = datetime.now()
        
        result["response_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
        if response.status_code == 200:
            result["status"] = "healthy"
        else:
            result["status"] = "unhealthy"
            result["error"] = f"HTTP {response.status_code}"
    
    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["error"] = f"Timeout após {timeout}s"
    
    except requests.exceptions.ConnectionError:
        result["status"] = "unreachable"
        result["error"] = "Conexão recusada"
    
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def check_tcp_port(host: str, port: int, name: str, timeout: int = 5) -> Dict:
    """Verifica se porta TCP está acessível."""
    import socket
    
    result = {
        "service": name,
        "host": host,
        "port": port,
        "status": "unknown",
        "error": None,
    }
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result_code = sock.connect_ex((host, port))
        sock.close()
        
        if result_code == 0:
            result["status"] = "healthy"
        else:
            result["status"] = "unreachable"
            result["error"] = f"Porta {port} não acessível"
    
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def print_result(result: Dict, show_response_time: bool = True) -> None:
    """Imprime resultado de um teste no console."""
    status = result["status"]
    service = result["service"]
    
    if status == "healthy":
        icon = "✅"
        color = Colors.GREEN
    elif status in ["unhealthy", "unreachable", "timeout"]:
        icon = "❌"
        color = Colors.RED
    else:
        icon = "⚠️"
        color = Colors.YELLOW
    
    status_text = colored(f"{icon} {status.upper()}", color)
    
    if show_response_time and result.get("response_time_ms"):
        print(f"{status_text} | {service} ({result['response_time_ms']}ms)")
    else:
        print(f"{status_text} | {service}")
    
    if result.get("error"):
        print(f"         └─ {colored(result['error'], Colors.RED)}")

def run_smoke_tests(base_url: str = "http://localhost") -> List[Dict]:
    """Executa todos os smoke tests."""
    results = []

    print(colored("\n" + "="*70, Colors.BOLD))
    print(colored("🔍 IntelliCare - Smoke Tests", Colors.BOLD))
    print(colored("="*70 + "\n", Colors.BOLD))

    # 1. Testar backends
    print(colored("📦 Backend Services (6 módulos)", Colors.BLUE))
    print("-" * 70)

    for service_id, config in BACKEND_SERVICES.items():
        url = urljoin(base_url.replace("localhost", f"localhost:{config['port']}"), "/health")
        if "localhost" not in base_url:
            # Para URLs de produção, usar subdomínio ou path
            url = f"{base_url}/{service_id}/health"

        result = check_http_endpoint(config["name"], url)
        results.append(result)
        print_result(result)

    print()

    # 2. Testar frontend
    print(colored("🌐 Frontend Service", Colors.BLUE))
    print("-" * 70)

    for service_id, config in FRONTEND_SERVICE.items():
        url = urljoin(base_url.replace("localhost", f"localhost:{config['port']}"), "/health")
        if "localhost" not in base_url:
            url = f"{base_url}/health"

        result = check_http_endpoint(config["name"], url)
        results.append(result)
        print_result(result)

    print()

    # 3. Testar infraestrutura (apenas localhost)
    if "localhost" in base_url or "127.0.0.1" in base_url:
        print(colored("🔧 Infrastructure Services", Colors.BLUE))
        print("-" * 70)

        for service_id, config in INFRASTRUCTURE_SERVICES.items():
            result = check_tcp_port("localhost", config["port"], config["name"])
            results.append(result)
            print_result(result, show_response_time=False)

        print()

    return results

def generate_summary(results: List[Dict]) -> Dict:
    """Gera resumo dos testes."""
    total = len(results)
    healthy = sum(1 for r in results if r["status"] == "healthy")
    unhealthy = total - healthy

    return {
        "timestamp": datetime.now().isoformat(),
        "total_services": total,
        "healthy": healthy,
        "unhealthy": unhealthy,
        "success_rate": round((healthy / total) * 100, 2) if total > 0 else 0,
        "all_healthy": healthy == total,
        "results": results,
    }

def print_summary(summary: Dict) -> None:
    """Imprime resumo final."""
    print(colored("="*70, Colors.BOLD))
    print(colored("📊 Resumo", Colors.BOLD))
    print(colored("="*70, Colors.BOLD))
    print(f"Total de serviços: {summary['total_services']}")
    print(f"Saudáveis: {colored(str(summary['healthy']), Colors.GREEN)}")
    print(f"Com problemas: {colored(str(summary['unhealthy']), Colors.RED)}")
    print(f"Taxa de sucesso: {summary['success_rate']}%")
    print()

    if summary["all_healthy"]:
        print(colored("✅ TODOS OS SERVIÇOS ESTÃO SAUDÁVEIS!", Colors.GREEN + Colors.BOLD))
    else:
        print(colored("❌ ALGUNS SERVIÇOS ESTÃO COM PROBLEMAS!", Colors.RED + Colors.BOLD))

    print(colored("="*70 + "\n", Colors.BOLD))

def save_json_report(summary: Dict, filepath: str) -> None:
    """Salva relatório em JSON."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(colored(f"📄 Relatório salvo em: {filepath}", Colors.GREEN))
    except Exception as e:
        print(colored(f"❌ Erro ao salvar relatório: {e}", Colors.RED))

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="IntelliCare Smoke Tests - Verifica saúde de todos os serviços"
    )
    parser.add_argument(
        "--url",
        default="http://localhost",
        help="URL base do deploy (padrão: http://localhost)"
    )
    parser.add_argument(
        "--json",
        help="Caminho para salvar relatório JSON"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Timeout em segundos para cada teste (padrão: 10)"
    )

    args = parser.parse_args()

    # Executar testes
    results = run_smoke_tests(base_url=args.url)

    # Gerar resumo
    summary = generate_summary(results)

    # Imprimir resumo
    print_summary(summary)

    # Salvar JSON se solicitado
    if args.json:
        save_json_report(summary, args.json)

    # Exit code: 0 se todos saudáveis, 1 caso contrário
    sys.exit(0 if summary["all_healthy"] else 1)

if __name__ == "__main__":
    main()

