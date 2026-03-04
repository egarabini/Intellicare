# NISE — Especificacoes Funcionais
**Data:** 2026-03-04
**Versao:** 1.0.0
**Modulo:** intellicare-nise (porta 8013)
**Homenagem:** Nise da Silveira (1905-1999) — psiquiatra brasileira pioneira no tratamento humanizado em saude mental

---

## 1. Proposito

A NISE e o agente de chatbot clinico e treinamento do IntelliCare.
Ela oferece um assistente conversacional para profissionais de saude e pacientes,
alimentado por protocolos clinicos e treinado no contexto do IntelliCare,
alem de gerenciar fluxos de trabalho via Flowise.

---

## 2. Funcionalidades Implementadas (v1.0 — documentado)

### 2.1 Chatbot Clinico (via Flowise)
- Interface conversacional para duvidas clinicas
- RAG sobre base de protocolos (intellicare-conhecimento)
- Contexto do paciente injetado via WANDA

### 2.2 Fluxos de Trabalho
- Gestao de flows Flowise para triagem
- Flow de acolhimento inicial do paciente
- Flow de triagem de sintomas com score de risco

### 2.3 Treinamento (Dr. Nise)
- Agente de treinamento para novos profissionais
- Quiz baseado em protocolos clinicos
- Feedback automatizado sobre respostas

---

## 3. Funcionalidades da Versao 2.0 (a implementar)

### 3.1 API REST com Flowise Integration
- Endpoint de chat que proxeia para Flowise
- Gestao de sessoes de conversa
- Historico de conversas persistido

### 3.2 Triagem Inteligente
- Score de risco para sintomas reportados (Manchester adaptado)
- Classificacao: urgente/prioritario/pouco urgente/nao urgente
- Integrar com WANDA para encaminhamento

### 3.3 RAG sobre Protocolos Clinicos
- Flowise flow conectado ao intellicare-conhecimento (ChromaDB)
- Respostas baseadas em diretrizes e protocolos validados
- Citacao da fonte do protocolo nas respostas

### 3.4 Chatbot para Pacientes
- Interface simplificada para leigos
- Linguagem acessivel (nao clinica)
- Integracao com WhatsApp via COMUNICACAO

### 3.5 Analytics de Conversas
- Topicos mais frequentes
- Taxa de resolucao sem escalada
- Satisfacao do usuario (feedback pos-chat)

---

## 4. Casos de Uso Principais

### UC-01: Duvida Clinica do Medico
**Ator:** Medico na UBS
**Fluxo:** Medico digita "protocolo para DRC estadio 3 com HAS" -> NISE consulta Flowise RAG -> Retorna orientacao baseada em protocolo com citacao

### UC-02: Triagem de Paciente
**Ator:** Paciente via WhatsApp
**Fluxo:** Paciente reporta sintomas -> NISE aplica triagem -> Classifica urgencia -> Encaminha para UBS (pouco urgente) ou UPA (urgente)

### UC-03: Onboarding de Novo Profissional
**Ator:** Enfermeiro recem-contratado
**Fluxo:** Acessa modulo de treinamento -> Dr. Nise apresenta casos clinicos -> Avalia respostas -> Gera relatorio de aptidao

---

## 5. Criterios de Aceite

- [ ] Health check responde 200
- [ ] POST /chat retorna resposta do chatbot
- [ ] Flowise flow de triagem funcionando
- [ ] RAG responde com citacao de protocolo
- [ ] Historico de conversa persistido
- [ ] Cobertura de testes >= 70%

---

*NISE v2.0 — Especificacoes Funcionais — 2026-03-04*
