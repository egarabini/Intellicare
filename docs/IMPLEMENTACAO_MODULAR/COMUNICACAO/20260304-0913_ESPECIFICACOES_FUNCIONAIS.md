# COMUNICACAO — Especificacoes Funcionais
**Data:** 2026-03-04
**Versao:** 1.0.0
**Modulo:** intellicare-comunicacao (porta 8005)
**Papel:** Sistema nervoso da plataforma — canal entre servico e paciente

---

## 1. Proposito

O modulo COMUNICACAO e o canal de mensagens do IntelliCare.
Ele orquestra o envio de mensagens atraves de multiplas plataformas
(Rocket.Chat, WhatsApp, SMS, Email, Jitsi) para equipes clinicas e pacientes.

---

## 2. Funcionalidades Implementadas (v1.0 — 133 testes, deps quebradas)

### 2.1 Rocket.Chat (Mensagens de Equipe)
- Envio de mensagens diretas e para canais
- Bot @intellicare para alertas automaticos
- Criacao de salas de caso multidisciplinar

### 2.2 WhatsApp via WAHA
- Envio de mensagens de texto, imagem e documento
- Templates de mensagem (lembretes, orientacoes)
- Webhook para receber respostas de pacientes
- Gestao de sessoes WAHA

### 2.3 SMS
- Envio via Twilio e Zenvia
- Fallback automatico entre provedores
- Templates de SMS para lembretes de consulta

### 2.4 Email
- Envio via SMTP configuravel
- Templates HTML com branding IntelliCare
- Suporte a anexos (PDFs de resultados)

### 2.5 Jitsi (Teleconsulta)
- Geracao de salas Jitsi autenticadas (JWT)
- Envio de link de teleconsulta via WhatsApp/Email
- Agendamento de salas com duracao definida

### 2.6 Motor de Roteamento
- Dispatcher inteligente: escolhe canal baseado em preferencia do paciente
- Fallback em cascata: WhatsApp → SMS → Email → Rocket.Chat
- Retry automatico com backoff exponencial
- Fila Redis para mensagens assincronas

---

## 3. Funcionalidades da Versao 2.0

### 3.1 Preferencias de Canal por Paciente
- Armazenar preferencia de contato no perfil (FHIR Patient extension)
- Respeitar janela de silencio (ex: nao enviar SMS apos 21h)
- Opt-out por canal

### 3.2 Templates Personalizaveis
- Templates por tenant (multi-tenancy)
- Variaveis dinamicas: nome, data, medicamento, etc.
- Suporte a portugues e espanhol

### 3.3 Historico e Auditoria
- Log de todas as mensagens enviadas (canal, status, timestamp)
- Status de entrega: enviado, entregue, lido, falhou
- Relatorio de engajamento por canal

### 3.4 Notificacoes Clinicas (AlertHub)
- Receber alertas do WANDA e roteár para canal correto da equipe
- Alertas criticos: encaminhar para RC com @here se urgente
- Integrar com Grafana para alertas de infra

---

## 4. Casos de Uso Principais

### UC-01: Lembrete de Consulta
**Ator:** Agendamento automatico (Kestra)
**Fluxo:** 24h antes → COMUNICACAO envia WhatsApp ao paciente → Se falhar, SMS → Se falhar, Email

### UC-02: Alerta Clinico
**Ator:** WANDA detecta valor critico
**Fluxo:** WANDA publica alerta → COMUNICACAO roteá para medico responsavel via RC (urgente) + SMS

### UC-03: Teleconsulta
**Ator:** Medico agendando consulta remota
**Fluxo:** Medico solicita sala → COMUNICACAO gera link Jitsi → Envia link para paciente via WhatsApp

---

## 5. Criterios de Aceite (v2.0)

- [ ] Health check responde 200
- [ ] Suite de testes: 0 falhas, >= 80% cobertura
- [ ] Envio via Rocket.Chat funcionando (infra ja deployada)
- [ ] Dispatcher roteia mensagem pelo canal certo
- [ ] Fallback funciona quando canal primario falha
- [ ] Log de mensagens persistido no PostgreSQL

---

*COMUNICACAO v2.0 — Especificacoes Funcionais — 2026-03-04*
