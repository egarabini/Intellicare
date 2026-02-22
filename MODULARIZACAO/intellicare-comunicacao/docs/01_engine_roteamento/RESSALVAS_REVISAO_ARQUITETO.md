# Domínio 1 — Engine de Roteamento Multi-Canal
## Ressalvas da Revisão do Arquiteto

> ⚠️ **ATUALIZAÇÃO (2026-02-16)**: A decisão de usar **Matrix como fallback universal** (itens R3/D3
> neste documento) foi **supersedida**. Matrix/Synapse foi descontinuado. O fallback para alertas
> CRITICAL/HIGH é agora **email + push notification**. Rocket.Chat é o canal primário de
> comunicação interna. Ver `INDICE_ESPECIFICACOES_FUNCIONAIS.md` para estado atualizado.

**Revisor**: Arquiteto de Comunicação (Copilot)
**Data**: 2026-02-15
**Documentos revisados**:
- `ESPECIFICACAO_TECNICA.md` (DEV2 — 263 linhas)
- `PLANO_IMPLEMENTACAO.md` (DEV2 — 171 linhas)
- `ESPECIFICACAO_FUNCIONAL.md` (Arquiteto — 1395 linhas, referência)

**Veredicto geral**: APROVADO COM RESSALVAS  
O trabalho do DEV2 demonstra boa compreensão do escopo, arquitetura coerente e plano de execução realista. Porém, há **8 itens que precisam de ajuste** antes ou durante a implementação, sendo 3 bloqueantes e 5 recomendados.

---

## PARTE A — RESSALVAS BLOQUEANTES (resolver antes de codificar)

### R1. Interface do Dispatcher incompleta (CRÍTICA)

**Problema**: A especificação técnica define o contrato `ChannelDispatcher(Protocol)` com apenas 2 membros (`channel: str` e `send()`). A funcional define `IChannelDispatcher(ABC)` com **7 membros obrigatórios**.

**Métodos ausentes na tech spec**:
```python
# Faltam no Protocol da tech spec:
async def is_available(self) -> bool
async def check_delivery_status(self, channel_message_id: str) -> DeliveryStatus
async def get_health(self) -> ChannelHealth
async def supports_read_receipt(self) -> bool
async def supports_rich_content(self) -> bool
```

**Impacto**: Sem `is_available()` e `get_health()`, o `DispatcherManager` não consegue fazer health check de canais (endpoint `GET /api/v1/channels/{channel}/health`). Sem `check_delivery_status()`, o `FallbackMonitor` não tem como verificar se a mensagem foi entregue/lida no canal externo. Os 5 domínios dependentes (D2, D3, D4) precisam desse contrato completo para implementar seus dispatchers.

**Ação requerida**: Atualizar o Protocol para incluir todos os 7 membros. A escolha de `Protocol` em vez de `ABC` é aceitável (até preferível em Python moderno), mas o contrato deve ser completo. Incluir também os modelos `ResolvedRecipient`, `RenderedContent`, `ChannelHealth` conforme a funcional.

**Adicionalmente, padronizar o `DispatchResult`**:
- Tech spec usa `ok: bool` → funcional usa `success: bool` → **adotar `success`** para consistência com os demais domínios
- Funcional inclui `timestamp: datetime` → **incluir** na definição

---

### R2. Hook LGPD não materializado (CRÍTICA)

**Problema**: A funcional define o passo 3 do pipeline como "CONSULTA DE PREFERÊNCIAS (LGPD)" e especifica que o `RoutingEngine` deve chamar o `LGPDComplianceService.can_send()` (D6, EF-COM-050) **antes** de despachar. A tech spec menciona LGPD apenas superficialmente na seção 7.3 ("Aplicar exclusão de canais e preferências").

**Impacto**: Se D1 não definir o ponto de extensão LGPD agora, será necessário refatorar o pipeline core quando D6 for implementado.

**Ação requerida**: Criar uma interface/Protocol `LGPDComplianceGateway`:

```python
class LGPDComplianceGateway(Protocol):
    async def can_send(
        self,
        patient_id: str,
        channel: str,
        intent_type: str,
        severity: str
    ) -> LGPDDecision: ...

@dataclass
class LGPDDecision:
    allowed: bool
    legal_basis: Optional[str]
    reason: str
    override_applied: bool = False
    defer_until: Optional[datetime] = None
```

Na implementação de D1, fornecer um `DefaultLGPDGateway` que:
- Para `severity == CRITICAL`: retorna `allowed=True` sempre
- Para `severity == HIGH` + alerta clínico: retorna `allowed=True`
- Para demais: verifica `excluded_channels` do intent e retorna `allowed=True` (sem tabela de preferências — D6 substituirá)

Quando D6 for implementado, ele fornecerá a implementação real e substituirá o default via injeção de dependência.

**O pipeline no `engine.py` deve ter o ponto de chamada explícito entre o passo 2 (resolução) e o passo 4 (seleção de regra).**

---

### R3. Endpoints de canais ausentes

**Problema**: A funcional define 3 endpoints de canais que não aparecem na tech spec:

```yaml
GET  /api/v1/channels                    # Lista canais registrados
GET  /api/v1/channels/{channel}/health   # Saúde detalhada
POST /api/v1/channels/{channel}/test     # Mensagem de teste (admin)
```

**Impacto**: São essenciais para operação (verificar quais canais estão ativos, diagnosticar problemas).

**Ação requerida**: Adicionar `api/channel_routes.py` ao escopo da Fase 4 ou 5. Depende diretamente de R1 (`is_available()`, `get_health()`).

---

## PARTE B — RESSALVAS RECOMENDADAS (resolver durante implementação)

### R4. Conceito de Timeline ausente

**Problema**: A funcional especifica que o endpoint `GET /api/v1/routing/intents/{intent_id}` retorna `timeline: List[TimelineEvent]` — uma lista cronológica de tudo que aconteceu com a intent (criada, regra aplicada, canal 1 enviado, canal 1 falhou, fallback para canal 2, entregue, etc.).

A tech spec menciona "trilha de evento" superficialmente na seção de transições de estado, mas não materializa o conceito.

**Recomendação**: Implementar `TimelineEvent` como uma lista de registros imutáveis (append-only) no banco, associados à intent:

```python
class TimelineEvent(BaseModel):
    timestamp: datetime
    event_type: str         # "created", "rule_matched", "dispatched", "sent", "delivered", "failed", "escalated"
    channel: Optional[str]
    details: Optional[Dict] # Metadados variáveis
```

Pode ser uma coluna JSONB na tabela `communication_intents` ou uma tabela separada `intent_timeline`. Recomendo coluna JSONB por simplicidade.

---

### R5. Endpoint de métricas do router

**Problema**: A funcional define `GET /api/v1/routing/metrics` com dados agregados (total_intents_today, by_status, by_severity, by_channel, avg_latency, fallback_rate, escalation_count). Não aparece na tech spec.

**Recomendação**: Incluir na Fase 5 (observabilidade). É independente do Prometheus — é uma API REST que consulta o banco para dashboards internos e outros módulos.

---

### R6. RecipientResolver precisa de mais detalhe

**Problema**: A tech spec menciona "Resolve `recipient_id` em contatos e canais possíveis" mas não detalha as fontes:
- `PROFESSIONAL` → Keycloak admin API → email, roles, unidade
- `PATIENT` → Banco local / API de cadastro → telefone, email, preferências
- `TEAM` → Expandir para lista de profissionais
- `BROADCAST` → Expandir `recipient_ids`

**Recomendação**: Na Fase 2, implementar `RecipientResolver` com adaptadores plugáveis:

```python
class RecipientSource(Protocol):
    async def resolve(self, recipient_id: str, recipient_type: str) -> ResolvedRecipient: ...

class KeycloakRecipientSource:  # Profissionais
class DatabaseRecipientSource:  # Pacientes
class TeamExpansionSource:      # Equipes → lista de profissionais
```

Isso permite que cada fonte seja testada isoladamente e substituída.

---

### R7. Idempotência precisa de mecanismo explícito

**Problema**: A tech spec menciona idempotência em riscos ("idempotência por `intent_id`/`source_event_id`"), mas não descreve o mecanismo.

**Recomendação**: Implementar dedup em duas camadas:
1. **Nível API**: `UNIQUE(source_module, source_event_id)` no banco — se o mesmo evento tentar gerar dois intents, o segundo retorna o intent_id do primeiro (idempotent)
2. **Nível Consumer Redis**: manter set de `event_id` processados em Redis com TTL de 24h

---

### R8. Templates seed no Plano de Implementação

**Problema**: O plano menciona "4 templates seed mínimos" na Fase 4, o que está correto. Porém, a funcional exige que cada template tenha **variantes para 5+ canais** (RC, push, email, WhatsApp, SMS) e **sample_params** para preview.

**Recomendação**: Garantir que os 4 templates seed incluam:
- Todas as 5 variantes de canal (mesmo que WhatsApp/SMS sejam placeholder)
- `params_schema` com JSON Schema validável
- `sample_params` funcionais para o endpoint de preview
- Carregar via migration/fixture Alembic (não hardcoded)

---

## PARTE C — DECISÕES ABERTAS (resposta do Arquiteto)

O DEV2 listou 3 decisões abertas na seção 11 da tech spec. Minhas respostas:

### D1. Estratégia de filas para agendamentos/timeouts

**Decisão**: **Redis delayed worker** (não APScheduler)

**Justificativa**:
- O IntelliCare já usa Redis Streams extensivamente (D5 — MultiEventConsumer)
- APScheduler é in-process e morre com o serviço, perdendo agendamentos
- Redis ZADD com score=timestamp + worker poll é mais resiliente e escalável
- Usar `ZADD scheduled_intents <timestamp> <intent_id>` + worker a cada 10s faz `ZRANGEBYSCORE` e processa

```python
# Padrão recomendado:
await redis.zadd("comm:scheduled_intents", {intent_id: send_timestamp})
# Worker poll:
due_intents = await redis.zrangebyscore("comm:scheduled_intents", 0, now_ts)
```

### D2. Fonte primária de preferências LGPD no primeiro ciclo

**Decisão**: **Tabela local + webhook de sync** (conforme D6)

**Justificativa**:
- D6 (EF-COM-050) cria a tabela `communication_preferences` no schema `comunicacao_operacional`
- D1 pode consultar diretamente essa tabela via `LGPDComplianceGateway`
- No primeiro ciclo (antes de D6 ser implementado), usar o `DefaultLGPDGateway` descrito em R2
- Consulta síncrona a serviço externo adiciona latência e ponto de falha ao caminho crítico

### D3. Canal primário para profissionais no modo degradado

**Decisão**: **Matrix como fallback universal** (com ressalva)

**Justificativa**:
- Matrix (Synapse) já está operacional no servidor
- Se Rocket.Chat cair, Matrix pode receber mensagens CRITICAL e HIGH
- LOW/MEDIUM podem aguardar RC voltar (não justificam fallback para Matrix)
- Implementar como regra de roteamento especial (não hardcoded):

```yaml
# Regra de modo degradado (priority: 1, mais alta)
id: rule_degraded_rc_fallback
conditions:
  severity: [CRITICAL, HIGH]
  # Ativada manualmente ou por health check do RC
action:
  channels:
    - channel: matrix
      timeout_seconds: 300
    - channel: push
      concurrent: true
```

**Ressalva**: Esta regra deve ser desativável (active=false por default) e ativada por operação manual ou automaticamente quando `RocketChatDispatcher.is_available() == false` por > 60s.

---

## RESUMO DE AÇÕES

| # | Item | Tipo | Quando | Impacto |
|---|------|------|--------|---------|
| R1 | Completar Protocol do Dispatcher (7 métodos) | BLOQUEANTE | Antes de codificar | D2, D3, D4 dependem |
| R2 | Criar LGPDComplianceGateway + DefaultLGPDGateway | BLOQUEANTE | Antes de codificar | Pipeline core |
| R3 | Adicionar endpoints de canais à tech spec | BLOQUEANTE | Antes de codificar | Operação |
| R4 | Implementar TimelineEvent | Recomendado | Fase 2 | UX/rastreabilidade |
| R5 | Adicionar endpoint /routing/metrics | Recomendado | Fase 5 | Dashboards |
| R6 | RecipientResolver com adaptadores plugáveis | Recomendado | Fase 2 | Testabilidade |
| R7 | Mecanismo de idempotência explícito | Recomendado | Fase 1-2 | Confiabilidade |
| R8 | Templates seed com 5 variantes + schema | Recomendado | Fase 4 | Completude |
| D1 | Scheduler: Redis delayed worker | Decisão | Fase 3 | Resiliência |
| D2 | LGPD: tabela local + DefaultGateway | Decisão | Fase 2 | Desacoplamento |
| D3 | Degradado: Matrix fallback (regra desativável) | Decisão | Fase 5 | Disponibilidade |

---

## INSTRUÇÃO FINAL

DEV2: **incorpore R1, R2 e R3 à especificação técnica** e confirme que o plano de implementação acomoda os itens R4–R8 nas fases indicadas. Após esse ajuste, pode iniciar a implementação.

Para as decisões D1/D2/D3 — estão fechadas e devem ser seguidas conforme descrito acima.

**O escopo funcional (EF-COM-001/002/003), a sequência de fases e as estimativas estão aprovados.**
