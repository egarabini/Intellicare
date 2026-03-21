---
tipo: briefing-completo
demanda: DEM-052
titulo: Relatórios PDF de Jornadas CarePlanner
dev: DEV-1
estimativa: 3h
prerequisito: DEM-027 (WeasyPrint instalado), DEM-040 (CareplannerJourneyDetail)
---

# DEM-052 — Relatórios PDF de Jornadas CarePlanner

## Contexto

O gestor pode visualizar a timeline de uma jornada no GestorUI mas não pode
exportar para PDF. Esta DEM adiciona o export de jornada completa em PDF —
útil para prontuário, auditoria e comunicação com o paciente.

WeasyPrint já está instalado (`DEM-027`) e o renderer existe em
`modules/admin/renderer.py` (ou similar). Reutilizar — não criar novo pipeline.

## Arquivos a modificar/criar

| Arquivo | Tipo |
|---------|------|
| `modules/careplanner/api/routes.py` | Modificar — endpoint `/journeys/{id}/report.pdf` |
| `modules/careplanner/services.py` | Modificar — método `generate_journey_report()` |
| `modules/careplanner/templates/journey_report.html` | **Novo** — template HTML |
| `modules/careplanner/repository.py` | Modificar — `get_journey_full(correlation_id)` |
| `frontend/GestorUI/src/pages/CareplannerJourneyDetail.tsx` | Modificar — botão "Exportar PDF" |
| `packages/intellicare-core/tests/test_careplanner_pdf.py` | **Novo** — 2 testes |

---

## STEP-001 — Verificar renderer existente

```bash
# Confirmar onde está o renderer WeasyPrint
grep -rn "WeasyPrint\|weasyprint\|HTML(" modules/ --include="*.py" | head -10

# Confirmar template base existente (DEM-027)
ls modules/admin/templates/ 2>/dev/null || ls modules/*/templates/ 2>/dev/null
```

Reutilizar a função de geração de PDF já existente. Não duplicar.

---

## STEP-002 — `get_journey_full()` em `repository.py`

```python
async def get_journey_full(
    self, ctx: TenantContext, correlation_id: UUID
) -> dict:
    """Retorna dados completos da jornada para o relatório PDF."""
    async with self._session(ctx) as db:
        # care_task
        task = (await db.execute(
            text("SELECT * FROM care_tasks WHERE correlation_id = :cid"),
            {"cid": str(correlation_id)}
        )).mappings().first()

        if not task:
            raise ValueError(f"Jornada {correlation_id} não encontrada")

        # care_events (timeline)
        events = (await db.execute(
            text("""
                SELECT event_type, payload, created_at
                FROM care_events
                WHERE correlation_id = :cid
                ORDER BY created_at ASC
            """),
            {"cid": str(correlation_id)}
        )).mappings().all()

        # care_conversation (mensagens)
        conversation = (await db.execute(
            text("""
                SELECT * FROM care_conversations
                WHERE correlation_id = :cid
            """),
            {"cid": str(correlation_id)}
        )).mappings().first()

    return {
        "task": dict(task),
        "events": [dict(e) for e in events],
        "conversation": dict(conversation) if conversation else {},
        "tenant_slug": ctx.tenant_slug,
        "generated_at": datetime.utcnow().isoformat(),
    }
```

---

## STEP-003 — Template HTML `journey_report.html`

Criar `modules/careplanner/templates/journey_report.html`:

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial, sans-serif; font-size: 12px; color: #333; margin: 40px; }
    h1 { color: #1a5276; font-size: 18px; border-bottom: 2px solid #1a5276; padding-bottom: 8px; }
    h2 { color: #2874a6; font-size: 14px; margin-top: 24px; }
    .header-info { background: #f4f6f7; padding: 12px; border-radius: 4px; margin-bottom: 20px; }
    .header-info table { width: 100%; }
    .header-info td { padding: 3px 8px; }
    .label { font-weight: bold; color: #555; width: 160px; }
    .event { padding: 6px 0; border-bottom: 1px solid #eee; display: flex; gap: 16px; }
    .event-time { color: #888; min-width: 140px; }
    .event-type { font-weight: bold; min-width: 200px; }
    .canal { display: inline-block; background: #d5e8d4; color: #28a745; padding: 2px 8px; border-radius: 3px; }
    .status-closed { color: #28a745; font-weight: bold; }
    .status-failed { color: #dc3545; font-weight: bold; }
    .status-expired { color: #fd7e14; font-weight: bold; }
    .footer { margin-top: 40px; font-size: 10px; color: #aaa; text-align: center; }
  </style>
</head>
<body>
  <h1>IntelliCare — Relatório de Jornada de Cuidado</h1>

  <div class="header-info">
    <table>
      <tr>
        <td class="label">Tenant:</td>
        <td>{{ tenant_slug }}</td>
        <td class="label">Correlation ID:</td>
        <td>{{ task.correlation_id }}</td>
      </tr>
      <tr>
        <td class="label">Paciente:</td>
        <td>{{ task.patient_ref }}</td>
        <td class="label">Canal:</td>
        <td><span class="canal">{{ task.channel }}</span></td>
      </tr>
      <tr>
        <td class="label">Tipo de Tarefa:</td>
        <td>{{ task.task_type }}</td>
        <td class="label">Status Final:</td>
        <td class="status-{{ task.status | lower }}">{{ task.status }}</td>
      </tr>
      <tr>
        <td class="label">Aberta em:</td>
        <td>{{ task.created_at }}</td>
        <td class="label">Fechada em:</td>
        <td>{{ task.updated_at }}</td>
      </tr>
    </table>
  </div>

  <h2>Timeline de Eventos</h2>
  {% for event in events %}
  <div class="event">
    <span class="event-time">{{ event.created_at }}</span>
    <span class="event-type">{{ event.event_type }}</span>
    <span>{{ event.payload | tojson if event.payload else '' }}</span>
  </div>
  {% endfor %}

  {% if conversation %}
  <h2>Dados da Conversa</h2>
  <div class="header-info">
    <table>
      {% if conversation.rc_room_id %}
      <tr><td class="label">Room ID (RC):</td><td>{{ conversation.rc_room_id }}</td></tr>
      {% endif %}
      {% if conversation.phone_e164 %}
      <tr><td class="label">Telefone:</td><td>{{ conversation.phone_e164 }}</td></tr>
      {% endif %}
    </table>
  </div>
  {% endif %}

  <div class="footer">
    Gerado em {{ generated_at }} — IntelliCare V3 &copy; {{ generated_at[:4] }}
  </div>
</body>
</html>
```

---

## STEP-004 — `generate_journey_report()` em `services.py`

```python
async def generate_journey_report(
    self, ctx: TenantContext, correlation_id: UUID
) -> bytes:
    """Gera PDF da jornada usando WeasyPrint."""
    from weasyprint import HTML
    from jinja2 import Environment, FileSystemLoader
    import os

    data = await self._repo.get_journey_full(ctx, correlation_id)

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("journey_report.html")
    html_content = template.render(**data)

    return HTML(string=html_content).write_pdf()
```

---

## STEP-005 — Endpoint em `routes.py`

```python
from fastapi.responses import Response

@router.get("/journeys/{correlation_id}/report.pdf")
async def journey_report_pdf(
    correlation_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    service: CareplannerService = Depends(get_service),
):
    """Exporta jornada CarePlanner como PDF."""
    pdf_bytes = await service.generate_journey_report(ctx, correlation_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=jornada_{correlation_id}.pdf"
        },
    )
```

---

## STEP-006 — Botão no GestorUI

Em `frontend/GestorUI/src/pages/CareplannerJourneyDetail.tsx`:

```tsx
// Adicionar ao lado do botão de vídeo existente
<Button
  variant="light"
  leftSection={<IconFileTypePdf size={16} />}
  component="a"
  href={`/api/v1/careplanner/journeys/${correlationId}/report.pdf`}
  target="_blank"
  rel="noopener noreferrer"
>
  Exportar PDF
</Button>
```

Import necessário:
```tsx
import { IconFileTypePdf } from '@tabler/icons-react'
```

---

## STEP-007 — Testes

```python
# packages/intellicare-core/tests/test_careplanner_pdf.py
import pytest

@pytest.mark.asyncio
async def test_journey_report_pdf_returns_pdf(client, gestor_token, existing_correlation_id):
    """GET /journeys/{id}/report.pdf retorna bytes de PDF válido."""
    resp = await client.get(
        f"/api/v1/careplanner/journeys/{existing_correlation_id}/report.pdf",
        headers={"Authorization": f"Bearer {gestor_token}"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    # PDFs começam com %PDF
    assert resp.content[:4] == b"%PDF"

@pytest.mark.asyncio
async def test_journey_report_pdf_not_found(client, gestor_token):
    """Jornada inexistente retorna 404."""
    import uuid
    resp = await client.get(
        f"/api/v1/careplanner/journeys/{uuid.uuid4()}/report.pdf",
        headers={"Authorization": f"Bearer {gestor_token}"},
    )
    assert resp.status_code == 404
```

Critério: **2 passed** (WeasyPrint disponível no ambiente de teste — ver conftest skip condicional em DEM-INF Fix WeasyPrint).

---

## STEP-008 — Commit

```
feat(careplanner): DEM-052 relatório PDF de jornada + botão GestorUI
```

Arquivos:
```
modules\careplanner\api\routes.py
modules\careplanner\services.py
modules\careplanner\repository.py
modules\careplanner\templates\journey_report.html
frontend\GestorUI\src\pages\CareplannerJourneyDetail.tsx
packages\intellicare-core\tests\test_careplanner_pdf.py
```
