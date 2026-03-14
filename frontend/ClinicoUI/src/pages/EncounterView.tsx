import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Grid, Stack, Title, Button, Textarea, Badge,
  Group, Text, Divider, Alert,
} from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import {
  useEncounterHistory,
  useOpenEncounter,
  useAddNote,
  useCloseEncounter,
} from '../hooks/useEncounters'
import { SLMAssistant } from '../components/SLMAssistant'

export function EncounterView() {
  const { patientId } = useParams<{ patientId: string }>()
  const pid = Number(patientId)

  const { data: encounters, isLoading } = useEncounterHistory(pid)
  const openEncounter = useOpenEncounter()
  const addNote = useAddNote(encounters?.find(e => e.status === 'open')?.id ?? 0)
  const closeEncounter = useCloseEncounter()

  const [noteContent, setNoteContent] = useState('')

  const activeEncounter = encounters?.find(e => e.status === 'open')

  const handleAddNote = async () => {
    if (!activeEncounter || !noteContent.trim()) return
    await addNote.mutateAsync(noteContent)
    setNoteContent('')
  }

  const handleClose = async () => {
    if (!activeEncounter) return
    await closeEncounter.mutateAsync({ encounterId: activeEncounter.id, patientId: pid })
  }

  if (isLoading) return <Text>Carregando...</Text>

  return (
    <Grid gutter="md">
      {/* Painel Esquerdo: Encontro / Nota SOAP */}
      <Grid.Col span={8}>
        <Stack>
          <Group justify="space-between">
            <Title order={3}>Encontro Atual</Title>
            {activeEncounter ? (
              <Badge color="green">Aberto</Badge>
            ) : (
              <Badge color="gray">Nenhum Aberto</Badge>
            )}
          </Group>

          {!activeEncounter && (
            <Button
              onClick={() => openEncounter.mutate(pid)}
              loading={openEncounter.isPending}
            >
              Abrir Novo Encontro
            </Button>
          )}

          {activeEncounter && (
            <>
              <Textarea
                label="Nota SOAP"
                placeholder="S: (Subjetivo) O: (Objetivo) A: (Avaliação) P: (Plano)"
                minRows={8}
                value={noteContent}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNoteContent(e.currentTarget.value)}
              />
              <Group>
                <Button
                  onClick={handleAddNote}
                  loading={addNote.isPending}
                  disabled={!noteContent.trim()}
                >
                  Salvar Nota
                </Button>
                <Button
                  color="red"
                  variant="outline"
                  onClick={handleClose}
                  loading={closeEncounter.isPending}
                >
                  Fechar Encontro
                </Button>
              </Group>
            </>
          )}

          <Divider label="Histórico" labelPosition="left" />
          {encounters?.filter(e => e.status === 'closed').map(enc => (
            <Alert key={enc.id} icon={<IconAlertCircle />} color="gray" variant="light">
              Encontro #{enc.id} — Fechado em {new Date(enc.ended_at!).toLocaleDateString('pt-BR')}
            </Alert>
          ))}
        </Stack>
      </Grid.Col>

      {/* Painel Direito: Assistente SLM */}
      <Grid.Col span={4}>
        <Stack>
          <Title order={4}>Assistente IA</Title>
          <SLMAssistant encounterContext={noteContent} />
        </Stack>
      </Grid.Col>
    </Grid>
  )
}
