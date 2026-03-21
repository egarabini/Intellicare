<div style="page-break-after: always;"></div>

# INTELLICARE
## Manual do Usuario
### Versao Pronta para Impressao

**Versao:** 1.0  
**Base funcional:** DEM-063  
**Status de staging clinico:** DEM-064 em andamento  
**Data:** 2026-03-21

---

## Controle do Documento

- **Titulo:** Manual do Usuario - IntelliCare
- **Tipo:** Operacional / Treinamento
- **Publico-alvo:** Admin, Gestor, Clinico, Paciente
- **Formato recomendado de exportacao:** PDF (A4, retrato)
- **Classificacao sugerida:** TREINAMENTO (com dados anonimizados)

---

## Sumario

1. [Apresentacao](#1-apresentacao)  
2. [Como Usar Este Manual](#2-como-usar-este-manual)  
3. [Visao Geral do Sistema](#3-visao-geral-do-sistema)  
4. [Perfil Administrador da Plataforma](#4-perfil-administrador-da-plataforma-adminui)  
5. [Perfil Gestor do Tenant](#5-perfil-gestor-do-tenant-gestorui)  
6. [Perfil Clinico](#6-perfil-clinico-clinicoui)  
7. [Perfil Paciente](#7-perfil-paciente-pacienteui)  
8. [Dashboards, Alertas e Relatorios](#8-dashboards-alertas-e-relatorios)  
9. [Boas Praticas de Uso](#9-boas-praticas-de-uso)  
10. [Erros Comuns e Acao Rapida](#10-erros-comuns-e-acao-rapida)  
11. [Checklist de Treinamento](#11-checklist-de-treinamento)  
12. [Anexos de Impressao](#12-anexos-de-impressao)  

---
<div style="page-break-after: always;"></div>

## 1) Apresentacao

O IntelliCare integra gestao, atendimento clinico e acompanhamento de jornadas de cuidado em uma plataforma unica.

Este manual foi escrito para uso pratico em operacao e treinamento, cobrindo as funcionalidades implementadas ate a DEM-063.

### Perfis atendidos

- Administrador da Plataforma
- Gestor do Tenant
- Clinico
- Paciente

### Objetivos deste manual

- orientar o uso por perfil;
- padronizar execucao de fluxos principais;
- facilitar onboarding de novos usuarios;
- apoiar operacao diaria com exemplos claros.

---

## 2) Como Usar Este Manual

### Ordem recomendada de leitura

1. Visao geral do sistema
2. Secao do seu perfil principal
3. Dashboards e alertas
4. Checklist de treinamento

### Convencoes usadas

- Campos e menus aparecem entre crases, exemplo: `Nova Jornada`.
- Status aparecem em maiusculas, exemplo: `FAILED`.
- Blocos `[INSERIR PRINT XX AQUI]` indicam local de imagem no PDF final.

### Referencias de apoio

- `08_PLANO_CAPTURA_PRINTS_GUIADOS.md`
- `09_STORYBOARD_PRINTS_POR_PERFIL.md`
- `10_MODELO_LEGENDAS_E_ANONIMIZACAO.md`
- `MANUAL_USUARIO_INTELLICARE_COMPLETO.md`

---
<div style="page-break-after: always;"></div>

## 3) Visao Geral do Sistema

### Modulos principais

- `admin`: governanca da plataforma e tenants.
- `gestor`: operacao do tenant e acompanhamento assistencial.
- `cuidado`: atendimento clinico e encontros.
- `florence`: notas clinicas (`FREE`/`SOAP`) com apoio IA.
- `oswaldo`: sugestao de CID-10 e prescricao.
- `careplanner`: jornadas multicanal.

### Fluxo assistencial resumido

1. Admin provisiona tenant.
2. Gestor prepara equipe, unidade e agenda.
3. Clinico realiza atendimento e registro.
4. Gestor/clinico acompanham jornadas.
5. Paciente acompanha agenda e historico compartilhavel.

### Canais de jornada suportados

- Rocket.Chat
- WhatsApp
- SMS
- E-mail

---
<div style="page-break-after: always;"></div>

## 4) Perfil Administrador da Plataforma (AdminUI)

### O que este perfil faz

- acompanha indicadores globais;
- cria e atualiza tenants;
- monitora operacao de modulos/servidores;
- acompanha financeiro e auditoria;
- exporta relatorios PDF.

### Fluxo: criar tenant

Campos obrigatorios:

- `Nome`
- `Slug` (gerado automaticamente)
- `Email do gestor`

Exemplo:

- Nome: `Clinica Sao Lucas`
- Slug: `clinica_sao_lucas`
- Email: `gestor.saolucas@cliente.com`

Resultado esperado:

- tenant criado e visivel na lista.

### Prints desta secao

`[INSERIR PRINT 01 AQUI - Dashboard Admin]`  
`[INSERIR PRINT 02 AQUI - Lista de Tenants]`  
`[INSERIR PRINT 03 AQUI - Novo Tenant (vazio)]`  
`[INSERIR PRINT 04 AQUI - Novo Tenant (preenchido)]`

---
<div style="page-break-after: always;"></div>

## 5) Perfil Gestor do Tenant (GestorUI)

### O que este perfil faz

- acompanha operacao assistencial do tenant;
- gerencia jornadas no CarePlanner;
- monitora pacientes, equipe, unidades e agenda;
- usa relatorios para decisao diaria.

### Dashboard do gestor (leitura rapida)

Indicadores:

- pacientes ativos;
- consultas hoje/semana/mes;
- faturas pendentes;
- unidades ativas;
- profissionais alocados.

### Fluxo: iniciar Nova Jornada

Campos criticos:

- `Referência do Paciente`
- `Tipo de Jornada`
- `Canal de Comunicação`
- `Telefone (E.164)` para WhatsApp/SMS
- `E-mail` para canal e-mail
- `Template` (opcional)
- `Incluir videoconsulta` (opcional)

Resultado esperado:

- retorno com `execution_id`;
- jornada visivel na listagem por status.

### Prints desta secao

`[INSERIR PRINT 05 AQUI - Dashboard Gestor]`  
`[INSERIR PRINT 06 AQUI - CarePlanner status]`  
`[INSERIR PRINT 07 AQUI - Nova Jornada formulario]`  
`[INSERIR PRINT 08 AQUI - Lista de jornadas filtrada]`  
`[INSERIR PRINT 09 AQUI - Agenda Gestor]`

---
<div style="page-break-after: always;"></div>

## 6) Perfil Clinico (ClinicoUI)

### O que este perfil faz

- organiza atendimento pela agenda do dia;
- abre/retoma/fecha encontro;
- registra nota Florence (FREE/SOAP);
- utiliza sugestao IA para acelerar escrita;
- registra CID-10 e prescricao no Oswaldo;
- exporta PDF clinico.

### Fluxo de atendimento (resumo)

1. selecionar consulta (`Atender`/`Retomar`);
2. abrir encontro (quando necessario);
3. preencher Florence;
4. preencher Oswaldo;
5. fechar encontro;
6. gerar PDF clinico.

### Exemplo SOAP

- Motivo: `cefaleia persistente ha 3 dias`
- S: queixa do paciente
- O: exame/sinais
- A: avaliacao
- P: conduta

### Exemplo prescricao

- CID-10: `R51 - Cefaleia`
- `Dipirona 500mg` - `1 comp 6/6h` - `3 dias`
- `Ibuprofeno 400mg` - `1 comp 8/8h` - `2 dias`

### Prints desta secao

`[INSERIR PRINT 10 AQUI - Dashboard Clinico]`  
`[INSERIR PRINT 11 AQUI - Encontro visao geral]`  
`[INSERIR PRINT 12 AQUI - Florence SOAP campos]`  
`[INSERIR PRINT 13 AQUI - Florence sugestao IA]`  
`[INSERIR PRINT 14 AQUI - Oswaldo prescricao itens]`  
`[INSERIR PRINT 15 AQUI - Historico prescricoes]`  
`[INSERIR PRINT 16 AQUI - Exportacao PDF Clinico]`  
`[INSERIR PRINT 17 AQUI - Jornadas do Clinico]`

---
<div style="page-break-after: always;"></div>

## 7) Perfil Paciente (PacienteUI)

### O que este perfil faz

- visualiza painel pessoal;
- consulta agenda;
- acompanha jornadas recebidas;
- visualiza historico clinico compartilhavel;
- acessa dados cadastrais e contato.

### Leitura de status de jornada

- `SENT`: mensagem enviada.
- `REPLIED`: paciente respondeu.
- `CLOSED`: jornada concluida.
- `FAILED`: falha de envio.
- `EXPIRED`: expirou sem resposta.

### Regra de privacidade

O historico exibido ao paciente nao inclui avaliacao clinica interna.

### Prints desta secao

`[INSERIR PRINT 18 AQUI - Painel Paciente]`  
`[INSERIR PRINT 19 AQUI - Agenda Paciente]`  
`[INSERIR PRINT 20 AQUI - Tabela Minhas Jornadas]`  
`[INSERIR PRINT 21 AQUI - Historico Timeline]`  
`[INSERIR PRINT 22 AQUI - Cadastro e Contato]`

---
<div style="page-break-after: always;"></div>

## 8) Dashboards, Alertas e Relatorios

### Dashboard Admin

Foco em saude da plataforma:

- tenants ativos/suspensos;
- receita mensal;
- custo de infraestrutura.

### Dashboard Gestor

Foco em operacao assistencial:

- volume de consultas;
- capacidade de equipe;
- acompanhamento de atividades recentes.

### CarePlanner (funil)

Fluxo esperado:

`CREATED -> DISPATCHED -> SENT -> REPLIED -> CLOSED`

Sinais de atencao:

- `FAILED` alto: revisar canal/credencial/contato;
- `EXPIRED` alto: revisar mensagem e janela de contato.

### Relatorios PDF

- Admin: tenants ativos.
- Clinico: PDF de encontro.
- Gestor: relatorios operacionais conforme fluxo habilitado.

---

## 9) Boas Praticas de Uso

- revisar todo conteudo gerado por IA antes de salvar;
- manter dados de contato do paciente atualizados;
- vincular jornada ao agendamento quando aplicavel;
- monitorar dashboards diariamente;
- usar dados ficticios em material de treinamento.

---

## 10) Erros Comuns e Acao Rapida

- Paciente nao recebeu mensagem: validar contato/canal e reenviar.
- Jornada com falha recorrente: revisar integracao do canal.
- Registro clinico incompleto: reforcar checklist SOAP.
- Indicador divergente: revisar filtros e periodo.

---

## 11) Checklist de Treinamento

- [ ] Admin criou tenant de teste.
- [ ] Gestor disparou jornada de teste.
- [ ] Clinico concluiu encontro com Florence e Oswaldo.
- [ ] PDF clinico gerado com sucesso.
- [ ] Paciente visualizou jornada e historico.

---
<div style="page-break-after: always;"></div>

## 12) Anexos de Impressao

### 12.1 Configuracao recomendada para exportar PDF

- Tamanho: A4
- Orientacao: Retrato
- Margens: 1.5 cm
- Escala: 100%
- Cabecalho/rodape do navegador: desativado

### 12.2 Checklist de qualidade do PDF final

- [ ] Sumario com links funcionando.
- [ ] Quebras de pagina corretas entre secoes.
- [ ] Todos os 22 prints inseridos.
- [ ] Legendas revisadas.
- [ ] Dados anonimizados.
- [ ] Revisao ortografica concluida.

### 12.3 Assinatura de aprovacao

- Responsavel pela montagem do PDF:
- Responsavel pela revisao funcional:
- Responsavel pela aprovacao final:
- Data:

---

## Rodape editorial

Documento de uso interno para treinamento e operacao.  
Atualize esta versao sempre que novas demandas alterarem fluxos de tela.

