---
tipo: plano-execucao
demanda: DEM-044
titulo: Criar Videoconsulta — botão abrir sessão Jitsi na JourneyDetail
status: pendente
dev: DEV-1
criado: 2026-03-18
---

# DEM-044 — Plano de Execução

## Estimativa

Tempo estimado: 1h | Complexidade: baixa

Sem backend. Sem migration. 3 arquivos frontend. Risco principal: verificar
o schema exato da resposta de `POST /consultations/video` antes de tipar.

---

## STEPs

### STEP-001 — Verificar schema do endpoint

```bash
grep -A 20 "open_video_session" modules/careplanner/api/routes.py
grep -A 20 "open_video_session" modules/careplanner/services.py
```

Confirmar campos retornados: `clinico_url`, `patient_url`, `room_name`, `expires_at`.
Ajustar interface `VideoSessionCreate` em `useGestor.ts` conforme resposta real.

### STEP-002 — Adicionar hook `useCreateVideoSession` em `useGestor.ts`

Conforme Bloco 1 de `02_TECNICA.md`.
Critério: `npm run build` sem erros de tipo.

### STEP-003 — Atualizar `CareplannerJourneyDetail.tsx`

Conforme Bloco 2 de `02_TECNICA.md`:
1. Adicionar imports
2. Adicionar hook e estado `videoCreated`
3. Substituir bloco de botões de vídeo
4. Adicionar Modal pós-criação

Critério: `npm run build` sem erros; botão "Criar Videoconsulta" aparece
na UI para jornadas em REPLIED/SENT sem sessão ativa.

### STEP-004 — Playwright + Commit

Adicionar 1 teste conforme Bloco 3 de `02_TECNICA.md`.

```bash
cd frontend/GestorUI && npm run test:e2e
```

Critério: **12 passed**.

Commit:
```
feat(careplanner): DEM-044 botao Criar Videoconsulta + modal com links
```

Arquivos:
```
frontend\GestorUI\src\hooks\useGestor.ts
frontend\GestorUI\src\pages\CareplannerJourneyDetail.tsx
frontend\GestorUI\e2e\careplanner.spec.ts
docs\demandas\DEM-044_VIDEO_SESSION_UI\
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Schema de resposta diferente do esperado | STEP-001 verifica antes de tipar |
| `CopyButton` não disponível na versão Mantine instalada | Substituir por `navigator.clipboard.writeText` com `useState` para feedback |
| Modal não fecha após navegar para outra rota | `setVideoCreated(null)` no `onClose` é suficiente |
