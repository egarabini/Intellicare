---
tipo: especificacao-funcional
demanda: DEM-044
titulo: Criar Videoconsulta — botão abrir sessão Jitsi na JourneyDetail
sprint: "4.4"
status: pronto-para-dev
planejador: Claude (PLANEJADOR)
criado: 2026-03-18
depende_de: [DEM-040, DEM-038]
habilita: [DEM-047]
tags: [careplanner, video, jitsi, gestorui, p2]
---

# DEM-044 — Criar Videoconsulta (botão abrir sessão Jitsi)

## Objetivo

O backend já tem `POST /careplanner/consultations/video` e `GET /careplanner/consultations/video/{id}`
desde a DEM-038 Fase B. A `CareplannerJourneyDetail` já exibe o botão "Entrar na
Videoconsulta" quando `video && !video.expired`. O que falta é o botão para
**criar** a sessão quando ela ainda não existe — hoje o gestor/clínico não tem
como iniciar uma videoconsulta pela UI.

---

## Estado Atual vs. Estado Desejado

| Item | Hoje | DEM-044 |
|------|------|---------|
| `GET /consultations/video/{id}` | ✅ | mantido |
| `POST /consultations/video` | ✅ | mantido |
| Botão "Entrar na Videoconsulta" | ✅ aparece quando sessão existe | mantido |
| Botão "Criar Videoconsulta" | ❌ não existe | ✅ aparece quando sessão não existe |
| Hook `useCreateVideoSession` | ❌ não existe | ✅ mutation POST |
| Modal pós-criação | ❌ | ✅ mostra `clinico_url` e `patient_url` com botão copiar |

---

## Critérios de Aceite

1. Na `CareplannerJourneyDetail`, quando `canHaveVideo = true` e não existe sessão
   ativa (`!video` ou `video.expired`), aparece o botão "Criar Videoconsulta"
   (cor violet, ícone `IconVideo`).

2. Ao clicar, dispara `POST /careplanner/consultations/video` com o `correlation_id`
   da jornada. O botão exibe estado de loading durante a chamada.

3. Após criação bem-sucedida, abre um modal com:
   - Título: "Videoconsulta criada"
   - Link do clínico: botão "Entrar como Clínico" (`clinico_url`, abre em nova aba)
   - Link do paciente: campo de texto com `patient_url` + botão "Copiar link"
   - Botão "Fechar"

4. Após fechar o modal, o hook `useVideoSession` é invalidado e o botão
   "Entrar na Videoconsulta" substitui o "Criar Videoconsulta" automaticamente.

5. Se a jornada já tem sessão ativa (`video && !video.expired`), o botão "Criar"
   não aparece — só o "Entrar" (comportamento atual mantido).

6. Erro de criação exibe `notifications.show` com cor vermelha.

7. 1 teste Playwright cobrindo o fluxo: botão "Criar" → mock POST → modal com links.

---

## O que NÃO está incluído

- Sala Jitsi embutida via iframe (videoconsulta in-app)
- Encerramento da sessão de vídeo pela UI
- Notificação ao paciente com o link (integração futura)
- Sessões de vídeo no ClinicoUI (DEM-045 cobre acesso leitura)

---

## Notas para o Agente Desenvolvedor

- `POST /careplanner/consultations/video` recebe `{ correlation_id: string }`.
  Verificar o schema exato em `routes.py` antes de escrever o hook.
- A resposta inclui `clinico_url`, `patient_url`, `room_name`, `expires_at`.
  Tipar em `useGestor.ts` junto com as interfaces existentes.
- `useQueryClient().invalidateQueries(['video-session', correlationId])` após
  mutação bem-sucedida para forçar refetch do `useVideoSession`.
- O botão "Copiar link" pode usar `navigator.clipboard.writeText(patient_url)`
  com feedback visual (ícone troca para `IconCheck` por 2s).
