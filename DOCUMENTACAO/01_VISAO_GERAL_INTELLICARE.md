# 1. Visao Geral do IntelliCare

## Objetivo do sistema

O IntelliCare organiza operacao assistencial e gestao clinica em uma plataforma unica, com foco em:

- produtividade da equipe de saude;
- continuidade do cuidado por jornadas multicanal;
- registro clinico estruturado;
- visibilidade gerencial por dashboards e relatorios.

## Perfis de usuario e o que cada um faz

- **Administrador da plataforma (AdminUI)**  
  Provisiona tenants, gerencia modulos/servidores, acompanha financeiro e auditoria.

- **Gestor do tenant (GestorUI)**  
  Opera unidade/equipe, acompanha pacientes e consultas, dispara jornadas CarePlanner, acompanha indicadores.

- **Clinico (ClinicoUI)**  
  Atende agenda, abre e fecha encontros, registra notas Florence, elabora prescricao Oswaldo, consulta jornadas e alertas.

- **Paciente (PacienteUI)**  
  Acompanha agenda, jornadas recebidas, historico clinico compartilhavel e dados cadastrais.

## Mapa funcional por modulo

- `admin`: governanca da plataforma (tenants, servidores, modulos, financeiro, usuarios admin, auditoria).
- `gestor`: gestao do tenant (pacientes, equipe, unidades, agenda, relatorios, RAG, careplanner).
- `cuidado`: atendimento clinico (encontro, prontuario evolutivo, agenda, assistente).
- `florence`: notas clinicas em formato livre ou SOAP, com sugestao IA.
- `oswaldo`: sugestao de CID-10 e prescricoes com apoio IA.
- `careplanner`: jornadas de cuidado por Rocket.Chat, WhatsApp, SMS e e-mail.

## Fluxo macro da jornada assistencial

1. Gestor estrutura tenant, equipe e unidades.
2. Gestor/operacao agenda paciente.
3. Clinico realiza atendimento (encontro).
4. Clinico registra nota (Florence) e prescricao (Oswaldo).
5. Gestor dispara/acompanha jornada no CarePlanner.
6. Paciente acompanha jornadas e historico compartilhavel.
7. Time acompanha indicadores em dashboards e relatorios PDF.

## Convencoes de status usadas no sistema

- Jornadas: `CREATED`, `DISPATCHED`, `SENT`, `REPLIED`, `CLOSED`, `FAILED`, `EXPIRED`.
- Atendimento/agenda: status operacional por consulta (ex.: em andamento, realizado).
- Prescricao: status de assinatura/estado da prescricao.

## O que esta fora de escopo nesta versao

- Validacao final de staging da sprint clinica (`DEM-064`) ainda em progresso.
- Qualquer funcionalidade nao citada explicitamente nos guias por perfil deve ser tratada como futura ou interna.
