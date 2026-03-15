import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Grid, Stack, Title, Button, Textarea, Badge,
  Group, Text, Divider, Alert, Select
} from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { IconAlertCircle } from '@tabler/icons-react'
import {
  useEncounterHistory,
  useOpenEncounter,
  useAddNote,
  useCloseEncounter,
  useUpdateEncounter,
  useSearchCid10,
} from '../hooks/useEncounters'
import { SLMAssistant } from '../components/SLMAssistant'

export function EncounterView() {
  const { patientId } = useParams<{ patientId: string }>()
  const pid = patientId as string

  const { data: encounters, isLoading } = useEncounterHistory(pid)
  const openEncounter = useOpenEncounter()
  const activeEncounterId = encounters?.find(e => e.status === 'open')?.id
  const addNote = useAddNote(activeEncounterId || '')
  const closeEncounter = useCloseEncounter()
  const updateEncounter = useUpdateEncounter()

  const [noteContent, setNoteContent] = useState('')
  const [prescription, setPrescription] = useState('')
  const [cidSearch, setCidSearch] = useState('')
  const [cidCode, setCidCode] = useState<string | null>(null)
  
  const [debouncedCid] = useDebouncedValue(cidSearch, 300)
  const { data: cids } = useSearchCid10(debouncedCid)
  const cidOptions = cids?.map(c => ({ value: c.code, label: `${c.code} - ${c.description}` })) || []

  const activeEncounter = encounters?.find(e => e.status === 'open')

  const handleAddNote = async () => {
    if (!activeEncounter || !noteContent.trim()) return
    await addNote.mutateAsync(noteContent)
    setNoteContent('')
  }

  const handleClose = async () => {
    if (!activeEncounter) return
    const updates: any = {}
    if (cidCode) updates.cid10_code = cidCode
    if (prescription.trim()) updates.prescription = prescription
    
    if (Object.keys(updates).length > 0) {
      await updateEncounter.mutateAsync({ encounterId: activeEncounter.id, data: updates })
    }
    await closeEncounter.mutateAsync({ encounterId: activeEncounter.id, patientId: patientId as string })
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
                minRows={6}
                value={noteContent}
                onChange={(e) => setNoteContent(e.currentTarget.value)}
              />
              
              <Select
                label="Hipótese Diagnóstica (CID-10)"
                placeholder="Buscar por código ou descrição"
                searchable
                searchValue={cidSearch}
                onSearchChange={setCidSearch}
                data={cidOptions}
                value={cidCode}
                onChange={setCidCode}
                nothingFoundMessage="Nenhum resultado."
                clearable
              />

              <Textarea
                label="Prescrição"
                placeholder="Ex: Dipirona 500mg, 1 cp de 6/6h"
                minRows={3}
                value={prescription}
                onChange={(e) => setPrescription(e.currentTarget.value)}
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
              <Text fw={500}>Encontro concluído em {new Date(enc.closed_at || '').toLocaleDateString('pt-BR')}</Text>
              {enc.cid10_code && <Text size="sm">CID: {enc.cid10_code}</Text>}
              {enc.prescription && <Text size="sm">Prescrição elaborada.</Text>}
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
