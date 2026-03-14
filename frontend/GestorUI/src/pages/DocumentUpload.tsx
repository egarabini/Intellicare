import { useState } from 'react'
import {
  ActionIcon,
  Badge,
  Group,
  Paper,
  Progress,
  Stack,
  Table,
  Text,
  Title,
  Tooltip,
} from '@mantine/core'
import { Dropzone, MIME_TYPES } from '@mantine/dropzone'
import { IconFile, IconTrash, IconUpload, IconX } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'

import { useDeleteDocument, useDocuments, useUploadDocument } from '../hooks/useDocuments'

export function DocumentUpload() {
  const { data: docs, isLoading } = useDocuments()
  const upload = useUploadDocument()
  const deleteDoc = useDeleteDocument()
  const [uploading, setUploading] = useState(false)

  const handleDrop = async (files: File[]) => {
    setUploading(true)
    for (const file of files) {
      try {
        await upload.mutateAsync(file)
        notifications.show({
          title: 'Upload concluído',
          message: `${file.name} ingerido com sucesso.`,
          color: 'green',
        })
      } catch {
        notifications.show({
          title: 'Erro no upload',
          message: `Falha ao processar ${file.name}.`,
          color: 'red',
        })
      }
    }
    setUploading(false)
  }

  const handleDelete = async (path: string) => {
    try {
      await deleteDoc.mutateAsync(path)
      notifications.show({ title: 'Removido', message: path, color: 'orange' })
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao remover.', color: 'red' })
    }
  }

  return (
    <Stack>
      <Title order={2}>Base de Conhecimento</Title>

      <Dropzone
        onDrop={handleDrop}
        accept={[
          MIME_TYPES.pdf,
          'application/msword',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        ]}
        maxSize={20 * 1024 * 1024}
        loading={uploading}
      >
        <Group justify="center" gap="xl" mih={100}>
          <Dropzone.Accept><IconUpload size={48} color="blue" /></Dropzone.Accept>
          <Dropzone.Reject><IconX size={48} color="red" /></Dropzone.Reject>
          <Dropzone.Idle><IconFile size={48} color="gray" /></Dropzone.Idle>
          <Stack gap={4} align="center">
            <Text size="lg" fw={500}>Arraste PDFs ou DOCXs aqui</Text>
            <Text size="sm" c="dimmed">Maximo 20 MB por arquivo</Text>
          </Stack>
        </Group>
      </Dropzone>

      {uploading && <Progress value={100} animated />}

      <Paper withBorder>
        <Table highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Arquivo</Table.Th>
              <Table.Th>Chunks</Table.Th>
              <Table.Th>Ultima atualizacao</Table.Th>
              <Table.Th>Acoes</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {docs?.map((d) => (
              <Table.Tr key={d.source_path}>
                <Table.Td>
                  <Text size="sm" ff="monospace">{d.source_path.split('/').pop()}</Text>
                </Table.Td>
                <Table.Td>
                  <Badge variant="light">{d.chunk_count} chunks</Badge>
                </Table.Td>
                <Table.Td>
                  {new Date(d.last_ingested_at).toLocaleDateString('pt-BR')}
                </Table.Td>
                <Table.Td>
                  <Tooltip label="Remover da base">
                    <ActionIcon
                      color="red"
                      variant="subtle"
                      onClick={() => handleDelete(d.source_path)}
                      loading={deleteDoc.isPending}
                    >
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Tooltip>
                </Table.Td>
              </Table.Tr>
            ))}
            {!isLoading && !docs?.length && (
              <Table.Tr>
                <Table.Td colSpan={4}>
                  <Text ta="center" c="dimmed" py="lg">Nenhum documento na base.</Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>
      </Paper>
    </Stack>
  )
}
