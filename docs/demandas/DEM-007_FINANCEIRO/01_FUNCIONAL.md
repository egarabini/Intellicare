---
dem: DEM-007
titulo: Módulo Financeiro — Contratos e Faturamento
tipo: FUNCIONAL
status: aprovado
criado: 2026-03-13
dependencias: [DEM-005]
---

# DEM-007 · 01 — Especificação Funcional

## Contexto e Motivação

Com os tenants sendo provisionados pelo Admin Backend (DEM-005), o próximo passo é registrar
o **vínculo contratual**: qual plano cada tenant contratou, quando, e qual o ciclo de faturamento.
O módulo Financeiro é o responsável por esse ciclo, garantindo que a plataforma possa:

1. Saber quais tenants estão em dia (e bloquear os inadimplentes automaticamente)
2. Gerar sumários de faturamento por período
3. Registrar histórico de pagamentos

> **Foco de V3**: o módulo cobre o ciclo administrativo (contratos, faturas, status de
> pagamento). Integração com gateway de pagamento (Stripe, PagSeguro) é Fase 3 e está
> **fora de escopo** desta DEM.

## Escopo

### Incluído

- **CRUD de Planos**: planos de assinatura (nome, preço, limites de usuários/storage)
- **Contratos de Tenant**: associar tenant a plano, data de início, ciclo (mensal/anual)
- **Ciclo de faturamento**: geração mensal de faturas (status: `pending`, `paid`, `overdue`)
- **Marcar fatura como paga**: operação manual pelo PLATFORM_ADMIN (automação de gateway → Fase 3)
- **Bloqueio por inadimplência**: tenant com fatura `overdue` > 30 dias → status `suspended`
- **Relatório de faturamento**: total por período (mês/ano)

### Excluído

- Integração com gateway de pagamento → Fase 3
- Portal do cliente (gestor ver suas faturas) → DEM-010 (Gestor Frontend)
- Nota fiscal / NFS-e → fora de escopo V3

## Atores

| Ator | Permissões |
|---|---|
| `PLATFORM_ADMIN` | Todas as operações |
| `TENANT_GESTOR` | Apenas leitura das próprias faturas (via API do módulo gestor) |
| `CLINICO` / `PACIENTE` | Nenhuma |

## Modelo de Domínio

```
Plan ──< Contract >── Tenant
               │
               └──< Invoice
```

- Um **Plan** define preço e limites
- Um **Contract** vincula Tenant a Plan por um período
- Um **Invoice** é gerado mensalmente por Contract

## Casos de Uso

### UC-1: Criar Plano

**POST** `/financeiro/plans`  
Campos: `name`, `price_brl` (centavos), `max_users`, `max_storage_gb`, `cycle` (`monthly`|`annual`)

### UC-2: Criar Contrato

**POST** `/financeiro/contracts`  
Associa um tenant a um plano. Define `start_date` e gera a primeira fatura.

### UC-3: Listar Faturas de Tenant

**GET** `/financeiro/contracts/{contract_id}/invoices`  
Retorna histórico com status de cada fatura.

### UC-4: Marcar Fatura como Paga

**PATCH** `/financeiro/invoices/{invoice_id}/pay`  
Marca `paid_at = now()`, status `paid`.

### UC-5: Relatório de Faturamento

**GET** `/financeiro/reports/billing?year=2025&month=10`  
Retorna total faturado, total pago, total pendente no período.

### UC-6: Job de Verificação de Inadimplência

Executado diariamente (via APScheduler ou Celery Beat).  
Identifica faturas com `due_date < now() - 30 days` e `status = overdue`.  
Chama `TenantService.update_status(slug, "suspended")`.

## Critérios de Aceite

| # | Critério |
|---|---|
| AC-1 | POST `/financeiro/plans` cria plano e retorna 201 |
| AC-2 | POST `/financeiro/contracts` gera contrato + primeira fatura com `due_date = start_date + 30d` |
| AC-3 | GET `/financeiro/contracts/{id}/invoices` retorna faturas paginadas |
| AC-4 | PATCH `/financeiro/invoices/{id}/pay` muda status para `paid` e registra `paid_at` |
| AC-5 | Tenant com fatura overdue > 30 dias tem status alterado para `suspended` |
| AC-6 | GET `/financeiro/reports/billing` retorna totais corretos |
| AC-7 | Todas as rotas retornam 403 para não-PLATFORM_ADMIN |
| AC-8 | `/financeiro/health` retorna 200 healthy |

## Modelo de Dados (público — schema `public`)

```sql
-- Planos
CREATE TABLE public.plans (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        NOT NULL UNIQUE,
    price_brl   INTEGER     NOT NULL,      -- centavos
    max_users   INTEGER     NOT NULL DEFAULT 50,
    max_storage_gb INTEGER  NOT NULL DEFAULT 10,
    cycle       TEXT        NOT NULL DEFAULT 'monthly' CHECK (cycle IN ('monthly','annual')),
    active      BOOLEAN     NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Contratos
CREATE TABLE public.contracts (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_slug TEXT        NOT NULL REFERENCES public.tenants(slug),
    plan_id     UUID        NOT NULL REFERENCES public.plans(id),
    start_date  DATE        NOT NULL,
    end_date    DATE,
    status      TEXT        NOT NULL DEFAULT 'active' CHECK (status IN ('active','cancelled')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Faturas
CREATE TABLE public.invoices (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id  UUID        NOT NULL REFERENCES public.contracts(id),
    tenant_slug  TEXT        NOT NULL,
    amount_brl   INTEGER     NOT NULL,     -- centavos
    due_date     DATE        NOT NULL,
    paid_at      TIMESTAMPTZ,
    status       TEXT        NOT NULL DEFAULT 'pending'
                             CHECK (status IN ('pending','paid','overdue')),
    period_start DATE        NOT NULL,
    period_end   DATE        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_invoices_tenant   ON public.invoices (tenant_slug, due_date);
CREATE INDEX idx_invoices_status   ON public.invoices (status, due_date);
CREATE INDEX idx_contracts_tenant  ON public.contracts (tenant_slug);
```
