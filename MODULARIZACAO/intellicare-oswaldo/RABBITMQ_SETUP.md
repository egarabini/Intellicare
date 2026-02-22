# RabbitMQ Setup para Teste Real

## Opção 1: Docker (Recomendado)

```bash
# Iniciar RabbitMQ com management UI
docker run -d \
  --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=guest \
  -e RABBITMQ_DEFAULT_PASS=guest \
  rabbitmq:3.12-management

# Verificar status
docker logs rabbitmq

# Acessar UI
# Browser: http://localhost:15672
# User: guest / Pass: guest
```

## Opção 2: Docker Compose

```bash
# Criar docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  rabbitmq:
    image: rabbitmq:3.12-management
    container_name: oswaldo-rabbitmq
    ports:
      - "5672:5672"    # AMQP
      - "15672:15672"  # Management UI
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

volumes:
  rabbitmq_data:
EOF

# Iniciar
docker-compose up -d

# Verificar logs
docker-compose logs -f rabbitmq
```

## Opção 3: Instalação Local (Windows)

1. Download: https://www.rabbitmq.com/install-windows.html
2. Instalar Erlang OTP primeiro (dependency)
3. Instalar RabbitMQ

```bash
# Verificar status
rabbitmqctl status

# Iniciar serviço
rabbitmq-server

# Enable management plugin
rabbitmq-plugins enable rabbitmq_management
```

## Verificar Conectividade

```bash
# Após RabbitMQ rodando, executar testes
python tests/test_rabbitmq_real.py

# Output esperado:
# ✅ PASS - test_publish_exame
# ✅ PASS - test_receive_exame
# ✅ PASS - test_publish_response
# ✅ PASS - test_receive_response
# ✅ PASS - test_queue_depth
# 
# 5/5 testes passaram (100%)
# 🎉 SUCESSO!
```

## RabbitMQ Management UI

- URL: http://localhost:15672
- User: guest
- Password: guest

### Dashboard
- Overview: Status geral
- Connections: Conexões ativas
- Channels: Canais AMQP
- Exchanges: Florence.events, Oswaldo.events
- Queues: 4 queues (oswaldo.exame_resultado, oswaldo.paciente_dados, etc)

## Troubleshooting

### Port Already in Use
```bash
# Encontrar processo usando porta 5672
netstat -ano | findstr :5672

# Encerrar processo
taskkill /PID <PID> /F
```

### Connection Refused
```bash
# Verificar se RabbitMQ está rodando
ps aux | grep rabbitmq  # Linux/Mac
tasklist | grep rabbitmq  # Windows

# Reiniciar a container
docker restart rabbitmq
```

### High Memory Usage
```bash
# RabbitMQ usa memory() baseado em:
# - Número de mensagens na fila
# - Número de conexões
# - Plugins habilitados

# Limpar queues (DEVELOPMENT ONLY)
rabbitmqctl reset
```

## Próximos Passos

Depois de RabbitMQ rodando, o fluxo completo será:

```
Florence (exame → RabbitMQ)
         ↓
Oswaldo Consumer (recebe → processa)
         ↓
Database (salva Estadiamento + Alerta)
         ↓
Oswaldo Publisher (envia resposta → RabbitMQ)
         ↓
Florence (recebe resposta)
```

## Testing Full E2E

1. RabbitMQ rodando:
   ```bash
   docker ps  # Verifica container
   ```

2. Oswaldo API rodando:
   ```bash
   python run_api_8002.py
   ```

3. Florence Consumer rodando:
   ```bash
   python -c "from src.oswaldo.integrations.rabbitmq_consumer import FlorenzeRabbitMQConsumer; c = FlorenzeRabbitMQConsumer(); c.connect(); c.setup_exchanges_and_queues(); c.start_consuming()"
   ```

4. Executar teste:
   ```bash
   python tests/test_rabbitmq_real.py
   ```

5. Monitorar RabbitMQ UI:
   - Watch queues → messages flowing
   - Watch connections → active connections
   - Watch metrics → Acks/Nacks

## Documentação Official

- RabbitMQ: https://www.rabbitmq.com/documentation.html
- Python pika: https://pika.readthedocs.io/en/stable/
- Docker rabbitmq: https://hub.docker.com/_/rabbitmq
