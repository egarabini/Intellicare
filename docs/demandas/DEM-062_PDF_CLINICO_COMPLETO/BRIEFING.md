# DEM-062 — Relatório PDF Clínico Completo (Florence + Oswaldo)

> **Dev:** DEV-1
> **Estimativa:** ~3.5h
> **Dependência:** DEM-052 (PDF jornadas, WeasyPrint instalado), DEM-055 (Florence), DEM-058 (Oswaldo)
> **Executor Matrix:** `generate_clinical_report()` → **Worker** (geração on-demand, sem efeito externo)

---

## Contexto

DEM-052 entregou PDF de jornadas CarePlanner. Esta DEM entrega o PDF **clínico**:
o relatório completo de um encontro médico — notas Florence (SOAP ou livre) +
prescrições Oswaldo + dados do paciente e do profissional.

O padrão WeasyPrint + Jinja2 já está estabelecido. Seguir a mesma arquitetura
de `modules/careplanner/` para o novo endpoint em `modules/florence/` ou em um
novo módulo `modules/clinico/reports/`.

---

## Fase A — Backend

### STEP-001 — Repository: `get_encounter_full()`

Criar método que agrega tudo de um encontro em um único payload:

```python
# modules/florence/repository.py (ou novo modules/clinico/repository.py)

async def get_encounter_full(ctx: TenantContext, encounter_id: int) -> dict | None:
    """
    Retorna dict com:
    - encounter: dados do encontro (data, profissional, paciente)
    - notes: lista de ClinicalNote do encontro
    - prescriptions: lista de Prescription do encontro
    """
    async with tenant_session(ctx) as session:
        encounter = await session.get(Encounter, encounter_id)
        if not encounter:
            return None

        notes = await florence_repo.get_notes_by_encounter(ctx, encounter_id)
        prescriptions = await oswaldo_repo.get_prescriptions_by_encounter(ctx, encounter_id)

        return {
            "encounter": encounter,
            "notes": notes,
            "prescriptions": prescriptions,
        }
```

### STEP-002 — Template HTML

`modules/florence/templates/clinical_report.html` (ou `modules/clinico/templates/`):

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial, sans-serif; font-size: 12px; color: #1a1a1a; }
    .header { background: #1a5276; color: white; padding: 16px; margin-bottom: 24px; }
    .header h1 { margin: 0; font-size: 18px; }
    .header p { margin: 4px 0 0; font-size: 11px; opacity: 0.85; }
    .section { margin-bottom: 20px; }
    .section h2 { color: #2874a6; border-bottom: 1px solid #aed6f1; padding-bottom: 4px; }
    .soap-field { margin-bottom: 10px; }
    .soap-label { font-weight: bold; color: #1a5276; }
    .prescription-item { padding: 6px 0; border-bottom: 1px solid #eee; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 10px;
             background: #d6eaf8; color: #1a5276; font-size: 10px; }
    .footer { margin-top: 32px; font-size: 10px; color: #888; text-align: center; }
  </style>
</head>
<body>
  <div class="header">
    <h1>Relatório de Encontro Clínico — IntelliCare</h1>
    <p>{{ encounter.patient_name }} | {{ encounter.scheduled_at | strftime('%d/%m/%Y %H:%M') }}
       | Dr(a). {{ encounter.professional_name }}</p>
  </div>

  {% if notes %}
  <div class="section">
    <h2>Notas Clínicas</h2>
    {% for note in notes %}
      <div style="margin-bottom:16px;">
        <span class="badge">{{ note.note_type }}</span>
        <span style="margin-left:8px; color:#888; font-size:10px;">
          {{ note.created_at | strftime('%d/%m/%Y %H:%M') }} — {{ note.author_name }}
        </span>
        {% if note.note_type == 'SOAP' %}
          {% if note.soap_s %}<div class="soap-field"><span class="soap-label">S:</span> {{ note.soap_s }}</div>{% endif %}
          {% if note.soap_o %}<div class="soap-field"><span class="soap-label">O:</span> {{ note.soap_o }}</div>{% endif %}
          {% if note.soap_a %}<div class="soap-field"><span class="soap-label">A:</span> {{ note.soap_a }}</div>{% endif %}
          {% if note.soap_p %}<div class="soap-field"><span class="soap-label">P:</span> {{ note.soap_p }}</div>{% endif %}
        {% else %}
          <p>{{ note.free_text }}</p>
        {% endif %}
      </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if prescriptions %}
  <div class="section">
    <h2>Prescrições</h2>
    {% for rx in prescriptions %}
      <div style="margin-bottom:12px;">
        {% if rx.cid10_code %}
          <strong>CID-10: {{ rx.cid10_code }}</strong> — {{ rx.cid10_desc }}<br>
        {% endif %}
        {% for item in rx.items %}
          <div class="prescription-item">
            <strong>{{ item.drug }}</strong> — {{ item.posology }}
            {% if item.duration %} ({{ item.duration }}){% endif %}
          </div>
        {% endfor %}
        {% if rx.notes %}<p style="color:#555;">{{ rx.notes }}</p>{% endif %}
      </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if not notes and not prescriptions %}
  <p style="color:#888;">Nenhum registro clínico encontrado para este encontro.</p>
  {% endif %}

  <div class="footer">
    Gerado em {{ generated_at | strftime('%d/%m/%Y %H:%M') }} · IntelliCare V3 · Documento confidencial
  </div>
</body>
</html>
```

### STEP-003 — Service: `generate_clinical_report()`

```python
# modules/florence/services.py (ou modules/clinico/services.py)

from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import os

def generate_clinical_report(data: dict) -> bytes:
    """Gera PDF do encontro clínico. Retorna bytes."""
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))

    def strftime(value, fmt):
        if value is None:
            return ""
        return value.strftime(fmt)

    env.filters["strftime"] = strftime

    template = env.get_template("clinical_report.html")
    html_str = template.render(**data, generated_at=datetime.now())
    return HTML(string=html_str).write_pdf()
```

### STEP-004 — Endpoint

```python
@router.get("/encounters/{encounter_id}/report.pdf")
async def encounter_report(
    encounter_id: int,
    ctx: TenantContext = Depends(get_tenant_context),
    _: UserClaims = Depends(require_roles(["CLINICO", "GESTOR"])),
):
    data = await get_encounter_full(ctx, encounter_id)
    if not data:
        raise HTTPException(404, "Encontro não encontrado")

    pdf_bytes = generate_clinical_report(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=encontro_{encounter_id}.pdf"},
    )
```

---

## Fase B — Frontend ClinicoUI

### STEP-005 — Botão no EncounterView

`ClinicoUI/pages/EncounterView.tsx` — adicionar ao lado dos botões existentes:

```tsx
import { IconFileTypePdf } from '@tabler/icons-react'

<Button
  component="a"
  href={`/api/encontros/${encounterId}/report.pdf`}
  target="_blank"
  variant="light"
  leftSection={<IconFileTypePdf size={16} />}
>
  Exportar PDF Clínico
</Button>
```

---

## Fase C — Testes

### STEP-006

`packages/intellicare-core/tests/test_clinical_report.py`:

```python
async def test_clinical_report_pdf_valid(async_client, seed_encounter_with_note):
    """PDF gerado começa com %PDF."""
    resp = await async_client.get(f"/encontros/{seed_encounter_with_note}/report.pdf")
    # Skipped se WeasyPrint ausente (conftest condicional)
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"

async def test_clinical_report_not_found(async_client):
    resp = await async_client.get("/encontros/999999/report.pdf")
    assert resp.status_code == 404
```

---

## Critérios de Aceite

- [ ] `GET /encontros/{id}/report.pdf` retorna PDF válido com notas e prescrições
- [ ] Template exibe campos SOAP individuais quando `note_type == SOAP`
- [ ] Template exibe prescrição com CID-10 e itens quando disponível
- [ ] Botão "Exportar PDF Clínico" visível no `EncounterView`
- [ ] 2 testes: bytes `%PDF` + 404

## Executor Matrix

| Componente | Categoria | Justificativa |
|---|---|---|
| `generate_clinical_report()` | Worker | Geração on-demand, sem efeito externo, não persiste |
| `get_encounter_full()` | Worker | Somente leitura, agrega dados existentes |
| Botão "Exportar PDF" | Worker | Link direto ao endpoint — sem side effect |
