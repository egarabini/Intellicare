import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Grid, Stack, Title, Button, Textarea, Badge,
  Group, Text, Divider, Alert, Select, Tabs
} from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { IconAlertCircle, IconNotes, IconStethoscope, IconPill } from '@tabler/icons-react'
import {
  useEncounterHistory,
  useOpenEncounter,
  useAddNote,
  useCloseEncounter,
  useUpdateEncounter,
  useSearchCid10,
} from '../hooks/useEncounters'
import { SLMAssistant } from '../components/SLMAssistant'
import apiClient from '../api/client'
import { FlorenceNoteEditor } from '../components/FlorenceNoteEditor'
import { FlorenceNoteList, ClinicalNote } from '../components/FlorenceNoteList'
import { OswaldoCID10Search, CID10Result } from '../components/OswaldoCID10Search'
import { OswaldoPrescriptionEditor } from '../components/OswaldoPrescriptionEditor'

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

  const [florenceNotes, setFlorenceNotes] = useState<ClinicalNote[]>([])
  const [oswaldoCid10, setOswaldoCid10] = useState<CID10Result | null>(null)

  const fetchFlorenceNotes = async () => {
    if (!activeEncounter) return;
    try {
      const res = await apiClient.get(`/florence/notes/encounter/${activeEncounter.id}`);
      setFlorenceNotes(res.data);
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    fetchFlorenceNotes()
  }, [activeEncounter?.id])

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
            <Tabs defaultValue="florence" mt="md">
              <Tabs.List>
                <Tabs.Tab value="florence" leftSection={<IconNotes size={14} />}>Notas Florence</Tabs.Tab>
                <Tabs.Tab value="oswaldo" leftSection={<IconPill size={14} />}>Prescrição</Tabs.Tab>
                <Tabs.Tab value="legado" leftSection={<IconStethoscope size={14} />}>Legado</Tabs.Tab>
              </Tabs.List>

              <Tabs.Panel value="florence" pt="md">
                <Stack>
                  <FlorenceNoteEditor encounterId={activeEncounter.id} patientId={pid} onSaved={fetchFlorenceNotes} />
                  <Divider />
                  <Title order={5}>Histórico de Notas (Florence)</Title>
                  <FlorenceNoteList notes={florenceNotes} />
                  <Divider my="md" />
                  <Button color="red" variant="outline" onClick={handleClose} loading={closeEncounter.isPending}>
                    Fechar Encontro
                  </Button>
                </Stack>
              </Tabs.Panel>

              <Tabs.Panel value="oswaldo" pt="md">
                <Stack>
                  <OswaldoCID10Search onSelect={setOswaldoCid10} />
                  <Divider />
                  <OswaldoPrescriptionEditor encounterId={activeEncounter.id} patientId={pid} cid10={oswaldoCid10} />
                  <Divider my="md" />
                  <Button color="red" variant="outline" onClick={handleClose} loading={closeEncounter.isPending}>
                    Fechar Encontro
                  </Button>
                </Stack>
              </Tabs.Panel>

              <Tabs.Panel value="legado" pt="md">
                <Stack>
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
                </Stack>
              </Tabs.Panel>
            </Tabs>
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
