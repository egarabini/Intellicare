---
tipo: funcional
demanda: DEM-083
titulo: ADR-004 + Identity Foundation
status: planejada
dev: CODEX
sprint: 2026-05-16
criado: 2026-03-23
---

# DEM-083 — Funcional: ADR-004 + Identity Foundation

## Objetivo

Estabelecer formalmente a decisão arquitetural de centralização de identidade (ADR-004) e implementar a fundação técnica: tabelas de identidade no schema `platform`, módulo `identity` com endpoints de lookup e find-or-create por CPF.

Esta DEM não migra dados existentes e não quebra nenhuma funcionalidade atual. Ela cria a infraestrutura que as DEMs seguintes irão consumir.

---

## Problema resolvido

Atualmente, o mesmo paciente físico (mesmo CPF) pode existir como N registros distintos em N schemas de tenant diferentes. Quando atualiza seu telefone em uma clínica, as outras não sabem. Quando exerce o direito ao esquecimento (LGPD), é preciso varrer todos os schemas. Quando o sistema crescer para centenas de estabelecimentos, esse problema se multiplica.

---

## O que será entregue

### ADR-004
Documento formal em `docs/adr/ADR-004-identity-centralization.md` registrando:
- O problema de identidade distribuída
- A decisão: `platform.pessoa` como Single Source of Truth
- As alternativas consideradas e os motivos de descarte
- As consequências e o plano de migração gradual

### Migration 021 — `platform.pessoa*`
Cinco tabelas novas no schema `platform` (que já existe):

- `platform.pessoa` — entidade base (UUID, tipo FISICA/JURIDICA)
- `platform.pessoa_fisica` — CPF, nome completo, data de nascimento, gênero
- `platform.pessoa_juridica` — CNPJ, razão social, nome fantasia
- `platform.pessoa_contato` — telefones, e-mails e endereços unificados em uma tabela com `tipo_contato`
- `platform.pessoa_estabelecimento` — vínculo pessoa ↔ tenant_slug (tabela de consentimento LGPD)

### Módulo `identity`
Novo módulo `modules/identity/` com:
- `GET /identity/pessoas/cpf/{cpf}` — busca pessoa por CPF (retorna 404 se não existir)
- `POST /identity/pessoas` — find-or-create por CPF (idempotente)
- `GET /identity/pessoas/{id}` — busca por UUID

---

## Critérios de aceite

- [ ] ADR-004 escrito e coerente com ADR-001 e ADR-002 existentes
- [ ] Migration 021 aplica sem erro em banco limpo e em banco com dados existentes
- [ ] `POST /identity/pessoas` com mesmo CPF duas vezes retorna o mesmo UUID (idempotência)
- [ ] `GET /identity/pessoas/cpf/00000000000` retorna 404 (CPF inexistente)
- [ ] `GET /identity/pessoas/{id}` retorna dados completos de `pessoa_fisica`
- [ ] 6+ testes cobrindo os cenários acima
- [ ] Zero impacto em testes existentes (a migration é aditiva, não modifica tabelas existentes)

---

## Fora de escopo desta DEM

- Migração de dados existentes dos tenants para `platform.pessoa`
- Integração com `paciente` ou `professionals` — isso é DEM-084 e DEM-085
- Frontend — sem UI nesta DEM
