# 9. Storyboard de Prints por Perfil

Este storyboard lista quais telas devem ser capturadas, o que mostrar e qual mensagem pedagogica cada imagem deve transmitir.

## 9.1 Admin (AdminUI)

### 01 - Dashboard geral

- **Arquivo:** `01_admin_dashboard_visao-geral.png`
- **Mostrar:** cards de tenants, receita e custo infra.
- **Legenda sugerida:** "Painel executivo da plataforma com saude operacional e financeira."

### 02 - Lista de tenants

- **Arquivo:** `02_admin_tenants_lista.png`
- **Mostrar:** tabela com ao menos 1 tenant ativo e 1 suspenso.
- **Legenda sugerida:** "Lista central de tenants para acompanhamento e governanca."

### 03 - Novo tenant (formulario vazio)

- **Arquivo:** `03_admin_tenants_novo_vazio.png`
- **Mostrar:** campos Nome, Slug e Email do gestor.
- **Legenda sugerida:** "Formulario de provisionamento de novo tenant."

### 04 - Novo tenant (exemplo preenchido)

- **Arquivo:** `04_admin_tenants_novo_preenchido.png`
- **Mostrar:** exemplo valido com slug gerado.
- **Legenda sugerida:** "Exemplo de preenchimento correto para criacao do tenant."

## 9.2 Gestor (GestorUI)

### 05 - Dashboard do tenant

- **Arquivo:** `05_gestor_dashboard_indicadores.png`
- **Mostrar:** cards de consultas, pacientes, unidades e equipe.
- **Legenda sugerida:** "Visao operacional da unidade para decisao diaria."

### 06 - CarePlanner (cards por status)

- **Arquivo:** `06_gestor_careplanner_status.png`
- **Mostrar:** cards `CREATED`, `SENT`, `REPLIED`, `FAILED`, `EXPIRED`.
- **Legenda sugerida:** "Funil de acompanhamento das jornadas de cuidado."

### 07 - Nova jornada (formulario)

- **Arquivo:** `07_gestor_careplanner_nova-jornada_formulario.png`
- **Mostrar:** tipo, canal, template, contato e opcao de videoconsulta.
- **Legenda sugerida:** "Configuracao completa de disparo de jornada multicanal."

### 08 - Lista de jornadas com filtro

- **Arquivo:** `08_gestor_careplanner_lista-filtrada.png`
- **Mostrar:** filtro por status aplicado + tabela resultante.
- **Legenda sugerida:** "Acompanhamento detalhado das jornadas por status."

### 09 - Agenda (visao gestor)

- **Arquivo:** `09_gestor_agenda_calendario.png`
- **Mostrar:** consultas no calendario.
- **Legenda sugerida:** "Planejamento assistencial por data e equipe."

## 9.3 Clinico (ClinicoUI)

### 10 - Dashboard minha agenda

- **Arquivo:** `10_clinico_dashboard_minha-agenda.png`
- **Mostrar:** consultas do dia e botao `Atender/Retomar`.
- **Legenda sugerida:** "Entrada principal do turno clinico."

### 11 - Encontro atual (visao geral)

- **Arquivo:** `11_clinico_encounter_visao-geral.png`
- **Mostrar:** abas Florence, Oswaldo e Legado.
- **Legenda sugerida:** "Tela de atendimento com registros clinicos estruturados."

### 12 - Florence SOAP (campos)

- **Arquivo:** `12_clinico_florence_soap_campos.png`
- **Mostrar:** motivo da consulta + campos S/O/A/P.
- **Legenda sugerida:** "Estruturacao de evolucao clinica no formato SOAP."

### 13 - Florence com sugestao IA

- **Arquivo:** `13_clinico_florence_ia_sugestao.png`
- **Mostrar:** botao de sugestao e campos preenchidos.
- **Legenda sugerida:** "Apoio IA para acelerar documentacao clinica."

### 14 - Oswaldo prescricao (itens)

- **Arquivo:** `14_clinico_oswaldo_prescricao_itens.png`
- **Mostrar:** CID-10 e lista de medicamentos com posologia.
- **Legenda sugerida:** "Elaboracao de prescricao com apoio de sugestao IA."

### 15 - Historico de prescricoes

- **Arquivo:** `15_clinico_oswaldo_historico.png`
- **Mostrar:** cards de prescricoes salvas.
- **Legenda sugerida:** "Rastreabilidade de condutas no encontro."

### 16 - Exportacao PDF clinico

- **Arquivo:** `16_clinico_encounter_pdf.png`
- **Mostrar:** botao `PDF Clinico` ou `Exportar PDF`.
- **Legenda sugerida:** "Geracao de relatorio clinico para continuidade de cuidado."

### 17 - Jornadas clinico (minhas jornadas)

- **Arquivo:** `17_clinico_careplanner_minhas-jornadas.png`
- **Mostrar:** switch de filtro `Minhas Jornadas`.
- **Legenda sugerida:** "Acompanhamento das jornadas sob responsabilidade do clinico."

## 9.4 Paciente (PacienteUI)

### 18 - Painel inicial

- **Arquivo:** `18_paciente_painel_inicial.png`
- **Mostrar:** proxima consulta, total futuro e historico.
- **Legenda sugerida:** "Resumo pessoal de acompanhamento em um unico painel."

### 19 - Agenda do paciente

- **Arquivo:** `19_paciente_agenda_consultas.png`
- **Mostrar:** compromissos futuros.
- **Legenda sugerida:** "Organizacao das consultas planejadas."

### 20 - Minhas jornadas

- **Arquivo:** `20_paciente_jornadas_tabela.png`
- **Mostrar:** colunas canal, status, abertura e fechamento.
- **Legenda sugerida:** "Transparencia das comunicacoes do cuidado."

### 21 - Historico clinico

- **Arquivo:** `21_paciente_historico_timeline.png`
- **Mostrar:** timeline com profissional e resumo.
- **Legenda sugerida:** "Linha do tempo com informacoes compartilhaveis da consulta."

### 22 - Meus dados/contato

- **Arquivo:** `22_paciente_cadastro_contato.png`
- **Mostrar:** dados cadastrais e canal de contato.
- **Legenda sugerida:** "Atualizacao cadastral e orientacao de comunicacao com a unidade."

## 9.5 Novos prints — Sprint 2026-04-25

### 23 - Clinico Linha do Tempo

- **Arquivo:** `23_clinico_paciente_linha-do-tempo.png`
- **Mostrar:** aba Linha do Tempo aberta com eventos mistos (consulta, nota, prescricao, tarefa).
- **Legenda sugerida:** "Visao longitudinal unificada do historico clinico do paciente."

### 24 - Clinico Imprimir Receituario

- **Arquivo:** `24_clinico_oswaldo_imprimir-receituario.png`
- **Mostrar:** historico de prescricoes com acao `Imprimir Receituário`.
- **Legenda sugerida:** "Emissao de receituario digital CFM/ANVISA a partir da prescricao registrada."

### 25 - Admin Prompts IA

- **Arquivo:** `25_admin_prompts-ia_editor-versoes.png`
- **Mostrar:** listagem de prompts, editor aberto e historico de versoes com acao de ativacao.
- **Legenda sugerida:** "Gestao de prompts clinicos com versionamento e rollback sem redeploy."
