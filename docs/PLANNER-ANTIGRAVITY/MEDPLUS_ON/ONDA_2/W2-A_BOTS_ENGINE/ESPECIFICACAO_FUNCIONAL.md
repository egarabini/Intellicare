# 📋 W2-A — Especificação Funcional: Bots Engine (Automações)

## 1. Objetivo

Criar um **engine de automações** (inspirado nos Bots do Medplum) que permite que tenants definam lógica de negócio customizada que executa automaticamente em resposta a eventos FHIR. Isso elimina a necessidade de redeploy para cada nova regra de negócio.

---

## 2. Conceito

Um **Bot** no IntelliCare é:
- Um script Python que executa em resposta a um evento FHIR (via Subscription)
- Configurável por tenant (cada tenant pode ter seus bots)
- Executa em **sandbox isolado** (sem acesso ao filesystem do host)
- Tem acesso a um **IntelliCareClient** autenticado para fazer operações FHIR
- Registra logs e AuditEvents de cada execução

---

## 3. Funcionalidades

### 3.1 CRUD de Bots
- Criar bot com nome, descrição e código Python
- Editar código do bot (versionado)
- Ativar/desativar bot
- Listar bots do tenant
- Ver histórico de execuções (logs + AuditEvents)

### 3.2 Triggers (Conexão com Subscriptions)
Um bot é ativado conectando-o a uma Subscription FHIR:
- `Subscription.channel.endpoint = "Bot/{bot_id}"`
- Quando o critério da Subscription é satisfeito, o Bot é executado
- O recurso que disparou o evento é passado como input

### 3.3 Contexto de Execução
O bot recebe:
- `input` — O recurso FHIR que disparou o evento
- `client` — IntelliCareClient autenticado (acesso FHIR)
- `secrets` — Segredos configurados pelo tenant (API keys, tokens)
- `event` — Metadados do evento (interaction, subscription_id)

### 3.4 Exemplos de Uso

| Bot | Trigger | Ação |
|---|---|---|
| Alerta Glicose Alta | `Observation?code=glucose&value-quantity=gt200` | Cria Communication para o médico responsável |
| Welcome Patient | `Patient` (create) | Envia email de boas-vindas via Comunicação |
| Lab Result Notification | `DiagnosticReport?status=final` | Cria Task para médico revisar resultado |
| Protocol Adherence | `MedicationRequest` (create) | Verifica se segue protocolo Oswaldo |
| Quality Indicator | `Encounter?status=finished` | Atualiza contadores de Donabedian |

### 3.5 Segurança
- Bots executam em **sandbox Python** (RestrictedPython ou subprocess isolado)
- Sem acesso ao filesystem, rede direta, ou variáveis de ambiente
- Timeout de 30 segundos por execução
- Somente imports permitidos (allowlist)
- Autenticação do client scoped ao tenant

---

## 4. Interface do Gestor

Via `intellicare-gestor`, o admin local pode:
1. Criar novo bot (editor de código básico)
2. Testar bot com recurso de exemplo
3. Conectar bot a subscription
4. Ver logs de execução
5. Ativar/desativar bot

---

## 5. Referência Medplum

| Componente | Arquivo | Nota |
|---|---|---|
| Bot Execution | `bots/execute.ts` | Dispatch: Lambda/VM/Fission |
| Bot Utilities | `bots/utils.ts` | Auth, secrets, storage |
| VM Context | `bots/vmcontext.ts` | Sandbox isolado Node.js |
| Bot Types | `bots/types.ts` | Request/Result interfaces |
