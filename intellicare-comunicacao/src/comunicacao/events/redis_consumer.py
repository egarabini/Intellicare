import redis
import json
from comunicacao.routing.engine import RoutingEngine
from comunicacao.dispatchers.manager import DispatcherManager

class RedisEventConsumer:
    """
    Consumidor de eventos do Redis Streams (stub, integra com pipeline de roteamento).
    """
    def __init__(self, redis_url: str = "redis://localhost:6379", stream: str = "comunicacao_events"):
        self.redis_url = redis_url
        self.stream = stream
        self.client = redis.Redis.from_url(redis_url)
        self.routing_engine = RoutingEngine()
        self.dispatcher_manager = DispatcherManager()

    def consume(self):
        # Exemplo: lê eventos do stream e processa
        last_id = '0-0'
        while True:
            events = self.client.xread({self.stream: last_id}, count=10, block=1000)
            for stream_name, messages in events:
                for msg_id, msg_data in messages:
                    event = {k.decode(): v.decode() for k, v in msg_data.items()}
                    # Processa evento
                    routing_result = self.routing_engine.route_intent(event)
                    self.dispatcher_manager.dispatch(routing_result["channel"], event)
                    last_id = msg_id
