import { useState } from 'react';
import { Button, SegmentedControl, Textarea, Stack, Paper } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import apiClient from '../api/client';

interface FlorenceNoteEditorProps {
  encounterId: string | number;
  patientId: string | number;
  onSaved: () => void;
}

export function FlorenceNoteEditor({ encounterId, patientId, onSaved }: FlorenceNoteEditorProps) {
  const [noteType, setNoteType] = useState<'FREE' | 'SOAP'>('FREE');
  const [loading, setLoading] = useState(false);
  const [fields, setFields] = useState({ s: '', o: '', a: '', p: '', free: '' });

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
            <Textarea 
              label="S — Subjetivo" 
              placeholder="Sintomas relatados pelo paciente..."
              minRows={2} autosize 
              value={fields.s} onChange={e => setFields({...fields, s: e.currentTarget.value})} 
            />
            <Textarea 
              label="O — Objetivo" 
              placeholder="Sinais vitais, exame físico, exames..."
              minRows={2} autosize 
              value={fields.o} onChange={e => setFields({...fields, o: e.currentTarget.value})} 
            />
            <Textarea 
              label="A — Avaliação" 
              placeholder="Diagnóstico, impressão clínica..."
              minRows={2} autosize 
              value={fields.a} onChange={e => setFields({...fields, a: e.currentTarget.value})} 
            />
            <Textarea 
              label="P — Plano" 
              placeholder="Conduta, medicações, orientações..."
              minRows={2} autosize 
              value={fields.p} onChange={e => setFields({...fields, p: e.currentTarget.value})} 
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
