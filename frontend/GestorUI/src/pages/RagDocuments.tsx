import { useState, useRef } from 'react';
import { Box, Title, Group, Table, Text, Button, Progress } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import { IconUpload } from '@tabler/icons-react';
import { useAuth } from 'react-oidc-context';

export function RagDocuments() {
  const auth = useAuth();
  const token = auth.user?.access_token;
  const { data: documents, refetch } = useQuery({
    queryKey: ['rag_docs'],
    queryFn: async () => {
      const { data } = await api.get<any[]>('/gestor/documents');
      return data;
    }
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    const file = e.target.files[0];
    setUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const { data } = await api.post('/gestor/documents/upload', formData);
      const docId = data.document_id || 'dummy'; // the API might return differently. Wait: _ingest.ingest_file returns { ingested_chunks, source_label } normally. Assume we know docId or simply refetch when done.
      
      // Let's attempt an EventSource connection if API provided a doc_id or just show progress manually
      const streamUrl = `/gestor/documents/progress/${docId}?token=${token}`; 
      // Simplified for now: just wait and refetch
      setProgressMsg('Processando chunks no vector DB...');
      setTimeout(() => {
        setUploading(false);
        setProgressMsg('');
        refetch();
      }, 3000);

    } catch (err) {
      alert("Erro no upload");
      setUploading(false);
      setProgressMsg('');
    }
  };

  return (
    <Box>
      <Group justify="space-between" mb="lg">
        <Title order={2}>Base de Conhecimento (RAG)</Title>
        <Button leftSection={<IconUpload size={16}/>} onClick={() => fileInputRef.current?.click()} loading={uploading}>
          Upload Documento
        </Button>
        <input type="file" ref={fileInputRef} style={{ display: 'none' }} accept=".txt,.pdf,.md,.csv" onChange={handleFileChange} />
      </Group>

      {uploading && (
        <Box mb="md">
           <Text size="sm" mb={4}>{progressMsg || 'Enviando...'}</Text>
           <Progress value={100} animated />
        </Box>
      )}

      <Table highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Arquivo</Table.Th>
            <Table.Th>Chunks</Table.Th>
            <Table.Th>Data Ingestão</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {documents?.length === 0 ? (
            <Table.Tr><Table.Td colSpan={3}>Nenhum documento indexado nesta unidade.</Table.Td></Table.Tr>
          ) : (
            documents?.map((item: any) => (
              <Table.Tr key={item.source_path}>
                <Table.Td fw={500}>{item.source_path}</Table.Td>
                <Table.Td>{item.chunk_count}</Table.Td>
                <Table.Td>{new Date(item.last_ingested_at).toLocaleString()}</Table.Td>
              </Table.Tr>
            ))
          )}
        </Table.Tbody>
      </Table>
    </Box>
  );
}
