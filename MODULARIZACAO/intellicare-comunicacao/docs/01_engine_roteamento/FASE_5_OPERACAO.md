# Fase 5 - Eventos e Consolidação - Guia de Operação

## 📋 Visão Geral

Este documento descreve a operação e troubleshooting da **Fase 5 - Eventos e Consolidação** do Engine de Roteamento do módulo IntelliCare Comunicação.

**Data de Conclusão**: 2026-02-17  
**Versão**: 1.0.0  
**Status**: ✅ Completo

---

## 🎯 Funcionalidades Implementadas

### 5.1 - Redis Consumer Integration ✅

**Descrição**: Integração do consumidor Redis com o RoutingEngine para processar eventos de outros módulos.

**Componentes**:
- `comunicacao/api/app.py` - Handler `_on_alert_event()` modificado
- `comunicacao/events/redis_consumer.py` - Event ID tracking adicionado

**Fluxo**:
1. Evento Redis é recebido no stream `intellicare:alert.created`
2. Handler `_on_alert_event()` é chamado
3. `CommunicationIntentCreate` é criado a partir do payload
4. Intent é roteado via `RoutingService.send_intent()`
5. Métricas são atualizadas

**Campos Obrigatórios no Evento Redis**:
- `patient_id` - ID do paciente
- `message` - Mensagem do alerta

**Campos Opcionais**:
- `source_module` - Módulo de origem (default: "unknown")
- `severity` - Severidade (default: "medium")
- `alert_type` - Tipo de alerta (default: "clinical_alert")
- `correlation_id` - ID de correlação
- `event_id` - ID do evento Redis (adicionado automaticamente)

---

### 5.2 - Metrics and Observability ✅

**Descrição**: Métricas Prometheus e logs estruturados para monitoramento operacional.

**Componentes**:
- `comunicacao/metrics.py` - 15 métricas Prometheus
- `comunicacao/api/app.py` - Endpoint `/metrics`
- `comunicacao/routing/engine.py` - Método `send_intent()` com métricas

**Métricas Disponíveis**:

#### Counters (7)
- `comm_intent_received_total` - Total de intents recebidos
- `comm_intent_completed_total` - Total de intents completados
- `comm_intent_failed_total` - Total de intents falhados
- `comm_delivery_attempt_total` - Total de tentativas de entrega
- `comm_channel_fallback_total` - Total de fallbacks entre canais
- `comm_redis_event_total` - Total de eventos Redis processados
- `comm_template_render_total` - Total de renderizações de template

#### Histograms (3)
- `comm_routing_latency_seconds` - Latência de processamento de intent
- `comm_delivery_latency_seconds` - Latência de entrega por canal
- `comm_template_render_latency_seconds` - Latência de renderização

#### Gauges (5)
- `comm_intents_in_progress` - Número de intents em progresso
- `comm_intents_scheduled` - Número de intents agendados
- `comm_delayed_tasks_pending` - Número de delayed tasks pendentes
- `comm_redis_consumer_status` - Status do Redis consumer (1=running, 0=stopped)
- `comm_dispatcher_health` - Health status de dispatchers

**Endpoint de Métricas**:
```bash
curl http://localhost:8005/metrics
```

**Configuração Prometheus** (`prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'intellicare-comunicacao'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8005']
```

---

### 5.3 - Keycloak Auth Middleware ✅

**Descrição**: Autenticação JWT via Keycloak e RBAC nos endpoints de routing e templates.

**Componentes**:
- `comunicacao/auth.py` - Middleware de autenticação
- `comunicacao/api/routing_routes.py` - Endpoints protegidos
- `comunicacao/api/template_routes.py` - Endpoints protegidos

**Roles Definidas**:
- `comunicacao_send` - Permissão para enviar intents
- `comunicacao_read` - Permissão para ler intents e métricas
- `comunicacao_admin` - Acesso administrativo completo
- `intellicare_admin` - Acesso global (todos os módulos)

**Modo Desenvolvimento**:
- Se `intellicare-auth` não estiver instalado, usa mock user
- Mock user tem todas as roles: `["intellicare_admin", "comunicacao_admin"]`
- Não requer token Bearer

**Modo Produção**:
- Requer `intellicare-auth` instalado: `pip install -e ../intellicare-auth`
- Requer token Bearer JWT do Keycloak
- Valida token localmente usando JWKS cache

**Exemplo de Requisição Autenticada**:
```bash
# Obter token do Keycloak
TOKEN=$(curl -X POST "https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/token" \
  -d "client_id=intellicare-comunicacao" \
  -d "client_secret=<secret>" \
  -d "grant_type=client_credentials" \
  | jq -r '.access_token')

# Usar token na requisição
curl -X POST http://localhost:8005/api/v1/routing/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_module": "intellicare-oswaldo",
    "recipient_type": "patient",
    "recipient_id": "patient-123",
    "severity": "high",
    "category": "clinical_alert",
    "content_raw": "Alerta crítico"
  }'
```

---

### 5.4 - Integration Tests ✅

**Descrição**: Testes de integração end-to-end cobrindo API, Redis events, autenticação e métricas.

**Arquivo**: `tests/integration/test_fase5_integration.py`

**Cobertura**:
- ✅ Envio de intent via API com autenticação
- ✅ Listagem de intents com autenticação
- ✅ Obtenção de métricas com autenticação
- ✅ Endpoint Prometheus `/metrics`
- ✅ Listagem e obtenção de templates
- ✅ Processamento de eventos Redis
- ✅ Envio de batch de intents
- ✅ Status do scheduler
- ✅ Listagem de regras de roteamento
- ✅ Validação de métricas Prometheus
- ✅ Tratamento de erros (campos faltando, payloads inválidos)

**Executar Testes**:
```bash
# Todos os testes de integração
python -m pytest tests/integration/test_fase5_integration.py -v

# Teste específico
python -m pytest tests/integration/test_fase5_integration.py::TestPhase5Integration::test_e2e_api_send_intent_with_auth -v

# Com cobertura
python -m pytest tests/integration/test_fase5_integration.py --cov=comunicacao --cov-report=html
```

---

## 🔧 Troubleshooting

### Problema: Redis Consumer não está processando eventos

**Sintomas**:
- Métrica `comm_redis_consumer_status` = 0
- Eventos Redis não geram intents
- Logs não mostram "Evento Redis roteado com sucesso"

**Diagnóstico**:
```bash
# Verificar status do consumer
curl http://localhost:8005/api/v1/events/consumer/status

# Verificar métricas
curl http://localhost:8005/metrics | grep comm_redis_consumer_status
```

**Soluções**:
1. Verificar se Redis está acessível:
   ```bash
   redis-cli -h localhost -p 6379 ping
   ```

2. Verificar configuração no `.env`:
   ```env
   MATRIX_ENABLE_EVENT_CONSUMER=true
   REDIS_URL=redis://localhost:6379
   ```

3. Reiniciar consumer via API:
   ```bash
   curl -X POST http://localhost:8005/api/v1/events/consumer/start
   ```

---

### Problema: Métricas Prometheus não aparecem

**Sintomas**:
- Endpoint `/metrics` retorna vazio ou erro
- Prometheus não consegue scrape

**Diagnóstico**:
```bash
# Testar endpoint diretamente
curl http://localhost:8005/metrics

# Verificar logs
tail -f logs/comunicacao.log | grep metrics
```

**Soluções**:
1. Verificar se `prometheus-client` está instalado:
   ```bash
   pip install prometheus-client
   ```

2. Verificar se endpoint está registrado:
   ```bash
   curl http://localhost:8005/api/v1/info
   ```

3. Verificar configuração Prometheus (`prometheus.yml`):
   ```yaml
   scrape_configs:
     - job_name: 'intellicare-comunicacao'
       scrape_interval: 15s
       static_configs:
         - targets: ['localhost:8005']
   ```

---

### Problema: Autenticação falhando (401 Unauthorized)

**Sintomas**:
- Requisições retornam 401 Unauthorized
- Logs mostram "Token inválido"

**Diagnóstico**:
```bash
# Verificar se está em modo dev (sem intellicare-auth)
python -c "import comunicacao.auth; print(comunicacao.auth._AUTH_AVAILABLE)"

# Verificar token JWT
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq
```

**Soluções**:
1. **Modo Desenvolvimento**: Não enviar token (mock user será usado)
   ```bash
   curl -X GET http://localhost:8005/api/v1/routing/intents
   ```

2. **Modo Produção**: Obter token válido do Keycloak
   ```bash
   TOKEN=$(curl -X POST "https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/token" \
     -d "client_id=intellicare-comunicacao" \
     -d "client_secret=<secret>" \
     -d "grant_type=client_credentials" \
     | jq -r '.access_token')
   ```

3. Verificar roles do usuário:
   ```bash
   echo $TOKEN | cut -d'.' -f2 | base64 -d | jq '.realm_access.roles'
   ```

---

### Problema: Autorização falhando (403 Forbidden)

**Sintomas**:
- Requisições retornam 403 Forbidden
- Logs mostram "Role não autorizada"

**Diagnóstico**:
```bash
# Verificar roles do token
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq '.realm_access.roles'
```

**Soluções**:
1. Verificar roles requeridas no endpoint (ver tabela de endpoints acima)

2. Adicionar role ao usuário no Keycloak:
   - Acessar Keycloak Admin Console
   - Realm: `bemcuidar`
   - Users → Selecionar usuário → Role Mappings
   - Adicionar role: `comunicacao_send`, `comunicacao_read`, ou `comunicacao_admin`

3. Usar usuário com role `intellicare_admin` (acesso global)

---

## 📊 Monitoramento

### Dashboards Grafana Recomendados

#### Dashboard 1: Routing Performance
- **Painel 1**: Taxa de intents recebidos (rate)
  ```promql
  rate(comm_intent_received_total[5m])
  ```

- **Painel 2**: Taxa de sucesso vs falha
  ```promql
  rate(comm_intent_completed_total[5m]) / rate(comm_intent_received_total[5m])
  ```

- **Painel 3**: Latência p50, p95, p99
  ```promql
  histogram_quantile(0.95, rate(comm_routing_latency_seconds_bucket[5m]))
  ```

#### Dashboard 2: Channel Health
- **Painel 1**: Tentativas de entrega por canal
  ```promql
  rate(comm_delivery_attempt_total[5m])
  ```

- **Painel 2**: Taxa de fallback
  ```promql
  rate(comm_channel_fallback_total[5m])
  ```

- **Painel 3**: Health status de dispatchers
  ```promql
  comm_dispatcher_health
  ```

---

## 🚀 Próximos Passos

Após a conclusão da Fase 5, as próximas fases do Engine de Roteamento são:

- **Fase 6**: Otimizações de performance e cache
- **Fase 7**: Suporte a novos canais (Telegram, Signal)
- **Fase 8**: Machine Learning para otimização de rotas

Para mais informações, consulte:
- `PLANO_IMPLEMENTACAO.md` - Plano completo de implementação
- `ESPECIFICACAO_TECNICA.md` - Especificação técnica detalhada
- `README.md` - Visão geral do módulo
