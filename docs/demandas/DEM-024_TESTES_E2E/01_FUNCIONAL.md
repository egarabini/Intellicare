# DEM-024 — Testes E2E (Playwright)

## Objetivo

Garantir que os 4 frontends do IntelliCare V3 funcionam corretamente do ponto de vista do usuário final, cobrindo os fluxos críticos de autenticação, navegação e operações CRUD principais. Os testes devem rodar automaticamente no pipeline CI e bloquear merges se falharem.

---

## Escopo funcional

### Fluxos obrigatórios por módulo

**AdminUI (`/admin-ui/`)**
- Login com `platform-admin` / `Admin@2025!`
- Dashboard carrega com métricas (não zerado)
- Listagem de tenants visível
- Criar tenant → formulário → salvar → aparece na lista
- Logout

**GestorUI (`/gestor-ui/`)**
- Login com `gestor.alfa` / `Demo@1234`
- Dashboard carrega com dados do tenant
- Listagem de pacientes visível
- Navegação entre: Dashboard → Pacientes → Documentos → Relatórios
- Logout

**ClinicoUI (`/clinico-ui/`)**
- Login com `dr.silva` / `Demo@1234`
- Dashboard carrega (agenda do dia visível)
- Listagem de pacientes
- Abrir prontuário de paciente → aba Encontros → visualizar encontro
- AI Assistant — campo de input visível
- Logout

**PacienteUI (`/paciente-ui/`)**
- Login com `paciente.alfa` / `Demo@1234`
- Painel do paciente carrega
- Navegação entre: Painel → Agenda → Histórico → Programas → Cadastro → Contato
- Logout

---

## Critérios de aceitação

1. Todos os testes passam no ambiente local com Docker Compose rodando
2. Tempo total da suíte < 5 minutos
3. Screenshots de falha são capturados automaticamente
4. Relatório HTML gerado após cada execução
5. Testes são independentes (cada teste inicia limpo, sem depender do anterior)
6. Nenhum teste usa `waitForTimeout` fixo — usar `waitForSelector` / `waitForResponse`
