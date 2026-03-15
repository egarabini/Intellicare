# DEM-033 — Portal: Seletor de Ambiente

## Objetivo

Substituir o botão "Explore a Plataforma" hardcoded para `/admin-ui/` por um modal de seleção de ambiente, permitindo que o usuário escolha explicitamente qual módulo deseja acessar com base no seu perfil.

---

## Problema identificado

O botão na `Hero` seção do portal apontava diretamente para `/admin-ui/`, levando qualquer visitante diretamente ao painel administrativo da plataforma, ignorando os outros 3 módulos (Gestor, Clínico, Paciente).

---

## Solução

Ao clicar em "Explore a Plataforma", um modal é aberto exibindo 4 cards — um para cada ambiente disponível.

---

## Ambientes disponíveis

| Ambiente | Perfil | URL de destino | Cor |
|----------|--------|----------------|-----|
| Administrativo | `PLATFORM_ADMIN` | `/admin-ui/` | Violeta |
| Gestor | `TENANT_GESTOR` | `/gestor-ui/` | Azul |
| Clínico | `CLINICO` | `/clinico-ui/` | Teal |
| Portal do Paciente | `PACIENTE` | `/paciente-ui/` | Verde |

---

## Layout do modal

```
┌─────────────────────────────────────────────┐
│ Selecionar Ambiente                    [✕]  │
│ Escolha o módulo de acordo com seu perfil   │
├──────────────────────┬──────────────────────┤
│ [🔐] Administrativo  │ [🏥] Gestor          │
│  Badge: Plataforma   │  Badge: Tenant       │
│  Gestão da plataforma│  Unidades, equipes,  │
│  servidores, módulos │  usuários do tenant  │
├──────────────────────┼──────────────────────┤
│ [🩺] Clínico         │ [👤] Portal Paciente │
│  Badge: Assistência  │  Badge: Paciente     │
│  Agenda, prontuário, │  Consultas, docs,    │
│  AI Assistant        │  agendamentos        │
└──────────────────────┴──────────────────────┘
```

### Comportamento

- Hover no card: eleva (translateY -3px) + borda colorida + seta `→` aparece
- Click no card: navega diretamente para o `href` do ambiente (sem fechar o modal antes)
- Modal fecha ao clicar fora ou no `✕`
- Overlay com `blur: 4`

---

## Critérios de aceitação

1. Botão "Explore a Plataforma" abre modal (não navega diretamente)
2. 4 cards exibidos em grid 2×2 (1 coluna em mobile)
3. Cada card exibe: ícone, nome do ambiente, badge de perfil, descrição
4. Click em qualquer card navega para o módulo correto
5. Hover com feedback visual (elevação + borda + seta)
6. Build sem erros TypeScript
