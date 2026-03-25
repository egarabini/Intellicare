# Manual do Usuario - IntelliCare (Versao Completa)

Documento consolidado para treinamento e operacao dos perfis do IntelliCare, com base no que ja foi desenvolvido ate a `DEM-090` (sprint 2026-05-23).

---

## 1) Apresentacao

O IntelliCare integra gestao, atendimento clinico e acompanhamento de jornadas de cuidado em uma plataforma unica.

Perfis cobertos neste manual:

- Administrador da Plataforma
- Gestor do Tenant
- Clinico
- Paciente

Objetivos deste manual:

- mostrar o que cada perfil pode fazer;
- orientar preenchimento de campos importantes;
- explicar leitura de dashboards e resultados;
- servir de base para treinamento interno.

---

## 2) Como usar este manual

- Use os fluxos por perfil na ordem sugerida.
- Cada secao contem objetivo, passos, exemplo e resultado esperado.
- Os slots de imagem devem ser preenchidos com os prints guiados do pacote de captura.

Referencias de apoio:

- `08_PLANO_CAPTURA_PRINTS_GUIADOS.md`
- `09_STORYBOARD_PRINTS_POR_PERFIL.md`
- `10_MODELO_LEGENDAS_E_ANONIMIZACAO.md`

---

## 3) Visao geral do sistema

### 3.1 Modulos principais

- `admin`: governanca da plataforma.
- `gestor`: operacao do tenant.
- `cuidado`: atendimento clinico.
- `florence`: notas clinicas (FREE/SOAP + sugestao IA).
- `oswaldo`: CID-10 e prescricao com apoio IA.
- `careplanner`: jornadas multicanal (Rocket.Chat, WhatsApp, SMS, e-mail).

### 3.2 Fluxo assistencial resumido

1. Admin provisiona tenant.
2. Gestor estrutura equipe/unidades.
3. Clinico realiza atendimento e registra conduta.
4. Gestor/clinico acompanham jornadas.
5. Paciente acompanha agenda, jornadas e historico compartilhavel.

### 3.3 Estado atual da plataforma (sprint 2026-04-18)

| Módulo | Smoke staging | Observação |
|--------|-------------|------------|
| Florence (notas IA) | ✅ 200 | |
| Oswaldo (prescrições IA) | ✅ 200 | |
| CarePlanner (jornadas) | ✅ trigger 202 | Kestra com flows condicionais ativos |
| Push PWA (notificações) | ✅ subscribe 201 | ClinicoUI + GestorUI |
| Multi-tenant (provisioning) | ✅ provision 201 | Suspend/reactivate funcionais |
| WhatsApp Evolution | ✅ state: open | |
| Health adapters | ✅ 200 | |

---

## 4) Perfil: Administrador da Plataforma (AdminUI)

### 4.1 O que o Administrador pode fazer

- visualizar indicadores globais da plataforma;
- criar e manter tenants;
- acompanhar servidores, modulos, financeiro e auditoria;
- gerenciar prompts IA com versionamento e rollback;
- exportar relatorio PDF de tenants.

### 4.2 Fluxo principal: provisionar tenant (TenantsManager)

Fluxo recomendado no menu `Tenants`:

- abrir `Provisionar Tenant`;
- preencher dados de provisionamento;
- acompanhar tenant na lista e operar ciclo de vida.

Campos de provisionamento:

- `Slug`
- `Nome`
- `Email do Gestor`
- `Plano` (quando habilitado no ambiente)

Exemplo:

- Slug: `clinica_sao_lucas`
- Nome: `Clinica Sao Lucas`
- Email do gestor: `gestor.saolucas@cliente.com`
- Plano: `PRO`

Resultado esperado:

- Tenant provisionado e visivel na grade.
- Acoes disponiveis: `Configurações`, `Suspender`, `Reativar`, `Remover (soft-delete)`.

### 4.3 Prompts IA (DEM-073)

- Acesso: `AdminUI` -> menu `Prompts IA` (`/admin/prompts`).
- O Admin pode editar prompts, salvar nova versao, ativar versao e fazer rollback.
- Prompts principais: `florence_soap`, `florence_free_text`, `oswaldo_prescription`, `oswaldo_cid10`.

### 4.4 Portal de Agentes

> As imagens dos agentes foram renomeadas — o sufixo `_ia` foi removido. Padrão atual: `agente_florence.png`, `agente_oswaldo.png`, `agente_marie.png` (sem `_ia`). Não afeta a interface visual.

### 4.5 Prints desta secao

`[INSERIR PRINT 01 AQUI - Dashboard Admin]`

`[INSERIR PRINT 02 AQUI - Lista de Tenants]`

`[INSERIR PRINT 03 AQUI - Novo Tenant (vazio)]`

`[INSERIR PRINT 04 AQUI - Novo Tenant (preenchido)]`

`[INSERIR PRINT 25 AQUI - Prompts IA no AdminUI]`

---

## 5) Perfil: Gestor do Tenant (GestorUI)

### 5.1 O que o Gestor pode fazer

- acompanhar indicadores operacionais do tenant;
- gerenciar jornadas do CarePlanner;
- consultar pacientes, agenda, equipe e unidades;
- acompanhar relatorios e operacao do dia.

### 5.2 Dashboard do tenant (leitura rapida)

Indicadores comuns:

- pacientes ativos;
- consultas hoje/semana/mes;
- faturas pendentes;
- documentos RAG;
- unidades ativas;
- profissionais alocados;
- atividades recentes.

Exemplo de decisao:

- se consultas sobem e equipe nao sobe, revisar escala.

### 5.3 Fluxo principal: Nova Jornada CarePlanner

Campos importantes:

- `Referência do Paciente`
- `Tipo de Jornada` (`ADESAO`, `MONITORAMENTO`, `CHECK_IN`, `TELECONSULTA`)
- `Canal de Comunicação`
- `Template de Mensagem` (opcional)
- `Telefone (E.164)` para WhatsApp/SMS
- `E-mail do paciente` para canal e-mail
- `Incluir videoconsulta` (opcional)
- `Referência do Clínico` (obrigatorio se incluir video)
- `Agendamento vinculado` (opcional)

Exemplo:

- Paciente: `53f3b4e1-7f91-4f09-8d58-4ef6c5fe99f0`
- Tipo: `CHECK_IN`
- Canal: `whatsapp`
- Telefone: `+5511999999999`
- Template: `CHECKIN_24H`

Resultado esperado:

- retorno com `execution_id`;
- jornada aparece no painel e evolui por status.

> **Nota:** Flows condicionais validados em staging (2026-03-21): fallback de canal WA→Email ativo, confirmação via WhatsApp automática, retry com backoff (2h→6h→24h).

### 5.4 Notificacoes push (DEM-066)

- No `NotificationBell`, usar o toggle para ativar/desativar push no navegador.
- Com push ativo, eventos criticos chegam mesmo fora da aba principal.

### 5.5 Prints desta secao

`[INSERIR PRINT 05 AQUI - Dashboard Gestor]`

`[INSERIR PRINT 06 AQUI - CarePlanner status]`

`[INSERIR PRINT 07 AQUI - Nova Jornada formulario]`

`[INSERIR PRINT 08 AQUI - Lista de jornadas filtrada]`

`[INSERIR PRINT 09 AQUI - Agenda Gestor]`

---

## 6) Perfil: Clinico (ClinicoUI)

### 6.1 O que o Clinico pode fazer

- acompanhar agenda do dia;
- revisar linha do tempo clinica longitudinal do paciente;
- abrir/retomar/fechar encontro;
- registrar notas Florence (FREE/SOAP);
- usar sugestao IA para SOAP;
- elaborar prescricao Oswaldo com CID-10;
- imprimir receituario digital no padrao CFM/ANVISA;
- exportar PDF clinico;
- acompanhar jornadas relacionadas ao cuidado.

### 6.2 Fluxo principal: atendimento completo

1. Abrir dashboard e selecionar consulta (`Atender`/`Retomar`).
2. Revisar aba padrao `Linha do Tempo` no perfil do paciente.
3. Abrir encontro se necessario.
4. Registrar conteudo em `Notas Florence`.
5. Registrar CID-10 e prescricao em `Prescrição`.
6. Imprimir receituario digital quando necessario.
7. Revisar e `Fechar Encontro`.
8. Gerar `PDF Clínico`.

### 6.3 Florence (SOAP) - exemplo pratico

Motivo da consulta: `cefaleia persistente ha 3 dias`

- S: sintomas relatados
- O: sinais/exame
- A: avaliacao clinica
- P: conduta/plano

Recurso IA:

- `Sugerir SOAP com IA` acelera preenchimento, mas exige revisao clinica.

### 6.4 Oswaldo (prescricao) - exemplo pratico

CID-10:

- `R51 - Cefaleia`

Itens:

- `Dipirona 500mg` - `1 comp 6/6h` - `3 dias`
- `Ibuprofeno 400mg` - `1 comp 8/8h` - `2 dias`

Receituario:

- No historico da prescricao, clicar em `Imprimir Receituário`.
- Tipos: `Receita Comum` e `Receita de Controle Especial`.

### 6.5 Linha do Tempo Clinica (DEM-071)

- Aba padrao no perfil do paciente.
- Consolida consultas, notas, prescricoes e tarefas de jornada em ordem cronologica.
- Permite filtros por tipo de evento e periodo.

### 6.6 Notificacoes push (DEM-066)

- No `NotificationBell`, ativar push para receber alertas clinicos no navegador.
- Recomendado manter habilitado durante o turno.

### 6.7 Prints desta secao

`[INSERIR PRINT 10 AQUI - Dashboard Clinico]`

`[INSERIR PRINT 11 AQUI - Encontro visao geral]`

`[INSERIR PRINT 12 AQUI - Florence SOAP campos]`

`[INSERIR PRINT 13 AQUI - Florence sugestao IA]`

`[INSERIR PRINT 14 AQUI - Oswaldo prescricao itens]`

`[INSERIR PRINT 15 AQUI - Historico prescricoes]`

`[INSERIR PRINT 16 AQUI - Exportacao PDF Clinico]`

`[INSERIR PRINT 17 AQUI - Jornadas do Clinico]`
`[INSERIR PRINT 23 AQUI - Linha do Tempo Clinica]`
`[INSERIR PRINT 24 AQUI - Imprimir Receituario]`

---

## 7) Perfil: Paciente (PacienteUI)

### 7.1 O que o Paciente pode fazer

- visualizar painel de acompanhamento;
- consultar agenda;
- acompanhar jornadas recebidas;
- visualizar historico clinico compartilhavel;
- acessar cadastro e contato.

### 7.2 Leitura de tela: Painel

Elementos:

- proxima consulta;
- total de consultas futuras;
- total de consultas realizadas;
- aviso da clinica (quando houver).

### 7.3 Leitura de tela: Minhas Jornadas

Colunas principais:

- canal;
- status;
- template;
- abertura;
- fechamento.

Interpretacao de status:

- `SENT`: enviado;
- `REPLIED`: paciente respondeu;
- `FAILED`: houve falha;
- `EXPIRED`: expirou sem resposta.

### 7.4 Historico Clinico

- timeline por data;
- profissional responsavel;
- resumo compartilhavel da consulta.

Regra de privacidade:

- informacoes internas de avaliacao clinica nao sao exibidas ao paciente.

### 7.5 Prints desta secao

`[INSERIR PRINT 18 AQUI - Painel Paciente]`

`[INSERIR PRINT 19 AQUI - Agenda Paciente]`

`[INSERIR PRINT 20 AQUI - Tabela Minhas Jornadas]`

`[INSERIR PRINT 21 AQUI - Historico Timeline]`

`[INSERIR PRINT 22 AQUI - Cadastro e Contato]`

---

## 8) Dashboards, alertas e relatorios

### 8.1 Dashboard Admin (executivo)

Foco:

- saude da plataforma e visao financeira.

### 8.2 Dashboard Gestor (operacional)

Foco:

- volume assistencial, capacidade de equipe e acao diaria.

### 8.3 CarePlanner (funil de jornada)

Fluxo esperado:

`CREATED -> DISPATCHED -> SENT -> REPLIED -> CLOSED`

Alertas:

- `FAILED` alto: revisar canal/credencial/contato.
- `EXPIRED` alto: revisar estrategia de mensagem e janela.

### 8.4 Relatorios PDF

- Admin: tenants ativos.
- Clinico: relatorio clinico do encontro.
- Clinico: receituario digital (comum/especial) no historico de prescricoes.
- Gestor/CarePlanner: relatorios conforme fluxo habilitado.

---

## 9) Boas praticas de uso

- revisar sugestoes IA antes de salvar;
- manter dados de contato do paciente atualizados;
- vincular jornada a agendamento quando possivel;
- usar dashboards diariamente para priorizacao;
- usar checklist de anonimização para material de treinamento.

---

## 10) Erros comuns e acao rapida

- **Nao recebi mensagem (paciente):** validar canal e contato; reenviar por canal alternativo.
- **Jornada travada em falha:** revisar credenciais/integracao do canal.
- **Registro clinico incompleto:** reforcar fluxo SOAP minimo.
- **Indicador divergente:** revisar filtros e periodo da consulta.

---

## 11) Checklist de treinamento (resumo)

- [ ] Admin criou tenant de teste.
- [ ] Gestor disparou jornada de teste.
- [ ] Clinico concluiu encontro com Florence + Oswaldo.
- [ ] PDF clinico foi gerado.
- [ ] Paciente visualizou jornada e historico.

---

## 12) Controle de versao do manual

- Versao: `Sprint 2026-04-18 — Concluída (DEMs 065–068)`
- Base funcional: `DEM-074`
- Status sprint mais recente: `2026-04-25 concluida`
- Local do arquivo: `DOCUMENTACAO/UTILIZACAO/MANUAL_USUARIO_INTELLICARE_COMPLETO.md`

