---
tipo: funcional
demanda: DEM-084
titulo: Patient Identity Integration
status: planejada
dev: DEV-2
sprint: 2026-05-16
criado: 2026-03-23
---

# DEM-084 — Funcional: Patient Identity Integration

## Objetivo

Integrar o cadastro de pacientes com o identity service criado na DEM-083. A partir desta DEM, todo novo paciente registrado no sistema terá um `pessoa_id` linkado a `platform.pessoa_fisica`. Pacientes existentes não são afetados (migração gradual).

---

## Problema resolvido

Hoje, `POST /cuidado/patients` cria um registro em `{schema}.paciente` com dados de identidade (nome, CPF, e-mail, telefone) diretamente no schema do tenant. O mesmo paciente em outro estabelecimento terá um segundo registro independente. Esta DEM corrige isso: o identity service é consultado primeiro, garantindo que a identidade seja única no sistema.

---

## O que será entregue

### Backend — `POST /cuidado/patients` integrado

Fluxo novo:
1. Receber CPF do payload
2. Chamar `identity_service.find_or_create_by_cpf(cpf, nome)` → retorna `pessoa_id`
3. Criar `{schema}.paciente` com `pessoa_id` preenchido
4. Registrar vínculo em `platform.pessoa_estabelecimento` (tenant_slug + pessoa_id)

### Migration tenant — `pessoa_id` em `paciente`

```sql
ALTER TABLE {schema}.paciente
ADD COLUMN IF NOT EXISTS pessoa_id UUID;
-- nullable: registros existentes não têm pessoa_id ainda
```

### `GET /cuidado/patients/{id}` — dados canônicos

Quando o paciente tem `pessoa_id`, retornar nome/CPF/contatos de `platform.pessoa_fisica` em vez dos campos locais (que passam a ser cache). Quando não tem (registro legado), comportamento atual mantido.

### Portal do Paciente — `GET /me/profile`

Retornar dados canônicos de `platform.pessoa_fisica` quando disponível. Se não (legado), retornar dados do tenant como hoje.

---

## Critérios de aceite

- [ ] `POST /cuidado/patients` com CPF cria `platform.pessoa` e preenche `pessoa_id`
- [ ] `POST /cuidado/patients` com CPF já existente em outro tenant reutiliza o mesmo `pessoa_id` (não duplica)
- [ ] Registro em `platform.pessoa_estabelecimento` criado ao vincular paciente a tenant
- [ ] `GET /cuidado/patients/{id}` retorna `pessoa_id` no response quando preenchido
- [ ] Pacientes legados (sem `pessoa_id`) continuam funcionando sem erro
- [ ] Timeline, prescrições, notas Florence — zero regressões
- [ ] Portal do Paciente `/me/profile` retorna `pessoa_id` quando disponível
- [ ] 6+ testes cobrindo os cenários acima

---

## Fora de escopo

- Migração de pacientes existentes para `platform.pessoa` — sprint futura
- Frontend de edição de dados canônicos — sprint futura
- Profissionais — DEM-085 (sprint seguinte)
