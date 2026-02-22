# 📅 PLANO DE IMPLEMENTAÇÃO: COMUNICAÇÃO E WORKFLOW

---

## 📌 INFORMAÇÕES DO PROJETO

**ID**: PROJ-05-COMUNICACAO-WORKFLOW-PLAN  
**Nome**: Sistema de Comunicação e Workflow Integrado - Plano de Implementação  
**Responsável**: DEV1  
**Data**: 26/03/2026  
**Versão**: 1.0  
**Status**: 📝 Em Planejamento  
**Duração**: 6 semanas (30 dias úteis)  
**Início Previsto**: 31/03/2026  
**Término Previsto**: 16/05/2026

---

## 🎯 OBJETIVO

Implementar sistema integrado de comunicação e workflow usando Rocket.Chat, Jitsi, Flowise e Kestra, seguindo abordagem incremental e testável.

---

## 📊 VISÃO GERAL DO CRONOGRAMA

```
SEMANA 1-2: Rocket.Chat + Jitsi        [██████████] 10 dias
SEMANA 3-4: Flowise + Chatbots         [██████████] 10 dias
SEMANA 5:   Kestra + Workflows         [█████░░░░░]  5 dias
SEMANA 6:   Integração e Testes        [█████░░░░░]  5 dias
```

---

## 📅 CRONOGRAMA DETALHADO

### **SEMANA 1-2: ROCKET.CHAT + JITSI (10 dias)**

#### **Dia 1-2 (31/03 - 01/04): Setup Rocket.Chat**

**Objetivos**:
- ✅ Configurar Rocket.Chat + MongoDB
- ✅ Configurar SSL/TLS (Traefik)
- ✅ Criar usuário admin
- ✅ Configurar canais básicos

**Tarefas**:
1. Criar `docker-compose.comunicacao.yml`
2. Configurar MongoDB 6.0+
3. Configurar Rocket.Chat 6.5+
4. Configurar Traefik (chat.gsi.srv.br)
5. Testar acesso web
6. Criar canais: #geral, #alertas, #suporte

**Entregáveis**:
- ✅ Rocket.Chat funcionando
- ✅ Acesso via https://chat.gsi.srv.br
- ✅ 3 canais criados
- ✅ Documentação de setup

**Critérios de Aceite**:
- Rocket.Chat acessível via HTTPS
- Login admin funcionando
- Canais criados e acessíveis

---

#### **Dia 3-4 (02/04 - 03/04): Integração Keycloak SSO**

**Objetivos**:
- ✅ Configurar OAuth2 no Rocket.Chat
- ✅ Integrar com Keycloak
- ✅ Testar login SSO
- ✅ Sincronizar usuários

**Tarefas**:
1. Criar client `intellicare-rocketchat` no Keycloak
2. Configurar OAuth2 no Rocket.Chat
3. Mapear roles Keycloak → Rocket.Chat
4. Criar script de sincronização de usuários
5. Testar login com usuários existentes

**Entregáveis**:
- ✅ SSO funcionando
- ✅ Usuários sincronizados
- ✅ Roles mapeadas
- ✅ Script de sincronização

**Critérios de Aceite**:
- Login via Keycloak funcionando
- Usuários criados automaticamente
- Roles aplicadas corretamente

---

#### **Dia 5-6 (04/04 - 07/04): Setup Jitsi**

**Objetivos**:
- ✅ Configurar Jitsi Meet
- ✅ Configurar JWT authentication
- ✅ Testar videoconferência
- ✅ Integrar com Keycloak

**Tarefas**:
1. Configurar Jitsi stack (web, jicofo, jvb, prosody)
2. Configurar JWT authentication
3. Configurar SSL (meet.gsi.srv.br)
4. Criar serviço de geração de tokens JWT
5. Testar criação de salas
6. Testar qualidade de vídeo

**Entregáveis**:
- ✅ Jitsi funcionando
- ✅ Acesso via https://meet.gsi.srv.br
- ✅ JWT authentication
- ✅ API de criação de salas

**Critérios de Aceite**:
- Jitsi acessível via HTTPS
- Salas criadas via API
- Vídeo com qualidade aceitável (<200ms latência)

---

#### **Dia 7-8 (08/04 - 09/04): Integração Rocket.Chat + Jitsi**

**Objetivos**:
- ✅ Integrar Jitsi no Rocket.Chat
- ✅ Botão "Iniciar Vídeo" nos canais
- ✅ Testar fluxo completo
- ✅ Registrar chamadas

**Tarefas**:
1. Configurar Jitsi integration no Rocket.Chat
2. Criar endpoint `/api/v1/video/create`
3. Implementar geração de JWT
4. Criar tabela `video_calls` no banco
5. Registrar início/fim de chamadas
6. Testar fluxo: Chat → Vídeo → Registro

**Entregáveis**:
- ✅ Botão "Vídeo" no Rocket.Chat
- ✅ Salas criadas automaticamente
- ✅ Chamadas registradas
- ✅ Testes end-to-end

**Critérios de Aceite**:
- Vídeo iniciado com 1 clique
- Sala criada automaticamente
- Chamada registrada no banco

---

#### **Dia 9-10 (10/04 - 11/04): Módulo FastAPI Comunicação**

**Objetivos**:
- ✅ Criar módulo `intellicare-comunicacao`
- ✅ Implementar API REST
- ✅ Integrar com Rocket.Chat API
- ✅ Implementar auditoria

**Tarefas**:
1. Criar estrutura do módulo
2. Configurar FastAPI + SQLAlchemy
3. Criar schema `comunicacao` no PostgreSQL
4. Implementar endpoints:
   - `GET /api/v1/channels`
   - `POST /api/v1/channels`
   - `POST /api/v1/messages/send`
   - `GET /api/v1/messages/history`
   - `POST /api/v1/video/create`
5. Implementar auditoria de mensagens
6. Criar testes unitários

**Entregáveis**:
- ✅ Módulo `intellicare-comunicacao` criado
- ✅ 5 endpoints funcionando
- ✅ Auditoria implementada
- ✅ 20+ testes unitários

**Critérios de Aceite**:
- API acessível via http://localhost:8010
- Todos os endpoints funcionando
- Testes passando (>80% cobertura)

---

### **SEMANA 3-4: FLOWISE + CHATBOTS (10 dias)**

#### **Dia 11-12 (14/04 - 15/04): Setup Flowise**

**Objetivos**:
- ✅ Configurar Flowise + Ollama
- ✅ Configurar PostgreSQL + pgvector
- ✅ Testar chatflow básico
- ✅ Integrar com Ollama

**Tarefas**:
1. Adicionar Flowise ao docker-compose
2. Configurar PostgreSQL (schema `flowise`)
3. Instalar pgvector extension
4. Configurar Ollama
5. Baixar modelo llama2:7b
6. Criar chatflow de teste
7. Testar RAG básico

**Entregáveis**:
- ✅ Flowise funcionando
- ✅ Acesso via http://localhost:3001
- ✅ Ollama com llama2:7b
- ✅ Chatflow de teste

**Critérios de Aceite**:
- Flowise acessível
- Chatflow respondendo
- RAG funcionando

---

#### **Dia 13-15 (16/04 - 18/04): Criar Chatbots**

**Objetivos**:
- ✅ Criar 5 chatbots (Geralda, Wanda, Dr. Nise, Florence, Oswaldo)
- ✅ Configurar bases de conhecimento
- ✅ Treinar modelos
- ✅ Testar respostas

**Tarefas**:
1. **Geralda Bot** (Suporte a Pacientes):
   - Criar chatflow
   - Base de conhecimento: FAQ pacientes
   - Testar perguntas comuns
2. **Wanda Bot** (Suporte a Profissionais):
   - Criar chatflow
   - Base de conhecimento: Protocolos clínicos
   - Testar perguntas técnicas
3. **Dr. Nise Bot** (Treinamento):
   - Reutilizar chatflow do NISE
   - Integrar com módulo NISE
4. **Florence Bot** (Análise Laboratorial):
   - Criar chatflow
   - Integrar com módulo Florence
5. **Oswaldo Bot** (Doenças Crônicas):
   - Criar chatflow
   - Integrar com módulo Oswaldo

**Entregáveis**:
- ✅ 5 chatbots criados
- ✅ Bases de conhecimento configuradas
- ✅ Testes de qualidade (>80% acurácia)

**Critérios de Aceite**:
- Cada bot responde corretamente
- Tempo de resposta <3s
- Confiança >80%

---

#### **Dia 16-18 (21/04 - 23/04): Integração Bots + Rocket.Chat**

**Objetivos**:
- ✅ Integrar bots no Rocket.Chat
- ✅ Configurar webhooks
- ✅ Implementar handler de mensagens
- ✅ Testar fluxo completo

**Tarefas**:
1. Configurar webhooks no Rocket.Chat
2. Criar endpoint `/api/v1/webhooks/rocketchat`
3. Implementar `BotHandler` class
4. Mapear menções (@geralda) → Chatflow
5. Implementar cache de sessões
6. Testar cada bot no Rocket.Chat
7. Implementar fallback para humano

**Entregáveis**:
- ✅ Bots respondendo no Rocket.Chat
- ✅ Webhooks configurados
- ✅ Handler implementado
- ✅ Testes de integração

**Critérios de Aceite**:
- Menção @geralda → Resposta do bot
- Tempo de resposta <5s
- Fallback funcionando

---

#### **Dia 19-20 (24/04 - 25/04): RAG Avançado**

**Objetivos**:
- ✅ Melhorar qualidade das respostas
- ✅ Implementar citação de fontes
- ✅ Implementar feedback loop
- ✅ Otimizar performance

**Tarefas**:
1. Adicionar mais documentos à base de conhecimento
2. Implementar citação de fontes
3. Criar sistema de feedback (👍👎)
4. Implementar aprendizado contínuo
5. Otimizar embeddings
6. Testar com casos reais

**Entregáveis**:
- ✅ RAG otimizado
- ✅ Fontes citadas
- ✅ Sistema de feedback
- ✅ Performance melhorada

**Critérios de Aceite**:
- Respostas com fontes
- Feedback registrado
- Tempo de resposta <3s

---

### **SEMANA 5: KESTRA + WORKFLOWS (5 dias)**

#### **Dia 21-22 (28/04 - 29/04): Setup Kestra**

**Objetivos**:
- ✅ Configurar Kestra
- ✅ Criar workflows básicos
- ✅ Testar execução
- ✅ Configurar triggers

**Tarefas**:
1. Adicionar Kestra ao docker-compose
2. Configurar PostgreSQL (schema `kestra`)
3. Criar workflow de teste
4. Configurar webhook triggers
5. Configurar schedule triggers
6. Testar execução manual

**Entregáveis**:
- ✅ Kestra funcionando
- ✅ Acesso via https://kestra.gsi.srv.br
- ✅ 2 workflows de teste
- ✅ Triggers configurados

**Critérios de Aceite**:
- Kestra acessível
- Workflows executando
- Triggers funcionando

---

#### **Dia 23-24 (30/04 - 02/05): Workflows de Comunicação**

**Objetivos**:
- ✅ Criar workflows de comunicação
- ✅ Implementar lembretes
- ✅ Implementar alertas
- ✅ Testar automações

**Tarefas**:
1. **Workflow: Lembrete de Consulta**
   - Trigger: D-1 da consulta
   - Ação: Enviar mensagem Rocket.Chat
2. **Workflow: Alerta de Exame Crítico**
   - Trigger: Webhook Florence
   - Ação: Notificar Oswaldo + Rocket.Chat
3. **Workflow: Relatório Diário**
   - Trigger: Cron (08:00)
   - Ação: Gerar relatório + Enviar
4. **Workflow: Backup de Conversas**
   - Trigger: Cron (00:00)
   - Ação: Backup PostgreSQL

**Entregáveis**:
- ✅ 4 workflows criados
- ✅ Testes de execução
- ✅ Documentação

**Critérios de Aceite**:
- Workflows executando corretamente
- Mensagens enviadas
- Logs registrados

---

#### **Dia 25 (05/05): Workflows de Integração**

**Objetivos**:
- ✅ Integrar módulos via Kestra
- ✅ Criar workflows de sincronização
- ✅ Testar comunicação entre módulos

**Tarefas**:
1. **Workflow: Florence → Oswaldo**
   - Exame crítico → Atualizar plano de cuidado
2. **Workflow: NISE → Certificação**
   - Treinamento completo → Emitir certificado
3. **Workflow: Donabedian → Relatório**
   - Calcular indicadores → Enviar relatório
4. Testar cada workflow
5. Implementar retry logic
6. Implementar error handling

**Entregáveis**:
- ✅ 3 workflows de integração
- ✅ Retry implementado
- ✅ Error handling

**Critérios de Aceite**:
- Workflows executando
- Integrações funcionando
- Erros tratados

---

### **SEMANA 6: INTEGRAÇÃO E TESTES (5 dias)**

#### **Dia 26-27 (06/05 - 07/05): Testes de Integração**

**Objetivos**:
- ✅ Testar fluxos completos
- ✅ Testar casos de uso
- ✅ Corrigir bugs
- ✅ Otimizar performance

**Tarefas**:
1. **Teste: Teleconsulta Completa**
   - Agendar → Lembrete → Vídeo → Registro
2. **Teste: Alerta Crítico**
   - Florence detecta → Kestra notifica → Oswaldo atualiza → Chat alerta
3. **Teste: Suporte via Bot**
   - Paciente pergunta → Bot responde → Escala humano
4. Corrigir bugs encontrados
5. Otimizar queries lentas
6. Melhorar UX

**Entregáveis**:
- ✅ 3 testes E2E passando
- ✅ Bugs corrigidos
- ✅ Performance otimizada

**Critérios de Aceite**:
- Todos os testes passando
- Performance aceitável
- UX validada

---

#### **Dia 28-29 (08/05 - 09/05): Documentação**

**Objetivos**:
- ✅ Documentar arquitetura
- ✅ Documentar APIs
- ✅ Criar guias de uso
- ✅ Criar troubleshooting

**Tarefas**:
1. Atualizar README.md
2. Documentar APIs (Swagger)
3. Criar guia de instalação
4. Criar guia de uso (usuários)
5. Criar guia de administração
6. Criar troubleshooting guide
7. Criar diagramas (Mermaid)

**Entregáveis**:
- ✅ Documentação completa
- ✅ Swagger atualizado
- ✅ 3 guias criados
- ✅ Diagramas

**Critérios de Aceite**:
- Documentação clara
- Swagger completo
- Guias testados

---

#### **Dia 30 (12/05): Validação Final**

**Objetivos**:
- ✅ Validação com stakeholders
- ✅ Demo completa
- ✅ Coleta de feedback
- ✅ Aprovação final

**Tarefas**:
1. Preparar ambiente de demo
2. Preparar apresentação
3. Executar demo completa
4. Coletar feedback
5. Documentar aprovações
6. Planejar melhorias futuras

**Entregáveis**:
- ✅ Demo executada
- ✅ Feedback coletado
- ✅ Aprovação documentada
- ✅ Plano de melhorias

**Critérios de Aceite**:
- Demo bem-sucedida
- Feedback positivo
- Aprovação obtida

---

## 📦 ENTREGÁVEIS FINAIS

### **Código**:
- ✅ Módulo `intellicare-comunicacao` (FastAPI)
- ✅ Docker Compose completo
- ✅ 10+ workflows Kestra
- ✅ 5 chatbots Flowise
- ✅ Scripts de setup

### **Documentação**:
- ✅ Especificação Funcional
- ✅ Especificação Técnica
- ✅ Plano de Implementação
- ✅ Guia de Instalação
- ✅ Guia de Uso
- ✅ Guia de Administração
- ✅ Troubleshooting Guide
- ✅ API Documentation (Swagger)

### **Testes**:
- ✅ 50+ testes unitários
- ✅ 20+ testes de integração
- ✅ 5+ testes E2E
- ✅ Cobertura >80%

---

## ⚠️ RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Problemas de integração Keycloak | Média | Alto | Testar SSO cedo, ter fallback |
| Performance de vídeo ruim | Média | Alto | Testar com carga, otimizar JVB |
| Bots com respostas ruins | Alta | Médio | Treinar bem, ter fallback humano |
| Workflows falhando | Média | Médio | Implementar retry + error handling |
| Atraso no cronograma | Média | Alto | Buffer de 20%, priorizar MVP |

---

## ✅ CRITÉRIOS DE SUCESSO

1. ✅ Rocket.Chat funcionando com SSO
2. ✅ Jitsi integrado e funcionando
3. ✅ 5 chatbots respondendo corretamente
4. ✅ 10+ workflows automatizados
5. ✅ Integração com 3+ módulos IntelliCare
6. ✅ Documentação completa
7. ✅ Testes passando (>80% cobertura)
8. ✅ Performance aceitável (<3s bots, <200ms vídeo)
9. ✅ LGPD compliance validado
10. ✅ Aprovação dos stakeholders

---

**Responsável**: DEV1  
**Data**: 26/03/2026  
**Versão**: 1.0  
**Status**: ✅ Plano de Implementação Completo

