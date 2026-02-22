#!/usr/bin/env python
"""
Test Script for Florence API Validation Endpoint
================================================

Script para testar manualmente o endpoint de validação clínica.

Uso:
    python test_endpoint_validacao.py
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# API base URL
API_URL = "http://localhost:8000/api/v1/validacao"

# Cores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'


def print_test(name: str, passed: bool):
    """Imprime resultado de um teste"""
    status = f"{GREEN}✅ PASSOU{RESET}" if passed else f"{RED}❌ FALHOU{RESET}"
    print(f"{status}: {name}")


def test_health_check():
    """Test: Health check endpoint"""
    print(f"\n{CYAN}=== Health Check ==={RESET}")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print_test("Health Check", response.status_code == 200)
        print(f"Status: {response.json()}")
        return True
    except Exception as e:
        print_test("Health Check", False)
        print(f"Erro: {str(e)}")
        return False


def test_tipos_suportados():
    """Test: Get supported exam types"""
    print(f"\n{CYAN}=== Tipos Suportados ==={RESET}")
    try:
        response = requests.get(f"{API_URL}/tipos-suportados", timeout=5)
        print_test("Tipos Suportados", response.status_code == 200)
        dados = response.json()
        print(f"Tipos: {dados['tipos']}")
        return True
    except Exception as e:
        print_test("Tipos Suportados", False)
        print(f"Erro: {str(e)}")
        return False


def test_validacao_hemograma_valido():
    """Test: Valid hemograma"""
    print(f"\n{CYAN}=== Validação: Hemograma Válido ==={RESET}")
    
    payload = {
        "tipo_exame": "hemograma",
        "sexo": "M",
        "dados": {
            "hemoglobina": 14.5,
            "hematocrito": 42.5,
            "plaquetas": 250,
            "leucocitos": 7.0,
            "diferenciais": {
                "neutrofilos": 60,
                "linfocitos": 30,
                "monocitos": 8,
                "eosinofilos": 2
            }
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}/validador-clinico",
            json=payload,
            timeout=5
        )
        print_test("Request Status", response.status_code == 200)
        resultado = response.json()
        print(f"Válido: {resultado['valido']}")
        print(f"Mensagem: {resultado['mensagem']}")
        return resultado['valido'] == True
    except Exception as e:
        print_test("Validação Hemograma", False)
        print(f"Erro: {str(e)}")
        return False


def test_validacao_hemograma_incoerente():
    """Test: Incoherent hemograma (Hb/Ht mismatch)"""
    print(f"\n{CYAN}=== Validação: Hemograma Incoerente ==={RESET}")
    
    payload = {
        "tipo_exame": "hemograma",
        "sexo": "M",
        "dados": {
            "hemoglobina": 14.5,
            "hematocrito": 30.0,  # Esperado ~43.5%, está em 30% = incoerente
            "plaquetas": 250,
            "leucocitos": 7.0,
            "diferenciais": {
                "neutrofilos": 60,
                "linfocitos": 30,
                "monocitos": 8,
                "eosinofilos": 2
            }
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}/validador-clinico",
            json=payload,
            timeout=5
        )
        print_test("Request Status", response.status_code == 200)
        resultado = response.json()
        print(f"Válido: {resultado['valido']}")
        print(f"Mensagem: {resultado['mensagem']}")
        return resultado['valido'] == False
    except Exception as e:
        print_test("Validação Hemograma Incoerente", False)
        print(f"Erro: {str(e)}")
        return False


def test_validacao_lipidograma():
    """Test: Valid lipidogram"""
    print(f"\n{CYAN}=== Validação: Lipidograma Válido ==={RESET}")
    
    payload = {
        "tipo_exame": "lipidograma",
        "dados": {
            "colesterol_total": 200,
            "triglicerida": 100,
            "hdl": 50,
            "ldl": 130
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}/validador-clinico",
            json=payload,
            timeout=5
        )
        print_test("Request Status", response.status_code == 200)
        resultado = response.json()
        print(f"Válido: {resultado['valido']}")
        print(f"Mensagem: {resultado['mensagem']}")
        return resultado['valido'] == True
    except Exception as e:
        print_test("Validação Lipidograma", False)
        print(f"Erro: {str(e)}")
        return False


def test_validacao_glicemia_normal():
    """Test: Normal fasting glucose"""
    print(f"\n{CYAN}=== Validação: Glicemia Normal (Jejum) ==={RESET}")
    
    payload = {
        "tipo_exame": "glicemia",
        "dados": {
            "glicemia": 90
        },
        "tipo_amostra": "jejum",
        "paciente_diabetico": False
    }
    
    try:
        response = requests.post(
            f"{API_URL}/validador-clinico",
            json=payload,
            timeout=5
        )
        print_test("Request Status", response.status_code == 200)
        resultado = response.json()
        print(f"Válido: {resultado['valido']}")
        print(f"Mensagem: {resultado['mensagem']}")
        return resultado['valido'] == True
    except Exception as e:
        print_test("Validação Glicemia", False)
        print(f"Erro: {str(e)}")
        return False


def test_validacao_glicemia_critica():
    """Test: Critical hyperglycemia"""
    print(f"\n{CYAN}=== Validação: Glicemia Crítica ==={RESET}")
    
    payload = {
        "tipo_exame": "glicemia",
        "dados": {
            "glicemia": 350
        },
        "tipo_amostra": "aleatoria",
        "paciente_diabetico": True
    }
    
    try:
        response = requests.post(
            f"{API_URL}/validador-clinico",
            json=payload,
            timeout=5
        )
        print_test("Request Status", response.status_code == 200)
        resultado = response.json()
        print(f"Válido: {resultado['valido']}")
        print(f"Mensagem: {resultado['mensagem']}")
        return resultado['valido'] == False  # Deveria ser inválido (crítico)
    except Exception as e:
        print_test("Validação Glicemia Crítica", False)
        print(f"Erro: {str(e)}")
        return False


def test_validacao_funcao_renal():
    """Test: Valid kidney function"""
    print(f"\n{CYAN}=== Validação: Função Renal Válida ==={RESET}")
    
    payload = {
        "tipo_exame": "funcao_renal",
        "age_anos": 45,
        "dados": {
            "creatinina": 1.0,
            "ureia": 15
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}/validador-clinico",
            json=payload,
            timeout=5
        )
        print_test("Request Status", response.status_code == 200)
        resultado = response.json()
        print(f"Válido: {resultado['valido']}")
        print(f"Mensagem: {resultado['mensagem']}")
        return resultado['valido'] == True
    except Exception as e:
        print_test("Validação Função Renal", False)
        print(f"Erro: {str(e)}")
        return False


def main():
    """Run all tests"""
    print(f"\n{YELLOW}{'='*60}")
    print(f"TESTE DO ENDPOINT DE VALIDAÇÃO - FLORENCE")
    print(f"{'='*60}{RESET}")
    
    print(f"\n⚠️  {YELLOW}Certifique-se que a API está rodando!{RESET}")
    print(f"Para iniciar: python -m uvicorn src.florence.api.main:app --reload")
    
    # Wait for user to confirm API is running
    input(f"\n{CYAN}Pressione ENTER para continuar (API já iniciada)...{RESET}")
    
    # Check if API is available
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
    except Exception as e:
        print(f"\n{RED}❌ Erro de conexão com API:{RESET}")
        print(f"   Certifique-se que o servidor está rodando em http://localhost:8000")
        print(f"   Comando: python -m uvicorn src.florence.api.main:app --reload")
        return
    
    # Run tests
    results = []
    
    results.append(("Health Check", test_health_check()))
    time.sleep(0.5)
    
    results.append(("Tipos Suportados", test_tipos_suportados()))
    time.sleep(0.5)
    
    results.append(("Hemograma Válido", test_validacao_hemograma_valido()))
    time.sleep(0.5)
    
    results.append(("Hemograma Incoerente", test_validacao_hemograma_incoerente()))
    time.sleep(0.5)
    
    results.append(("Lipidograma Válido", test_validacao_lipidograma()))
    time.sleep(0.5)
    
    results.append(("Glicemia Normal", test_validacao_glicemia_normal()))
    time.sleep(0.5)
    
    results.append(("Glicemia Crítica", test_validacao_glicemia_critica()))
    time.sleep(0.5)
    
    results.append(("Função Renal", test_validacao_funcao_renal()))
    
    # Summary
    print(f"\n{YELLOW}{'='*60}")
    print(f"RESUMO DOS TESTES")
    print(f"{'='*60}{RESET}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nResultados:")
    for name, result in results:
        status = f"{GREEN}✅{RESET}" if result else f"{RED}❌{RESET}"
        print(f"{status} {name}")
    
    print(f"\n{CYAN}Total: {passed}/{total} testes passaram{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}{'='*60}")
        print(f"🎉 TODOS OS TESTES PASSARAM!")
        print(f"API está pronta para uso!{RESET}")
        print(f"{'='*60}{RESET}")
    else:
        print(f"\n{RED}{'='*60}")
        print(f"⚠️  {total - passed} teste(s) falharam")
        print(f"Verifique os erros acima{RESET}")
        print(f"{'='*60}{RESET}")


if __name__ == "__main__":
    main()
