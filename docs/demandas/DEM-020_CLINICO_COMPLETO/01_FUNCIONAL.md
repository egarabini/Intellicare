# DEM-020 — Clínico Frontend Completo

## Objetivo

Completar o módulo Clínico transformando o MVP atual (2 páginas soltas, sem
navegação) em uma aplicação profissional completa para médicos, enfermeiros e
demais membros da equipe clínica do tenant.

O Clínico é o módulo de **uso mais frequente** da plataforma — é onde o
profissional passa o dia de trabalho. Precisa ser rápido, limpo e focado no
fluxo clínico, não administrativo.

## Diferença dos módulos vizinhos

| Módulo | Perfil | Foco |
|--------|--------|------|
| AdminUI | PLATFORM_ADMIN | Plataforma, tenants, billing |
| GestorUI | TENANT_GESTOR | Estabelecimento: financeiro, equipe, RAG, configurações |
| **ClinicoUI** | **CLINICO** | **Minha agenda, meus pacientes, SOAP, IA assistente** |

O Clínico **não gerencia** outros clínicos, não vê financeiro, não faz upload
RAG — essas funções são do Gestor. O Clínico só vê os dados do seu tenant e,
dentro disso, o contexto da sua prática clínica.

## Atores

| Ator | Papel |
|------|-------|
| CLINICO | Médico, enfermeiro, fisioterapeuta, etc. — usuário principal |
| TENANT_GESTOR | Pode acessar em modo read-only para auditoria (opcional) |

## Funcionalidades

### F01 — AppShell com navegação

Shell da aplicação com sidebar lateral (Mantine AppShell):

**Menu lateral:**
- 🏠 Início (Minha Agenda Hoje)
- 📅 Agenda
- 👤 Pacientes
- 📋 Encontros Recentes
- 🤖 Assistente IA
- ⚙️ Meu Perfil

Header: nome do clínico logado + badge do tenant + botão logout.

Role guard na entrada: verifica `realm_access.roles` inclui `CLINICO`.
Se não tiver a role → redireciona para `/unauthorized`.

### F02 — Dashboard (Minha Agenda Hoje)

Tela inicial após login. Responde à pergunta: "O que tenho hoje?"

- Lista dos agendamentos do dia (paciente + horário + tipo + status)
- Contador de pendências: consultas abertas sem nota fechada
- Últimas 3 notificações
- Botão rápido "Iniciar Atendimento" em cada item da agenda

Dados via: `GET /cuidado/my-agenda?date=2026-03-14`

### F03 — Agenda (Calendário)

Calendário semanal/mensal dos agendamentos do clínico logado.

- Visualização semana (padrão) e mês
- Cada evento: paciente + tipo + status (badge colorido)
- Click no evento → abre diretamente o EncounterView do paciente
- Filtro por tipo de consulta (consulta, retorno, exame)

Dados via: `GET /cuidado/my-agenda?from=...&to=...`

### F04 — Lista de Pacientes (aprimorada)

Evolução da `PatientList` atual:

- Busca por nome/CPF com debounce 400ms (já existe — manter)
- Adicionar: data de nascimento, última consulta, badge de programas ativos
- Ação rápida: "Novo Atendimento" em cada linha
- Paginação (20 por página)
- Ao clicar: abre Perfil Clínico do Paciente (F05)

### F05 — Perfil Clínico do Paciente (novo)

Página dedicada por paciente — substitui o acesso direto ao EncounterView.

Layout em abas (Mantine Tabs):

**Aba 1 — Resumo**
- Dados cadastrais (nome, CPF, data nasc., plano de saúde, contato)
- Alergias e alertas (campo livre editável)
- Medicações em uso (lista editável)
- Programas de saúde em que está inscrito

**Aba 2 — Atendimentos**
- Histórico de encontros (data, clínico, notas SOAP resumidas)
- Botão "Novo Atendimento" → abre EncounterView

**Aba 3 — Documentos**
- Documentos RAG vinculados ao paciente (read-only — upload é papel do Gestor)

### F06 — EncounterView (aprimorado)

Evolução do componente atual (manter SOAP + SLM Assistant):

- Adicionar breadcrumb: Pacientes > [Nome] > Atendimento #123
- Adicionar CID-10 lookup: campo de busca → autocomplete → salva no encontro
- Adicionar campo "Prescrição" (texto livre, abaixo do SOAP)
- Ao fechar encontro: pede confirmação com resumo do que será salvo
- Histórico de notas do encontro exibido abaixo (já parcialmente implementado)

### F07 — Assistente IA (página dedicada)

Evolução do SLMAssistant existente como página própria (além do painel no EncounterView):

- Input de texto livre para consultas sem contexto de paciente
- Histórico da conversa na sessão (em memória, sem localStorage)
- Sugestões rápidas: "Diagnóstico diferencial", "Protocolo de tratamento", "Resumo clínico"
- Indicador do modelo SLM ativo (ex: llama3.2:1b)

### F08 — Meu Perfil

- Nome, especialidade, CRM/COREN (editável)
- E-mail (read-only — gerenciado pelo Keycloak)
- Preferências: tema claro/escuro, idioma (pt-BR fixo por ora)

## Critérios de Aceite

- [ ] AppShell renderiza em todas as páginas com menu ativo correto
- [ ] Role guard bloqueia acesso sem role `CLINICO`
- [ ] Dashboard lista agendamentos do dia corretamente
- [ ] PatientList busca e pagina corretamente
- [ ] Perfil do Paciente carrega dados do paciente + histórico de encontros
- [ ] EncounterView mantém funcionalidade existente (SOAP + SLM)
- [ ] Assistente IA funciona standalone sem contexto de encontro
- [ ] Build sem erros TypeScript: `npm run build`
- [ ] Build copiado para `static/clinico-ui/`
