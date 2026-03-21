import { useState } from 'react';
import { Button, Group, SegmentedControl, Text, Textarea, TextInput, Stack, Paper } from '@mantine/core';
import { IconSparkles } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import apiClient from '../api/client';

interface FlorenceNoteEditorProps {
  encounterId: string | number;
  patientId: string | number;
  onSaved: () => void;
}

interface SuggestionMeta {
  confidence: string;
  model: string;
}

export function FlorenceNoteEditor({ encounterId, patientId, onSaved }: FlorenceNoteEditorProps) {
  const [noteType, setNoteType] = useState<'FREE' | 'SOAP'>('FREE');
  const [loading, setLoading] = useState(false);
  const [suggesting, setSuggesting] = useState(false);
  const [fields, setFields] = useState({ s: '', o: '', a: '', p: '', free: '' });
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [suggestionMeta, setSuggestionMeta] = useState<SuggestionMeta | null>(null);

  const handleSuggest = async () => {
    setSuggesting(true);
    setSuggestionMeta(null);
    try {
      const resp = await apiClient.post('/florence/notes/suggest', {
        encounter_id: Number(encounterId),
        patient_id: Number(patientId),
        chief_complaint: chiefComplaint,
      });
      const suggestion = resp.data;
      setFields({
        s: suggestion.soap_s,
        o: suggestion.soap_o,
        a: suggestion.soap_a,
        p: suggestion.soap_p,
        free: fields.free,
      });
      setSuggestionMeta({ confidence: suggestion.confidence, model: suggestion.model });
    } catch (err: any) {
      notifications.show({
        title: 'Erro',
        message: err.message || 'Falha ao obter sugestão IA',
        color: 'red',
      });
    } finally {
      setSuggesting(false);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const payload = {
        encounter_id: Number(encounterId),
        patient_id: Number(patientId),
        note_type: noteType,
        ...(noteType === 'SOAP'
          ? { soap_s: fields.s, soap_o: fields.o, soap_a: fields.a, soap_p: fields.p }
          : { free_text: fields.free })
      };

      await apiClient.post('/florence/notes', payload);
      
      notifications.show({
        title: 'Sucesso',
        message: 'Anotação salva com sucesso',
        color: 'green'
      });
      
      setFields({ s: '', o: '', a: '', p: '', free: '' });
      onSaved();
    } catch (err: any) {
      notifications.show({
        title: 'Erro',
        message: err.message || 'Falha ao salvar anotação',
        color: 'red'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper withBorder p="md" radius="md">
      <Stack gap="md">
        <SegmentedControl
          value={noteType}
          onChange={(v) => setNoteType(v as 'FREE' | 'SOAP')}
          data={[
            { label: 'Texto livre', value: 'FREE' },
            { label: 'SOAP', value: 'SOAP' }
          ]}
        />

        {noteType === 'SOAP' ? (
          <>
            <TextInput
              label="Motivo da consulta"
              placeholder="Descreva brevemente o motivo"
              value={chiefComplaint}
              onChange={(e) => setChiefComplaint(e.currentTarget.value)}
              data-testid="florence-chief-complaint"
            />
            <Group>
              <Button
                leftSection={<IconSparkles size={14} />}
                variant="light"
                color="violet"
                loading={suggesting}
                disabled={!chiefComplaint}
                onClick={handleSuggest}
                data-testid="btn-suggest-soap"
              >
                Sugerir SOAP com IA
              </Button>
              {suggestionMeta?.confidence === 'low' && (
                <Text size="xs" c="dimmed">
                  Sugestão gerada por regras (LLM não configurado) — revise com atenção.
                </Text>
              )}
            </Group>
            <Textarea 
              label="S — Subjetivo" 
              placeholder="Sintomas relatados pelo paciente..."
              minRows={2} autosize 
              value={fields.s} onChange={e => setFields({...fields, s: e.currentTarget.value})}
              data-testid="florence-soap-s"
            />
            <Textarea 
              label="O — Objetivo" 
              placeholder="Sinais vitais, exame físico, exames..."
              minRows={2} autosize 
              value={fields.o} onChange={e => setFields({...fields, o: e.currentTarget.value})}
              data-testid="florence-soap-o"
            />
            <Textarea 
              label="A — Avaliação" 
              placeholder="Diagnóstico, impressão clínica..."
              minRows={2} autosize 
              value={fields.a} onChange={e => setFields({...fields, a: e.currentTarget.value})}
              data-testid="florence-soap-a"
            />
            <Textarea 
              label="P — Plano" 
              placeholder="Conduta, medicações, orientações..."
              minRows={2} autosize 
              value={fields.p} onChange={e => setFields({...fields, p: e.currentTarget.value})}
              data-testid="florence-soap-p"
            />
          </>
        ) : (
          <Textarea 
            label="Anotação" 
            placeholder="Digite a anotação clínica..."
            minRows={6} autosize 
            value={fields.free} onChange={e => setFields({...fields, free: e.currentTarget.value})} 
          />
        )}

        <Button onClick={handleSave} loading={loading}>
          Salvar nota
        </Button>
      </Stack>
    </Paper>
  );
}
