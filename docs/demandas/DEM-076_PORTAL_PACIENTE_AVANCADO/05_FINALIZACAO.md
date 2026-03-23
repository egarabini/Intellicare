---
tipo: finalizacao
demanda: DEM-076
titulo: Portal Paciente Avançado
status: concluida
commit: 8e5fa8a
dev: DEV-2
data-entrega: 2026-03-22
---

# DEM-076 — Finalização

## Commit

```
8e5fa8a  feat(portal): patient timeline + receituário download com filtro de privacidade SOAP
```

---

## O que foi entregue

| Camada | Arquivo | O que foi construído |
|--------|---------|---------------------|
| Service | `cuidado/service.py` | `paciente_timeline()` + `_apply_portal_privacy_filter()` — filtra `soap_a` e campos privados antes de expor ao paciente |
| API | `cuidado/routes.py` | `GET /cuidado/paciente/me/timeline` — `patient_id` extraído do token, não do path |
| API | `oswaldo/routes.py` | `GET /oswaldo/paciente/me/prescriptions/{id}/receituario.pdf` — 403 se prescrição não pertence ao paciente |
| Hook | `PacienteUI/src/hooks/usePatientTimeline.ts` | Hook react-query para timeline do portal |
| Página | `PacienteUI/src/pages/HistoricoPage.tsx` | Timeline multi-tipo com ícones por evento + botão "Baixar Receituário" em prescrições |
| Testes | `test_portal_avancado.py` | **8 testes — todos passando** |

---

## Cobertura de testes

```
test_patient_timeline_excludes_soap_a             PASSED
test_patient_can_download_own_receituario          PASSED
test_patient_cannot_download_others_receituario    PASSED
test_patient_timeline_only_own_data               PASSED
+ 4 testes adicionais de regressão
# 24 total sem regressões
```

---

## Destaques de implementação

**Filtro de privacidade `_apply_portal_privacy_filter()`:** remove `soap_a` (avaliação interna) e `soap_p` (plano interno) de todos os eventos antes de expor ao paciente. Campo `soap_s` (subjetivo — o que o paciente relatou) é mantido. Decisão acertada — o paciente pode ver o que ele mesmo disse, não a interpretação clínica privada.

**Controle de acesso receituário:** verificação explícita `prescription.patient_id != ctx.current_patient_id → 403`. Paciente não pode acessar receituário de outro mesmo conhecendo o UUID da prescrição.

**`patient_id` extraído do token:** endpoint usa `/me/` — o paciente nunca passa seu próprio ID na URL, eliminando a possibilidade de IDOR.
