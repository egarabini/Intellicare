# DEM-019 — Gestor Módulo Completo

## Objetivo

Completar o módulo Gestor com todas as funcionalidades operacionais que o
gestor de clínica precisa para o dia a dia: gestão de pacientes, agendamentos,
relatórios financeiros, upload de documentos RAG, controle de programas de
saúde e visão consolidada do tenant.

## Atores

| Ator | Papel |
|------|-------|
| TENANT_GESTOR | Usuário principal — acessa todas as telas |
| PLATFORM_ADMIN | Pode impersonar qualquer tenant (read-only) |

## Funcionalidades

### F01 — Dashboard do Gestor

Tela inicial após login com KPIs do tenant:

- Total de pacientes ativos
- Consultas hoje / semana / mês
- Faturas pendentes (valor total em aberto)
- Documentos RAG indexados
- Últimas 5 atividades do tenant (audit trail)

Atualização automática a cada 60 segundos.

### F02 — Gestão de Pacientes

Lista paginada de pacientes com busca por nome/CPF/e-mail.

Ações disponíveis:
- **Cadastrar** novo paciente (nome, CPF, data nascimento, e-mail, telefone, plano de saúde)
- **Editar** dados cadastrais
- **Desativar** paciente (soft delete — não remove histórico)
- **Ver perfil** — abre página de detalhe com histórico de consultas e programas

### F03 — Agendamentos

Calendário mensal/semanal com consultas do tenant.

- Criar agendamento: paciente + clínico + data/hora + tipo (consulta, retorno, exame)
- Editar / cancelar agendamento
- Visualização por clínico (filtro)
- Status: agendado → confirmado → realizado → cancelado

### F04 — Relatórios Financeiros

- Lista de faturas do tenant com filtros (período, status, paciente)
- Total faturado / total recebido / inadimplência (%)
- Exportar CSV
- Marcar fatura como paga manualmente

### F05 — Documentos RAG

- Upload de arquivos (PDF, DOCX, TXT) para indexação no módulo RAG
- Lista de documentos indexados (nome, data upload, status: processando/indexado/erro)
- Excluir documento (remove do índice vetorial)
- Progresso de indexação em tempo real via SSE

### F06 — Programas de Saúde

- Lista de programas ativos do tenant
- Criar novo programa (nome, descrição, critérios de elegibilidade)
- Ver pacientes inscritos em cada programa
- Inscrever / remover paciente de programa
- Relatório de cobertura (% de pacientes elegíveis inscritos)

### F07 — Equipe Clínica

- Lista de clínicos do tenant
- Convidar novo clínico (envia e-mail via Keycloak)
- Desativar clínico
- Ver agenda de cada clínico

### F08 — Configurações do Tenant

- Editar nome, CNPJ, telefone, endereço, logo
- Alterar plano (exibe planos disponíveis — apenas visualização, sem checkout)
- Ver limites de uso (pacientes, clínicos, storage RAG)

## Regras de Negócio

- **Isolamento**: gestor só vê dados do próprio tenant (schema `tenant_{slug}`)
- **Soft delete**: pacientes e clínicos desativados mantêm histórico intacto
- **CPF único por tenant**: não pode cadastrar o mesmo CPF duas vezes no mesmo tenant
- **Agenda sem conflito**: não permite dois agendamentos para o mesmo clínico no mesmo horário
- **Upload RAG**: limite de 50 MB por arquivo; formatos aceitos: PDF, DOCX, TXT, MD

## Critérios de Aceite

- [ ] Dashboard exibe KPIs reais do banco (não mock)
- [ ] Cadastro de paciente valida CPF e bloqueia duplicata no tenant
- [ ] Agendamento impede conflito de horário
- [ ] Upload RAG aciona pipeline de indexação e exibe progresso SSE
- [ ] Exportação CSV de faturas funciona no browser
- [ ] Todos os endpoints retornam 403 para usuários de outros tenants
