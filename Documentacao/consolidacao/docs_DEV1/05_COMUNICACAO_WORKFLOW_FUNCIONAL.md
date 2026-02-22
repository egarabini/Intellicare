# 📋 ESPECIFICAÇÃO FUNCIONAL: COMUNICAÇÃO E WORKFLOW

---

## 📌 INFORMAÇÕES DO PROJETO

**ID**: PROJ-05-COMUNICACAO-WORKFLOW  
**Nome**: Sistema de Comunicação e Workflow Integrado  
**Responsável**: DEV1  
**Data**: 26/03/2026  
**Versão**: 1.0  
**Status**: 📝 Em Especificação

---

## 🎯 OBJETIVO

Implementar um sistema integrado de **comunicação** e **workflow** para o ecossistema IntelliCare, permitindo:

1. **Comunicação em tempo real** entre stakeholders (pacientes, profissionais, equipe)
2. **Videoconferência** integrada para teleconsultas
3. **Chatbots inteligentes** com IA para suporte automatizado
4. **Orquestração de workflows** complexos entre módulos

---

## 🔄 MUDANÇA ESTRATÉGICA

### **Stack Anterior (Descontinuado)**:
- ❌ ~~Synapse/Element~~ (Matrix Protocol)
- ❌ ~~N8N~~ (Workflow Automation)

### **Nova Stack (Implementação)**:
- ✅ **Rocket.Chat** - Plataforma de comunicação open-source
- ✅ **Jitsi** - Videoconferência open-source
- ✅ **Flowise** - RAG/Chatbot/LLM Workflows
- ✅ **Kestra** - Orquestração de workflows de dados

---

## 📊 VISÃO GERAL DO SISTEMA

### **Componentes Principais**

```
┌─────────────────────────────────────────────────────────────┐
│                    INTELLICARE ECOSYSTEM                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Rocket.Chat  │  │    Jitsi     │  │   Flowise    │      │
│  │ (Messaging)  │  │   (Video)    │  │  (AI/RAG)    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                    ┌───────┴────────┐                        │
│                    │     Kestra     │                        │
│                    │  (Workflows)   │                        │
│                    └───────┬────────┘                        │
│                            │                                 │
│  ┌─────────────────────────┴──────────────────────────┐     │
│  │         IntelliCare Modules Integration            │     │
│  │  (Florence, Oswaldo, Donabedian, NISE, etc.)       │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 REQUISITOS FUNCIONAIS

### **RF-01: Comunicação em Tempo Real (Rocket.Chat)**

#### RF-01.1: Mensagens Instantâneas
- **Descrição**: Usuários podem trocar mensagens em tempo real
- **Atores**: Pacientes, Profissionais de Saúde, Equipe Administrativa
- **Funcionalidades**:
  - Chat 1:1 (paciente ↔ profissional)
  - Grupos/Canais (equipes, especialidades)
  - Mensagens diretas e em grupo
  - Histórico de conversas
  - Busca de mensagens
  - Notificações push

#### RF-01.2: Canais Organizacionais
- **Descrição**: Canais estruturados por contexto
- **Tipos de Canais**:
  - **#geral**: Comunicação geral da equipe
  - **#alertas**: Alertas clínicos urgentes
  - **#suporte**: Suporte técnico
  - **#equipe-[especialidade]**: Canais por especialidade
  - **#paciente-[id]**: Canal dedicado por paciente

#### RF-01.3: Integração com Agentes IA
- **Descrição**: Bots inteligentes nos canais
- **Agentes**:
  - **Geralda Bot**: Suporte a pacientes
  - **Wanda Bot**: Suporte a profissionais
  - **Dr. Nise Bot**: Treinamento médico
  - **Florence Bot**: Análise laboratorial
  - **Oswaldo Bot**: Doenças crônicas

#### RF-01.4: Autenticação e Segurança
- **Descrição**: Integração com Keycloak (SSO)
- **Funcionalidades**:
  - Login único (SSO)
  - Controle de acesso por perfil
  - Criptografia end-to-end (opcional)
  - Auditoria de mensagens
  - LGPD compliance

---

### **RF-02: Videoconferência (Jitsi)**

#### RF-02.1: Teleconsultas
- **Descrição**: Consultas médicas por vídeo
- **Funcionalidades**:
  - Criar sala de vídeo
  - Convidar participantes
  - Compartilhar tela
  - Gravar consulta (com consentimento)
  - Chat durante vídeo
  - Qualidade adaptativa

#### RF-02.2: Integração com Rocket.Chat
- **Descrição**: Iniciar vídeo direto do chat
- **Fluxo**:
  1. Usuário clica em "Iniciar Vídeo" no chat
  2. Sala Jitsi é criada automaticamente
  3. Link é compartilhado no canal
  4. Participantes entram na sala
  5. Consulta é registrada no FHIR (se aplicável)

#### RF-02.3: Agendamento de Consultas
- **Descrição**: Agendar teleconsultas
- **Funcionalidades**:
  - Criar agendamento
  - Enviar convites
  - Lembretes automáticos
  - Cancelamento/Reagendamento
  - Integração com calendário

---

### **RF-03: Chatbots Inteligentes (Flowise)**

#### RF-03.1: RAG (Retrieval-Augmented Generation)
- **Descrição**: Chatbots com conhecimento contextual
- **Funcionalidades**:
  - Base de conhecimento médico
  - Busca semântica
  - Respostas contextualizadas
  - Fontes citadas
  - Confiança calculada

#### RF-03.2: Workflows LLM
- **Descrição**: Automação com IA
- **Casos de Uso**:
  - Triagem automática de mensagens
  - Sugestões de respostas
  - Análise de sentimento
  - Extração de informações
  - Classificação de urgência

#### RF-03.3: Integração com Módulos
- **Descrição**: Chatbots acessam dados dos módulos
- **Integrações**:
  - **NISE**: Dr. Nise para treinamento
  - **Florence**: Análise de exames
  - **Oswaldo**: Acompanhamento de crônicos
  - **Donabedian**: Indicadores de qualidade

---

### **RF-04: Orquestração de Workflows (Kestra)**

#### RF-04.1: Workflows de Comunicação
- **Descrição**: Automação de processos de comunicação
- **Exemplos**:
  - Enviar lembrete de consulta (D-1)
  - Notificar resultado de exame crítico
  - Escalar alerta não respondido
  - Enviar relatório semanal

#### RF-04.2: Workflows de Integração
- **Descrição**: Sincronização entre módulos
- **Exemplos**:
  - Florence detecta exame crítico → Notifica Oswaldo
  - Oswaldo cria plano de cuidado → Notifica equipe no Rocket.Chat
  - NISE completa treinamento → Atualiza certificação
  - Donabedian calcula indicador → Envia relatório

#### RF-04.3: Workflows Agendados
- **Descrição**: Tarefas recorrentes
- **Exemplos**:
  - Relatório diário de alertas (08:00)
  - Backup de conversas (00:00)
  - Limpeza de mensagens antigas (semanal)
  - Sincronização de usuários (horária)

---

## 👥 ATORES DO SISTEMA

### **1. Paciente**
- Recebe mensagens da equipe
- Participa de teleconsultas
- Interage com Geralda Bot
- Acessa histórico de conversas

### **2. Profissional de Saúde**
- Comunica com pacientes
- Realiza teleconsultas
- Recebe alertas clínicos
- Interage com Wanda Bot

### **3. Equipe Administrativa**
- Gerencia canais
- Monitora comunicações
- Gera relatórios
- Configura workflows

### **4. Agentes IA (Bots)**
- Respondem perguntas
- Fornecem suporte
- Executam ações automatizadas
- Aprendem com interações

---

## 📋 CASOS DE USO PRINCIPAIS

### **CU-01: Teleconsulta Agendada**

**Ator**: Profissional de Saúde, Paciente  
**Pré-condições**: Consulta agendada no sistema  
**Fluxo**:
1. Sistema envia lembrete D-1 (Kestra)
2. No horário, sistema cria sala Jitsi
3. Envia link para paciente e profissional (Rocket.Chat)
4. Participantes entram na sala
5. Consulta é realizada
6. Sistema registra consulta no FHIR
7. Gera ata automática (Flowise)

**Pós-condições**: Consulta documentada, ata gerada

---

### **CU-02: Alerta de Exame Crítico**

**Ator**: Florence (módulo), Oswaldo (módulo), Profissional  
**Pré-condições**: Exame crítico detectado  
**Fluxo**:
1. Florence detecta exame crítico
2. Publica evento no Kestra
3. Kestra notifica Oswaldo
4. Oswaldo avalia impacto no plano de cuidado
5. Kestra envia alerta no Rocket.Chat (#alertas)
6. Profissional recebe notificação
7. Profissional responde no chat
8. Sistema registra ação tomada

**Pós-condições**: Alerta tratado, ação documentada

---

### **CU-03: Suporte via Chatbot**

**Ator**: Paciente, Geralda Bot  
**Pré-condições**: Paciente tem dúvida  
**Fluxo**:
1. Paciente envia mensagem no Rocket.Chat
2. Geralda Bot (Flowise) recebe mensagem
3. Bot busca resposta na base de conhecimento (RAG)
4. Bot responde com informação contextualizada
5. Se não souber, escala para humano
6. Interação é registrada para aprendizado

**Pós-condições**: Dúvida respondida ou escalada

---

## 🔒 REQUISITOS NÃO-FUNCIONAIS

### **RNF-01: Performance**
- Mensagens entregues em <1s
- Vídeo com latência <200ms
- Chatbot responde em <3s
- Workflows executam em <5s

### **RNF-02: Disponibilidade**
- Uptime 99.9%
- Redundância de serviços
- Backup automático
- Recuperação de desastres

### **RNF-03: Segurança**
- Autenticação SSO (Keycloak)
- Criptografia TLS 1.3
- Auditoria completa
- LGPD compliance
- Consentimento explícito

### **RNF-04: Escalabilidade**
- Suportar 1000+ usuários simultâneos
- 10.000+ mensagens/dia
- 100+ salas de vídeo simultâneas
- Escala horizontal

### **RNF-05: Usabilidade**
- Interface intuitiva
- Mobile-friendly
- Acessibilidade (WCAG 2.1)
- Suporte a múltiplos idiomas

---

## 📅 CRONOGRAMA ESTIMADO

**Duração Total**: 6 semanas (30 dias úteis)

### **Semana 1-2**: Rocket.Chat + Jitsi
- Setup e configuração
- Integração SSO
- Canais básicos
- Testes de vídeo

### **Semana 3-4**: Flowise + Chatbots
- Configurar Flowise
- Criar chatflows
- Integrar com Rocket.Chat
- Treinar modelos

### **Semana 5**: Kestra + Workflows
- Configurar Kestra
- Criar workflows básicos
- Integrar com módulos
- Testes de automação

### **Semana 6**: Integração e Testes
- Integração completa
- Testes end-to-end
- Documentação
- Treinamento

---

## ✅ CRITÉRIOS DE ACEITAÇÃO

1. ✅ Rocket.Chat funcionando com SSO
2. ✅ Jitsi integrado ao Rocket.Chat
3. ✅ 3+ chatbots funcionando (Geralda, Wanda, Dr. Nise)
4. ✅ 5+ workflows automatizados
5. ✅ Integração com 3+ módulos IntelliCare
6. ✅ Documentação completa
7. ✅ Testes de carga passando
8. ✅ LGPD compliance validado

---

**Responsável**: DEV1  
**Data**: 26/03/2026  
**Versão**: 1.0  
**Status**: ✅ Especificação Funcional Completa

