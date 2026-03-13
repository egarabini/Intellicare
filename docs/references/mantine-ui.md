---
tipo: referencia
tecnologia: Mantine UI
versao: "7.x"
tags: [referencia, mantine, react, frontend, ui]
---

# Mantine UI — Referência Rápida

> Component library usada no frontend clínico (DEM-015). React 18 + TypeScript.

---

## Setup (Vite + React)

```tsx
// main.tsx
import { MantineProvider } from '@mantine/core';
import '@mantine/core/styles.css';

function App() {
  return (
    <MantineProvider theme={theme}>
      <RouterProvider router={router} />
    </MantineProvider>
  );
}
```

---

## Theme IntelliCare

```tsx
import { createTheme } from '@mantine/core';

const theme = createTheme({
  primaryColor: 'teal',      // cor principal clínica
  fontFamily: 'Inter, sans-serif',
  defaultRadius: 'md',
  components: {
    Button: { defaultProps: { size: 'sm' } },
    TextInput: { defaultProps: { size: 'sm' } },
  },
});
```

---

## Componentes mais usados

### Layout

```tsx
import { AppShell, NavLink, Group, Stack, Container } from '@mantine/core';

<AppShell navbar={{ width: 240 }} header={{ height: 56 }}>
  <AppShell.Header>...</AppShell.Header>
  <AppShell.Navbar>
    <NavLink label="Pacientes" href="/pacientes" />
    <NavLink label="Consultas" href="/consultas" />
  </AppShell.Navbar>
  <AppShell.Main>
    <Container size="lg">{children}</Container>
  </AppShell.Main>
</AppShell>
```

### Tabelas

```tsx
import { Table } from '@mantine/core';

<Table striped highlightOnHover>
  <Table.Thead>
    <Table.Tr>
      <Table.Th>Nome</Table.Th>
      <Table.Th>CPF</Table.Th>
    </Table.Tr>
  </Table.Thead>
  <Table.Tbody>{rows}</Table.Tbody>
</Table>
```

### Formulários

```tsx
import { useForm } from '@mantine/form';
import { TextInput, Button } from '@mantine/core';

const form = useForm({
  initialValues: { name: '', cpf: '' },
  validate: {
    name: (v) => (v.length < 2 ? 'Nome muito curto' : null),
    cpf: (v) => (v.length !== 11 ? 'CPF inválido' : null),
  },
});

<form onSubmit={form.onSubmit(handleSubmit)}>
  <TextInput label="Nome" {...form.getInputProps('name')} />
  <TextInput label="CPF" {...form.getInputProps('cpf')} />
  <Button type="submit">Salvar</Button>
</form>
```

### Notificações

```tsx
import { notifications } from '@mantine/notifications';

notifications.show({
  title: 'Sucesso',
  message: 'Paciente cadastrado',
  color: 'green',
});
```

---

## Hooks úteis

| Hook | Uso |
|------|-----|
| `useForm` | Formulários com validação |
| `useDisclosure` | Controlar modais/drawers |
| `useDebouncedValue` | Debounce em busca |
| `useMediaQuery` | Responsividade |

---

## Integração com TanStack Query

```tsx
import { useQuery } from '@tanstack/react-query';
import { Loader, Alert } from '@mantine/core';

function PatientList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['patients'],
    queryFn: () => api.get('/cuidado/patients'),
  });

  if (isLoading) return <Loader />;
  if (error) return <Alert color="red">{error.message}</Alert>;

  return <Table>...</Table>;
}
```

---

## Integração com Auth (Keycloak)

```tsx
import { useAuth } from 'react-oidc-context';

function Header() {
  const auth = useAuth();
  return (
    <Group>
      <Text>{auth.user?.profile.name}</Text>
      <Button onClick={() => auth.signoutRedirect()}>Sair</Button>
    </Group>
  );
}
```

---

## Links úteis

- [Mantine docs](https://mantine.dev)
- [Mantine form](https://mantine.dev/form/use-form/)
- [Mantine notifications](https://mantine.dev/x/notifications/)
- [AppShell](https://mantine.dev/core/app-shell/)

