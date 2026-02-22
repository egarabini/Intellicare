# Comunicação como Plataforma de Serviço (CPaaS) \- Documento Técnico

Versão: 1.0  
Plataforma Intellicare — Engenharia do Cuidado / HDG

# 1\. Sumário Executivo

O CPaaS da Plataforma Intellicare fornece comunicação omnicanal de forma padronizada, segura e auditável.  
Ele **transporta** mensagens, mas não decide **conteúdo**, **momento** ou **intenção** — isso pertence ao MCP.

## 1.1 Conceito de CPaaS na Plataforma Intellicare

A Comunicação como Plataforma de Serviço (CPaaS) é um modelo em que os serviços de comunicação — mensagens, voz, vídeo, notificações e canais digitais — são disponibilizados por meio de APIs e SDKs padronizados.

A CPaaS centraliza:

* canais (WhatsApp, SMS, e-mail, voz, vídeo, chat-web, push)

* autenticação e segurança dos canais

* gestão de filas, rotas e tentativas

* registro de logs e auditoria

* políticas de engajamento

* comunicação outbound e inbound

Em vez de cada aplicação implementar sua própria lógica de envio/recebimento de mensagens, a CPaaS fornece **um ponto único de comunicação** para todo o ecossistema Intellicare (MCP, CarePlanner, portais, apps móveis e integrações externas).

# 2\. Escopo e Relação com a Arquitetura

O CPaaS corresponde à **Camada de Comunicação e Engajamento (CPaaS)** da [Arquitetura Conceitual da Plataforma Intellicare](https://docs.google.com/document/d/1XlhRzUAhIwFiWinfmeOiBAiJARDVpFl4wYpJKLldCcg/edit?tab=t.0).  
Este documento detalha:

- APIs e responsabilidades  
- limites (o que CPaaS não faz)  
- interação com MCP, IA Services e GC Cuidado  
- segurança e auditoria  
- pipeline inbound/outbound

# 3\. Posicionamento na Arquitetura \- As Camadas da Plataforma Intellicare

A **Camada CPaaS** conecta:

- MCP (quem decide)  
- Canais digitais (WhatsApp, Rocket.Chat, SMS, e-mail, voz)  
- CPaaS como transportador

## 3.1 Papéis Institucionais da CPaaS

A CPaaS desempenha quatro papéis principais:

### 1\. Orquestração de Canais de Comunicação

Integra canais diversos por meio de APIs consistentes.  
 Permite que o MCP ou o CarePlanner acionem comunicações sem conhecer a tecnologia de cada canal.

### 2\. Engajamento Operacional da Coordenação do Cuidado

Suporta fluxos como:

* lembretes de consultas

* follow-up pós-alta

* orientações clínicas

* alertas e escalonamentos

* campanhas de engajamento longitudinal

Eventos relevantes são registrados no GC Cuidado como parte da jornada.

### 3\. Integração com Aplicações Internas e Terceiros

Novos módulos (ex.: vídeo de teleconsulta) integram-se facilmente seguindo as APIs CPaaS.

### 4\. Geração de Dados de Engajamento

A CPaaS alimenta o Lakehouse com métricas como:

* taxa de resposta

* tempo para resposta

* perfil do engajamento por canal

* eficácia operacional

# 4\. Responsabilidades do CPaaS

- Enviar mensagens definidas pelo MCP.  
- Transportar comunicação por canal adequado.  
- Tratar filas, retries e timeouts.  
- Receber mensagens inbound.  
- Entregar ao MCP eventos digitais para triagem.  
- Registrar status de entrega.  
- Emitir logs padronizados.

# 5\. Limites (O que o CPaaS NÃO faz)

- NÃO decide conteúdo.  
- NÃO interpreta intenção.  
- NÃO escolhe canal sozinho.  
- NÃO executa protocolos.  
- NÃO aplica regras da jornada.  
- NÃO envia mensagens sem MCP/APLICAÇÃO autorizada.

## 6\. Interações

### MCP → CPaaS

- mensagens outbound  
- parâmetros de canal  
- contexto da jornada

### CPaaS → MCP

- mensagens inbound  
- eventos de erro  
- confirmação/fracasso de entrega  
- logs operacionais

### CPaaS → GC Cuidado

- registra eventos operacionais de comunicação

### CPaaS → FHIR

- registra Communication apenas quando acionado pelo MCP

## 6.1 Relação da CPaaS com os Repositórios da Plataforma

*(integração RSC-FHIR, GC e Lakehouse)*

### RSC FHIR Server

Registra apenas comunicações com relevância clínica/gerencial.  
 Exemplos:

* orientação clínica formal → Communication

* teleconsulta → Encounter

### GC Cuidado (repositório operacional)

Registra:

* tentativas de contato

* falhas

* confirmação

* reagendamentos

* follow-ups

* engajamento não clínico

### Lakehouse (analítico e pesquisa)

Consolida métricas agregadas, séries históricas e análises de performance.

*Essa separação garante que o RSC não seja sobrecarregado com logs operacionais, e que o GC não seja usado como base analítica.*

## 6.2 Integração Estruturada CPaaS ↔ MCP (Model–Context–Protocol)

### Model

Avalia dados clínicos (RSC), operacionais (GC) e analíticos (Lakehouse) para identificar prioridades de contato.

### Context

Define se a interação é triagem, planejamento, coordenação ou conclusão.  
 Determina se a CPaaS deve ser acionada e em qual modalidade.

### Protocol

Define regras:

* canal preferencial

* critérios de disparo

* número de tentativas

* escalonamento navegado (mensagem → ligação → vídeo)

* quando registrar Communication no FHIR

O MCP gera eventos estruturados consumidos pela CPaaS.

# 7\. Segurança e IAM

- autenticação obrigatória no IAM  
- auditoria completa das mensagens  
- políticas LGPD aplicadas a todos os canais  
- consentimento armazenado no GC Cuidado

## 7.1 Segurança, Privacidade e LGPD Aplicadas à CPaaS

A CPaaS implementa:

* autenticação/autorização via IAM

* criptografia em trânsito

* chaves de API com escopo limitado

* logs e auditoria de comunicações

* controle de finalidade e minimização

* políticas de consentimento registradas no GC Cuidado

* verificação de integridade e proteção anti-spoofing

# 8\. Fluxos Operacionais

### Outbound

MCP → CPaaS → Canal → Destinatário  
CPaaS registra status no GC Cuidado.

### Inbound

Destinatário → Canal → CPaaS → MCP  
MCP interpreta intenção (com apoio de IA Services se necessário).

# 9\. Roadmap

- clusterização conversacional  
- fallback automático entre canais  
- integração futura com telessaúde síncrona

## 9.1 Evolução Prevista da CPaaS

A arquitetura da CPaaS permite evoluir sem impactar o núcleo MCP/GC:

* inclusão de novos canais emergentes

* integração nativa com plataformas de vídeo/teleconsulta

* automação inteligente de roteamento por canal

* APIs públicas controladas para parceiros externos

* suporte a bots especializados e orquestradores conversacionais

* expansão para outros serviços (monitoramento domiciliar, ambulatorial, crônicos, paliativo)

# 10\. Conclusão

O CPaaS é o backbone de comunicação da plataforma.  
Ele não contém lógica: apenas transporte e registro.