# DEM-033 — Portal: Seletor de Ambiente — Especificação Técnica

## 1. Arquivos alterados

### 1.1 Novo componente: `frontend/Portal/src/components/EnvironmentSelector.tsx`

Componente Mantine Modal com 4 cards interativos.

**Estrutura:**
```tsx
interface Environment {
  id: string;
  label: string;
  description: string;
  role: string;
  href: string;
  icon: React.ComponentType;
  color: string;       // cor Mantine (violet, blue, teal, green)
  badge: string;
}

const ENVIRONMENTS: Environment[] = [
  { id: 'admin',    href: '/admin-ui/',    color: 'violet', ... },
  { id: 'gestor',   href: '/gestor-ui/',   color: 'blue',   ... },
  { id: 'clinico',  href: '/clinico-ui/',  color: 'teal',   ... },
  { id: 'paciente', href: '/paciente-ui/', color: 'green',  ... },
];
```

**Ícones usados (`@tabler/icons-react`):**
- `IconShieldLock` — Administrativo
- `IconBuildingHospital` — Gestor
- `IconStethoscope` — Clínico
- `IconUser` — Paciente
- `IconArrowRight` — indicador de hover

**Props:**
```tsx
interface EnvironmentSelectorProps {
  opened: boolean;
  onClose: () => void;
}
```

---

### 1.2 Atualizado: `frontend/Portal/src/components/Hero.tsx`

```tsx
import { useState } from 'react';
import { EnvironmentSelector } from './EnvironmentSelector';

export function Hero() {
  const [selectorOpened, setSelectorOpened] = useState(false);

  return (
    <>
      <Box ...>
        {/* ... */}
        <Button size="xl" color="teal" onClick={() => setSelectorOpened(true)}>
          Explore a Plataforma
        </Button>
        {/* ... */}
      </Box>

      <EnvironmentSelector
        opened={selectorOpened}
        onClose={() => setSelectorOpened(false)}
      />
    </>
  );
}
```

**Mudança chave:** `component="a" href="/admin-ui/"` → `onClick={() => setSelectorOpened(true)}`

---

## 2. Traefik — Fix `http://intellicare.ia.br` 403

### Problema

A rota `intellicare-portal-http` usava o middleware `redirect-to-https`, que redireciona HTTP → HTTPS. Como o certificado Let's Encrypt ainda não foi emitido (DNS apontou para o VPS recentemente), o endpoint HTTPS não tem cert válido → 403/SSL error.

### Fix em `infra/docker-compose.yml`

```yaml
# ANTES (redireciona HTTP → HTTPS — falha sem cert):
- "traefik.http.routers.intellicare-portal-http.middlewares=redirect-to-https"

# DEPOIS (serve HTTP direto via o mesmo service do HTTPS):
- "traefik.http.routers.intellicare-portal-http.service=intellicare-portal"
```

O service `intellicare-portal` já está definido:
```yaml
- "traefik.http.services.intellicare-portal.loadbalancer.server.port=8000"
```

**Resultado:** `http://intellicare.ia.br` serve o portal via HTTP enquanto o cert Let's Encrypt não é emitido. Quando o cert for emitido, `https://intellicare.ia.br` também funcionará automaticamente.

> **Nota:** O cert Let's Encrypt será emitido automaticamente pelo Traefik na próxima tentativa ACME (ocorre dentro de minutos após DNS propagar e Traefik reiniciar). Para forçar: deletar `infra/letsencrypt/acme.json` no VPS e fazer `docker compose restart traefik`.

---

## 3. Sequência de execução

```bash
# 1. Build do Portal
cd frontend/Portal && npx vite build

# 2. Aplicar as statics (volume mount já cuida disso — apenas restart)
docker compose --env-file infra/.env -f infra/docker-compose.yml \
  restart intellicare-service

# 3. Recriar o container Traefik com a nova config (docker-compose.yml alterado)
docker compose --env-file infra/.env -f infra/docker-compose.yml \
  up -d traefik

# (Opcional) Forçar reemissão do cert Let's Encrypt:
# rm -f infra/letsencrypt/acme.json
# docker compose --env-file infra/.env -f infra/docker-compose.yml restart traefik
```

---

## 4. Checklist de entrega

- [ ] `EnvironmentSelector.tsx` criado com 4 cards
- [ ] `Hero.tsx` atualizado — botão abre modal
- [ ] Hover nos cards: eleva + borda colorida + seta
- [ ] Click em card: navega para o módulo correto
- [ ] `docker-compose.yml`: `intellicare-portal-http` serve HTTP direto (sem redirect)
- [ ] Build sem erros TypeScript
- [ ] `http://intellicare.ia.br` acessível no VPS
- [ ] Commit: `feat(DEM-033): portal - seletor de ambiente + fix traefik http`
