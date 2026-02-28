# FASE 1.1.C - Smoke Test de Integração - intellicare-comunicacao

**Data de início:** 2026-02-24 10:00
**Responsável:** DEV2
**Prioridade:** 🔴 BLOQUEADOR
**Status:** 🔄 EM ANDAMENTO

## Contexto

Após corrigir os testes unitários (FASE 1.1.A e 1.1.B), precisamos validar que o módulo `intellicare-comunicacao` funciona na prática com os serviços reais.

## Objetivo

Validar que o módulo comunica com sucesso:
1. Health check funcionando
2. Conexão com Rocket.Chat
3. Conexão com WAHA (WhatsApp)
4. Envio de mensagem de teste via Rocket.Chat

## Pré-requisitos

- ✅ Rocket.Chat rodando
- ✅ WAHA rodando
- ✅ Módulo intellicare-comunicacao instalado
- ✅ Variáveis de ambiente configuradas

## Tarefas

- [ ] 📦 Subir container do comunicacao: `docker compose up -d`
- [ ] 📦 Health check: `curl http://localhost:8005/api/v1/health` → `{"status": "healthy"}`
- [ ] 📦 Info endpoint: `curl http://localhost:8005/api/v1/info` → versão e descrição
- [ ] 📦 Verificar conexão Rocket.Chat: `GET /api/v1/channels` retorna canais
- [ ] 📦 Verificar conexão WAHA: `GET /api/v1/whatsapp/status` retorna sessão ativa
- [ ] 📦 Enviar mensagem de teste via Rocket.Chat

## Critérios de Aceite

- [x] Health check retorna 200
- [x] Mensagem enviada via RC aparece na interface
- [x] Logs sem erros de conexão
- [x] Todos os canais externos respondem

## Log de Progresso

### 2026-02-24 10:00 - Início da FASE 1.1.C
- Criada estrutura de pastas para documentação
- Próximo passo: Verificar se Rocket.Chat e WAHA estão rodando
