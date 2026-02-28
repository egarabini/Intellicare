# F5 — Especificação Funcional: Billing + Auditoria Global

> **Fase:** 5 | **Prioridade:** P2  
> **Depende de:** F1 (intellicare-admin — deve existir para receber billing)  
> **Pode rodar em paralelo com:** F2, F3, F4  
> **Estimativa:** 10 dias | **Módulos:** `intellicare-admin` (expandir), novo serviço de billing

---

## 1. Objetivo

Implementar o sistema de billing (cobrança) e auditoria global para a plataforma multi-tenant. Inclui cálculo automático de uso, geração de faturas, alertas de limite e auditoria cross-tenant.

---

## 2. Requisitos Funcionais

### RF-F5-001: Coleta de Métricas de Uso

**Regras:**
1. Cada módulo reporta métricas de uso ao final de cada request (via Redis pub/sub)
2. Métricas coletadas: requests por módulo, SMS enviados, emails enviados, storage usado
3. Agregação por tenant, por dia
4. Dados armazenados em `platform.usage_metrics`

### RF-F5-002: Cálculo de Billing Mensal

**Regras:**
1. No dia 1 de cada mês (ou sob demanda), gerar `BillingRecord` para cada tenant ativo
2. Valor = preço do plano + excedentes (se houver)
3. Excedentes: SMS acima do limite → R$ 0,15/unidade; Usuários acima → R$ 29,90/unidade
4. Tenant com plano `trial` → R$ 0,00 (gratuito durante trial)
5. Fatura gerada com `payment_status = "pending"`

### RF-F5-003: Controle de Pagamento

**Regras:**
1. Webhook de gateway de pagamento atualiza `payment_status` para `paid`
2. Se `pending` por mais de 5 dias → `overdue` + alerta ao super-admin
3. Se `overdue` por mais de 15 dias → tenant `suspended`
4. Super-admin pode dar `grace` (período de carência): não suspende por N dias adicionais
5. Reativação: pagamento confirmado → `status = active`

### RF-F5-004: Alertas de Limite

**Regras:**
1. Quando tenant atinge 80% do limite de SMS/mês → alerta ao admin-local
2. Quando tenant atinge 100% → bloquear envios + alerta
3. Quando plano trial expira em 7 dias → notificar admin-local
4. Quando trial expira → tenant status = `suspended`, mostrar tela de upgrade

### RF-F5-005: Auditoria Global

**Regras:**
1. Toda ação no `intellicare-admin` é logada em `platform.audit_global`
2. Toda impersonação é logada com detalhes completos
3. Pesquisável: por data, ator, ação, tenant alvo
4. Imutável (append-only, sem updates/deletes)
5. Retenção: mínimo 5 anos (LGPD)

### RF-F5-006: Relatórios

**Regras:**
1. Dashboard financeiro: receita total, inadimplência, crescimento
2. Relatório por tenant: histórico de usage, pagamentos
3. Exportação CSV/PDF

---

## 3. API Endpoints

| Método | Endpoint | Descrição | Persona |
|---|---|---|---|
| `GET` | `/admin/billing/summary` | Dashboard financeiro | Financeiro |
| `GET` | `/admin/billing/{tenant_id}` | Histórico de billing do tenant | Financeiro |
| `POST` | `/admin/billing/generate` | Gerar faturas do mês atual | Super-Admin |
| `PATCH` | `/admin/billing/{record_id}/status` | Atualizar status pagamento | Financeiro |
| `POST` | `/admin/billing/{record_id}/grace` | Conceder carência | Super-Admin |
| `GET` | `/admin/usage/{tenant_id}` | Métricas de uso do tenant | Super-Admin |
| `GET` | `/admin/audit` | Log de auditoria global | Super-Admin |
| `GET` | `/admin/audit/export` | Exportar auditoria (CSV) | Super-Admin |
| `GET` | `/admin/alerts` | Alertas ativos | Super-Admin |

---

## 4. Cenários de Teste

| # | Cenário | Saída Esperada |
|---|---|---|
| CT-01 | Gerar billing mensal | BillingRecord criado para cada tenant ativo |
| CT-02 | Tenant excede limite de SMS | Excedente calculado e cobrado |
| CT-03 | Fatura pendente > 15 dias | Tenant suspenso automaticamente |
| CT-04 | Pagamento confirmado | Status atualizado, tenant reativado |
| CT-05 | Trial expirando em 7 dias | Notificação enviada ao admin-local |
| CT-06 | Auditoria de impersonação | Log com ator, ação, tenant alvo, timestamp |
| CT-07 | Exportar relatório CSV | Arquivo gerado com dados corretos |
