import { useState } from 'react';
import {
  Modal,
  SimpleGrid,
  Card,
  Text,
  ThemeIcon,
  Stack,
  Title,
  Badge,
  Group,
  Anchor,
} from '@mantine/core';
import {
  IconShieldLock,
  IconBuildingHospital,
  IconStethoscope,
  IconUser,
  IconArrowRight,
} from '@tabler/icons-react';

interface Environment {
  id: string;
  label: string;
  description: string;
  role: string;
  subdomain: string;
  path: string;
  icon: any;
  color: string;
  badge: string;
}

const ENVIRONMENTS: Environment[] = [
  {
    id: 'admin',
    label: 'Administrativo',
    description: 'Gestão da plataforma, servidores, módulos, financeiro e usuários administradores.',
    role: 'PLATFORM_ADMIN',
    subdomain: 'admin',
    path: '/admin-ui/',
    icon: IconShieldLock,
    color: 'violet',
    badge: 'Plataforma',
  },
  {
    id: 'gestor',
    label: 'Gestor',
    description: 'Controle do tenant: unidades de saúde, equipes, usuários e relatórios de uso.',
    role: 'TENANT_GESTOR',
    subdomain: 'gestor',
    path: '/gestor-ui/',
    icon: IconBuildingHospital,
    color: 'blue',
    badge: 'Tenant',
  },
  {
    id: 'clinico',
    label: 'Clínico',
    description: 'Agenda, prontuário eletrônico, CID-10, AI Assistant e gestão de profissionais.',
    role: 'CLINICO',
    subdomain: 'clinico',
    path: '/clinico-ui/',
    icon: IconStethoscope,
    color: 'teal',
    badge: 'Assistência',
  },
  {
    id: 'paciente',
    label: 'Portal do Paciente',
    description: 'Histórico de consultas, documentos, agendamentos e acesso ao perfil pessoal.',
    role: 'PACIENTE',
    subdomain: 'paciente',
    path: '/paciente-ui/',
    icon: IconUser,
    color: 'green',
    badge: 'Paciente',
  },
];

const LOCAL_DEV_PORTS: Record<string, string> = {
  admin: '5174',
  gestor: '5175',
  clinico: '5173',
  paciente: '5177',
};

const getEnvUrl = (subdomain: string, path: string) => {
  if (typeof window === 'undefined') return path;
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname.startsWith('127.')) {
    // Redireciona para os servidores Vite isolados de desenvolvimento local
    const devPort = LOCAL_DEV_PORTS[subdomain];
    if (devPort) {
      return `http://${hostname}:${devPort}${path}`;
    }
    return path;
  }
  // Remove possible subdomains to get root domain: e.g. intellicare.ia.br
  const rootDomain = hostname.split('.').slice(-3).join('.') === 'intellicare.ia.br' 
    ? 'intellicare.ia.br' 
    : hostname; 
  return `https://${subdomain}.${rootDomain}${path}`;
};

interface EnvironmentSelectorProps {
  opened: boolean;
  onClose: () => void;
}

export function EnvironmentSelector({ opened, onClose }: EnvironmentSelectorProps) {
  const [hovered, setHovered] = useState<string | null>(null);

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={
        <Stack gap={4}>
          <Title order={3}>Selecionar Ambiente</Title>
          <Text size="sm" c="dimmed">
            Escolha o módulo de acesso de acordo com seu perfil
          </Text>
        </Stack>
      }
      size="xl"
      centered
      overlayProps={{ blur: 4 }}
    >
      <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md" mt="xs">
        {ENVIRONMENTS.map((env) => {
          const Icon = env.icon;
          const isHovered = hovered === env.id;
          return (
            <Anchor
              key={env.id}
              href={getEnvUrl(env.subdomain, env.path)}
              underline="never"
              onMouseEnter={() => setHovered(env.id)}
              onMouseLeave={() => setHovered(null)}
            >
              <Card
                shadow={isHovered ? 'md' : 'xs'}
                radius="md"
                withBorder
                p="lg"
                style={{
                  cursor: 'pointer',
                  transition: 'transform 0.15s ease, box-shadow 0.15s ease',
                  transform: isHovered ? 'translateY(-3px)' : 'none',
                  borderColor: isHovered ? `var(--mantine-color-${env.color}-4)` : undefined,
                }}
              >
                <Stack gap="sm">
                  <Group justify="space-between" align="flex-start">
                    <ThemeIcon size={48} radius="md" color={env.color} variant="light">
                      <Icon size={26} stroke={1.5} />
                    </ThemeIcon>
                    <Badge color={env.color} variant="light" size="sm">
                      {env.badge}
                    </Badge>
                  </Group>

                  <div>
                    <Group gap={6} align="center">
                      <Text fw={700} size="lg">
                        {env.label}
                      </Text>
                      {isHovered && (
                        <IconArrowRight size={16} stroke={2} color={`var(--mantine-color-${env.color}-6)`} />
                      )}
                    </Group>
                    <Text size="xs" c="dimmed" mb={4}>
                      Perfil: {env.role}
                    </Text>
                    <Text size="sm" c="dimmed" lh={1.5}>
                      {env.description}
                    </Text>
                  </div>
                </Stack>
              </Card>
            </Anchor>
          );
        })}
      </SimpleGrid>
    </Modal>
  );
}
