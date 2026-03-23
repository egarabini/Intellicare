---
tipo: plano-execucao
demanda: DEM-076
titulo: Portal Paciente Avançado
status: em-execucao
dev: DEV-2
criado: 2026-03-22
---

# DEM-076 — Plano de Execução

## Estimativa

Tempo estimado: ~3.5h | Complexidade: média

Maior risco: filtro de privacidade — garantir que nenhum campo `soap_a` vaze para o portal. Testar explicitamente antes de mergear.

---

## Ordem de execução

### Bloco 1 — Backend timeline do portal (60min)
1. Em `cuidado/services.py`, criar `get_patient_timeline_for_portal(patient_id, ctx, limit, offset)`
   - Chama `clinical_timeline()` internamente
   - Passa resultado por `_apply_portal_privacy_filter()`
2. Em `cuidado/routes.py`, adicionar `GET /cuidado/paciente/me/timeline`
   - Extrai `patient_id` do token (`ctx.current_patient_id`), não do path
   - Retorna `ClinicalTimelineResponse` filtrado
3. Testar manualmente: `pytest test_portal_avancado.py::test_patient_timeline_excludes_soap_a`

### Bloco 2 — Backend receituário do paciente (30min)
4. Em `oswaldo/routes.py`, adicionar `GET /oswaldo/paciente/me/prescriptions/{id}/receituario.pdf`
5. Implementar verificação `prescription.patient_id != ctx.current_patient_id → 403`
6. Reutilizar `generate_receituario()` já existente (DEM-072) — sem duplicação
7. Testar: `test_patient_can_download_own_receituario` + `test_patient_cannot_download_others_receituario`

### Bloco 3 — Frontend HistoricoPage (60min)
8. Criar `usePatientTimeline.ts` com react-query chamando `GET /cuidado/paciente/me/timeline`
9. Atualizar `HistoricoPage.tsx`:
   - Substituir lista estática por `usePatientTimeline()`
   - Adicionar ícones por tipo de evento
   - Adicionar botão "Baixar Receituário" nos eventos `prescription`
   - Implementar "Carregar mais" (paginação por offset)
10. Verificar no browser: clique em "Baixar Receituário" abre PDF em nova aba

### Bloco 4 — Testes completos (30min)
11. Completar `test_portal_avancado.py` com os 4 testes
12. `pytest test_portal_avancado.py test_clinical_timeline.py -v` — sem regressões

---

## Gotcha — `patient_id` no token vs. no path

O endpoint `/cuidado/paciente/me/timeline` usa `me` no path — o `patient_id` deve ser extraído do JWT do paciente, não de um parâmetro de path. Isso garante que o paciente nunca pode consultar a timeline de outro passando um ID diferente na URL.

Verificar que o `get_patient_context()` dependency injeta corretamente o `current_patient_id` a partir do claim do token Keycloak.

---

## Gotcha — Reuso de `generate_receituario()` sem duplicação

O endpoint novo (`/oswaldo/paciente/me/...`) deve **importar e chamar** `generate_receituario()` do `oswaldo/services.py` — não copiar o código. Se DEV-1 ainda não mergeou DEM-072, DEV-2 deve fazer `git pull --rebase` antes de iniciar este bloco.

---

## Entrega

```
feat(portal): patient timeline + receituário download com filtro de privacidade SOAP
```
Hash → enviar ao ARQUITETO após `git push origin HEAD:main` confirmado.
