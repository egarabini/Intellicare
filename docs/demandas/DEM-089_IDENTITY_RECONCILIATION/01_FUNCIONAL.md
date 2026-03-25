# DEM-089 — Identity Reconciliation + Admin View

## Contexto

As DEMs 084 e 088 garantem que **novos** pacientes e profissionais cadastrados a partir da sprint 2026-05-16 recebam `pessoa_id` automaticamente. Porém, todos os registros **anteriores** têm `pessoa_id = NULL` — mesmo aqueles que já tinham CPF preenchido antes da migration 022/024.

Esta DEM resolve dois problemas complementares:

1. **Reconciliação em batch** — processar pacientes (e profissionais) existentes com CPF preenchido e vincular `pessoa_id` retroativamente.
2. **Admin View** — página no AdminUI para o platform-admin visualizar e monitorar o estado da identidade centralizada: quantas pessoas na `platform.pessoa_fisica`, quantos vínculos por tenant, percentual de cobertura (com vs sem `pessoa_id`).

## O que esta DEM entrega

### Reconciliação

- Endpoint protegido `POST /admin/identity/reconcile?scope=patients` e `scope=professionals`
- Processa em batch: itera sobre registros com CPF não-null e `pessoa_id` IS NULL, chama `find_or_create_by_cpf()` para cada um
- Idempotente: pode ser executado múltiplas vezes sem efeito colateral
- Retorna relatório: `{ "processed": N, "linked": N, "skipped": N, "errors": [] }`

### Admin View

- Nova página `IdentityPage` no AdminUI (`/admin-ui/identity`)
- Mostra: total de `platform.pessoa_fisica`, vínculos por tenant (pacientes + profissionais), cobertura %
- Botão "Reconciliar" que dispara o endpoint acima com confirmação modal

## Critério de aceite

```
POST /admin/identity/reconcile?scope=patients
Authorization: Bearer <platform-admin>
→ { "processed": N, "linked": N, "skipped": 0, "errors": [] }

GET /admin/identity/stats
→ { "total_pessoas": N, "tenants": [{ "slug": "alfa", "patients_linked": N, "patients_total": N }] }
```

Página AdminUI carrega sem erro e exibe stats reais do banco.
