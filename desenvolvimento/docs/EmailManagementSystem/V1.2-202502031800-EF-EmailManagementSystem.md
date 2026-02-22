# 📧 Especificação Funcional - Sistema de Gerenciamento de Emails

**Projeto:** IntelliCare Email Management System  
**Versão:** 1.0  
**Data:** 2025-02-03  
**Autor:** IntelliCare Team

---

## 1. VISÃO GERAL

### 1.1 Objetivo

Implementar um **sistema robusto e profissional** de gerenciamento de emails em Python para o projeto IntelliCare, com:

- ✅ Envio assíncrono de emails (não bloqueia requisições)
- ✅ Templates profissionais e responsivos
- ✅ Fila de prioridades (urgente, normal, baixa)
- ✅ Retry automático em caso de falha
- ✅ Logs e auditoria completa
- ✅ Monitoramento em tempo real
- ✅ Suporte a múltiplos provedores (SMTP, Mailgun, SendGrid)
- ✅ Agendamento de emails
- ✅ Anexos e emails HTML

### 1.2 Escopo

**Incluído:**
- Sistema de filas com Celery + Redis
- Templates Jinja2 responsivos
- API REST para envio de emails
- Dashboard de monitoramento (Flower)
- Logs estruturados em banco de dados
- Validação de emails
- Rate limiting
- Webhooks para status de entrega

**Não incluído (futuro):**
- Interface web de gerenciamento
- Editor WYSIWYG de templates
- A/B testing de emails
- Segmentação avançada

---

## 2. REQUISITOS FUNCIONAIS

### RF01 - Envio de Email Assíncrono

**Descrição:** Sistema deve enviar emails em background sem bloquear requisições HTTP.

**Critérios de Aceitação:**
- Requisição HTTP retorna imediatamente com ID da tarefa
- Email é processado em fila Celery
- Retry automático: 3 tentativas com backoff exponencial
- Timeout: 30 segundos por tentativa

**Prioridades:**
- `URGENT`: Processado imediatamente (ex: tokens de verificação)
- `NORMAL`: Processado em até 1 minuto
- `LOW`: Processado em até 5 minutos

---

### RF02 - Templates Profissionais

**Descrição:** Sistema deve suportar templates HTML responsivos com variáveis dinâmicas.

**Templates Padrão:**
1. **Verificação de Email** - Token de 5 dígitos
2. **Atualização de Status** - Mudanças em solicitações
3. **Boas-vindas** - Novo usuário
4. **Recuperação de Senha** - Link de reset
5. **Notificação de Agente** - Resultados de análise
6. **Relatório Periódico** - Resumo semanal/mensal

**Recursos:**
- Variáveis Jinja2: `{{ nome }}`, `{{ protocolo }}`, etc.
- Suporte a HTML + texto plano (fallback)
- Imagens inline (base64)
- Responsivo (mobile-first)
- Branding IntelliCare

---

### RF03 - Logs e Auditoria

**Descrição:** Todo email enviado deve ser registrado com metadados completos.

**Dados Registrados:**
- ID único do email
- Destinatário(s)
- Assunto
- Template usado
- Variáveis do template
- Status (pending, sent, failed, bounced)
- Tentativas de envio
- Timestamps (criado, enviado, entregue, aberto, clicado)
- Provedor usado (SMTP, Mailgun, etc.)
- Erros (se houver)

**Retenção:**
- Logs: 90 dias
- Emails com erro: 180 dias

---

### RF04 - Monitoramento

**Descrição:** Dashboard em tempo real para acompanhar filas e status.

**Métricas:**
- Emails na fila (por prioridade)
- Taxa de sucesso/falha (últimas 24h)
- Tempo médio de envio
- Emails por hora/dia
- Alertas de falhas consecutivas

**Ferramenta:** Flower (interface web do Celery)

---

### RF05 - Múltiplos Provedores

**Descrição:** Suporte a diferentes provedores de email com fallback automático.

**Provedores Suportados:**
1. **SMTP** (Gmail, Outlook, servidor próprio)
2. **Mailgun** (API)
3. **SendGrid** (API)
4. **Amazon SES** (futuro)

**Fallback:**
- Provedor primário falha → tenta secundário
- Configurável por ambiente (dev, staging, prod)

---

## 3. REQUISITOS NÃO FUNCIONAIS

### RNF01 - Performance
- Processar 1000 emails/minuto
- Latência API < 100ms
- Fila Redis com persistência

### RNF02 - Confiabilidade
- Uptime 99.9%
- Retry automático
- Dead letter queue para falhas permanentes

### RNF03 - Segurança
- Credenciais em variáveis de ambiente
- Validação de emails (formato + DNS)
- Rate limiting: 100 emails/minuto por IP
- Sanitização de HTML (prevenir XSS)

### RNF04 - Escalabilidade
- Workers Celery horizontalmente escaláveis
- Redis Cluster para alta disponibilidade
- Suporte a múltiplas filas

---

## 4. CASOS DE USO

### UC01 - Enviar Email de Verificação

**Ator:** Sistema IntelliCare  
**Pré-condição:** Usuário criou solicitação

**Fluxo Principal:**
1. Sistema gera token de 5 dígitos
2. Sistema chama API: `POST /api/emails/send`
3. API valida dados e cria tarefa Celery
4. API retorna `task_id` imediatamente
5. Worker Celery processa email
6. Email é enviado via provedor
7. Status atualizado no banco de dados
8. Webhook registra entrega (se disponível)

**Fluxo Alternativo:**
- 6a. Provedor falha → retry após 1 minuto
- 6b. 3 falhas → move para dead letter queue
- 6c. Email inválido → marca como failed

---

## 5. ARQUITETURA

```
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION                       │
│                  (API REST + Endpoints)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    CELERY WORKERS                            │
│              (Processamento Assíncrono)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Worker 1 │  │ Worker 2 │  │ Worker N │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    REDIS (Broker)                            │
│         ┌──────────────┬──────────────┬──────────────┐      │
│         │ Queue URGENT │ Queue NORMAL │ Queue LOW    │      │
│         └──────────────┴──────────────┴──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                EMAIL PROVIDERS                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │   SMTP   │  │ Mailgun  │  │SendGrid  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    POSTGRESQL                                │
│              (Logs + Histórico + Auditoria)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. CRONOGRAMA

| Fase | Atividade | Duração |
|------|-----------|---------|
| 1 | Setup (Celery, Redis, FastAPI) | 1 dia |
| 2 | Implementação Core | 2 dias |
| 3 | Templates Jinja2 | 1 dia |
| 4 | Provedores (SMTP, Mailgun) | 1 dia |
| 5 | Logs e Banco de Dados | 1 dia |
| 6 | Testes | 1 dia |
| 7 | Monitoramento (Flower) | 0.5 dia |
| 8 | Documentação | 0.5 dia |
| **TOTAL** | | **8 dias** |

---

## 7. MÉTRICAS DE SUCESSO

- ✅ 99% de emails entregues com sucesso
- ✅ Tempo médio de envio < 5 segundos
- ✅ Zero downtime durante deploy
- ✅ Logs completos de 100% dos emails

---

**Próximo documento:** Especificação Técnica (ET) com código completo de implementação.

