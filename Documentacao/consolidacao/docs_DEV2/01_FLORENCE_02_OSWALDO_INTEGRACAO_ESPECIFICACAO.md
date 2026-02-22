# ESPECIFICAÇÃO TÉCNICA: INTEGRAÇÃO FLORENCE ↔ OSWALDO

## 📌 ID: DEV2-INTEG-001
## 📅 Data: 12/02/2026
## 👤 Responsável: DEV2
## ⏰ Deadline: 22/02/2026
## 🎯 Prioridade: 🔴 CRÍTICA

---

## 🎯 OBJETIVO

Definir arquitetura de integração bidirecional entre Florence (Análise Laboratorial) e Oswaldo (Doenças Crônicas), permitindo:
1. Florence → Oswaldo: Notificar exames críticos
2. Oswaldo → Florence: Solicitar histórico de exames para diagnóstico
3. Comunicação assíncrona via message queue (RabbitMQ/Redis)

---

## 🏗️ ARQUITETURA

### Fluxo Geral

```
PACIENTE
   │
   ├─→ FLORENCE (Exames Laboratoriais)
   │      │
   │      ├─ Coleta hemograma, glicemia, lipídios, etc
   │      └─ Interpreta: Crítuco? Requer diagnóstico?
   │         │
   │         └─ [TRIGGER] Exame crítico detectado
   │            │
   │            └─→ EVENT BUS (RabbitMQ)
   │               │
   │               └─→ OSWALDO (Doenças Crônicas)
   │                     │
   │                     ├─ Recebe notificação
   │                     ├─ Busca exames históricos
   │                     ├─ Consulta condições conhecidas
   │                     └─ Reclassifica estadiamento
   │                        │
   │                        └─→ Retorna diagnóstico para Florence
   │
   └─→ RESULTADO: Interpretação completa (lab + clínica)


Fluxo inverso (menos frequente):
   
   OSWALDO (em follow-up de paciente)
       │
       └─→ Precisa histórico de exames
           │
           └─→ REQUEST: "Get últimos 6 meses de exames"
               │
               └─→ FLORENCE
                   │
                   └─→ RESPONSE: JSON with exames + interpretações
```

---

## 📡 PROTOCOLO DE COMUNICAÇÃO

### Padrão: Event-Driven Async

**Por quê?**
- Florence não pode esperar resposta (SLA <100ms)
- Oswaldo pode levar mais tempo para cálculos (aceitável)
- Desacoplamento: Florida falha não afeta Oswaldo

### Message Broker

```yaml
Broker: RabbitMQ (ou Redis Streams)
Exchange: florence_events
Routes:
  - florence.exame.critico      # Evento crítico detectado
  - florence.exame.created      # Novo exame criado
  - florence.alerta.novo        # Novo alerta gerado

Queues:
  - oswaldo_critical_alerts     # Oswaldo consome alertas críticos
  - florence_responses          # Florence consome respostas
```

---

## 📜 TIPOS DE EVENTOS

### Evento 1: Exame Crítico Detectado

**Disparo**: Florence detecta valor crítico

**Exemplo**: Glicemia = 400 mg/dL (crítico para diabete)

**Schema**:
```json
{
  "event_id": "73f9c3d7-2b1a-4a5e-9c3f-1a8e7b2c4d6f",
  "event_type": "florence.exame.critico",
  "timestamp": "2026-02-12T15:30:45Z",
  "paciente": {
    "paciente_id_hash": "a1f2c3d4e5f6...",
    "idade_estimada": 45,
    "sexo": "M"
  },
  "exame": {
    "exame_id": 12345,
    "tipo": "LABORATORIO",
    "data": "2026-02-12"
  },
  "parametro_critico": {
    "nome": "Glicemia",
    "valor": 400,
    "unidade": "mg/dL",
    "valor_normal": "70-99",
    "severidade": "VERMELHO",  # VERMELHO, AMARELO, VERDE
    "interpretacao": "Glicemia severamente elevada. Risco de cetoacidose diabética."
  },
  "condicoes_conhecidas": [
    "Diabetes Mellitus tipo 2",
    "Hipertensão"
  ],
  "historico_glicemia_7dias": [
    {"data": "2026-02-05", "valor": 250},
    {"data": "2026-02-06", "valor": 280},
    {"data": "2026-02-10", "valor": 350},
    {"data": "2026-02-12", "valor": 400}
  ]
}
```

### Evento 2: Novo Exame Criado

**Disparo**: Todo novo exame em Florence

**Schema**:
```json
{
  "event_id": "abc123...",
  "event_type": "florence.exame.created",
  "timestamp": "2026-02-12T15:30:00Z",
  "exame_id": 12345,
  "paciente_id_hash": "a1f2c3d4e5f6...",
  "tipo_exame": "LABORATORIO",
  "componentes": [
    {"parametro": "Hemoglobina", "valor": 14.5, "unidade": "g/dL"},
    {"parametro": "Glicemia", "valor": 400, "unidade": "mg/dL"}
  ]
}
```

### Evento 3: Novo Alerta Gerado

**Disparo**: Florence gera alerta automático

**Schema**:
```json
{
  "event_id": "xyz456...",
  "event_type": "florence.alerta.novo",
  "timestamp": "2026-02-12T15:35:00Z",
  "alerta_id": 99999,
  "paciente_id_hash": "a1f2c3d4e5f6...",
  "tipo": "CRITICO",  # CRITICO, AVISO, INFORMATIVO
  "titulo": "Glicemia crítica detectada",
  "descricao": "Paciente com diabetes tipo 2 apresenta glicemia 400 mg/dL",
  "recomendacoes": [
    "Verificar funcionalidade medicação",
    "Monitorar HbA1C",
    "Solicitar avaliação urgente endocrinologia"
  ]
}
```

---

## 🔗 ENDPOINTS DE INTEGRAÇÃO

### API 1: Consultar Exames Históricos (Florence → Oswaldo)

**Endpoint**:
```http
GET /api/v1/integracao/oswaldo/exames-historico
Authorization: Bearer {token_sistema_oswaldo}
Content-Type: application/json

{
  "paciente_id_hash": "a1f2c3d4e5f6...",
  "dias_retroativos": 180,
  "incluir_parametros": ["glicemia", "pressao", "hemoglobina"],
  "minimo_severidade": "AMARELO"
}
```

**Response**:
```json
{
  "paciente_id_hash": "a1f2c3d4e5f6...",
  "exames": [
    {
      "exame_id": 12340,
      "data": "2026-02-05",
      "tipo": "LABORATORIO",
      "resultados": [
        {
          "parametro": "Glicemia",
          "valor": 250,
          "unidade": "mg/dL",
          "status": "AMARELO"
        }
      ],
      "interpretacao_florence": "Glicemia elevada..."
    }
  ],
  "total_exames": 12,
  "periodo": "180 dias"
}
```

### API 2: Receber Diagnóstico De Oswaldo (Oswaldo → Florence)

**Endpoint**:
```http
POST /api/v1/integracao/oswaldo/resposta-diagnostico
Authorization: Bearer {token_sistema_florence}
Content-Type: application/json

{
  "event_id_referencia": "73f9c3d7-2b1a-4a5e...",
  "paciente_id_hash": "a1f2c3d4e5f6...",
  "diagnostico": {
    "numero": "E11.65",  # CID-10
    "descricao": "Diabetes mellitus tipo 2 com hiperglicemia",
    "estagio": "ESTAGIO_2",
    "condicoes_detectadas": [
      {
        "condicao": "DIABETES_TIPO_2",
        "estagio": "ESTAGIO_2",
        "evidencia": "Glicemia 400 mg/dL + História de 7 dias elevada"
      }
    ]
  },
  "recomendacoes_clinicas": [
    {
      "tipo": "MEDICACAO",
      "texto": "Aumentar dose de metformina"
    },
    {
      "tipo": "MONITORAMENTO",
      "texto": "Medir HbA1C em 2 meses"
    }
  ],
  "timestamp_processamento": "2026-02-12T15:40:00Z"
}
```

### API 3: Health Check (Validar Conexão)

```http
GET /api/v1/integracao/health
Response: {"status": "ok", "timestamp": "2026-02-12T15:45:00Z"}
```

---

## 💾 BANCO DE DADOS

### Tabela: `evento_integracao`

```sql
CREATE TABLE evento_integracao (
    -- Identificação
    evento_id UUID PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,  -- florence.exame.critico, oswaldo.diagnostico, etc
    
    -- Referência
    paciente_id_hash CHAR(64) NOT NULL,
    exame_id INT,
    
    -- Payload
    payload JSON NOT NULL,  -- Dados completos do evento
    
    -- Rastreamento
    timestamp_evento TIMESTAMP NOT NULL,
    timestamp_recebido TIMESTAMP DEFAULT NOW(),
    timestamp_processado TIMESTAMP,
    
    -- Status
    status VARCHAR(20) DEFAULT 'PENDENTE',  -- PENDENTE, PROCESSANDO, CONCLUIDO, ERRO
    erro_msg VARCHAR(500),
    tentativas INT DEFAULT 0,
    max_tentativas INT DEFAULT 3,
    
    -- Auditoria
    sistema_origem VARCHAR(50),  -- FLORENCE, OSWALDO
    sistema_destino VARCHAR(50),
    
    -- Índices
    INDEX idx_paciente_data (paciente_id_hash, timestamp_evento),
    INDEX idx_status (status),
    INDEX idx_event_type (event_type)
);
```

### Tabela: `integracao_log`

```sql
CREATE TABLE integracao_log (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- Rastreamento
    evento_id UUID NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Detalhes
    origem_sistema VARCHAR(50),
    destino_sistema VARCHAR(50),
    acao VARCHAR(200),  -- "Evento enviado", "Resposta recebida", etc
    resultado VARCHAR(50),  -- SUCESSO, FALHA, TENTATIVA
    
    -- Debug
    http_status INT,
    resposta_tempo_ms INT,
    erro_detalhes VARCHAR(1000),
    
    -- Índices
    INDEX idx_evento (evento_id),
    INDEX idx_timestamp (timestamp)
);
```

---

## 🔌 IMPLEMENTAÇÃO FLORENCE

### Publisher: Enviar Evento Crítico

```python
# src/florence/integrations/oswaldo_publisher.py

from typing import Dict, Any
from uuid import uuid4
from datetime import datetime
import json
import pika
import logging

logger = logging.getLogger(__name__)

class OswaldoPublisher:
    """
    Publica eventos de Florence para Oswaldo via RabbitMQ
    """
    
    def __init__(self, rabbitmq_url: str):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        self.channel = self.connection.channel()
        
        # Declarar exchange
        self.channel.exchange_declare(
            exchange='florence_events',
            exchange_type='direct',
            durable=True
        )
    
    def publicar_exame_critico(
        self,
        paciente_id_hash: str,
        exame_id: int,
        parametro_critico: Dict[str, Any]
    ) -> str:
        """
        Publica evento de exame crítico para Oswaldo
        
        Args:
            paciente_id_hash: Hash do paciente
            exame_id: ID do exame em Florence
            parametro_critico: Dict com nome, valor, interpretação
            
        Returns:
            evento_id para rastreamento
        """
        
        evento_id = str(uuid4())
        
        # Construir payload
        evento = {
            "event_id": evento_id,
            "event_type": "florence.exame.critico",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "paciente": {
                "paciente_id_hash": paciente_id_hash
            },
            "exame": {
                "exame_id": exame_id
            },
            "parametro_critico": parametro_critico
        }
        
        # Publicar em RabbitMQ
        self.channel.basic_publish(
            exchange='florence_events',
            routing_key='florence.exame.critico',
            body=json.dumps(evento),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistente
                content_type='application/json'
            )
        )
        
        logger.info(f"Evento publicado: {evento_id}")
        
        # Registrar em banco de dados
        self._registrar_evento(evento)
        
        return evento_id
    
    def _registrar_evento(self, evento: Dict):
        """Registra evento em banco para auditoria"""
        # Implementar: INSERT em evento_integracao
        pass
    
    def fechar(self):
        self.connection.close()


# Uso em Service de Florence:
# 
# publisher = OswaldoPublisher(rabbitmq_url)
# 
# if parametro.severidade == "VERMELHO":
#     evento_id = publisher.publicar_exame_critico(
#         paciente_id_hash=paciente_hash,
#         exame_id=exame.id,
#         parametro_critico={
#             "nome": parametro.nome,
#             "valor": parametro.valor,
#             "unidade": parametro.unidade,
#             "severidade": "VERMELHO"
#         }
#     )
```

### Subscriber: Receber Resposta de Oswaldo

```python
# src/florence/integrations/oswaldo_subscriber.py

from typing import Callable
import json
import pika
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class OswaldoSubscriber:
    """
    Consome respostas de Oswaldo para Florence
    """
    
    def __init__(self, rabbitmq_url: str, db_session):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        self.channel = self.connection.channel()
        self.db = db_session
        
        # Declarar queue para receber respostas
        self.channel.queue_declare(
            queue='florence_responses',
            durable=True
        )
        
        self.channel.queue_bind(
            exchange='oswaldo_events',
            queue='florence_responses',
            routing_key='oswaldo.diagnostico.resposta'
        )
    
    def iniciar_consumo(self):
        """Inicia consumer que fica aguardando mensagens"""
        
        self.channel.basic_consume(
            queue='florence_responses',
            on_message_callback=self._processar_resposta,
            auto_ack=False
        )
        
        logger.info("Aguardando respostas de Oswaldo...")
        self.channel.start_consuming()
    
    def _processar_resposta(self, ch, method, properties, body):
        """
        Processa resposta de Oswaldo
        
        Args:
            body: JSON com diagnostico de Oswaldo
        """
        try:
            msg = json.loads(body)
            evento_id = msg.get('event_id_referencia')
            
            # Atualizar banco
            self.db.query(EventoIntegracao).filter(
                EventoIntegracao.evento_id == evento_id
            ).update({
                'status': 'PROCESSADO',
                'payload': msg,
                'timestamp_processado': datetime.utcnow()
            })
            self.db.commit()
            
            logger.info(f"Resposta processada: {evento_id}")
            
            # ACK: Só marca como lido se processou com sucesso
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Erro processando resposta: {e}")
            # NACK: Recoloca na fila para tentar novamente
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
```

### API Endpoint: Consultar Exames para Oswaldo

```python
# src/florence/routers/integracao.py

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/integracao", tags=["Integracao"])

@router.get("/oswaldo/exames-historico")
async def obter_exames_historico(
    paciente_id_hash: str,
    dias_retroativos: int = 180,
    db: Session = Depends(get_db),
    token_sistema: str = Security(verificar_token_oswaldo)
):
    """
    Retorna exames históricos para diagnóstico em Oswaldo
    
    Requer autenticação de sistema Oswaldo
    """
    
    # Validar hash
    if len(paciente_id_hash) != 64:
        raise HTTPException(status_code=400, detail="Paciente hash inválido")
    
    # Verificar data limite
    data_limite = datetime.utcnow() - timedelta(days=dias_retroativos)
    
    # Buscar exames
    exames = db.query(Exame).filter(
        Exame.paciente_id_hash == paciente_id_hash,
        Exame.data_exame >= data_limite
    ).order_by(Exame.data_exame.desc()).all()
    
    # Serializar resposta
    resposta = {
        "paciente_id_hash": paciente_id_hash,
        "exames": [
            {
                "exame_id": e.id,
                "data": e.data_exame.isoformat(),
                "tipo": e.tipo,
                "resultados": [
                    {
                        "parametro": r.parametro,
                        "valor": r.valor,
                        "unidade": r.unidade,
                        "status": r.status
                    }
                    for r in e.componentes
                ]
            }
            for e in exames
        ],
        "total_exames": len(exames),
        "periodo_dias": dias_retroativos,
        "data_consulta": datetime.utcnow().isoformat()
    }
    
    # Log de auditoria
    logger.info(f"Exames consultados para Oswaldo: {paciente_id_hash}")
    
    return resposta
```

---

## 🔌 IMPLEMENTAÇÃO OSWALDO

### Subscriber: Receber Eventos de Florence

```python
# src/oswaldo/integrations/florence_subscriber.py

class FlorenceSubscriber:
    """
    Consome eventos críticos de Florence e processa diagnósticos
    """
    
    def __init__(self, rabbitmq_url: str, db_session, http_client):
        self.rabbitmq_url = rabbitmq_url
        self.db = db_session
        self.http_client = http_client
    
    def processar_exame_critico(self, evento: Dict):
        """
        Processa evento de exame crítico de Florence
        
        1. Busca histórico exames
        2. Analisa com algoritmos
        3. Reclassifica estadiamento
        4. Envia resposta para Florence
        """
        
        paciente_id_hash = evento['paciente']['paciente_id_hash']
        
        # 1. Buscar histórico
        exames_historico = self._obter_exames_florence(paciente_id_hash)
        
        # 2. Buscar condições conhecidas
        condicoes = self.db.query(CondicaoCronica).filter(
            CondicaoCronica.paciente_id_hash == paciente_id_hash
        ).all()
        
        # 3. Processar com serviços clínicos
        service_reclassificacao = ReclassificacaoService(self.db)
        service_validacao = ValidacaoClinicaService(self.db)
        
        diagnostico = service_reclassificacao.processar_parametro_critico(
            evento['parametro_critico'],
            exames_historico,
            condicoes
        )
        
        # 4. Enviar resposta para Florence
        resposta = {
            "event_id_referencia": evento['event_id'],
            "paciente_id_hash": paciente_id_hash,
            "diagnostico": diagnostico,
            "timestamp_processamento": datetime.utcnow().isoformat()
        }
        
        publisher = FlorencePublisher(self.rabbitmq_url)
        publisher.publicar_resposta(resposta)
    
    def _obter_exames_florence(self, paciente_id_hash: str) -> Dict:
        """Busca exames via API de Florence"""
        
        url = "http://florence-api:8000/api/v1/integracao/oswaldo/exames-historico"
        
        response = self.http_client.get(
            url,
            params={
                "paciente_id_hash": paciente_id_hash,
                "dias_retroativos": 180
            },
            headers={
                "Authorization": f"Bearer {os.environ['OSWALDO_TOKEN']}"
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Erro buscando exames: {response.status_code}")
            raise IntegrationException("Não foi possível buscar exames")
        
        return response.json()


# Uso:
# subscriber = FlorenceSubscriber(rabbitmq_url, db, http_client)
# subscriber.iniciar_consumo()
```

### Publisher: Enviar Diagnóstico para Florence

```python
# src/oswaldo/integrations/florence_publisher.py

class FlorencePublisher:
    """
    Publica diagnósticos para Florence
    """
    
    def __init__(self, rabbitmq_url: str):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        self.channel = self.connection.channel()
        
        self.channel.exchange_declare(
            exchange='oswaldo_events',
            exchange_type='direct',
            durable=True
        )
    
    def publicar_resposta(self, resposta: Dict) -> bool:
        """
        Publica resposta diagnóstica para Florence
        """
        
        try:
            self.channel.basic_publish(
                exchange='oswaldo_events',
                routing_key='oswaldo.diagnostico.resposta',
                body=json.dumps(resposta),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            logger.info(f"Resposta publicada: {resposta['event_id_referencia']}")
            return True
            
        except Exception as e:
            logger.error(f"Erro publicando resposta: {e}")
            return False
```

---

## 🧪 TESTES DE INTEGRAÇÃO

### Teste 1: Fluxo Completo

```python
# tests/test_integracao_florence_oswaldo.py

@pytest.mark.integration
def test_fluxo_critico_completo(db_session, rabbitmq_url):
    """
    Testa fluxo completo:
    1. Florence detecta glicemia crítica
    2. Publica evento
    3. Oswaldo recebe e processa
    4. Oswaldo envia diagnóstico
    5. Florence recebe resposta
    """
    
    # Setup: Criar paciente com diabetes conhecida
    paciente = criar_paciente_teste(
        db_session,
        cpf="12345678901",
        condicoes=["DIABETES_TIPO_2"]
    )
    
    publisher = OswaldoPublisher(rabbitmq_url)
    
    # 1. Florence cria exame com glicemia crítica
    evento_id = publisher.publicar_exame_critico(
        paciente_id_hash=paciente.paciente_id_hash,
        exame_id=123,
        parametro_critico={
            "nome": "Glicemia",
            "valor": 400,
            "unidade": "mg/dL",
            "severidade": "VERMELHO"
        }
    )
    
    # 2. Verificar que evento foi registrado
    evento = db_session.query(EventoIntegracao).filter(
        EventoIntegracao.evento_id == evento_id
    ).first()
    
    assert evento is not None
    assert evento.status == 'PENDENTE'
    
    # 3. Processar com Oswaldo (simular consumo de evento)
    subscriber = FlorenceSubscriber(rabbitmq_url, db_session, client_http)
    resposta_oswaldo = subscriber.processar_exame_critico(evento.payload)
    
    # 4. Verificar resposta
    assert resposta_oswaldo['diagnostico']['numero'] == 'E11.65'  # CID-10 Diabetes
    assert 'DIABETES' in resposta_oswaldo['diagnostico']['condicoes_detectadas'][0]['condicao']
    
    # 5. Verificar que Florence recebeu resposta
    evento_atualizado = db_session.query(EventoIntegracao).filter(
        EventoIntegracao.evento_id == evento_id
    ).first()
    
    assert evento_atualizado.status == 'PROCESSADO'
    assert evento_atualizado.timestamp_processado is not None


@pytest.mark.integration
def test_health_check_integracao():
    """Valida que sistemas conseguem se comunicar"""
    
    # Florence health
    response = client_florence.get("/api/v1/integracao/health")
    assert response.status_code == 200
    
    # Oswaldo health
    response = client_oswaldo.get("/api/v1/integracao/health")
    assert response.status_code == 200


@pytest.mark.integration
def test_timeout_resposta():
    """Testa comportamento se Oswaldo não responder"""
    
    evento_id = publisher.publicar_exame_critico(...)
    
    # Esperar timeout padrão (ex: 5 segundos)
    time.sleep(6)
    
    evento = db_session.query(EventoIntegracao).filter(
        EventoIntegracao.evento_id == evento_id
    ).first()
    
    # Deve ter tentado reenviar
    assert evento.tentativas >= 1
    assert evento.status in ['PENDENTE', 'ERRO']
```

---

## ⚠️ TRATAMENTO DE ERROS

### Cenário 1: Oswaldo Indisponível

```
1. Florence publica evento
2. RabbitMQ armazena (durável)
3. Oswaldo fica offline
4. Se Oswaldo volta em <24h:
   - Consome eventos pendentes
   - Processa normalmente
5. Se Oswaldo fica offline >24h:
   - Admin recebe alerta
   - Eventos são movidos para dead-letter queue
   - Requerer processamento manual
```

### Cenário 2: Falha de Rede

```
1. Florence publica evento (sucesso)
2. Oswaldo processa (sucesso)
3. Oswaldo tenta responder (falha rede)
4. Admin recebe alerta após 3 tentativas
5. Florence tem timeout e trata como "aguardando resposta"
```

### Cenário 3: Validação Falha

```
1. Florence publica evento com schema inválido
2. Oswaldo rejeita (nack)
3. Evento volta para fila
4. Tentativa 2, 3, então para
5. Dead-letter queue para investigação
```

---

## 📊 MONITORAMENTO

### Métricas Prometheus

```python
from prometheus_client import Counter, Histogram

# Eventos publicados
florence_eventos_publicados = Counter(
    'florence_eventos_publicados_total',
    'Total de eventos publicados para Oswaldo',
    ['event_type']
)

# Respostas recebidas
oswaldo_respostas_recebidas = Counter(
    'oswaldo_respostas_recebidas_total',
    'Total de respostas recebidas do Oswaldo'
)

# Latência ponta-a-ponta
latencia_integracao = Histogram(
    'integracao_latencia_segundos',
    'Latência do evento até resposta',
    buckets=(1, 2, 5, 10, 30, 60)
)

# Erros
erros_integracao = Counter(
    'integracao_erros_total',
    'Total de erros de integração',
    ['tipo_erro']
)
```

---

## 🚀 CRONOGRAMA DE IMPLEMENTAÇÃO

- [ ] 13/02: Definir schema de eventos (CONCLUÍDO: este doc)
- [ ] 14/02: Implementar RabbitMQ setup
- [ ] 15/02: Implementar Publisher em Florence
- [ ] 16/02: Implementar Subscriber em Florence
- [ ] 17/02: Implementar Publisher em Oswaldo
- [ ] 18/02: Implementar Subscriber em Oswaldo
- [ ] 19/02: Testes de integração
- [ ] 20/02: Testes de failover
- [ ] 21/02: Documentação de operação
- [ ] 22/02: **Apresentação para aprovação ✅**

---

**Status**: 🟡 **PRONTO PARA IMPLEMENTAÇÃO**

*Última atualização: 12/02/2026*

