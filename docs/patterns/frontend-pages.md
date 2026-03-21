# Frontend Pages

Padroes derivados principalmente de DEM-040, DEM-041, DEM-045 e das paginas atuais de GestorUI e ClinicoUI.

## Hook em `src/hooks/`, UI na pagina

### Evidencia concreta
- DEM-040 colocou `useCareplannerTasks`, `useCareplannerTask`, `useVideoSession`, `useTriggerJourney` e `useCloseTask` em [`frontend/GestorUI/src/hooks/useGestor.ts`](/c:/Users/egara/INTELLICARE/frontend/GestorUI/src/hooks/useGestor.ts).
- DEM-045 repetiu a separacao no ClinicoUI com `useCareplanner.ts`, em vez de importar hook do GestorUI entre apps distintos.
- [`frontend/GestorUI/src/pages/ProfilePage.tsx`](/c:/Users/egara/INTELLICARE/frontend/GestorUI/src/pages/ProfilePage.tsx) mostra o mesmo padrao: pagina controla estado e invoca hook de dados/mutacao.

### Regra
- Chamada HTTP, cache e invalidacao ficam no hook.
- Componente de pagina decide layout, filtro, modal e notificacao.
- Nao compartilhar hook de um frontend para outro quando os apps sao buildados separadamente.

## Pagina list/detail com cache e refetch curto

### Caso real
- DEM-040 definiu dashboard de jornadas e tela de detalhe.
- Em [`frontend/GestorUI/src/hooks/useGestor.ts`](/c:/Users/egara/INTELLICARE/frontend/GestorUI/src/hooks/useGestor.ts), `useCareplannerTasks` usa `queryKey` com filtro e pagina e faz `refetchInterval: 15_000`.
- O detalhe usa `useCareplannerTask(correlationId)` com `refetchInterval: 10_000`.

### Regra
- Lista usa `queryKey` com todos os filtros visiveis.
- Mutacao invalida a lista e o agregado relacionado, nao apenas o detalhe local.
- Quando a tela precisa refletir status operacional, o projeto prefere refetch interval curto a websockets improvisados.

## Layout de detalhe: info principal e timeline

### Caso real
- DEM-040 definiu o detalhe da jornada com timeline.
- DEM-045 manteve o detalhe clinico em modo read-only, preservando card de dados e timeline de eventos.

### Regra
- Detail page do dominio tende a separar contexto principal e historico de eventos/acoes.
- Quando o usuario tem menos permissao, a pagina reaproveita o mesmo detalhe e remove as mutacoes, em vez de duplicar fluxo.

## Mantine 7: preferir o componente simples quando o caso e simples

### Evidencia concreta
- [`frontend/GestorUI/src/pages/ProfilePage.tsx`](/c:/Users/egara/INTELLICARE/frontend/GestorUI/src/pages/ProfilePage.tsx) usa `NativeSelect` para tipo de unidade.
- Nas DEMs de CarePlanner, `Badge` aparece sempre com `variant` e `size`, sem depender de props menos estaveis.
- `TextInput` e `useForm` nas DEM-040/041 seguem o fluxo `form.getInputProps(...)` ou `value/onChange`, sem redundar dois modelos ao mesmo tempo.

### Regra
- Dropdown simples: `NativeSelect`.
- Campo controlado por form: nao somar `getInputProps` com `onChange` extra sem necessidade.
- Badge de status: padronizar em `variant="light"` e cor derivada de mapa de status.

## Canal e filtro nao podem ficar hardcoded

### Caso real
- DEM-041 introduziu templates por `channel` e obrigou o frontend a carregar templates filtrados por canal ativo.
- O payload de trigger em `useGestor.ts` e os testes E2E de `careplanner_multicanal.spec.ts` mostram que `rocketchat`, `whatsapp` e `sms` precisam trafegar do formulario ate a API.

### Regra
- Hook que busca dado dependente de canal precisa receber `channel` como parametro.
- Se um canal novo entrar no enum e a UI continuar assumindo Rocket.Chat, o bug vai reaparecer no trigger e no dispatcher.

## OIDC de SPA: raiz da app, nao callback ficticio

### Evidencia concreta
- [`frontend/GestorUI/src/auth/AuthProvider.tsx`](/c:/Users/egara/INTELLICARE/frontend/GestorUI/src/auth/AuthProvider.tsx) usa `redirect_uri: ${window.location.origin}/gestor-ui/`.
- [`frontend/ClinicoUI/src/auth/AuthProvider.tsx`](/c:/Users/egara/INTELLICARE/frontend/ClinicoUI/src/auth/AuthProvider.tsx) usa `redirect_uri: ${window.location.origin}/clinico-ui/`.
- [`frontend/PacienteUI/src/auth/AuthProvider.tsx`](/c:/Users/egara/INTELLICARE/frontend/PacienteUI/src/auth/AuthProvider.tsx) segue a mesma regra com `/paciente-ui/`.

### Regra
- SPA do IntelliCare captura o retorno do OIDC na propria raiz da app.
- Se o ambiente apontar para `/callback`, a navegacao quebra porque essa rota nao existe como pagina real.
