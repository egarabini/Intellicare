# DEM-029 — Agendamento de Consultas — Especificação Técnica

## 1. Escopo de alterações

Esta DEM não cria novos endpoints — trabalha sobre os endpoints de agendamento já existentes em `/cuidado/appointments`. As alterações são de robustez no backend e de UX/estado nos dois frontends.

---

## 2. Backend — `modules/cuidado/`

### `service.py`

**Método `get_patient_appointments()`:**
```python
# Resolução do paciente com fallback duplo:
# 1. Busca por user_id (keycloak_id)
# 2. Se não encontrar, busca por e-mail (para tenants com schema legado)
# 3. Tenta full_name, fallback para name (compatibilidade com migration antiga)

# Resolução do clínico responsável:
# JOIN com tenant_users por professional_id para obter o nome
```

**Método `confirm_appointment()` / `cancel_appointment()`:**
```python
# Antes: retornava 500 se appointment não existia
# Depois: SELECT antes do UPDATE, lança HTTPException(404) se não encontrado
#         ou se appointment.patient_id != patient_id do usuário logado
```

### `router.py`

Nenhum endpoint novo. Correções nos handlers existentes:
- `PATCH /cuidado/appointments/{id}/confirm`
- `PATCH /cuidado/appointments/{id}/cancel`

Ambos passam a propagar o 404 do service corretamente.

---

## 3. Frontend — ClinicoUI

### `src/hooks/useMyAgenda.ts`

```ts
// Adicionado: polling periódico (30s) via setInterval
// Adicionado: filtro por status no hook (parâmetro opcional)
// Corrigido: formatação de data via toLocaleDateString() em vez de toISOString().slice(0,10)
//            (evita desvio de -1 dia em fusos UTC-3)
```

### `src/pages/Agenda.tsx`

```tsx
// Adicionado: <Select> para filtro por status (todos / scheduled / confirmed / cancelled / in_progress)
// Adicionado: resumo de totais por status no topo da lista
// Adicionado: auto-refresh via hook atualizado
```

---

## 4. Frontend — PacienteUI

### `src/hooks/usePaciente.ts`

```ts
// Adicionado: campo clinico_nome na resposta de appointments
// Adicionado: polling periódico (60s)
// Corrigido: tratamento de erro 404 em confirm/cancel (exibe mensagem ao usuário)
```

### `src/pages/AgendaPage.tsx`

```tsx
// Adicionado: exibição do nome do profissional em cada consulta
// Adicionado: invalidate/refetch após confirmar ou cancelar
// Adicionado: feedback visual de loading durante ação
```

### `src/pages/PainelPage.tsx`

```tsx
// Corrigido: painel de "próximas consultas" atualiza após confirm/cancel
// Adicionado: polling periódico (60s) no painel
```

---

## 5. Testes — `packages/intellicare-core/tests/test_cuidado_portal.py`

```python
# test_get_appointments_fallback_email    — resolve paciente por e-mail quando user_id não existe
# test_confirm_appointment_not_found      — confirm retorna 404 para appointment inexistente
# test_cancel_appointment_wrong_patient   — cancel retorna 404 para appointment de outro paciente
```

Execução: `pytest tests/test_cuidado_portal.py -q` → 3 passed

---

## 6. Statics gerados

```
packages/intellicare-core/intellicare_core/static/
├── clinico-ui/
│   ├── index.html          (atualizado)
│   └── assets/index-hKhvesH7.js  (novo bundle)
└── paciente-ui/
    ├── index.html          (atualizado)
    └── assets/index-DcsDlz46.js  (novo bundle)
```

Bundles anteriores removidos automaticamente pelo `emptyOutDir: true` do Vite.

---

## 7. Checklist de entrega

- [x] `service.py`: fallback full_name/name + fallback user_id/e-mail
- [x] `service.py`: confirm/cancel retornam 404 coerente
- [x] `router.py`: propaga 404 do service
- [x] `useMyAgenda.ts`: polling + filtro por status + data local
- [x] `Agenda.tsx`: filtro de status + resumo de totais
- [x] `usePaciente.ts`: nome do clínico + polling + tratamento 404
- [x] `AgendaPage.tsx`: exibe profissional + refresh após ação
- [x] `PainelPage.tsx`: atualiza após confirm/cancel + polling
- [x] `test_cuidado_portal.py`: 3 testes passando
- [x] Build ClinicoUI: ok
- [x] Build PacienteUI: ok
