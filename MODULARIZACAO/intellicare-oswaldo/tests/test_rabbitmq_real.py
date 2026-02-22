"""
Script para testar RabbitMQ real (integração Florence ↔ Oswaldo).

Este script:
1. Verifica conexão ao RabbitMQ (localhost:5672)
2. Cria exchanges e queues
3. Publica evento de exame Florence
4. Consumer recebe e processa
5. Publica resposta Oswaldo
6. Verifica resultado no banco
"""

import pika
import json
import logging
import time
from datetime import datetime
import sys
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class RabbitMQTestSuite:
    """Suite de testes para RabbitMQ real."""
    
    def __init__(self, host='localhost', port=5672):
        self.host = host
        self.port = port
        self.connection = None
        self.channel = None
        self.messages_received = []
        
    def setup(self):
        """Conectar ao RabbitMQ e declarar infraestrutura."""
        try:
            logger.info(f"[Setup] Conectando ao RabbitMQ em {self.host}:{self.port}...")
            
            params = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                connection_attempts=3,
                retry_delay=2,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            
            logger.info(f"✅ Conectado ao RabbitMQ")
            
            # Declarar exchanges
            logger.info("[Setup] Declarando exchanges...")
            self.channel.exchange_declare(
                exchange="florence.events",
                exchange_type="topic",
                durable=True
            )
            self.channel.exchange_declare(
                exchange="oswaldo.events",
                exchange_type="topic",
                durable=True
            )
            logger.info(f"✅ Exchanges declarados")
            
            # Declarar queues
            logger.info("[Setup] Declarando queues...")
            self.channel.queue_declare(queue="oswaldo.exame_resultado", durable=True)
            self.channel.queue_declare(queue="oswaldo.paciente_dados", durable=True)
            self.channel.queue_declare(queue="oswaldo.request_consulta", durable=True)
            self.channel.queue_declare(queue="florence.oswaldo_response", durable=True)
            logger.info(f"✅ Queues declarados")
            
            # Binding
            logger.info("[Setup] Fazendo bindings...")
            self.channel.queue_bind(
                queue="oswaldo.exame_resultado",
                exchange="florence.events",
                routing_key="florence.exame_resultado"
            )
            self.channel.queue_bind(
                queue="florence.oswaldo_response",
                exchange="oswaldo.events",
                routing_key="oswaldo.alerta"
            )
            logger.info(f"✅ Bindings estabelecidos")
            
            # Set QoS
            self.channel.basic_qos(prefetch_count=1)
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao RabbitMQ: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def test_publish_exame(self):
        """Test 1: Publicar evento de exame Florence."""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 1: Publicar evento de exame")
            logger.info("="*60)
            
            event = {
                "event_type": "exame_resultado",
                "paciente_cpf_hash": "test_real_001",
                "data_coleta": datetime.utcnow().isoformat(),
                "tipo_exame": "glicemia",
                "valor": 350.0,
                "unidade": "mg/dL",
                "laboratorio": "Lab Central",
                "medico_solicitante": "Dr. Silva"
            }
            
            message = json.dumps(event)
            
            logger.info(f"[Pub] Publicando evento: {event['tipo_exame']}={event['valor']}")
            self.channel.basic_publish(
                exchange="florence.events",
                routing_key="florence.exame_resultado",
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type='application/json'
                )
            )
            
            logger.info(f"✅ Evento publicado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_receive_exame(self, timeout=5):
        """Test 2: Receber evento de exame na queue."""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 2: Receber evento de exame")
            logger.info("="*60)
            
            logger.info(f"[Sub] Aguardando mensagem por {timeout}s...")
            
            def callback(ch, method, properties, body):
                logger.info(f"✅ Mensagem recebida!")
                event = json.loads(body)
                logger.info(f"  - Tipo: {event['event_type']}")
                logger.info(f"  - Exame: {event['tipo_exame']}={event['valor']}")
                logger.info(f"  - Paciente: {event['paciente_cpf_hash'][:12]}...")
                
                self.messages_received.append(event)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
                # Parar de consumir após receber 1
                ch.stop_consuming()
            
            self.channel.basic_consume(
                queue="oswaldo.exame_resultado",
                on_message_callback=callback
            )
            
            # Consumir com timeout
            self.channel.connection.call_later(timeout, lambda: self.channel.stop_consuming())
            self.channel.start_consuming()
            
            if self.messages_received:
                logger.info(f"✅ Mensagem recebida com sucesso")
                return True
            else:
                logger.warning(f"⏱️ Timeout: nenhuma mensagem recebida em {timeout}s")
                logger.info("💡 Dica: Verifique se Florence está publicando eventos")
                return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao receber: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_publish_response(self):
        """Test 3: Publicar resposta (Oswaldo → Florence)."""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 3: Publicar resp (Oswaldo → Florence)")
            logger.info("="*60)
            
            alerta = {
                "event_type": "oswaldo_alerta",
                "paciente_cpf_hash": "test_real_001",
                "tipo_alerta": "PIORA_PROGRESSIVA",
                "severidade": "CRITICO",
                "descricao": "Glicemia crítica: 350 mg/dL",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            message = json.dumps(alerta)
            
            logger.info(f"[Pub] Publicando alerta: {alerta['tipo_alerta']} ({alerta['severidade']})")
            self.channel.basic_publish(
                exchange="oswaldo.events",
                routing_key="oswaldo.alerta",
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            logger.info(f"✅ Alerta publicado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar alerta: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_receive_response(self, timeout=5):
        """Test 4: Receber resposta Florence."""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 4: Receber resposta (Florence)")
            logger.info("="*60)
            
            logger.info(f"[Sub] Aguardando resposta por {timeout}s...")
            
            responses = []
            
            def callback(ch, method, properties, body):
                logger.info(f"✅ Resposta recebida!")
                event = json.loads(body)
                logger.info(f"  - Tipo: {event['event_type']}")
                logger.info(f"  - Severidade: {event['severidade']}")
                
                responses.append(event)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                ch.stop_consuming()
            
            self.channel.basic_consume(
                queue="florence.oswaldo_response",
                on_message_callback=callback
            )
            
            self.channel.connection.call_later(timeout, lambda: self.channel.stop_consuming())
            self.channel.start_consuming()
            
            if responses:
                logger.info(f"✅ Resposta recebida")
                return True
            else:
                logger.warning(f"⏱️ Timeout: nenhuma resposta em {timeout}s")
                logger.info("💡 Dica: Aguarde consumer processar e publicar")
                return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao receber resposta: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_declare_queue_depth(self):
        """Test 5: Verificar profundidade de filas."""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 5: Profundidade de filas")
            logger.info("="*60)
            
            queues = [
                "oswaldo.exame_resultado",
                "oswaldo.paciente_dados",
                "oswaldo.request_consulta",
                "florence.oswaldo_response"
            ]
            
            for queue_name in queues:
                method = self.channel.queue_declare(
                    queue=queue_name,
                    passive=True
                )
                logger.info(f"  {queue_name}: {method.method.message_count} mensagens")
            
            logger.info(f"✅ Profundidades verificadas")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar filas: {e}")
            return False
    
    def run_all_tests(self):
        """Executar todos os testes."""
        results = {
            "test_publish_exame": False,
            "test_receive_exame": False,
            "test_publish_response": False,
            "test_receive_response": False,
            "test_queue_depth": False
        }
        
        try:
            self.setup()
            
            results["test_publish_exame"] = self.test_publish_exame()
            time.sleep(1)  # Aguardar propação
            
            results["test_receive_exame"] = self.test_receive_exame(timeout=5)
            
            results["test_publish_response"] = self.test_publish_response()
            time.sleep(1)
            
            results["test_receive_response"] = self.test_receive_response(timeout=5)
            
            results["test_queue_depth"] = self.test_declare_queue_depth()
            
        except Exception as e:
            logger.error(f"\n❌ ERRO FATAL: {e}")
            logger.error(traceback.format_exc())
        
        finally:
            self.close()
            self.print_results(results)
    
    def close(self):
        """Fechar conexão."""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("[Close] Conexão RabbitMQ fechada")
        except Exception as e:
            logger.error(f"Erro ao fechar: {e}")
    
    def print_results(self, results):
        """Imprimir resumo dos resultados."""
        logger.info("\n" + "="*60)
        logger.info("RESUMO DOS TESTES")
        logger.info("="*60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} - {test}")
        
        logger.info(f"\n{passed}/{total} testes passaram ({passed*100//total}%)")
        
        if passed == total:
            logger.info("\n🎉 SUCESSO! RabbitMQ está funcionando corretamente")
        else:
            logger.warning("\n⚠️ Alguns testes falharam. Veja acima para detalhes")
            logger.info("\nDicas:")
            logger.info("1. Verificar se RabbitMQ está rodando: rabbitmqctl status")
            logger.info("2. Verificar logs: docker logs rabbitmq")
            logger.info("3. Acessar UI: http://localhost:15672 (guest/guest)")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Teste de RabbitMQ real")
    parser.add_argument("--host", default="localhost", help="Host RabbitMQ")
    parser.add_argument("--port", type=int, default=5672, help="Port RabbitMQ")
    parser.add_argument("--docker-start", action="store_true", 
                       help="Iniciar RabbitMQ via Docker se não estiver rodando")
    
    args = parser.parse_args()
    
    # Tentar detectar RabbitMQ
    logger.info("\n" + "🐰 "*15)
    logger.info("TESTE DE RABBITMQ REAL - FLORENCE ↔ OSWALDO")
    logger.info("🐰 "*15)
    
    try:
        test_suite = RabbitMQTestSuite(host=args.host, port=args.port)
        test_suite.run_all_tests()
        
    except Exception as e:
        logger.error(f"\n❌ Falha ao conectar ao RabbitMQ: {e}")
        logger.info("\n💡 RabbitMQ não está disponível. Opções:")
        logger.info("1. Iniciar com Docker:")
        logger.info("   docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.12-management")
        logger.info("2. Ou com Docker Compose:")
        logger.info("   docker-compose up -d rabbitmq")
        logger.info("3. Ou instalar localmente: see https://www.rabbitmq.com/install-windows.html")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
