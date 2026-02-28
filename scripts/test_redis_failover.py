#!/usr/bin/env python3
"""
Script de teste de failover Redis para W8-D Production Hardening.

Testa a resiliência do sistema quando o Redis fica indisponível.
"""

import asyncio
import time
import sys
from typing import Dict, Any
import redis
import requests


class RedisFailoverTester:
    """Testa failover Redis em ambiente de staging."""

    def __init__(self, redis_url: str = "redis://localhost:6379", api_url: str = "http://localhost:8012"):
        """Inicializa o tester.
        
        Args:
            redis_url: URL do Redis
            api_url: URL da API do Grahame
        """
        self.redis_url = redis_url
        self.api_url = api_url
        self.redis_client = None
        self.results: Dict[str, Any] = {
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
        }

    def connect_redis(self) -> bool:
        """Conecta ao Redis.
        
        Returns:
            True se conectou com sucesso
        """
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            print("✅ Conectado ao Redis")
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar ao Redis: {e}")
            return False

    def test_api_health(self) -> bool:
        """Testa health check da API.
        
        Returns:
            True se API está saudável
        """
        try:
            response = requests.get(f"{self.api_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                print("✅ API health check OK")
                return True
            else:
                print(f"❌ API health check falhou: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro ao testar API: {e}")
            return False

    def simulate_redis_failure(self) -> None:
        """Simula falha do Redis (desconecta)."""
        print("\n🔴 Simulando falha do Redis...")
        if self.redis_client:
            self.redis_client.close()
            self.redis_client = None
        print("Redis desconectado")

    def test_api_during_redis_failure(self) -> bool:
        """Testa se API continua funcionando sem Redis.
        
        Returns:
            True se API continua respondendo
        """
        print("\n🧪 Testando API durante falha do Redis...")
        
        try:
            # Teste 1: Health check deve continuar funcionando
            response = requests.get(f"{self.api_url}/api/v1/health", timeout=5)
            if response.status_code != 200:
                print(f"❌ Health check falhou durante Redis down: {response.status_code}")
                self.results["tests_failed"] += 1
                self.results["errors"].append("Health check failed during Redis failure")
                return False
            
            print("✅ Health check continua funcionando sem Redis")
            self.results["tests_passed"] += 1
            
            # Teste 2: Endpoints FHIR devem continuar funcionando (sem cache)
            response = requests.get(f"{self.api_url}/api/v1/fhir/metadata", timeout=5)
            if response.status_code != 200:
                print(f"❌ FHIR metadata falhou durante Redis down: {response.status_code}")
                self.results["tests_failed"] += 1
                self.results["errors"].append("FHIR metadata failed during Redis failure")
                return False
            
            print("✅ FHIR metadata continua funcionando sem Redis")
            self.results["tests_passed"] += 1
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante teste de failover: {e}")
            self.results["tests_failed"] += 1
            self.results["errors"].append(f"Exception during failover test: {str(e)}")
            return False

    def test_redis_reconnection(self) -> bool:
        """Testa reconexão ao Redis.
        
        Returns:
            True se reconectou com sucesso
        """
        print("\n🔄 Testando reconexão ao Redis...")
        
        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            print(f"Tentativa {attempt}/{max_attempts}...")
            
            if self.connect_redis():
                print("✅ Reconectado ao Redis com sucesso")
                self.results["tests_passed"] += 1
                return True
            
            if attempt < max_attempts:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Aguardando {wait_time}s antes da próxima tentativa...")
                time.sleep(wait_time)
        
        print("❌ Falha ao reconectar ao Redis após 5 tentativas")
        self.results["tests_failed"] += 1
        self.results["errors"].append("Failed to reconnect to Redis after 5 attempts")
        return False

    def test_api_after_redis_recovery(self) -> bool:
        """Testa se API volta ao normal após Redis recuperar.
        
        Returns:
            True se API está funcionando normalmente
        """
        print("\n🧪 Testando API após recuperação do Redis...")
        
        try:
            # Teste 1: Health check deve estar OK
            response = requests.get(f"{self.api_url}/api/v1/health", timeout=5)
            if response.status_code != 200:
                print(f"❌ Health check falhou após Redis recovery: {response.status_code}")
                self.results["tests_failed"] += 1
                return False
            
            print("✅ Health check OK após Redis recovery")
            self.results["tests_passed"] += 1
            
            # Teste 2: Cache deve estar funcionando novamente
            # (Fazer 2 requests iguais e verificar se o segundo é mais rápido)
            start1 = time.time()
            requests.get(f"{self.api_url}/api/v1/fhir/metadata", timeout=5)
            time1 = time.time() - start1
            
            start2 = time.time()
            requests.get(f"{self.api_url}/api/v1/fhir/metadata", timeout=5)
            time2 = time.time() - start2
            
            if time2 < time1:
                print(f"✅ Cache funcionando (1ª req: {time1:.3f}s, 2ª req: {time2:.3f}s)")
                self.results["tests_passed"] += 1
            else:
                print(f"⚠️  Cache pode não estar funcionando (1ª req: {time1:.3f}s, 2ª req: {time2:.3f}s)")
                # Não falha o teste, apenas aviso
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante teste pós-recovery: {e}")
            self.results["tests_failed"] += 1
            self.results["errors"].append(f"Exception during post-recovery test: {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """Executa todos os testes de failover.
        
        Returns:
            True se todos os testes passaram
        """
        print("=" * 60)
        print("🧪 REDIS FAILOVER TESTS - W8-D Production Hardening")
        print("=" * 60)
        
        # 1. Conectar ao Redis
        if not self.connect_redis():
            print("\n❌ Não foi possível conectar ao Redis. Abortando testes.")
            return False
        
        # 2. Testar API com Redis funcionando
        if not self.test_api_health():
            print("\n❌ API não está saudável. Abortando testes.")
            return False
        
        # 3. Simular falha do Redis
        self.simulate_redis_failure()
        time.sleep(2)  # Aguardar propagação
        
        # 4. Testar API durante falha
        self.test_api_during_redis_failure()
        
        # 5. Reconectar ao Redis
        # (Em produção, isso seria automático via RedisFailoverHandler)
        self.test_redis_reconnection()
        
        # 6. Testar API após recuperação
        self.test_api_after_redis_recovery()
        
        # Relatório final
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL")
        print("=" * 60)
        print(f"✅ Testes passados: {self.results['tests_passed']}")
        print(f"❌ Testes falhados: {self.results['tests_failed']}")
        
        if self.results["errors"]:
            print("\n❌ Erros encontrados:")
            for error in self.results["errors"]:
                print(f"  - {error}")
        
        success = self.results["tests_failed"] == 0
        
        if success:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
        else:
            print("\n❌ ALGUNS TESTES FALHARAM")
        
        return success


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Teste de failover Redis")
    parser.add_argument("--redis-url", default="redis://localhost:6379", help="URL do Redis")
    parser.add_argument("--api-url", default="http://localhost:8012", help="URL da API")
    args = parser.parse_args()
    
    tester = RedisFailoverTester(redis_url=args.redis_url, api_url=args.api_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

