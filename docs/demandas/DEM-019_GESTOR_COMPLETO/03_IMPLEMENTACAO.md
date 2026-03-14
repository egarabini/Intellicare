# IMPLEMENTACAO.md — Gestor Módulo Completo

## Objetivo
Implementar o módulo Gestor (`modules/gestor`), englobando APIs, tabelas no PostgreSQL (com as migrações), lógica de negócios, e os componentes da interface do usuário (GestorUI).

## O que foi desenvolvido

### 1. Migrações e Banco de Dados (`modules/gestor/migrations.py` e `main.py`)
- Mapeamento e criação automática de tabelas `patients` e `appointments` em schemas isolados no PostgreSQL para cada tenant na inicialização (`startup`).
- Separação adequada dos componentes de negócio isolando permissões.
- UUID nativo implementado para chaves estrangeiras (`patient_id`, `clinician_id`).
- Constraint de unique no CPF nos pacientes (buscando prevenir conflitos de cadastro).

### 2. Endpoints e Contratos de Serviço
- **Pacientes**: Foram implementados os métodos listar com full-text-search, criar, obter, editar e dar baixa (soft delete `active = false`). Validações rigorosas de unicidade do CPF implementadas.
- **Consultas (Appointments)**: Funcionalidades completas de agendamento validando possíveis conflitos entre agendamentos sob a alçada de um mesmo clínico e mesma janela de horário (trazendo o isolamento exigido).
- **Dashboard**: Consumo instantâneo das totalizações via `dashboard_stats()`, reportando número de pacientes ativos, consultas (hoje, na semana e mês), contas a receber, e arquivos em RAG.
- **Documentos (RAG)**: Adaptada API para prover progressão SSE via `documents/progress` e consumir da nova base knowledge_base.
- **Faturamento (Invoices)**: Integração com endpoints que entregam uma listagem em CSV e oferecem atalho para processar `mark-paid`.
- **Programas de Saúde**: Contratos que expõem os mecanismos para agrupar pacientes monitorados via "Programas" com listagem e exportação do relatório de cobertura do status programático.

### 3. Aplicativo Frontend `GestorUI` (`frontend/GestorUI/`)
- Mapeados e configurados via `react-query` os custom hooks centralizados no gestor `useGestor.ts`.
- Construção das páginas e componentes em Mantine listados:
  - `Dashboard.tsx`: Visão rápida dos KPIs vitais de gestão de pacientes.
  - `PatientList.tsx` e `PatientProfile.tsx`: Interface detalhada de busca, gerenciamento e prontuários básicos.
  - `AppointmentCalendar.tsx`: Listagem com filtros para agendas clínicas.
  - `InvoiceList.tsx`: Fechamento e exportação de CSV em relação a faturas e a possibilidade de marcação monetária.
  - `ProgramList.tsx` e `ClinicianList.tsx`: Módulo de equipe interna para inclusão de clínicos e agrupamentos de tratamento prolongado em programas vigentes.
  - `RagDocuments.tsx`: Janela de suporte ao RAG e SSE Progress.
  - `TenantSettings.tsx`: Manutenção básica da unidade de saúde.
  
- O processo de build em `npm build` gera os pacotes diretamente no diretório `modules/gestor/static` seguindo o comportamento do vite.config customizado do monorepo.

### 4. Testes (`tests/test_gestor.py`)
- Adicionadas fixtures no `conftest.py` e simulações para suportar Tenant Context no Pydantic.
- Todos os endpoints passaram por cobertura exata de casos exigidos na especificação: Isolamento de tenant na listagem, Verificação de conflito de agenda na deleção, Multiplicidade impedida em CPF.

## Próximos Passos
O módulo base encontra-se estável para interações do usuário. Validações adicionais poderão englobar atualizações na UI de detalhes médicos dos perfis em versões incrementais.
