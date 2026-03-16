import { AppShell, NavLink, Group, Avatar, Text, Badge } from '@mantine/core';
import { IconHome, IconCalendar, IconUsers, IconRobot, IconSettings, IconUsersGroup, IconStethoscope } from '@tabler/icons-react';
import { useAuth } from 'react-oidc-context';
import { useNavigate, useLocation } from 'react-router-dom';

const NAV_ITEMS = [
  { path: '/dashboard',  icon: IconHome,      label: 'Início' },
  { path: '/agenda',     icon: IconCalendar,  label: 'Agenda' },
  { path: '/patients',       icon: IconUsers,       label: 'Pacientes' },
  { path: '/groups',          icon: IconUsersGroup,  label: 'Grupos' },
  { path: '/professionals',   icon: IconStethoscope, label: 'Profissionais' },
  { path: '/clinical-users',  icon: IconUsers,       label: 'Equipe' },
  { path: '/assistant',       icon: IconRobot,       label: 'Assistente IA' },
  { path: '/profile',    icon: IconSettings,  label: 'Meu Perfil' },
];

export function ClinicoShell({ children }: { children: React.ReactNode }) {
  const auth = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const name = auth.user?.profile?.name ?? 'Clínico'
  const tenant = auth.user?.profile?.['tenant_slug'] ?? ''

  return (
    <AppShell navbar={{ width: 220, breakpoint: 'sm' }} padding="md">
      <AppShell.Navbar p="xs">
        <Group mb="md" px="xs">
          <Avatar radius="xl" color="blue">{name[0]}</Avatar>
          <div>
            <Text size="sm" fw={500}>{name as string}</Text>
            <Badge size="xs" color="gray">{tenant as string}</Badge>
          </div>
        </Group>
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.path}
            label={item.label}
            leftSection={<item.icon size={18} />}
            active={location.pathname.startsWith(item.path)}
            onClick={() => navigate(item.path)}
            mb={4}
          />
        ))}
        <NavLink
          label="Sair"
          mt="auto"
          onClick={() => void auth.signoutRedirect()}
          color="red"
        />
      </AppShell.Navbar>
      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  )
}
