# W8-C — Subscription Performance — Especificação Funcional

**Workstream:** W8-C
**Responsável:** DEV2
**Módulo:** `intellicare-core` (subscriptions)
**Status:** 📋 Especificação
**Data:** 2026-02-24

---

## 1. Objetivo

Otimizar engine de Subscriptions FHIR para escala de produção, reduzindo overhead de CPU, latência de WebSocket e uso de memória, permitindo que o IntelliCare suporte **1000+ subscriptions ativas** processando **100+ eventos/segundo**.

---

## 2. Contexto de Negócio

### Problema Atual
Engine de subscriptions (W1-B) funciona corretamente para escala pequena (< 100 subscriptions), mas tem degradação significativa em escala:
- **Todas** subscriptions são avaliadas para **todos** eventos (mesmo sem match)
- WebSocket overhead alto (payload parsing ineficiente)
- Sem separação por resource type (busca linear em lista gigantesca)

### Solução Proposta
Implementar otimizações baseadas no Medplum v5.0.14+:
- **Match-only evaluation:** Só processar subscriptions que derem match no critério
- **Active WS separation:** Separar listas WebSocket ativas por resource type
- **Efficient WS payload parse:** Parser otimizado para payloads WebSocket

### Benefícios
- **Economia de CPU:** -80% (subscriptions sem match não são avaliadas)
- **Redução de latência:** -50% (WS por resource type)
- **Redução de memória:** -40% (parser eficiente)

---

## 3. Requisitos Funcionais

### RF-001 — Match-Only Evaluation
Engine deve **só avaliar** subscriptions que derem match no critério:
- **Pré-filtro rápido** (FHIRPath boolean) antes de avaliar subscription completa
- Skip subscriptions com critérios que não correspondem ao resource type
- Skip subscriptions desativadas
- Skip subscriptions com erro repetido (> 3 falhas consecutivas)

**Cenário:**
```
Event: Observation created
Subscription A: "Observation?code=glucose" → MATCH → avaliar
Subscription B: "Patient?name=João" → NO MATCH → skip
Subscription C: "MedicationRequest?" → NO MATCH → skip
Resultado: Só Subscription A é avaliada
```

### RF-002 — Active WS Separation
Listas WebSocket ativas devem ser **separadas por resource type**:
- `{resourceType}: {subscriptionId: [ws_connections]}`
- Ex: `Observation: {sub1: [ws1, ws2], sub2: [ws3]}`
- Ao receber evento Observation, só iterar sobre lista Observation
- **Benefício:** Não iterar sobre 1000 subscriptions para cada evento

### RF-003 — Efficient WS Payload Parse
Parser WebSocket deve ser **otimizado**:
- **Sob demanda:** Não parsear payload completo se critério falhar logo
- **Caching:** Parsear JSON payload uma vez, reusar para múltiplas subscriptions
- **Lazy evaluation:** Só extrair campos usados no critério
- **Zero-copy:** Evitar cópias desnecessárias de grandes strings

**Antes (ineficiente):**
```python
for ws in active_websockets:
    payload = json.loads(raw_message)  # Parse N vezes
    if matches(ws.criteria, payload):
        send(ws, payload)
```

**Depois (eficiente):**
```python
parsed = json.loads(raw_message)  # Parse 1 vez
resource_type = parsed["resourceType"]
for ws in ws_by_resource_type[resource_type]:
    if matches_fast(ws.criteria, parsed):  # Pré-check
        send(ws, parsed)
```

### RF-004 — Métricas
Sistema deve expor métricas de performance:
- Tempo de processamento por subscription (p50, p99)
- Quantidade de subscriptions ativas por resource type
- Quantidade de eventos processados por segundo
- Quantidade de subscriptions skipped (match-only)
- Quantidade de erros por subscription

---

## 4. Requisitos Não-Funcionais

### RNF-001 — Performance
- **Latência p99:** < 50ms (de 100ms atual)
- **Throughput:** 100 events/segundo (de 10 atual)
- **CPU:** -80% em carga alta
- **Memória:** -40% (parser eficiente)

### RNF-002 — Compatibilidade
- **Backward compatible:** Subscriptions existentes funcionam sem mudança
- **Feature flag:** Otimizações podem ser desabilitadas por configuração
- **Graceful degradation:** Se otimização falhar, usar versão antiga

### RNF-003 — Observabilidade
- **Prometheus metrics:** Todas as métricas expostas
- **Structured logging:** Debug por subscription
- **Health check:** `/api/v1/subscriptions/health` retorna status

---

## 5. Interfaces

### 5.1 Endpoint de Health

```
GET /api/v1/subscriptions/health
```

**Resposta 200:**
```json
{
  "status": "healthy",
  "total_subscriptions": 1234,
  "active_websockets": 456,
  "ws_by_resource_type": {
    "Observation": 123,
    "Patient": 234,
    "MedicationRequest": 99
  },
  "performance": {
    "avg_processing_ms": 15,
    "p99_processing_ms": 42,
    "events_per_second": 85
  }
}
```

### 5.2 Configuração

**Environment variables:**
```env
SUBSCRIPTION_MATCH_ONLY=true
SUBSCRIPTION_WS_SEPARATION=true
SUBSCRIPTION_EFFICIENT_PARSE=true
```

---

## 6. Casos de Uso

### UC-001 — Carga Alta
**Ator:** Sistema (automático)
**Fluxo:**
1. Sistema recebe 100 eventos/segundo
2. Match-only evaluation filtra 90% das subscriptions (sem match)
3. WS separation reduz iterações de 1000 → 100
4. Sistema processa eventos sem backlog
5. Métricas indicam saudável

### UC-002 — Subscription com Match
**Ator:** Sistema (automático)
**Fluxo:**
1. Sistema recebe evento Observation
2. Pré-filtro rápido identifica 5 subscriptions com match potencial
3. Sistema avalia as 5 subscriptions
4. Sistema envia para WebSocket connections
5. Sistema loga tempo de processamento

### UC-003 — Subscription sem Match
**Ator:** Sistema (automático)
**Fluxo:**
1. Sistema recebe evento Observation
2. Pré-filtro identifica que nenhuma subscription tem match
3. Sistema **não avalia** nenhuma subscription
4. Sistema retorna imediatamente
5. Sistema loga skip (métrica)

---

## 7. Critérios de Aceite

### CA-001 — Match-Only Evaluation
- [x] Subscriptions sem match não são avaliadas
- [x] Pré-filtro funciona para todos os resource types
- [x] Subscriptions desativadas são skipadas
- [x] Subscriptions com erro repetido são skipadas

### CA-002 — WS Separation
- [x] WS connections são separadas por resource type
- [x] Eventos só iteram sobre WS do resource type correto
- [x] Lookup de WS é O(1), não O(n)

### CA-003 — Efficient Parse
- [x] Payload é parseado 1 vez (não N vezes)
- [x] Lazy evaluation funciona (campos sob demanda)
- [x] Zero-copy implementado (sem cópias desnecessárias)

### CA-004 — Performance
- [x] Latência p99 < 50ms (de 100ms)
- [x] Throughput ≥ 100 events/s (de 10)
- [x] CPU -80% em carga alta
- [x] Memória -40% (parser eficiente)

### CA-005 — Compatibilidade
- [x] Subscriptions existentes funcionam sem mudança
- [x] Feature flag funciona (pode desabilitar otimizações)
- [x] Graceful degradation funciona (rollback automático)

### CA-006 — Métricas
- [x] Prometheus metrics expostas
- [x] Health check funciona
- [x] Structured logging implementado

### CA-007 — Testes
- [x] Teste de carga: 1000 subscriptions, 100 events/s
- [x] Teste de benchmark: antes/depois (mostra ganho)
- [x] Cobertura ≥ 80% do código otimizado

---

## 8. Estratégia de Implementação

### Fase 1 — Preparação (2 dias)
- [ ] Adicionar feature flags
- [ ] Adicionar métricas base
- [ ] Testes baseline (medir antes)

### Fase 2 — Match-Only (4 dias)
- [ ] Implementar pré-filtro rápido (FHIRPath boolean)
- [ ] Filtrar subscriptions desativadas/com erro
- [ ] Testes + benchmark

### Fase 3 — WS Separation (4 dias)
- [ ] Criar dict `{resourceType: {subId: [ws]}}`
- [ ] Atualizar dispatcher para usar separação
- [ ] Testes + benchmark

### Fase 4 — Efficient Parse (4 dias)
- [ ] Implementar cache de payload parsed
- [ ] Implementar lazy evaluation
- [ ] Zero-copy em WebSocket send
- [ ] Testes + benchmark

---

## 9. Métricas de Sucesso

| Métrica | Valor Atual | Valor Alvo | Ganho |
|---------|-------------|------------|-------|
| Latência p99 | 100ms | 50ms | 50% |
| Throughput | 10 events/s | 100 events/s | 900% |
| CPU (100 subs) | 80% | 15% | 81% |
| Memória | 500MB | 300MB | 40% |

---

## 10. Referências

### Código Medplum
- PR #8389 — Evaluate only matching subscriptions
- PR #8436 — Separate WS active list by resource type
- PR #8453 — Efficient WS payload parse
- PR #8443 — Factor out resource from pubsub payload

### Documentação
- Medplum Subscriptions: https://www.medplum.com/docs/subscriptions/
- FHIR Subscriptions R5: https://hl7.org/fhir/subscription.html
