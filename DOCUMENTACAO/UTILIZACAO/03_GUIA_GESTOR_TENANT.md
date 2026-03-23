# 3. Guia do Gestor do Tenant (GestorUI)

## Menu principal relevante

- `Dashboard`
- `CarePlanner`
- `Pacientes`
- `Agenda/Consultas`
- `Equipe`
- `Unidades`
- `Usuarios do Tenant`
- `Relatorios`
- `Financeiro`
- `Configuracoes`

## 3.1 Dashboard do tenant

### Indicadores principais

- Pacientes ativos
- Consultas hoje/semana/mes
- Faturas pendentes (R$)
- Documentos RAG
- Unidades ativas
- Profissionais alocados
- Atividades recentes

### Exemplo de leitura de dashboard

- Pacientes ativos: `1.240`
- Consultas hoje: `86`
- Consultas semana: `402`
- Faturas pendentes: `R$ 18.230,00`

Acao sugerida: se consultas sobem e equipe nao sobe, revisar alocacao de profissionais.

## 3.2 CarePlanner - Operacao de jornadas

### O que esta disponivel

- Cards por status (`CREATED`, `DISPATCHED`, `SENT`, `REPLIED`, `CLOSED`, `FAILED`, `EXPIRED`)
- Filtro por status
- Lista paginada de jornadas
- Abertura de detalhe por jornada
- Acao `Nova Jornada`

### Tela "Nova Jornada" - campos e preenchimento

- `Referência do Paciente` (obrigatorio)  
  Exemplo: `53f3b4e1-7f91-4f09-8d58-4ef6c5fe99f0`
- `Tipo de Jornada` (obrigatorio)  
  Opcoes: `ADESAO`, `MONITORAMENTO`, `CHECK_IN`, `TELECONSULTA`
- `Canal de Comunicação` (obrigatorio)  
  Opcoes: Rocket.Chat, WhatsApp, SMS, E-mail
- `Template de Mensagem` (opcional)
- `Telefone (E.164)` (obrigatorio para WhatsApp/SMS)  
  Exemplo: `+5511999999999`
- `E-mail do paciente` (obrigatorio para canal E-mail)  
  Exemplo: `paciente@email.com`
- `Incluir videoconsulta` (opcional)
- `Referência do Clínico` (obrigatorio se videoconsulta ativa)
- `Agendamento vinculado` (opcional, UUID)

### Resultado esperado apos iniciar

- Mensagem de sucesso com `execution_id`.
- Jornada entra na lista com status inicial.
- Evolucao de status conforme canal e resposta do paciente.

## 3.3 Templates de mensagem

- Gestor pode trabalhar com templates ativos por canal.
- Recomendado manter linguagem objetiva e humana.
- Usar placeholders apenas quando validados pelo fluxo vigente.

## 3.4 Pacientes, unidades e equipe

### Operacoes usuais

- Consultar pacientes e abrir detalhe.
- Manter unidades ativas e dados de unidade.
- Manter profissionais e usuarios do tenant.

### Boa pratica

- Vincular jornada ao agendamento quando possivel para rastreabilidade.

## 3.5 Exemplo de rotina diaria do Gestor

1. Abrir dashboard e revisar consultas do dia.
2. Verificar cards do CarePlanner (foco em `FAILED` e `EXPIRED`).
3. Disparar novas jornadas para faltosos/monitoramento.
4. Revisar equipe e capacidade por unidade.
5. Exportar relatorios necessarios para coordinacao.

## 3.6 Notificacoes push (DEM-066)

### Onde ativar

- No sino de notificacoes (`NotificationBell`), no canto superior da interface.
- Usar o toggle de push para `Ativar notificações push` ou `Desativar notificações push`.

### Comportamento esperado

- Com push ativo, o navegador recebe notificacoes mesmo fora da aba ativa.
- Ao clicar na notificacao, o Gestor e direcionado para a tela relacionada (ex.: detalhe de jornada CarePlanner).

### Checklist rapido

- Permitir notificacoes no navegador.
- Confirmar que o toggle ficou habilitado.
- Fazer um evento de teste e validar recebimento.
