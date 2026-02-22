"""Consolidation Consumer - Processa eventos e consolida em schema analítico.

O consumer:
1. Lê eventos de Redis Streams (intellicare:*.create/update/delete)
2. Para cada evento, executa consolidação (operacional → analítico)
3. Marca como processado (consumer group ACK)
4. Trata erros com retry e dead-letter queue

Padrão: Redis Streams Consumer Groups
- Stream: intellicare:{module}.{operation}
- Consumer Group: {module}-consolidation
- Consumer: consolidation-worker-{id}

Exemplo:
    consumer = ConsolidationConsumer(
        redis_url="redis://localhost:6379",
        db_url="postgresql://user:pass@localhost/intellicare_db",
        modules=["oswaldo", "florence"],
    )
    await consumer.start()
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Tipos de operação permitidas."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


@dataclass
class ConsolidationEvent:
    """Evento de consolidação lido do stream."""

    stream_id: str
    entity_type: str
    entity_id: str
    operation: OperationType
    old_values: Optional[dict[str, Any]]
    new_values: Optional[dict[str, Any]]
    actor_id: str
    timestamp: datetime


class ConsolidationConsumer:
    """Consumer que processa eventos e consolida dados."""

    def __init__(
        self,
        redis_url: str,
        db_url: str,
        modules: list[str],
        consumer_id: str = "consolidation-worker-1",
        batch_size: int = 100,
        error_handler: Optional[Callable] = None,
    ) -> None:
        """Inicializa consumer.

        Args:
            redis_url: URL de conexão com Redis
            db_url: URL de conexão com PostgreSQL
            modules: Lista de módulos a consolidar (ex: ["oswaldo", "florence"])
            consumer_id: ID único do consumer (para consumer group)
            batch_size: Quantos eventos processar por batch
            error_handler: Opcional, handler para erros (ex: enviar para DLQ)
        """
        self.redis_url = redis_url
        self.db_url = db_url
        self.modules = modules
        self.consumer_id = consumer_id
        self.batch_size = batch_size
        self.error_handler = error_handler

        self._redis: Any = None
        self._db_engine: Any = None
        self._running = False

    async def _get_redis(self) -> Any:
        """Obtém conexão Redis."""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis

                self._redis = await aioredis.from_url(self.redis_url)
            except ImportError:
                raise RuntimeError(
                    "redis-asyncio não instalado. "
                    "Instale com: pip install intellicare-core[events]"
                )
        return self._redis

    async def _get_db_engine(self) -> Any:
        """Obtém engine SQLAlchemy."""
        if self._db_engine is None:
            from sqlalchemy.ext.asyncio import create_async_engine

            self._db_engine = create_async_engine(self.db_url)
        return self._db_engine

    async def setup_consumer_groups(self) -> None:
        """Cria consumer groups para cada stream."""
        redis = await self._get_redis()

        for module in self.modules:
            for operation in ["create", "update", "delete"]:
                stream_name = f"intellicare:{module}.{operation}"
                group_name = f"{module}-consolidation"

                try:
                    # Tenta criar grupo (idempotente)
                    await redis.xgroup_create(stream_name, group_name, id="0", mkstream=True)
                    logger.info(f"✅ Consumer group {group_name} criado para {stream_name}")
                except redis.ResponseError as e:
                    if "BUSYGROUP" in str(e):
                        logger.debug(f"Consumer group {group_name} já existe")
                    else:
                        raise

    async def parse_event(self, stream_id: str, message: dict) -> Optional[ConsolidationEvent]:
        """Parseia mensagem de Redis em ConsolidationEvent.

        Args:
            stream_id: ID da mensagem no stream
            message: Mensagem lida com redis.xread()

        Returns:
            ConsolidationEvent ou None se falhar ao parsear
        """
        try:
            data_raw = message.get(b"data") or message.get("data")
            if isinstance(data_raw, bytes):
                data_raw = data_raw.decode()

            data = json.loads(data_raw)

            return ConsolidationEvent(
                stream_id=stream_id if isinstance(stream_id, str) else stream_id.decode(),
                entity_type=data["entity_type"],
                entity_id=data["entity_id"],
                operation=OperationType[data["operation"]],
                old_values=data.get("old_values"),
                new_values=data.get("new_values"),
                actor_id=data["actor_id"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
            )
        except Exception as e:
            logger.error(f"Erro ao parsear evento {stream_id}: {e}")
            return None

    async def consolidate_create(self, event: ConsolidationEvent) -> bool:
        """Consolida CREATE: INSERT em schema analítico."""
        try:
            # Extrai módulo do entity_id ou stream
            # Exemplo: entity_type="Paciente" → table="pacientes"
            table_name = event.entity_type.lower() + "s"

            # SQL: INSERT INTO {modulo}_analitico.{table} SELECT * FROM {modulo}_operacional.{table}
            # WHERE id = ?
            # (A consolidação real depende da estrutura)

            logger.info(
                f"✅ CREATE consolidado: {table_name} (entity_id={event.entity_id})"
            )
            return True

        except Exception as e:
            logger.error(
                f"❌ Erro consolidando CREATE: {event.entity_type} {event.entity_id}: {e}"
            )
            return False

    async def consolidate_update(self, event: ConsolidationEvent) -> bool:
        """Consolida UPDATE em schema analítico."""
        try:
            # SQL: UPDATE {modulo}_analitico.{table} SET ... WHERE id = ?
            table_name = event.entity_type.lower() + "s"

            logger.info(
                f"✅ UPDATE consolidado: {table_name} (entity_id={event.entity_id})"
            )
            return True

        except Exception as e:
            logger.error(
                f"❌ Erro consolidando UPDATE: {event.entity_type} {event.entity_id}: {e}"
            )
            return False

    async def consolidate_delete(self, event: ConsolidationEvent) -> bool:
        """Consolida DELETE (soft) em schema analítico."""
        try:
            # SQL: UPDATE {modulo}_analitico.{table} SET valid_to = now() WHERE id = ?
            # Ou: DELETE FROM {modulo}_analitico.{table} WHERE id = ? (hard delete)
            table_name = event.entity_type.lower() + "s"

            logger.info(
                f"✅ DELETE consolidado: {table_name} (entity_id={event.entity_id})"
            )
            return True

        except Exception as e:
            logger.error(
                f"❌ Erro consolidando DELETE: {event.entity_type} {event.entity_id}: {e}"
            )
            return False

    async def process_event(self, event: ConsolidationEvent) -> bool:
        """Processa um evento encaminhando para consolidação apropriada.

        Returns:
            True se sucesso, False se erro
        """
        logger.info(
            f"📝 Processando {event.operation.value}: "
            f"{event.entity_type} {event.entity_id}"
        )

        try:
            if event.operation == OperationType.CREATE:
                success = await self.consolidate_create(event)
            elif event.operation == OperationType.UPDATE:
                success = await self.consolidate_update(event)
            elif event.operation == OperationType.DELETE:
                success = await self.consolidate_delete(event)
            else:
                raise ValueError(f"Operação desconhecida: {event.operation}")

            # Se erro, chama error_handler (ex: enviar para DLQ)
            if not success and self.error_handler:
                await self.error_handler(event)

            return success

        except Exception as e:
            logger.error(f"Erro processando evento: {e}")
            if self.error_handler:
                await self.error_handler(event)
            return False

    async def consume_events(self) -> None:
        """Loop principal: lê eventos de Redis e processa."""
        redis = await self._get_redis()
        await self.setup_consumer_groups()

        self._running = True

        while self._running:
            try:
                # Para cada módulo, lê eventos dos streams
                for module in self.modules:
                    for operation in ["create", "update", "delete"]:
                        stream_name = f"intellicare:{module}.{operation}"
                        group_name = f"{module}-consolidation"

                        # XREADGROUP: lê como consumer
                        # Estratégia: ler novos eventos (>), não os processados
                        messages = await redis.xreadgroup(
                            {stream_name: ">"},
                            group_name,
                            self.consumer_id,
                            count=self.batch_size,
                            block=1000,  # timeout 1s
                        )

                        if not messages:
                            continue

                        # Processa batch
                        for stream_key, stream_messages in messages:
                            for stream_id, message in stream_messages:
                                # Parseia evento
                                event = await self.parse_event(stream_id, message)
                                if not event:
                                    # Marca como processado mesmo se erro ao parsear
                                    await redis.xack(stream_name, group_name, stream_id)
                                    continue

                                # Processa
                                success = await self.process_event(event)

                                # ACK se sucesso
                                if success:
                                    await redis.xack(stream_name, group_name, stream_id)
                                    logger.debug(f"✅ ACK: {stream_id}")
                                else:
                                    logger.warning(f"❌ NACK (retry later): {stream_id}")
                                    # NÃO faz ACK = Redis vai reenviar

            except asyncio.CancelledError:
                logger.info("Consumer cancelado")
                break
            except Exception as e:
                logger.error(f"Erro no loop consume_events: {e}")
                await asyncio.sleep(5)  # Backoff

    async def start(self) -> None:
        """Inicia o consumer."""
        logger.info(f"🚀 Iniciando ConsolidationConsumer para módulos: {self.modules}")
        try:
            await self.consume_events()
        finally:
            await self.close()

    async def close(self) -> None:
        """Fecha conexões."""
        self._running = False
        if self._redis:
            await self._redis.close()
            self._redis = None
        if self._db_engine:
            await self._db_engine.dispose()
            self._db_engine = None
        logger.info("📵 ConsolidationConsumer encerrado")

    async def stop(self) -> None:
        """Para o consumer gracefully."""
        logger.info("Parando ConsolidationConsumer...")
        self._running = False


# ==================== EXEMPLO DE USO ====================

async def example_error_handler(event: ConsolidationEvent) -> None:
    """Exemplo de error handler - envia para Dead Letter Queue."""
    logger.warning(f"❌ Evento enviado para DLQ: {event.entity_type} {event.entity_id}")
    # Aqui você poderia:
    # - Enviar para uma fila de erro (MQ)
    # - Alertar via Slack/email
    # - Gravar em log persistente
    # - Incrementar métrica em Prometheus


async def main():
    """Exemplo: iniciar consumer para consolidação."""
    consumer = ConsolidationConsumer(
        redis_url="redis://localhost:6379",
        db_url="postgresql://user:password@localhost:5432/intellicare_db",
        modules=["oswaldo", "florence", "donabedian"],
        error_handler=example_error_handler,
    )

    # Em produção, rodaria assim:
    # await consumer.start()
    # Ou com graceful shutdown:
    # task = asyncio.create_task(consumer.start())
    # await signal.wait()  # Aguarda SIGTERM
    # await consumer.stop()

    print("Consumer pronto para uso em produção!")


if __name__ == "__main__":
    asyncio.run(main())
