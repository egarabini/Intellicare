# F4 — Especificação Funcional: Adaptação dos Módulos Clínicos

> **Fase:** 4 | **Prioridade:** P2  
> **Depende de:** F0 (TenantContext) — **NÃO depende de F1, F2 ou F3**  
> **Pode rodar em paralelo com:** F1, F2, F3, F5  
> **Estimativa:** 10 dias | **Módulos:** Todos os agentes clínicos + comunicação

---

## 1. Objetivo

Adaptar **todos os módulos clínicos existentes** para receberem e utilizarem o `TenantContext` de F0, garantindo que cada módulo opere isolado dentro do schema do tenant.

> [!TIP]
> Esta fase pode iniciar **imediatamente após F0**, em paralelo com F1. Um DEV pode trabalhar nisto enquanto outro cria o intellicare-admin.

---

## 2. Módulos Afetados

| Módulo | Tipo de Alteração | Complexidade |
|---|---|---|
| `intellicare-comunicacao` | Alta — routing, dispatchers, LGPD, logs | 🔴 Alta |
| `intellicare-zilda` | Média — cache, CNES queries | 🟡 Média |
| `intellicare-oswaldo` | Média — perfis DRC, classificação | 🟡 Média |
| `intellicare-florence` | Média — análise laboratorial | 🟡 Média |
| `intellicare-geralda` | Média — planos de cuidado | 🟡 Média |
| `intellicare-donabedian` | Baixa — indicadores de qualidade | 🟢 Baixa |
| `intellicare-grahame` | Média — FHIR resources | 🟡 Média |
| `intellicare-wanda` | Baixa — assistente IA | 🟢 Baixa |

---

## 3. Padrão de Alteração (Aplicar a TODOS)

### RF-F4-001: Injetar TenantContext em cada módulo

**Para cada módulo, o DEV deve:**

1. Importar `get_tenant_context` de `intellicare-auth`
2. Adicionar `ctx: TenantContext = Depends(get_tenant_context)` em TODOS os endpoints
3. Passar `ctx` para os services
4. Services usam `TenantAwareSessionFactory.get_session(ctx)` ao invés de session direta
5. Redis (se usado) → usar `TenantRedisClient` com o `ctx`

### RF-F4-002: Isolamento de Dados

**Regras por módulo:**

| Módulo | Dados que precisam de isolamento |
|---|---|
| `comunicacao` | `ExternalMessageLog`, `CommunicationIntent`, `ChannelConfig`, `LGPDConsent`, `DeliveryResult` |
| `zilda` | Cache CNES por estabelecimento, resultados de busca |
| `oswaldo` | Classificações DRC, perfis de pacientes |
| `florence` | Resultados de análise laboratorial |
| `geralda` | Planos de cuidado, alertas |
| `donabedian` | Avaliações de qualidade |
| `grahame` | Resources FHIR (Patient, Observation, etc.) |
| `wanda` | Histórico de conversação IA |

### RF-F4-003: Configuração por Tenant

**Regras:**
1. Cada módulo deve consultar `tenant_{id}.settings` para configs sobrescritas
2. Se não houver config por tenant, usar config global (env var)
3. Exemplo: Hospital A usa SMTPConfig diferente de Hospital B

### RF-F4-004: Verificação de Módulo Ativo

**Regras:**
1. Antes de processar, cada módulo verifica se está ativo para o tenant
2. Se desativado → HTTP 403 "Módulo não disponível para sua organização"
3. Verificação via cache (Redis) para não bater no banco a cada request

---

## 4. Detalhamento: `intellicare-comunicacao` (Mais Complexo)

### Alterações específicas:

1. **RoutingEngine** — Regras de roteamento por tenant (tenant A prioriza SMS, tenant B prioriza Email)
2. **DispatcherManager** — Configurações de provider por tenant (Twilio para A, Zenvia para B)
3. **LGPD** — Consentimentos isolados por tenant/paciente
4. **Templates** — Templates de mensagem por tenant
5. **Redis Streams** — Eventos prefixados com `tenant:{id}:intellicare:*`

### Alterações específicas por dispatcher:

| Dispatcher | Alteração |
|---|---|
| `EmailDispatcher` | SMTPConfig do tenant (settings) |
| `SMSDispatcher` | Provider config do tenant (Twilio/Zenvia/SNS keys) |
| `WhatsAppDispatcher` | Número do WhatsApp Business do tenant |
| `PushDispatcher` | VAPID keys do tenant |
| `JitsiDispatcher` | Domain/App ID do tenant |

---

## 5. Cenários de Teste

| # | Cenário | Saída Esperada |
|---|---|---|
| CT-01 | Tenant A classifica DRC (Oswaldo) | Resultado salvo no schema do tenant A |
| CT-02 | Tenant B busca CNES (Zilda) | Cache isolado, não vê dados de A |
| CT-03 | Tenant A envia SMS via Twilio | Config Twilio do tenant A usada |
| CT-04 | Tenant B envia SMS via Zenvia | Config Zenvia do tenant B usada |
| CT-05 | Módulo desativado para tenant | HTTP 403 |
| CT-06 | Backward-compatibility single-tenant | Todos módulos funcionam com `tenant_id=default` |
