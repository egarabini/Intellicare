import { Stack, Card, Text, Badge, Group, TypographyStylesProvider } from '@mantine/core';

export interface ClinicalNote {
  id: number;
  encounter_id: number;
  patient_id: number;
  author_name: string;
  note_type: 'FREE' | 'SOAP';
  soap_s?: string;
  soap_o?: string;
  soap_a?: string;
  soap_p?: string;
  free_text?: string;
  created_at: string;
}

interface FlorenceNoteListProps {
  notes: ClinicalNote[];
}

export function FlorenceNoteList({ notes }: FlorenceNoteListProps) {
  if (!notes || notes.length === 0) {
    return (
      <Text c="dimmed" fs="italic" ta="center" mt="xl">
        Nenhuma anotação registrada neste encontro.
      </Text>
    );
  }

  return (
    <Stack gap="sm" mt="md">
      {notes.map((note) => (
        <Card key={note.id} withBorder shadow="sm" radius="md" padding="md">
          <Group justify="space-between" mb="xs">
            <Group gap="xs">
              <Text fw={500}>{note.author_name}</Text>
              <Text size="xs" c="dimmed">
                {new Date(note.created_at).toLocaleString('pt-BR')}
              </Text>
            </Group>
            <Badge color={note.note_type === 'SOAP' ? 'blue' : 'gray'} variant="light">
              {note.note_type}
            </Badge>
          </Group>

          {note.note_type === 'SOAP' ? (
            <Stack gap="xs">
              {note.soap_s && <div><Text fw={600} size="sm">S:</Text><Text size="sm">{note.soap_s}</Text></div>}
              {note.soap_o && <div><Text fw={600} size="sm">O:</Text><Text size="sm">{note.soap_o}</Text></div>}
              {note.soap_a && <div><Text fw={600} size="sm">A:</Text><Text size="sm">{note.soap_a}</Text></div>}
              {note.soap_p && <div><Text fw={600} size="sm">P:</Text><Text size="sm">{note.soap_p}</Text></div>}
            </Stack>
          ) : (
            <TypographyStylesProvider p={0}>
              <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                {note.free_text}
              </Text>
            </TypographyStylesProvider>
          )}
        </Card>
      ))}
    </Stack>
  );
}
