---
dem: DEM-007
titulo: Módulo Financeiro — Implementação
tipo: IMPLEMENTACAO
status: concluído
criado: 2026-03-13
---

# DEM-007 · 03 — Implementação

## Arquivos Criados

| Arquivo | Papel |
|---------|-------|
| `db/platform_migrations/002_financeiro_tables.sql` | DDL: `public.plans`, `public.contracts`, `public.invoices` + índices |
| `modules/financeiro/__init__.py` | Marcador de pacote |
| `modules/financeiro/schemas.py` | 7 Pydantic models (PlanCreate, PlanResponse, ContractCreate, ContractResponse, InvoiceResponse, BillingReport) |
| `modules/financeiro/service.py` | `FinanceiroService` — CRUD planos, contratos, faturas, relatório, job inadimplência |
| `modules/financeiro/router.py` | `APIRouter(/financeiro)` — 8 endpoints |
| `modules/financeiro/scheduler.py` | APScheduler — job diário às 03:00 (mark_overdue_and_suspend) |
| `modules/financeiro/main.py` | `Module(BaseModule)` — contrato obrigatório |
| `tests/financeiro/__init__.py` | Pacote de testes |
| `tests/financeiro/test_financeiro_service.py` | 9 testes unitários — todos passando |

## Endpoints

| Método | Rota | Função |
|--------|------|--------|
| GET | `/financeiro/health` | Health check |
| GET | `/financeiro/plans` | Listar planos ativos |
| POST | `/financeiro/plans` | Criar plano |
| POST | `/financeiro/contracts` | Criar contrato + primeira fatura |
| GET | `/financeiro/contracts/{id}/invoices` | Listar faturas do contrato |
| PATCH | `/financeiro/invoices/{id}/pay` | Marcar fatura como paga |
| GET | `/financeiro/reports/billing` | Relatório de faturamento por período |

## Lógica de Negócio

- **Criação de contrato**: ao criar, gera automaticamente a primeira fatura com `due_date = start_date + 30d`
- **Pagamento**: marca `status = 'paid'` e registra `paid_at = now()`
- **Job de inadimplência** (diário às 03:00):
  1. Marca faturas com `due_date < hoje` como `overdue`
  2. Identifica tenants com fatura `overdue` há > 30 dias
  3. Atualiza `public.tenants.status = 'suspended'`

## Testes

```
tests/financeiro/test_financeiro_service.py — 9 passed
  ✓ test_plan_price_negativo
  ✓ test_plan_cycle_invalido
  ✓ test_plan_criacao_valida
  ✓ test_plan_defaults
  ✓ test_plan_price_zero_valido
  ✓ test_contract_create_schema
  ✓ test_contract_create_with_specific_date
  ✓ test_billing_report_schema
  ✓ test_plan_cycle_annual
```

## Dependências

- `intellicare-core` (DEM-003): `BaseModule`, `TenantContext`, `require_role`, `get_engine`
- `public.tenants` (DEM-005): FK em `contracts.tenant_slug`
- `python-dateutil`: `relativedelta` para cálculo de período
- `APScheduler`: job de inadimplência

## Decisões

- Tabelas no schema `public` (não tenant-specific) — financeiro é gestão global da plataforma
- Preços em centavos (INTEGER) — evita problemas de arredondamento com float
- Job conta `rowcount` para evitar log falso de suspensão quando tenant já está suspenso

