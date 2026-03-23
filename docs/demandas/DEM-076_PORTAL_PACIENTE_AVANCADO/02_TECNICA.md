---
tipo: especificacao-tecnica
demanda: DEM-076
titulo: Portal Paciente Avançado
---

# DEM-076 — Especificação Técnica

## Mapa de mudanças

| Arquivo | Tipo | O que muda |
|---------|------|-----------|
| `modules/cuidado/routes.py` | Modificar | `GET /cuidado/paciente/me/timeline` — timeline filtrada para paciente autenticado |
| `modules/cuidado/services.py` | Modificar | `get_patient_timeline_for_portal()` — aplica filtro de privacidade sobre `clinical_timeline()` |
| `modules/oswaldo/routes.py` | Modificar | `GET /oswaldo/paciente/me/prescriptions/{id}/receituario.pdf` — endpoint com autenticação de paciente |
| `frontend/PacienteUI/src/pages/HistoricoPage.tsx` | Modificar | Adicionar timeline + botão "Baixar Receituário" por prescrição |
| `frontend/PacienteUI/src/hooks/usePatientTimeline.ts` | **Novo** | Hook react-query para timeline do portal |
| `packages/intellicare-core/tests/test_portal_avancado.py` | **Novo** | 4+ testes de privacidade e controle de acesso |

---

## Endpoint — Timeline do Portal

```
GET /cuidado/paciente/me/timeline?limit=20&offset=0
Authorization: Bearer {paciente_token}
```

**Diferença em relação ao endpoint do clínico (`/cuidado/patients/{id}/timeline`):**
- Autenticação: token do paciente (role `PACIENTE`), não do clínico
- Filtro de privacidade aplicado via `_apply_portal_privacy_filter(events)`
- `patient_id` extraído do token (não do path) — paciente só vê seus próprios dados

---

## Filtro de privacidade — `_apply_portal_privacy_filter()`

```python
def _apply_portal_privacy_filter(events: list[TimelineEvent]) -> list[TimelineEvent]:
    """Remove ou mascara campos privados antes de expor ao paciente."""
    filtered = []
    for event in events:
        if event.type == "clinical_note":
            # Ocultar notas SOAP_A (avaliação clínica interna)
            if event.metadata.get("note_type") == "soap" and event.metadata.get("soap_a"):
                event.metadata.pop("soap_a", None)
                event.metadata.pop("soap_p", None)  # plano interno também
        if event.type == "encounter":
            # Ocultar avaliação interna do encontro
            event.metadata.pop("soap_a", None)
        filtered.append(event)
    return filtered
```

---

## Endpoint — Receituário do Paciente

```
GET /oswaldo/paciente/me/prescriptions/{prescription_id}/receituario.pdf?type=simple
Authorization: Bearer {paciente_token}
```

**Controle de acesso:**
```python
@router.get("/paciente/me/prescriptions/{prescription_id}/receituario.pdf")
async def get_my_receituario(
    prescription_id: UUID,
    type: PrescriptionType = PrescriptionType.simple,
    ctx = Depends(get_patient_context),
):
    # Verificar que a prescrição pertence ao paciente autenticado
    prescription = get_prescription(prescription_id, ctx)
    if prescription.patient_id != ctx.current_patient_id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    pdf_bytes = generate_receituario(prescription, type)
    return Response(content=pdf_bytes, media_type="application/pdf")
```

---

## Frontend — `HistoricoPage.tsx`

Estrutura da página atualizada:

```
┌─ Meu Histórico ───────────────────────────────────────────────┐
│                                                                │
│  Linha do Tempo                                               │
│  ─────────────────────────────────────────────────────────   │
│  📅 15/03/2026  Consulta — Dor torácica                       │
│  📋 14/03/2026  Nota Clínica — Avaliação subjetiva            │
│  💊 10/03/2026  Prescrição — Atenolol 50mg                    │
│                              [Baixar Receituário]             │
│  🔔 05/03/2026  Jornada — Acompanhamento pós-consulta         │
│                                                               │
│  [Carregar mais]                                              │
└───────────────────────────────────────────────────────────────┘
```

Comportamento:
- Botão "Baixar Receituário" aparece **apenas** nos eventos do tipo `prescription`
- Clique: `window.open('/api/oswaldo/paciente/me/prescriptions/{id}/receituario.pdf?type=simple', '_blank')`
- Ícones Mantine por tipo: `IconStethoscope` (consulta), `IconNotes` (nota), `IconPill` (prescrição), `IconBell` (jornada)
- Paginação com `limit=20`, botão "Carregar mais" appenda eventos

---

## Testes — `test_portal_avancado.py`

| Teste | Cenário |
|-------|---------|
| `test_patient_timeline_excludes_soap_a` | Timeline do portal não retorna campo `soap_a` |
| `test_patient_can_download_own_receituario` | Paciente A baixa receituário da sua própria prescrição → 200 PDF |
| `test_patient_cannot_download_others_receituario` | Paciente A tenta baixar receituário de prescrição do paciente B → 403 |
| `test_patient_timeline_only_own_data` | Timeline do portal retorna apenas eventos do paciente autenticado |
