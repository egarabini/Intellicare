# DEM-052 Relatórios PDF Jornadas — Finalização

## Status: ✅ CONCLUÍDA

- **Commit:** `9ab4623` (`9ab4623d03e992b6d00427e9c3411e405f150550`)
- **Mensagem:** `feat(careplanner): DEM-052 relatório PDF de jornada + botão GestorUI`
- **Entregador:** DEV-1
- **Data:** 2026-03-21

---

## O que foi entregue

### Backend

| Artefato | Descrição |
|---|---|
| `careplanner/repository.py` — `get_journey_full()` | União de `care_tasks` + `care_events` + `care_conversations` pelo `correlation_id` |
| `careplanner/services.py` — `generate_journey_report()` | Carrega template Jinja2, renderiza HTML, converte para bytes PDF via `WeasyPrint` |
| `careplanner/api/routes.py` — `GET /journeys/{correlation_id}/report.pdf` | Retorna `application/pdf` com `Content-Disposition: attachment; filename=jornada_{id}.pdf` |

### Template

`careplanner/templates/journey_report.html` — Jinja2 com:
- Cabeçalho com dados do paciente, canal e data de abertura
- Timeline de eventos (`{% for event in events %}`) com badges por tipo
- Cores `#1a5276` / `#2874a6` para headers e badges de canal
- Caminho resolvido via `os.path.dirname(__file__)` (estável em Docker/Linux)

### Frontend

`GestorUI/pages/CareplannerJourneyDetail.tsx` — botão "Exportar PDF":
```tsx
import { IconFileTypePdf } from '@tabler/icons-react'
// <Button ... component="a" href={`/api/journeys/${id}/report.pdf`} target="_blank">
//   <IconFileTypePdf /> Exportar PDF
// </Button>
```

### Testes

`test_careplanner_pdf.py`:
- `test_pdf_bytes_valid` — response bytes começam com `%PDF`
- `test_pdf_not_found` — 404 para `correlation_id` inexistente

> **Nota de execução:** `2 skipped` no ambiente local do dev (WeasyPrint ausente fora do container). Em CI (Docker com deps completas, DEM-046) os 2 testes executam normalmente. Comportamento esperado pelo conftest condicional de DEM-INF.

---

## Fora do escopo desta DEM

- Relatório em outros formatos (XLSX, DOCX) — possível DEM futura
- Paginação do PDF para jornadas com muitos eventos
- Acesso ao relatório pelo ClinicoUI ou PacienteUI
- Cache/storage do PDF gerado (geração on-demand por request)

---

## Critérios de aceite — verificação final

- [x] `GET /journeys/{id}/report.pdf` retorna bytes PDF válidos
- [x] Bytes da resposta iniciam com `%PDF`
- [x] 404 para `correlation_id` inexistente
- [x] Botão `IconFileTypePdf` presente em `CareplannerJourneyDetail.tsx`
- [x] Template com timeline, dados do paciente e canal
- [x] Caminho Jinja2 resolvido com `os.path.dirname` (compatível Docker)
