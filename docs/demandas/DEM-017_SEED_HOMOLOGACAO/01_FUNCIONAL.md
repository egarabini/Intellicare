# DEM-017 — Seed de Dados e Homologação

## 1. Contexto e Motivação

O IntelliCare V3 está com todos os módulos implementados e testados unitariamente. Esta demanda tem dois objetivos complementares: popular o sistema com dados fictícios em volume realista para validar o comportamento em condições próximas à produção, e executar os ciclos completos de uso de ponta a ponta (onboarding de tenant, uso clínico, billing, suspensão, reativação).

---

## 2. Escopo

### Incluído

| Entregável | Detalhe |
|---|---|
| `tools/scripts/seed_demo.py` | Script de carga completa — idempotente, pode ser re-executado |
| `tools/scripts/reset_demo.py` | Script de limpeza — volta ao estado pré-seed |
| `docs/demandas/DEM-017/roteiro_homologacao.md` | Roteiro passo a passo dos ciclos de validação |
| `03_IMPLEMENTACAO.md` | Evidências de execução e resultados |

### Fora do Escopo

- Dados reais de pacientes
- Testes de carga automatizados (k6, locust) — fase futura
- Deploy em produção

---

## 3. Volume de Dados

### Plataforma (schema `public`)

| Entidade | Quantidade |
|---|---|
| Tenants | 3 (estados diferentes) |
| Planos | 3 (basic, pro, enterprise) |
| Contratos | 3 (um por tenant) |
| Faturas | 18 (6 meses × 3 tenants — pagas, pendentes, vencidas) |

### Por tenant (schema `tenant_{slug}`)

| Entidade | Quantidade |
|---|---|
| Usuários no Keycloak | 5 (1 gestor + 3 clínicos + 1 paciente) |
| Pacientes cadastrados | 50 |
| Programas de saúde | 3 (Hipertensão, Diabetes, Pré-natal) |
| Matrículas em programas | ~90 (80% dos pacientes em ≥1 programa) |
| Encontros clínicos | 200 (distribuídos nos últimos 90 dias) |
| Notas SOAP | 200 (uma por encontro) |
| Documentos RAG ingeridos | 5 PDFs fictícios (protocolos clínicos) |
| Consultas SLM logadas | 30 (simuladas no `slm_query_log`) |

---

## 4. Tenants de Demonstração

| Slug | Nome | Plano | Status | Objetivo do teste |
|---|---|---|---|---|
| `clinica-alfa` | Clínica Alfa Saúde | pro | active | Fluxo completo normal |
| `hospital-beta` | Hospital Beta | enterprise | active | Volume alto, múltiplos clínicos |
| `consultorio-gamma` | Consultório Gamma | basic | suspended | Validar bloqueio de acesso |

---

## 5. Usuários de Demonstração (por tenant)

| Username | Role | Senha | Tenant |
|---|---|---|---|
| `gestor.alfa` | TENANT_GESTOR | `Demo@1234` | clinica-alfa |
| `dr.silva` | CLINICO | `Demo@1234` | clinica-alfa |
| `dr.santos` | CLINICO | `Demo@1234` | clinica-alfa |
| `dr.oliveira` | CLINICO | `Demo@1234` | clinica-alfa |
| `paciente.alfa` | PACIENTE | `Demo@1234` | clinica-alfa |
| *(mesma estrutura para hospital-beta e consultorio-gamma)* | | | |

---

## 6. Ciclos de Homologação

### Ciclo 1 — Onboarding de Tenant
1. Login como `platform-admin` no Portal → AdminUI
2. Criar novo tenant `demo-homolog` via formulário
3. Verificar: schema `tenant_demo_homolog` criado no PostgreSQL
4. Verificar: grupo `demo-homolog` criado no Keycloak
5. Verificar: audit log registrado

### Ciclo 2 — Uso Clínico Completo
1. Login como `gestor.alfa` → GestorUI
2. Fazer upload de documento PDF → verificar ingestão RAG (chunks no pgvector)
3. Login como `dr.silva` → ClinicoUI
4. Buscar paciente → abrir encontro → escrever nota SOAP
5. Acionar assistente SLM → verificar resposta em PT-BR com fontes
6. Fechar encontro
7. Verificar log em `slm_query_log`

### Ciclo 3 — Programas de Saúde
1. Login como `gestor.alfa` → verificar cobertura dos 3 programas
2. Verificar pacientes com overdue > 30 dias (deve haver ~20% do total)
3. Login como `dr.silva` → matricular paciente em programa
4. Verificar cobertura atualizada

### Ciclo 4 — Billing e Inadimplência
1. Verificar faturas do tenant `clinica-alfa` (pagas e pendentes)
2. Executar manualmente o job de inadimplência: `POST /financeiro/jobs/overdue`
3. Verificar tenant com fatura vencida → status `suspended`
4. Marcar fatura como paga: `PATCH /financeiro/invoices/{id}/pay`
5. Reativar tenant: `PATCH /admin/tenants/{slug}/status`
6. Verificar acesso restaurado

### Ciclo 5 — Isolamento Multi-tenant
1. Login como `dr.silva` (clinica-alfa) → buscar pacientes
2. Confirmar que pacientes do `hospital-beta` não aparecem
3. Tentar acessar endpoint de `hospital-beta` com token de `clinica-alfa` → 403

### Ciclo 6 — Tenant Suspenso
1. Tentar login com `gestor.gamma` (consultorio-gamma — suspended)
2. Verificar bloqueio na camada de middleware
3. Verificar que o schema `tenant_consultorio_gamma` existe no PostgreSQL (dados preservados)

---

## 7. Critérios de Aceite

- [ ] Seed executa sem erros em ambiente com Docker rodando
- [ ] Re-execução do seed não duplica dados (idempotente)
- [ ] Reset limpa todos os dados de demo sem afetar estrutura
- [ ] Todos os 6 ciclos de homologação executados com sucesso
- [ ] Isolamento multi-tenant confirmado (Ciclo 5)
- [ ] SLM responde em PT-BR com latência < 300ms first token (Ciclo 2)
- [ ] Job de inadimplência suspende corretamente (Ciclo 4)
- [ ] `03_IMPLEMENTACAO.md` com evidências (prints de terminal / curl output)

---

## 8. Dependências

| DEM | Razão |
|---|---|
| DEM-002 | Stack Docker operacional |
| DEM-004 | Keycloak configurado com `setup_keycloak.py` |
| DEM-005 | Admin backend (criar tenants, migrations) |
| DEM-007 | Financeiro (planos, contratos, faturas) |
| DEM-008 | E2E suite (reutilizar fixtures de conftest.py) |
| DEM-009 | RAG pipeline (ingestão de documentos) |
| DEM-010 | SLM (respostas clínicas) |
| DEM-013 | Cuidado (pacientes, encontros) |
| DEM-014 | Programas (matrículas, cobertura) |
