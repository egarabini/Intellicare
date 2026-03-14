---
dem: DEM-015
titulo: Frontend Clínico — Interface do Profissional de Saúde
tipo: IMPLEMENTACAO
status: concluido
criado: 2026-03-13
---

# DEM-015 · 03 — Relatório de Implementação

## O que foi feito

Implementação completa do **ClinicoUI**: SPA React para o profissional de saúde (CLINICO), com busca de pacientes, gestão de encontros, notas SOAP e assistente SLM com streaming SSE.

### Principais Entregas

1. **ClinicoUI (`frontend/ClinicoUI/`)**
   - **Scaffold**: package.json, tsconfig.json, vite.config.ts, index.html
   - **Auth (`src/auth/`)**: AuthProvider com `react-oidc-context`, client_id `clinico-ui`, tokens em memória (sem localStorage — RNF-03)
   - **TokenSync**: sync do access_token para sessionStorage durante a sessão
   - **API Client (`src/api/client.ts`)**: axios com interceptor Bearer token
   - **Hooks**: `usePatients` (busca com debounce, mín. 3 chars) e `useEncounters` (CRUD encontros + notas)
   - **SLMAssistant**: componente SSE streaming via Fetch API + ReadableStream, com AbortController para cancelamento
   - **PatientList**: busca full-text, tabela clicável, paginação
   - **EncounterView**: layout Grid 8/4 — painel esquerdo (encontro + notas SOAP) + painel direito (assistente IA)

2. **Infraestrutura**
   - Client `clinico-ui` adicionado ao Keycloak via `setup_keycloak.py` (step 8)
   - Mount `/clinico-ui/` no `main.py` para servir build estática
   - Script `build_clinico_ui.sh` para CI/CD

3. **Validação**
   - `tsc --noEmit` → 0 erros
   - Type declaration `@tabler/icons-react` via `src/types/tabler-icons.d.ts`

## Arquivos Criados/Modificados

| Arquivo | Ação |
|---------|------|
| `frontend/ClinicoUI/*` | Criado — projeto completo React + Vite + Mantine |
| `frontend/ClinicoUI/src/auth/AuthProvider.tsx` | Criado — OIDC com Keycloak (clinico-ui) |
| `frontend/ClinicoUI/src/auth/TokenSync.tsx` | Criado — sync token para sessionStorage |
| `frontend/ClinicoUI/src/api/client.ts` | Criado — axios com interceptor Bearer |
| `frontend/ClinicoUI/src/hooks/usePatients.ts` | Criado — busca pacientes com debounce |
| `frontend/ClinicoUI/src/hooks/useEncounters.ts` | Criado — CRUD encontros + notas |
| `frontend/ClinicoUI/src/components/SLMAssistant.tsx` | Criado — SSE streaming com AbortController |
| `frontend/ClinicoUI/src/pages/PatientList.tsx` | Criado — lista de pacientes |
| `frontend/ClinicoUI/src/pages/EncounterView.tsx` | Criado — encontro + nota SOAP + assistente IA |
| `frontend/ClinicoUI/src/App.tsx` | Criado — app com rotas e auth |
| `frontend/ClinicoUI/src/main.tsx` | Criado — entry point |
| `frontend/ClinicoUI/src/types/tabler-icons.d.ts` | Criado — type declarations |
| `tools/scripts/setup_keycloak.py` | Modificado — client clinico-ui (step 8) |
| `tools/scripts/build_clinico_ui.sh` | Criado — script de build |
| `packages/intellicare-core/intellicare_core/main.py` | Modificado — mount /clinico-ui/ |

## Decisões Técnicas

- **Tokens em memória**: `userStore: undefined` no OIDC config garante que tokens não persistem em localStorage (RNF-03, segurança HIPAA-like). Tokens não sobrevivem a reload — comportamento intencional.
- **SSE via Fetch API**: Não usamos EventSource pois precisamos de POST com body JSON. Fetch + ReadableStream permite streaming com headers customizados.
- **Sem @mantine/dropzone**: Upload de documentos reusa endpoint `/gestor/documents/upload` já existente; esta UI foca no fluxo clínico (encontros + SLM).

## Próximos Passos

- Testes E2E com fluxo completo: login dr.ana → busca paciente → encontro → nota SOAP → assistente SLM → fechar encontro
- Integração com DEM-013 (Cuidado Backend) e DEM-010 (SLM/Ollama) para validação real de streaming
