# DEM-035 — Notificações Frontend (Sino nos 4 Módulos)

## Objetivo

Adicionar um sino de notificações (`NotificationBell`) no header dos 4 módulos do IntelliCare (AdminUI, GestorUI, ClinicoUI, PacienteUI), consumindo em tempo real o endpoint SSE `/notifications/stream` implementado na DEM-026. O usuário deve ver o número de notificações não lidas e poder visualizá-las e marcá-las como lidas sem sair da página.

---

## Contexto

O módulo de notificações (DEM-026) está operacional no backend com 12 endpoints, SSE e WebSocket. Esta DEM conecta esse backend aos frontends: exibe o badge de contagem no header e uma lista recente acessível via clique no sino.

---

## Comportamentos esperados

### 1. Badge de contagem
- O sino aparece no header de todos os 4 módulos, à direita do título e à esquerda do e-mail do usuário
- O badge mostra o número de notificações não lidas (`is_read = false`)
- Se não há notificações não lidas, o badge não é exibido (zero fica oculto)
- O badge atualiza em tempo real via SSE — sem necessidade de recarregar a página

### 2. Popover ao clicar no sino
- Ao clicar no sino, abre um Popover/Drawer com as últimas 20 notificações (mistas: lidas e não lidas)
- Cada item exibe: título, mensagem resumida (máx. 80 chars), data relativa ("há 2 min"), indicador visual de não lida (fundo levemente colorido ou ponto azul)
- Clicar em uma notificação não lida a marca como lida (`PATCH /notifications/{id}/read`) e atualiza o badge imediatamente
- Exibe mensagem "Nenhuma notificação" quando a lista está vazia

### 3. SSE — conexão em tempo real
- Ao montar, o hook abre conexão SSE com `/notifications/stream` (token via query param)
- Novas notificações chegando via SSE são inseridas no topo da lista automaticamente
- Se SSE desconectar, o hook tenta reconectar após 5s (máx. 3 tentativas), depois para silenciosamente
- Se o backend não tiver o módulo de notificações ativo, o sino simplesmente não aparece (resposta 404 → componente renderiza `null`)

### 4. UX
- O sino usa `IconBell` do `@tabler/icons-react`; quando há não-lidas, exibe badge vermelho com a contagem (máx "9+" para ≥ 10)
- Clique fora do popover fecha-o
- O popover tem scroll interno para listas longas; altura máxima de 400px

---

## Canais afetados

| Módulo | Header atual | Ajuste necessário |
|--------|-------------|------------------|
| AdminUI | `<Group justify="space-between">` — Title + email | Adicionar `NotificationBell` entre os dois |
| GestorUI | `<Group justify="space-between">` — Title + Group(email + btn Sair) | Adicionar `NotificationBell` no Group direito, antes do email |
| ClinicoUI | `ClinicoShell` sem Header — apenas Navbar | **Adicionar `AppShell.Header` height 56** com Title + NotificationBell + nome do usuário |
| PacienteUI | `<Group justify="space-between">` — Title + email | Adicionar `NotificationBell` entre os dois |

---

## Critérios de aceitação

1. Badge com contagem correta aparece no header dos 4 módulos após login
2. SSE entrega nova notificação ao frontend em tempo real (criada via API → aparece no sino em < 5s)
3. Clicar em notificação não lida a marca como lida e decrementa o badge
4. Popover fecha ao clicar fora
5. Se módulo de notificações retornar 404, o sino não aparece (sem console error visível)
6. Em dispositivos mobile (breakpoint < sm), o sino continua visível no header
7. Nenhum módulo pré-existente quebra — todos os testes E2E existentes continuam passando
