# EF-COM-034 — Integração WAHA como Ferramenta Auxiliar

> **Domínio:** D4 — Notificações e Canais Externos  
> **Prioridade:** MÉDIA  
> **Depende de:** D1 (Engine Roteamento), D4.3 (WhatsApp Meta API)  
> **Estimativa:** 5–7 dias  
> **Classificação:** Ferramenta auxiliar — homologação, dev e fallback

---

## 1. Objetivo

Integrar o **WAHA** (WhatsApp HTTP API, open-source) ao módulo intellicare-comunicacao como **backend alternativo** para o canal WhatsApp, permitindo:

1. **Homologação e desenvolvimento** sem custo por mensagem (Meta API cobra)
2. **Fallback opcional** quando a Meta API estiver indisponível
3. **Validação de fluxos** da agente Geralda com pacientes via WhatsApp

> [!IMPORTANT]
> A **Meta WhatsApp Business API** permanece como **canal principal em produção**. O WAHA é **complementar**, não substituto.

---

## 2. Contexto e Justificativa

### 2.1 Problema

- Meta API exige verificação de negócio e cobra por mensagem
- Em homologação/dev, o custo e a burocracia atrasam testes
- Falhas na Meta API deixam o canal WhatsApp indisponível sem alternativa

### 2.2 Solução

- WAHA usa protocolo WhatsApp Web (self-hosted, sem custo por mensagem)
- Permite testes completos antes de homologar com a Meta
- Pode ser usado como fallback configurável em produção

### 2.3 Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Violação ToS WhatsApp | Usar apenas em homologação/dev; em produção, apenas como fallback explícito |
| Bloqueio de conta | Seguir guia "How to Avoid Blocking"; número dedicado; evitar spam |
| LGPD | Mesmo gateway de conformidade e auditoria do canal Meta |

---

## 3. Personas e Casos de Uso

### 3.1 Personas

| Persona | Descrição | Uso do WAHA |
|---------|-----------|-------------|
| **Desenvolvedor** | Implementa integrações | Testes locais/homologação sem Meta API |
| **QA** | Valida fluxos | Homologação de cenários Geralda ↔ paciente |
| **Operador** | Configura produção | Fallback quando Meta API falha |
| **Geralda (agente)** | Cuidado ao paciente | Envio de lembretes, orientações via WhatsApp |

### 3.2 Casos de Uso

| ID | Caso de Uso | Ator | Pré-condição | Fluxo Principal | Pós-condição |
|----|--------------|------|--------------|----------------|--------------|
| CU-034-01 | Enviar mensagem via WAHA | Sistema (Geralda) | WAHA configurado e sessão ativa | 1. RoutingEngine escolhe canal whatsapp<br>2. Backend=waha selecionado<br>3. WAHAClient envia POST /api/sendText<br>4. Log em ExternalMessageLog | Mensagem entregue; log auditável |
| CU-034-02 | Fallback Meta → WAHA | Sistema | Meta API falhou; WAHA habilitado | 1. Meta retorna erro<br>2. Dispatcher tenta WAHA<br>3. WAHA envia mensagem<br>4. Log com provider=waha | Mensagem entregue via WAHA |
| CU-034-03 | Health check WAHA | Operador | WAHA rodando | GET /api/sessions/default → status | Status disponível no dashboard |
| CU-034-04 | Configurar backend WhatsApp | Operador | Acesso admin | WHATSAPP_BACKEND=meta\|waha\|auto | Backend ativo conforme config |

---

## 4. Requisitos Funcionais

### RF-034-001: Seleção de Backend WhatsApp

**Descrição:** O sistema deve permitir escolher o backend WhatsApp via variável de ambiente.

**Regras:**
1. `WHATSAPP_BACKEND=meta` — usa apenas Meta API (padrão produção)
2. `WHATSAPP_BACKEND=waha` — usa apenas WAHA (homologação/dev)
3. `WHATSAPP_BACKEND=auto` — Meta primeiro; se falhar, tenta WAHA (fallback)
4. Se `waha` ou `auto`, exige `WAHA_BASE_URL` e `WAHA_SESSION` configurados

**Critérios de aceite:**
- [ ] Variável WHATSAPP_BACKEND lida na inicialização
- [ ] Valor inválido gera log de warning e usa `meta`
- [ ] Em `auto`, fallback só ocorre após falha explícita da Meta

---

### RF-034-002: Cliente WAHA (WAHAClient)

**Descrição:** Cliente HTTP para comunicação com a API WAHA.

**Regras:**
1. Base URL configurável (`WAHA_BASE_URL`, ex: `http://waha:3000`)
2. Sessão configurável (`WAHA_SESSION`, default: `default`)
3. API Key opcional (`WAHA_API_KEY`) para autenticação
4. Método `send_text(to, text)` → POST /api/sendText
5. Formato `chatId`: número sem `+` + `@c.us` (ex: `5511999999999@c.us`)
6. Para números BR: usar `chatId` do endpoint checkNumberStatus se necessário (números antigos)
7. Timeout configurável (default: 30s)
8. Retorno: `message_id` ou exceção com detalhes do erro

**Critérios de aceite:**
- [ ] WAHAClient implementado em `comunicacao/channels/whatsapp/waha_client.py`
- [ ] Suporta envio de texto simples
- [ ] Trata erros HTTP (4xx, 5xx) com mensagens claras
- [ ] Log de cada envio (to, message_id ou erro)

---

### RF-034-003: WhatsAppDispatcher com Backend Pluggável

**Descrição:** O WhatsAppDispatcher deve suportar backends Meta e WAHA.

**Regras:**
1. WhatsAppDispatcher recebe `backend: Literal["meta", "waha", "auto"]`
2. Em `meta`: usa WhatsAppClient (Meta) — comportamento atual
3. Em `waha`: usa WAHAClient — ignora templates; envia `content.body` como texto
4. Em `auto`: tenta Meta; em falha, tenta WAHA
5. Metadata do log deve incluir `provider: "meta"` ou `provider: "waha"`
6. Para WAHA: não exige `template_name`; usa texto livre
7. Session 24h: em WAHA não se aplica (protocolo diferente); registrar log mesmo assim para auditoria

**Critérios de aceite:**
- [ ] Dispatcher escolhe backend conforme config
- [ ] Em modo `waha`, envia texto sem template
- [ ] Em modo `auto`, fallback funciona após falha Meta
- [ ] ExternalMessageLog registra provider correto

---

### RF-034-004: Configuração WAHA

**Descrição:** Variáveis de ambiente para WAHA.

**Regras:**
1. `WAHA_BASE_URL` — URL base (ex: `http://localhost:3000`)
2. `WAHA_SESSION` — Nome da sessão (default: `default`)
3. `WAHA_API_KEY` — Opcional; header `X-Api-Key`
4. `WAHA_TIMEOUT_SECONDS` — Timeout HTTP (default: 30)
5. Se `WHATSAPP_BACKEND=waha|auto` e `WAHA_BASE_URL` vazio → log warning e desabilita WAHA

**Critérios de aceite:**
- [ ] WhatsAppConfig estendido ou WAHAConfig criado
- [ ] Validação na inicialização
- [ ] Documentação em README e GUIA_CONFIGURACAO

---

### RF-034-005: Health Check WAHA

**Descrição:** Verificar se WAHA está disponível e sessão ativa.

**Regras:**
1. Endpoint WAHA: `GET /api/sessions/{session}` ou `GET /api/status`
2. Se 200 e session `STARTED` → available=True
3. Se timeout ou 5xx → available=False
4. Incluir no `ChannelHealth` do canal whatsapp: `details.backend`, `details.waha_available` (quando auto)

**Critérios de aceite:**
- [ ] health_check do dispatcher consulta WAHA quando backend=waha ou auto
- [ ] Resposta inclui status da sessão

---

### RF-034-006: Recebimento de Mensagens (Webhook WAHA)

**Descrição:** (Opcional Fase 1) Processar mensagens recebidas via webhook WAHA.

**Regras:**
1. WAHA envia eventos via webhook configurável
2. Endpoint: `POST /api/v1/whatsapp/waha/webhook`
3. Processar evento `message` → extrair texto, remetente, message_id
4. Emitir evento Redis `whatsapp.message.received` para pipeline Geralda
5. Registrar em ExternalMessageLog (direction=inbound)

**Critérios de aceite:**
- [ ] Webhook handler implementado
- [ ] Evento Redis emitido
- [ ] Log de auditoria

**Nota:** Pode ser deixado para fase 2 se prioridade for apenas envio.

---

### RF-034-007: Conformidade LGPD e Auditoria

**Descrição:** WAHA deve respeitar o mesmo gateway LGPD e auditoria do canal Meta.

**Regras:**
1. Todas as mensagens enviadas via WAHA passam por LGPDComplianceGateway
2. ExternalMessageLog com `provider_message_id`, `provider: "waha"`
3. Nenhum dado sensível em logs (apenas IDs, timestamps)
4. Opt-in do paciente verificado antes do envio

**Critérios de aceite:**
- [ ] Fluxo de envio passa por compliance
- [ ] Logs auditáveis
- [ ] Sem vazamento de conteúdo em logs

---

## 5. Requisitos Não Funcionais

### RNF-034-01: Performance

- Latência de envio WAHA: < 5s (P95)
- Timeout configurável; default 30s

### RNF-034-02: Segurança

- WAHA_API_KEY em variável de ambiente, nunca em código
- Webhook WAHA (se implementado) validar origem (IP ou token)

### RNF-034-03: Observabilidade

- Métrica: `communication_messages_sent_total{channel="whatsapp", provider="waha"}`
- Log estruturado: provider, message_id, intent_id

---

## 6. Cenários de Teste

| # | Cenário | Entrada | Saída Esperada |
|---|---------|---------|----------------|
| 1 | Envio via WAHA (backend=waha) | intent whatsapp, WAHA ativo | Mensagem entregue; provider=waha no log |
| 2 | Envio via Meta (backend=meta) | intent whatsapp, Meta configurada | Mensagem entregue; provider=meta (comportamento atual) |
| 3 | Fallback Meta→WAHA (backend=auto) | Meta falha (timeout), WAHA ativo | Mensagem entregue via WAHA |
| 4 | WAHA indisponível | WAHA down, backend=waha | DispatchResult success=False, erro claro |
| 5 | Health check WAHA | GET sessions | ChannelHealth available conforme WAHA |
| 6 | Número BR antigo | +5511987654321 | chatId correto (possível uso checkNumberStatus) |

---

## 7. Dependências Externas

- **WAHA**: Docker image `devlikeapro/waha` ou similar
- **Documentação**: https://waha.devlike.pro/docs/
- **API**: REST; Swagger em `{WAHA_BASE_URL}/docs`

---

## 8. Referências

- [WAHA Quick Start](https://waha.devlike.pro/docs/overview/quick-start/)
- [WAHA Send Messages](https://waha.devlike.pro/docs/how-to/send-messages/)
- [How to Avoid Blocking](https://waha.devlike.pro/docs/overview/%EF%B8%8F-how-to-avoid-blocking/)
- [EF-COM-011](../04_notificacoes_canais_externos/) — Integração D4
- [EF-011 intellicare-geralda](../../../intellicare-geralda/docs/specs/fase-04-integracao-agentes/EF-011_INTEGRACAO_COMUNICACAO.md) — Geralda ↔ Comunicação
