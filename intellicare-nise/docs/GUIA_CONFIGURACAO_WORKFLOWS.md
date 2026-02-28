# 🔧 Guia de Configuração de Workflows Kestra

**Versão**: 1.0.0  
**Data**: 15/02/2026  
**Módulo**: IntelliCare NISE

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Workflows Disponíveis](#workflows-disponíveis)
4. [Configuração](#configuração)
5. [Secrets e Variáveis](#secrets-e-variáveis)
6. [Triggers](#triggers)
7. [Monitoramento](#monitoramento)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 VISÃO GERAL

Este guia descreve como configurar e gerenciar os **workflows Kestra** do módulo NISE.

### O que é Kestra?

**Kestra** é uma plataforma de orquestração de workflows declarativa baseada em YAML. Permite automatizar processos complexos de forma visual e manutenível.

### Benefícios

- ✅ **Declarativo**: Workflows definidos em YAML
- ✅ **Visual**: UI para monitoramento e debugging
- ✅ **Escalável**: Execução paralela e distribuída
- ✅ **Confiável**: Retry automático e error handling
- ✅ **Auditável**: Histórico completo de execuções

---

## 🏗️ ARQUITETURA

### Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                     Kestra Server                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Scheduler  │  │   Executor   │  │   Worker     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Workflows   │  │  Executions  │  │    Queue     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Services                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     NISE     │  │   Oswaldo    │  │   Florence   │     │
│  │   (8000)     │  │   (8002)     │  │   (8001)     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Fluxo de Execução

1. **Trigger**: Workflow é disparado (schedule, webhook, manual)
2. **Scheduler**: Kestra agenda execução
3. **Executor**: Kestra executa tasks sequencialmente
4. **Worker**: Tasks são executadas em workers
5. **Storage**: Resultados são armazenados no PostgreSQL
6. **Notification**: Notificações são enviadas (se configurado)

---

## 📦 WORKFLOWS DISPONÍVEIS

### 1. Alerta Crítico Notificação

**ID**: `alerta-critico-notificacao`  
**Namespace**: `intellicare`  
**Arquivo**: `kestra/alerta-critico-notificacao.yml`

**Propósito**: Processar alertas críticos de pacientes e enviar notificações.

**Inputs**:
- `paciente_id` (STRING, required): ID do paciente
- `alerta_id` (STRING, required): ID do alerta
- `tipo_alerta` (STRING, default: "critico"): Tipo de alerta
- `mensagem` (STRING, required): Mensagem do alerta

**Tasks**:
1. `buscar_paciente`: Busca dados do paciente no NISE
2. `identificar_responsaveis`: Identifica equipe responsável
3. `enviar_email`: Envia email para médico
4. `enviar_rocketchat`: Envia mensagem no Rocket.Chat
5. `registrar_log`: Registra log de notificação

**Triggers**:
- **Webhook**: Chamado pelo Oswaldo quando alerta é criado
- **Polling**: Verifica alertas a cada 5 minutos

**Tempo de Execução**: ~30-60 segundos

---

### 2. Reclassificação de Plano

**ID**: `reclassificacao-plano`  
**Namespace**: `intellicare`  
**Arquivo**: `kestra/reclassificacao-plano.yml`

**Propósito**: Reclassificação automática de planos de cuidado baseada em novos dados clínicos.

**Inputs**:
- `paciente_id` (STRING, optional): ID do paciente (se vazio, processa todos)
- `condicao` (STRING, default: "todas"): Condição a reclassificar

**Tasks**:
1. `buscar_pacientes`: Busca pacientes com reclassificação pendente
2. `processar_pacientes`: Loop para cada paciente
   - `calcular_estadiamento`: Calcula novo estadiamento
   - `verificar_mudanca`: Verifica se houve mudança
   - `atualizar_plano`: Atualiza plano de cuidado
   - `notificar_equipe`: Notifica equipe
   - `registrar_auditoria`: Registra auditoria
3. `gerar_relatorio`: Gera relatório final

**Triggers**:
- **Diário**: Às 02:00 (horário de baixo uso)
- **Semanal**: Domingos às 03:00 (reclassificação completa)
- **Webhook**: Manual via API

**Tempo de Execução**: ~60-180 segundos (depende do número de pacientes)

---

### 3. Acompanhamento Periódico

**ID**: `acompanhamento-periodico`  
**Namespace**: `intellicare`  
**Arquivo**: `kestra/acompanhamento-periodico.yml`

**Propósito**: Acompanhamento periódico de pacientes crônicos com envio de lembretes.

**Inputs**:
- `periodo` (STRING, required): Período (diario, semanal, mensal)
- `condicao` (STRING, default: "todas"): Condição a acompanhar
- `dias_atraso_minimo` (INT, default: 7): Dias de atraso mínimo

**Tasks**:
1. `buscar_pacientes_acompanhamento`: Busca pacientes pendentes
2. `processar_pacientes_acompanhamento`: Loop para cada paciente
   - `verificar_ultima_consulta`: Verifica última consulta
   - `verificar_ultimos_exames`: Verifica últimos exames
   - `calcular_atraso`: Calcula dias de atraso
   - `verificar_envio_lembrete`: Verifica se deve enviar
   - `buscar_contato`: Busca dados de contato
   - `enviar_email_lembrete`: Envia email
   - `enviar_sms_lembrete`: Envia SMS
   - `registrar_contato`: Registra tentativa
3. `gerar_relatorio_acompanhamento`: Gera relatório final

**Triggers**:
- **Diário**: Às 08:00 (atraso >= 3 dias)
- **Semanal**: Segundas às 09:00 (atraso >= 7 dias)
- **Mensal**: Dia 1 às 10:00 (atraso >= 30 dias)

**Tempo de Execução**: ~60-180 segundos (depende do número de pacientes)

---

## ⚙️ CONFIGURAÇÃO

### 1. Configurar Kestra no Docker Compose

**Arquivo**: `docker-compose.yml`

```yaml
kestra:
  image: kestra/kestra:latest
  container_name: intellicare-kestra
  ports:
    - "8080:8080"
  environment:
    - KESTRA_CONFIGURATION_DATABASE_TYPE=postgres
    - KESTRA_CONFIGURATION_DATABASE_URL=jdbc:postgresql://postgres:5432/intellicare_kestra
    - KESTRA_CONFIGURATION_QUEUE_TYPE=postgres
    - KESTRA_CONFIGURATION_REPOSITORY_TYPE=postgres
  volumes:
    - ./kestra:/app/workflows:ro
    - kestra-data:/app/storage
  depends_on:
    - postgres
```

### 2. Criar Database no PostgreSQL

```sql
-- Conectar ao PostgreSQL
psql -U intellicare -h localhost

-- Criar database para Kestra
CREATE DATABASE intellicare_kestra;

-- Conceder permissões
GRANT ALL PRIVILEGES ON DATABASE intellicare_kestra TO intellicare;
```

### 3. Subir Kestra

```bash
# Subir serviço Kestra
docker-compose up -d kestra

# Verificar logs
docker-compose logs -f kestra

# Aguardar inicialização (pode demorar 30-60s)
sleep 60

# Verificar health
curl http://localhost:8080/api/v1/health
```

### 4. Acessar UI do Kestra

```bash
# Abrir no navegador
open http://localhost:8080
```

**Credenciais** (se autenticação estiver habilitada):
- **Usuário**: admin
- **Senha**: (configurar via variável de ambiente)

---

## 🔐 SECRETS E VARIÁVEIS

### 1. Configurar Secrets no Kestra

Secrets são usados para armazenar informações sensíveis (senhas, API keys, etc.).

#### Via UI

1. Acesse http://localhost:8080
2. Vá em **Settings** → **Secrets**
3. Clique em **Add Secret**
4. Preencha:
   - **Key**: Nome do secret (ex: `SMTP_PASSWORD`)
   - **Value**: Valor do secret
   - **Namespace**: `intellicare` (ou deixe global)
5. Clique em **Save**

#### Via API

```bash
# Criar secret via API
curl -X POST http://localhost:8080/api/v1/secrets \
  -H "Content-Type: application/json" \
  -d '{
    "key": "SMTP_PASSWORD",
    "value": "senha_secreta",
    "namespace": "intellicare"
  }'
```

### 2. Secrets Necessários

Configure os seguintes secrets para os workflows funcionarem:

| Secret Key | Descrição | Exemplo |
|------------|-----------|---------|
| `SMTP_HOST` | Servidor SMTP | `smtp.gmail.com` |
| `SMTP_PORT` | Porta SMTP | `587` |
| `SMTP_USER` | Usuário SMTP | `noreply@intellicare.com` |
| `SMTP_PASSWORD` | Senha SMTP | `***` |
| `ROCKETCHAT_WEBHOOK_URL` | Webhook Rocket.Chat | `http://rocketchat:3000/hooks/...` |
| `ROCKETCHAT_TOKEN` | Token Rocket.Chat | `***` |
| `SMS_API_KEY` | API Key SMS | `***` |
| `SMS_API_URL` | URL API SMS | `https://api.sms.com/send` |

### 3. Usar Secrets nos Workflows

```yaml
tasks:
  - id: enviar_email
    type: io.kestra.plugin.notifications.mail.MailSend
    from: "{{ secret('SMTP_USER') }}"
    to: "{{ outputs.buscar_paciente.body.medico_email }}"
    subject: "Alerta Crítico - Paciente {{ inputs.paciente_id }}"
    htmlTextContent: "{{ inputs.mensagem }}"
    host: "{{ secret('SMTP_HOST') }}"
    port: "{{ secret('SMTP_PORT') }}"
    username: "{{ secret('SMTP_USER') }}"
    password: "{{ secret('SMTP_PASSWORD') }}"
```

### 4. Variáveis de Ambiente

Configure variáveis de ambiente no `.env`:

```bash
# Kestra
KESTRA_URL=http://localhost:8080
KESTRA_API_KEY=

# NISE
NISE_URL=http://nise:8000

# Oswaldo
OSWALDO_URL=http://oswaldo:8002

# Florence
FLORENCE_URL=http://florence:8001
```

---

## ⏰ TRIGGERS

### 1. Tipos de Triggers

#### Schedule (Cron)

Executa workflow em horários específicos.

```yaml
triggers:
  - id: schedule_diario
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 2 * * *"  # Diariamente às 02:00
```

**Exemplos de Cron**:
- `*/5 * * * *`: A cada 5 minutos
- `0 * * * *`: A cada hora
- `0 2 * * *`: Diariamente às 02:00
- `0 3 * * 0`: Domingos às 03:00
- `0 10 1 * *`: Dia 1 de cada mês às 10:00

#### Webhook

Executa workflow via chamada HTTP.

```yaml
triggers:
  - id: webhook_alerta
    type: io.kestra.plugin.core.trigger.Webhook
    key: "alerta_critico_webhook_key"
```

**Chamar webhook**:
```bash
curl -X POST http://localhost:8080/api/v1/executions/webhook/intellicare/alerta-critico-notificacao/alerta_critico_webhook_key \
  -H "Content-Type: application/json" \
  -d '{
    "paciente_id": "PAC001",
    "alerta_id": "ALT001",
    "tipo_alerta": "critico",
    "mensagem": "Pressão arterial crítica"
  }'
```

#### Manual

Executa workflow manualmente via UI ou API.

```bash
# Via API
curl -X POST http://localhost:8080/api/v1/executions \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "intellicare",
    "flowId": "alerta-critico-notificacao",
    "inputs": {
      "paciente_id": "PAC001",
      "alerta_id": "ALT001",
      "tipo_alerta": "critico",
      "mensagem": "Pressão arterial crítica"
    }
  }'
```

### 2. Configurar Triggers

#### Habilitar/Desabilitar Trigger

```bash
# Desabilitar trigger
curl -X PUT http://localhost:8080/api/v1/flows/intellicare/alerta-critico-notificacao/triggers/schedule_diario/disable

# Habilitar trigger
curl -X PUT http://localhost:8080/api/v1/flows/intellicare/alerta-critico-notificacao/triggers/schedule_diario/enable
```

#### Listar Triggers

```bash
# Listar todos os triggers
curl http://localhost:8080/api/v1/flows/intellicare/alerta-critico-notificacao/triggers
```

---

## 📊 MONITORAMENTO

### 1. UI do Kestra

Acesse http://localhost:8080 para:

- **Dashboard**: Visão geral de execuções
- **Executions**: Lista de execuções (filtrar por status, workflow, data)
- **Flows**: Lista de workflows
- **Logs**: Logs detalhados de cada execução
- **Gantt**: Visualização de timeline de execução

### 2. Métricas

#### Via API

```bash
# Listar execuções recentes
curl http://localhost:8080/api/v1/executions?namespace=intellicare&size=10

# Obter execução específica
curl http://localhost:8080/api/v1/executions/{execution_id}

# Obter logs de execução
curl http://localhost:8080/api/v1/executions/{execution_id}/logs
```

#### Via NISE API

```bash
# Health check
curl http://localhost:8000/api/v1/workflows/health

# Listar execuções
curl http://localhost:8000/api/v1/workflows/executions

# Obter execução específica
curl http://localhost:8000/api/v1/workflows/executions/{execution_id}
```

### 3. Alertas

Configure alertas para falhas de workflow:

```yaml
errors:
  - id: error_handler
    type: io.kestra.plugin.notifications.mail.MailSend
    from: "{{ secret('SMTP_USER') }}"
    to: "dev@intellicare.com"
    subject: "Workflow Failed - {{ flow.id }}"
    htmlTextContent: |
      <h2>Workflow Failed</h2>
      <p><strong>Workflow:</strong> {{ flow.id }}</p>
      <p><strong>Execution:</strong> {{ execution.id }}</p>
      <p><strong>Error:</strong> {{ task.error }}</p>
    host: "{{ secret('SMTP_HOST') }}"
    port: "{{ secret('SMTP_PORT') }}"
    username: "{{ secret('SMTP_USER') }}"
    password: "{{ secret('SMTP_PASSWORD') }}"
```

### 4. Logs

#### Visualizar Logs

```bash
# Logs do Kestra
docker-compose logs -f kestra

# Logs de execução específica (via UI)
# http://localhost:8080/ui/executions/{execution_id}/logs
```

#### Níveis de Log

- **INFO**: Informações gerais
- **WARN**: Avisos (não críticos)
- **ERROR**: Erros (execução falhou)
- **DEBUG**: Informações detalhadas (desenvolvimento)

---

## 🔧 TROUBLESHOOTING

### Problema 1: Workflow Não Aparece na UI

**Sintomas**: Workflow YAML criado mas não aparece no Kestra.

**Causas**:
- Arquivo YAML não está montado no container
- Erro de sintaxe no YAML
- Namespace incorreto

**Soluções**:

```bash
# 1. Verificar se arquivo está montado
docker exec intellicare-kestra ls -la /app/workflows

# 2. Validar sintaxe YAML
docker exec intellicare-kestra kestra flow validate /app/workflows/alerta-critico-notificacao.yml

# 3. Reiniciar Kestra
docker-compose restart kestra

# 4. Verificar logs
docker-compose logs kestra | grep ERROR
```

### Problema 2: Workflow Falha com "Connection Refused"

**Sintomas**: Workflow falha ao chamar serviços externos (NISE, Oswaldo).

**Causas**:
- Serviço não está rodando
- URL incorreta
- Network Docker incorreta

**Soluções**:

```bash
# 1. Verificar serviços
docker-compose ps

# 2. Testar conectividade do Kestra
docker exec intellicare-kestra curl http://nise:8000/health

# 3. Verificar network
docker network inspect intellicare_default

# 4. Verificar URLs no workflow
# Usar nomes de serviço Docker (ex: http://nise:8000, não http://localhost:8000)
```

### Problema 3: Trigger Schedule Não Executa

**Sintomas**: Trigger schedule configurado mas workflow não executa.

**Causas**:
- Trigger desabilitado
- Cron expression incorreta
- Timezone incorreto

**Soluções**:

```bash
# 1. Verificar se trigger está habilitado
curl http://localhost:8080/api/v1/flows/intellicare/alerta-critico-notificacao/triggers

# 2. Habilitar trigger
curl -X PUT http://localhost:8080/api/v1/flows/intellicare/alerta-critico-notificacao/triggers/schedule_diario/enable

# 3. Validar cron expression
# Use https://crontab.guru para validar

# 4. Verificar timezone do Kestra
docker exec intellicare-kestra date
```

### Problema 4: Secrets Não Funcionam

**Sintomas**: Workflow falha com erro de autenticação.

**Causas**:
- Secret não configurado
- Nome do secret incorreto
- Namespace incorreto

**Soluções**:

```bash
# 1. Listar secrets
curl http://localhost:8080/api/v1/secrets?namespace=intellicare

# 2. Criar secret
curl -X POST http://localhost:8080/api/v1/secrets \
  -H "Content-Type: application/json" \
  -d '{
    "key": "SMTP_PASSWORD",
    "value": "senha_secreta",
    "namespace": "intellicare"
  }'

# 3. Verificar uso no workflow
# {{ secret('SMTP_PASSWORD') }} - correto
# {{ secret('smtp_password') }} - incorreto (case-sensitive)
```

### Problema 5: Workflow Muito Lento

**Sintomas**: Workflow demora muito para executar.

**Causas**:
- Muitos pacientes para processar
- Serviços externos lentos
- Recursos insuficientes

**Soluções**:

```bash
# 1. Aumentar workers do Kestra
# docker-compose.yml:
# command: server standalone --worker-thread=8

# 2. Adicionar paralelização no workflow
# Usar EachParallel em vez de EachSequential

# 3. Adicionar timeout nas tasks
timeout: PT5M  # 5 minutos

# 4. Monitorar recursos
docker stats intellicare-kestra
```

---

## ✅ CHECKLIST DE CONFIGURAÇÃO

Antes de usar workflows em produção:

- [ ] Kestra rodando e saudável
- [ ] Database PostgreSQL configurado
- [ ] Workflows carregados (visíveis na UI)
- [ ] Secrets configurados
- [ ] Triggers habilitados
- [ ] Alertas de erro configurados
- [ ] Monitoramento configurado
- [ ] Testes E2E passando
- [ ] Documentação atualizada
- [ ] Backup configurado

---

**Última atualização**: 15/02/2026
**Versão do guia**: 1.0.0
**Autor**: Equipe IntelliCare


