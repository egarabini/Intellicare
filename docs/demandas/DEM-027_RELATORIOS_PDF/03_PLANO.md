# DEM-027 — Relatórios PDF — Plano de Execução

Este arquivo contém as etapas planejadas para implementação da demanda DEM-027, em resposta aos documentos 01_FUNCIONAL e 02_TECNICA.

## 1. Configuração de Infraestrutura e Core
- Atualizar o `deploy/Dockerfile` (ou similar) no estágio Python, adicionando as bibliotecas apt: `libpango-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz0b`, `libfontconfig1`.
- Adicionar `weasyprint` no `pyproject.toml` do `packages/intellicare-core`.

## 2. Motor de Renderização (Core)
- Criar `packages/intellicare-core/intellicare_core/pdf/__init__.py`.
- Criar `packages/intellicare-core/intellicare_core/pdf/renderer.py` com a configuração do `Jinja2` e a função `render_pdf()`.
- Criar a estrutura `packages/intellicare-core/intellicare_core/pdf/templates/`.
- Criar `base.html` contendo os estilos `@page` de paginação, cabeçalho e rodapé.

## 3. Desenvolvimento dos Templates e Endpoints (Backend)
- **Admin**:
  - `admin_receita.html` e endpoint `GET /admin/relatorios/receita?mes=`
  - `admin_tenants.html` e endpoint `GET /admin/relatorios/tenants`
- **Gestor**:
  - `gestor_consultas.html` e endpoint `GET /gestor/relatorios/consultas`
  - `gestor_profissionais.html` e endpoint `GET /gestor/relatorios/profissionais/{unit_id}`
- **Cuidado (Clínico)**:
  - `clinico_prontuario.html` e endpoint `GET /cuidado/relatorios/prontuario/{patient_id}`
  - `clinico_agenda.html` e endpoint `GET /cuidado/relatorios/agenda?data=`

## 4. Frontend Hooks e Interface
- Criar uma abstração de utilitário/hook genérico `downloadPdf` para lidar com a requisição e Blob do PDF.
- Implementar os botões de Download em:
  - Admin: Financeiro (Receita Mensal) e Dashboard (Lista de Tenants)
  - Gestor: Tela nova de relatórios e UnitsPage (Profissionais da Unidade)
  - Cuidado (ClinicoUI): PatientProfile e Agenda.

## 5. Testes e Validação Front / Back
- Validar se o comportamento retorna mensagens adequadas em "Tabelas Vazias".
- Validar no Browser o download via hook (Blob).
- Implementar unit-tests nos routers.
