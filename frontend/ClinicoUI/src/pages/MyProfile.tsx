import { Box, Title, Text, Card, Group, Stack, Avatar, Button, FileInput, TextInput, Badge, Alert } from '@mantine/core';
import { IconCertificate, IconUpload, IconTrash, IconShieldCheck } from '@tabler/icons-react';
import { useAuth } from 'react-oidc-context';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import apiClient from '../api/client';

interface CertificateStatus {
  has_certificate: boolean;
  subject_name?: string;
  valid_until?: string;
}

function useCertificateStatus() {
  return useQuery<CertificateStatus>({
    queryKey: ['certificate-status'],
    queryFn: async () => {
      const { data } = await apiClient.get('/oswaldo/professionals/me/certificate');
      return data;
    },
    retry: false,
  });
}

function useUploadCertificate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, password }: { file: File; password: string }) => {
      const form = new FormData();
      form.append('file', file);
      form.append('password', password);
      const { data } = await apiClient.post('/oswaldo/professionals/me/certificate', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['certificate-status'] }),
  });
}

function useDeleteCertificate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await apiClient.delete('/oswaldo/professionals/me/certificate');
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['certificate-status'] }),
  });
}

export function MyProfile() {
  const auth = useAuth();
  const p = auth.user?.profile;
  const name = p?.name ?? 'Clínico';
  const email = p?.email ?? '';
  const tenant = p?.['tenant_slug'] ?? '';

  const certQuery = useCertificateStatus();
  const uploadMut = useUploadCertificate();
  const deleteMut = useDeleteCertificate();

  const [pfxFile, setPfxFile] = useState<File | null>(null);
  const [pfxPassword, setPfxPassword] = useState('');

  const handleUpload = () => {
    if (!pfxFile || !pfxPassword) return;
    uploadMut.mutate({ file: pfxFile, password: pfxPassword }, {
      onSuccess: () => { setPfxFile(null); setPfxPassword(''); },
    });
  };

  return (
    <Box>
      <Title order={2} mb="lg">Meu Perfil</Title>

      <Card withBorder shadow="sm" radius="md" maw={600} mb="lg">
        <Group>
          <Avatar size="xl" color="blue" radius="xl">{(name as string)[0]}</Avatar>
          <Stack gap={0}>
            <Title order={3}>{name as string}</Title>
            <Text c="dimmed">{email as string}</Text>
          </Stack>
        </Group>

        <Stack mt="xl" gap="xs">
          <Group justify="space-between">
            <Text fw={500}>Cargo / Role:</Text>
            <Text>{((p?.realm_access as any)?.roles as string[])?.includes('CLINICO') ? 'Clínico (CLINICO)' : 'Administrador'}</Text>
          </Group>
          <Group justify="space-between">
            <Text fw={500}>Tenant Principal:</Text>
            <Text>{tenant as string}</Text>
          </Group>
        </Stack>
      </Card>

      {/* ── Certificado Digital A1 ───────────────────────────────── */}
      <Card withBorder shadow="sm" radius="md" maw={600}>
        <Group mb="md">
          <IconCertificate size={24} />
          <Title order={4}>Certificado Digital</Title>
        </Group>

        {certQuery.data?.has_certificate ? (
          <Stack gap="sm">
            <Alert icon={<IconShieldCheck size={20} />} color="green" variant="light">
              Certificado ativo — receituários serão assinados digitalmente.
            </Alert>
            <Group justify="space-between">
              <Text fw={500}>Titular:</Text>
              <Text size="sm">{certQuery.data.subject_name}</Text>
            </Group>
            <Group justify="space-between">
              <Text fw={500}>Validade:</Text>
              <Badge color={new Date(certQuery.data.valid_until!) > new Date() ? 'green' : 'red'}>
                {certQuery.data.valid_until}
              </Badge>
            </Group>
            <Button
              color="red"
              variant="light"
              leftSection={<IconTrash size={16} />}
              loading={deleteMut.isPending}
              onClick={() => deleteMut.mutate()}
            >
              Remover Certificado
            </Button>
          </Stack>
        ) : (
          <Stack gap="sm">
            <Text size="sm" c="dimmed">
              Envie seu certificado ICP-Brasil tipo A1 (.pfx) para assinar receituários digitalmente.
            </Text>
            <FileInput
              label="Arquivo .pfx"
              placeholder="Selecionar certificado"
              accept=".pfx"
              leftSection={<IconUpload size={16} />}
              value={pfxFile}
              onChange={setPfxFile}
            />
            <TextInput
              label="Senha do certificado"
              type="password"
              placeholder="Digite a senha do .pfx"
              value={pfxPassword}
              onChange={(e) => setPfxPassword(e.currentTarget.value)}
            />
            {uploadMut.isError && (
              <Alert color="red" variant="light">
                {(uploadMut.error as any)?.response?.data?.detail ?? 'Erro ao enviar certificado'}
              </Alert>
            )}
            <Button
              leftSection={<IconCertificate size={16} />}
              loading={uploadMut.isPending}
              disabled={!pfxFile || !pfxPassword}
              onClick={handleUpload}
            >
              Enviar Certificado
            </Button>
          </Stack>
        )}
      </Card>
    </Box>
  );
}
