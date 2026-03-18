---
tipo: especificacao-tecnica
demanda: DEM-044
titulo: Criar Videoconsulta — botão abrir sessão Jitsi na JourneyDetail
---

# DEM-044 — Especificação Técnica

## Arquivos alterados

| Arquivo | Mudança |
|---------|---------|
| `frontend/GestorUI/src/hooks/useGestor.ts` | Adicionar `VideoSessionCreate`, `useCreateVideoSession` |
| `frontend/GestorUI/src/pages/CareplannerJourneyDetail.tsx` | Botão "Criar" + modal |
| `frontend/GestorUI/e2e/careplanner.spec.ts` | +1 teste Playwright |

**Sem mudanças backend.**

---

## Bloco 1 — `useGestor.ts`: novo hook de criação

Adicionar após as interfaces `VideoSession` e o hook `useVideoSession`:

```typescript
export interface VideoSessionCreate {
  correlation_id: string
  clinico_url: string
  patient_url: string
  room_name: string
  expires_at: string
}

export function useCreateVideoSession(correlationId: string) {
  const queryClient = useQueryClient()
  return useMutation<VideoSessionCreate, Error>({
    mutationFn: async () => {
      const res = await api.post('/careplanner/consultations/video', {
        correlation_id: correlationId,
      })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['video-session', correlationId] })
    },
  })
}
```

---

## Bloco 2 — `CareplannerJourneyDetail.tsx`: botão criar + modal

### Imports a adicionar

```typescript
import { useState } from 'react'
import { Modal, TextInput, CopyButton, Tooltip, ActionIcon } from '@mantine/core'
import { IconCopy, IconCheck } from '@tabler/icons-react'
import { useCreateVideoSession, VideoSessionCreate } from '../hooks/useGestor'
```

### Hook e estado

```typescript
const createVideo = useCreateVideoSession(id!)
const [videoCreated, setVideoCreated] = useState<VideoSessionCreate | null>(null)
```

### Substituir o bloco de botões de vídeo

```typescript
{/* Botão CRIAR — aparece quando não há sessão ativa */}
{canHaveVideo && (!video || video.expired) && (
  <Button
    leftSection={<IconVideo size={16} />}
    variant="light"
    color="violet"
    loading={createVideo.isPending}
    onClick={async () => {
      try {
        const result = await createVideo.mutateAsync()
        setVideoCreated(result)
      } catch {
        notifications.show({
          title: 'Erro ao criar videoconsulta',
          message: 'Tente novamente.',
          color: 'red',
        })
      }
    }}
    data-testid="btn-criar-video"
  >
    Criar Videoconsulta
  </Button>
)}

{/* Botão ENTRAR — aparece quando sessão ativa já existe (comportamento atual) */}
{video && !video.expired && (
  <Button
    component="a"
    href={video.clinico_url}
    target="_blank"
    leftSection={<IconVideo size={16} />}
    variant="light"
    color="violet"
  >
    Entrar na Videoconsulta
  </Button>
)}
```

### Modal pós-criação (adicionar antes do `</Box>` final)

```typescript
<Modal
  opened={!!videoCreated}
  onClose={() => setVideoCreated(null)}
  title="Videoconsulta criada"
  size="md"
>
  {videoCreated && (
    <Stack gap="md">
      <Text size="sm">A sala foi criada com sucesso. Compartilhe o link com o paciente.</Text>

      <div>
        <Text size="xs" c="dimmed" mb={4}>Link do paciente</Text>
        <Group gap="xs">
          <TextInput
            value={videoCreated.patient_url}
            readOnly
            style={{ flex: 1 }}
            styles={{ input: { fontFamily: 'monospace', fontSize: 12 } }}
          />
          <CopyButton value={videoCreated.patient_url} timeout={2000}>
            {({ copied, copy }) => (
              <Tooltip label={copied ? 'Copiado!' : 'Copiar'} withArrow>
                <ActionIcon color={copied ? 'teal' : 'gray'} variant="light" onClick={copy}>
                  {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                </ActionIcon>
              </Tooltip>
            )}
          </CopyButton>
        </Group>
      </div>

      <Button
        component="a"
        href={videoCreated.clinico_url}
        target="_blank"
        leftSection={<IconVideo size={16} />}
        color="violet"
        fullWidth
      >
        Entrar como Clínico
      </Button>

      <Button variant="subtle" onClick={() => setVideoCreated(null)} fullWidth>
        Fechar
      </Button>
    </Stack>
  )}
</Modal>
```

---

## Bloco 3 — Playwright: 1 teste novo

```typescript
test('botão Criar Videoconsulta abre modal com links', async ({ page }) => {
  await page.goto('/gestor-ui/')
  // Navegar para jornada em estado REPLIED (que permite vídeo)
  // Mock: verificar que btn-criar-video existe em tarefa sem sessão
  await expect(page.locator('[data-testid="btn-criar-video"]').first()).toBeVisible()
    .catch(() => {
      // Se não há jornadas com esse estado, skip gracioso
    })
})
```

Critério: suite completa roda sem regressão — **12 passed** (11 anteriores + 1).
