"""Locust load testing for HL7v2 endpoint.

Execute com:
    locust -f locustfile.py --host=http://localhost:8012

Web UI: http://localhost:8089
"""

import os
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# Mensagem HL7v2 de teste
HL7_MESSAGE_TEMPLATE = """MSH|^~\\&|TASY|HSP|GRAHAME|INTELLICARE|20260225120000||ADT^A04|MSG{msg_id}|P|2.5
EVN|A04|20260225120000
PID|1||{patient_id}^^^HSP^MR||Silva^João^Carlos||19800101|M|||Rua das Flores, 123^^São Paulo^SP^01234-567^BR||11987654321||PT|C|CAT|||123456789||||||BR
PV1|1|I|UTI^101^01^HSP||||123456^Santos^Maria^A^^^Dra.||||||CLI||||V|||||||||||||||||||||||||20260225120000"""


class HL7v2User(HttpUser):
    """Usuário simulado que envia mensagens HL7v2."""
    
    # Tempo de espera entre requisições (em segundos)
    wait_time = between(0.1, 0.5)
    
    # API Key (deve ser configurada via variável de ambiente)
    api_key = os.getenv("HL7V2_API_KEY", "")
    
    # Contador de mensagens
    msg_counter = 0
    
    def on_start(self):
        """Executado quando o usuário inicia."""
        if not self.api_key:
            raise ValueError(
                "API Key não configurada! "
                "Configure a variável de ambiente HL7V2_API_KEY"
            )
    
    @task
    def send_adt_a04(self):
        """Envia mensagem ADT^A04."""
        # Incrementa contador
        self.msg_counter += 1
        
        # Gera mensagem com IDs únicos
        message = HL7_MESSAGE_TEMPLATE.format(
            msg_id=str(self.msg_counter).zfill(10),
            patient_id=str(10000 + (self.msg_counter % 1000)),
        )
        
        # Envia requisição
        with self.client.post(
            "/api/v1/hl7v2/adt-a04",
            data=message,
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/x-hl7-v2",
            },
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                # Rate limit - não marca como falha
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Executado quando o teste inicia."""
    print("\n" + "=" * 70)
    print("🚀 INICIANDO TESTE DE CARGA HL7v2")
    print("=" * 70)
    print(f"Host: {environment.host}")
    print(f"Target: 1000+ req/s")
    
    # Verifica se é master (em modo distribuído)
    if isinstance(environment.runner, MasterRunner):
        print(f"Modo: Distribuído (Master)")
        print(f"Workers esperados: {environment.runner.worker_count}")
    else:
        print(f"Modo: Local")
    
    print("=" * 70 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Executado quando o teste termina."""
    stats = environment.stats
    
    print("\n" + "=" * 70)
    print("📊 RESULTADOS DO TESTE DE CARGA")
    print("=" * 70)
    
    # Estatísticas gerais
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    success_rate = (total_requests - total_failures) / total_requests * 100 if total_requests > 0 else 0
    
    print(f"\n🚀 Throughput:")
    print(f"   Total de requisições: {total_requests}")
    print(f"   Requisições bem-sucedidas: {total_requests - total_failures}")
    print(f"   Requisições falhadas: {total_failures}")
    print(f"   Taxa de sucesso: {success_rate:.2f}%")
    print(f"   RPS (atual): {stats.total.current_rps:.2f} req/s")
    print(f"   RPS (total médio): {stats.total.total_rps:.2f} req/s")
    
    # Target check
    if stats.total.total_rps >= 1000:
        print(f"   ✅ TARGET ATINGIDO! (>= 1000 req/s)")
    else:
        print(f"   ⚠️  Abaixo do target (< 1000 req/s)")
    
    # Latência
    print(f"\n⏱️  Latência:")
    print(f"   Média: {stats.total.avg_response_time:.2f}ms")
    print(f"   Mínima: {stats.total.min_response_time:.2f}ms")
    print(f"   Máxima: {stats.total.max_response_time:.2f}ms")
    print(f"   P50 (mediana): {stats.total.get_response_time_percentile(0.50):.2f}ms")
    print(f"   P95: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"   P99: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    
    # Erros
    if stats.errors:
        print(f"\n❌ Erros:")
        for error in stats.errors.values():
            print(f"   {error.method} {error.name}: {error.occurrences} ({error.error})")
    
    print("\n" + "=" * 70)


# Configurações de exemplo para diferentes cenários
"""
# Cenário 1: Warmup (100 usuários, 10 req/s)
locust -f locustfile.py --host=http://localhost:8012 --users 100 --spawn-rate 10 --run-time 1m

# Cenário 2: Carga média (500 usuários, 50 req/s)
locust -f locustfile.py --host=http://localhost:8012 --users 500 --spawn-rate 50 --run-time 5m

# Cenário 3: Carga alta (1000 usuários, 100 req/s)
locust -f locustfile.py --host=http://localhost:8012 --users 1000 --spawn-rate 100 --run-time 10m

# Cenário 4: Stress test (2000 usuários, 200 req/s)
locust -f locustfile.py --host=http://localhost:8012 --users 2000 --spawn-rate 200 --run-time 15m

# Modo distribuído (master + workers)
# Master:
locust -f locustfile.py --master --host=http://localhost:8012

# Worker (executar em múltiplas máquinas/terminais):
locust -f locustfile.py --worker --master-host=localhost
"""

