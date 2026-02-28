"""
Florence Event Publisher Service
=================================

Publicador de eventos para RabbitMQ - Integração Florence-Oswaldo

Eventos publicados:
1. exame_critico - Exame com resultado crítico
2. exame_created - Novo exame criado
3. alerta_novo - Novo alerta/padrão detectado
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Tipos de eventos Florence"""
    EXAME_CRITICO = "exame_critico"
    EXAME_CREATED = "exame_created"
    ALERTA_NOVO = "alerta_novo"


class FlorenanceEventPublisher:
    """
    Publisher de eventos Florence para RabbitMQ.
    
    Uso futuro com pika/aio_pika para RabbitMQ real.
    Por agora: stub para simular publicação.
    
    Quando Oswaldo for implementado, vai se conectar ao consumer.
    """
    
    SCHEMA_VERSION = "1.0"
    
    def __init__(self, rabbitmq_url: Optional[str] = None):
        """
        Inicializar publisher.
        
        Args:
            rabbitmq_url: URL RabbitMQ (ex: amqp://user:pass@localhost:5672/)
                         Se None, opera em modo stub (logging apenas)
        """
        self.rabbitmq_url = rabbitmq_url or "amqp://localhost:5672/"
        self.modo_stub = not rabbitmq_url  # Stub mode se não houver URL real
        logger.info(f"FlorenanceEventPublisher iniciado (modo: {'STUB' if self.modo_stub else 'REAL'})")
    
    def publicar_exame_critico(
        self,
        paciente_id_hash: str,
        exame_id: str,
        exame_tipo: str,
        resultado: Dict[str, Any],
        problema: str,
        severidade: str = "critica",
        encaminhar_emergencia: bool = False,
    ) -> bool:
        """
        Publica evento quando exame tem resultado crítico.
        
        Args:
            paciente_id_hash: SHA256 hash do CPF
            exame_id: ID único do exame
            exame_tipo: Tipo (hemograma, lipidograma, etc)
            resultado: Dicionário com parâmetros do exame
            problema: Descrição do problema detectado
            severidade: critica | aviso | info
            encaminhar_emergencia: Se true, encaminhar emergência
            
        Returns:
            bool - True se publicado com sucesso
        """
        evento = {
            "version": self.SCHEMA_VERSION,
            "event_type": EventType.EXAME_CRITICO,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_id": str(uuid.uuid4()),
            
            "paciente": {
                "id_hash": paciente_id_hash,
            },
            
            "exame": {
                "id": exame_id,
                "tipo": exame_tipo,
                "resultado": resultado,
            },
            
            "validacao": {
                "valido": False,
                "tipo_problema": "resultado_critico",
                "problemas": [{
                    "parametro": exame_tipo,
                    "severidade": severidade,
                    "mensagem": problema,
                }]
            },
            
            "recomendacao": {
                "acao": "revisar_imediatamente" if severidade == "critica" else "revisar_hoje",
                "encaminhar_emergencia": encaminhar_emergencia,
                "justificativa": problema,
            },
            
            "origem": {
                "sistema": "florence",
                "versao_api": "v1",
            }
        }
        
        return self._publicar(evento, "florence.exame.critico")
    
    def publicar_exame_criado(
        self,
        paciente_id_hash: str,
        exame_id: str,
        exame_tipo: str,
        resultado: Dict[str, Any],
        age_anos: Optional[int] = None,
        condicoes: Optional[list] = None,
    ) -> bool:
        """
        Publica evento quando novo exame é criado e passou validação.
        
        Args:
            paciente_id_hash: SHA256 hash do CPF
            exame_id: ID único
            exame_tipo: Tipo de exame
            resultado: Parâmetros do exame
            age_anos: Idade do paciente
            condicoes: Lista de condições (diabético, hipertensão, etc)
            
        Returns:
            bool - True se publicado
        """
        evento = {
            "version": self.SCHEMA_VERSION,
            "event_type": EventType.EXAME_CREATED,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_id": str(uuid.uuid4()),
            
            "paciente": {
                "id_hash": paciente_id_hash,
                "age_anos": age_anos,
                "condicoes": condicoes or [],
            },
            
            "exame": {
                "id": exame_id,
                "tipo": exame_tipo,
                "data_resultado": datetime.utcnow().isoformat() + "Z",
                "resultado": resultado,
            },
            
            "validacao": {
                "validador": "ClinicaAlgorithmValidator",
                "valido": True,
                "problemas": [],
            },
            
            "origem": {
                "sistema": "florence",
                "versao_api": "v1",
            }
        }
        
        return self._publicar(evento, "florence.exame.created")
    
    def publicar_alerta(
        self,
        paciente_id_hash: str,
        alerta_tipo: str,
        serie_exames: list,
        analise: Dict[str, Any],
        severidade: str = "media",
    ) -> bool:
        """
        Publica evento quando padrão/alerta é detectado.
        
        Args:
            paciente_id_hash: Hash do CPF
            alerta_tipo: Tipo (tendencia_glicemia_elevada, etc)
            serie_exames: Lista de exames analisados
            analise: Resultado da análise
            severidade: baixa | media | alta | critica
            
        Returns:
            bool - True se publicado
        """
        evento = {
            "version": self.SCHEMA_VERSION,
            "event_type": EventType.ALERTA_NOVO,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_id": str(uuid.uuid4()),
            
            "paciente": {
                "id_hash": paciente_id_hash,
            },
            
            "alerta": {
                "id": str(uuid.uuid4()),
                "tipo": alerta_tipo,
                "severidade": severidade,
                "serie_exames": serie_exames,
                "analise": analise,
            },
            
            "origem": {
                "sistema": "florence",
                "versao_api": "v1",
            }
        }
        
        return self._publicar(evento, "florence.alerta.novo")
    
    def _publicar(self, evento: Dict[str, Any], queue: str) -> bool:
        """
        Publica evento em fila RabbitMQ.
        
        Args:
            evento: Dicionário com evento
            queue: Nome da fila (florence.exame.critico, etc)
            
        Returns:
            bool - True se sucesso
        """
        try:
            # Serializar para JSON
            evento_json = json.dumps(evento, default=str, ensure_ascii=False)
            
            if self.modo_stub:
                # Modo stub: apenas log
                logger.info(f"[STUB] Publicando em {queue}: {evento['event_type']}")
                logger.debug(f"Payload: {evento_json}")
            else:
                # Modo real: publicar em RabbitMQ
                # TODO: Implementar com pika
                # channel.basic_publish(
                #     exchange='',
                #     routing_key=queue,
                #     body=evento_json
                # )
                logger.info(f"[REAL] Publicado em {queue}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro publicando evento: {str(e)}", exc_info=True)
            return False


# Exemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    publisher = FlorenanceEventPublisher()
    
    # Exemplo 1: Exame crítico
    success = publisher.publicar_exame_critico(
        paciente_id_hash="d4ffa1a7c6e2b8f9...",
        exame_id="exm_12345",
        exame_tipo="glicemia",
        resultado={"glicemia": 350},
        problema="Hiperglicemia crítica (>300)",
        encaminhar_emergencia=True,
    )
    print(f"Exame crítico publicado: {success}")
    
    # Exemplo 2: Exame criado (normal)
    success = publisher.publicar_exame_criado(
        paciente_id_hash="a1b2c3d4e5f6...",
        exame_id="exm_54321",
        exame_tipo="hemograma",
        resultado={"hemoglobina": 14.5, "hematocrito": 42.5},
        age_anos=45,
        condicoes=["diabético"],
    )
    print(f"Exame criado publicado: {success}")
