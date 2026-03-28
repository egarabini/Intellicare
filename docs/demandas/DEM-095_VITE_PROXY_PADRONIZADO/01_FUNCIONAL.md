# DEM-095 — Proxies Vite Padronizados

## Contexto

Durante a validação do seletor de ambientes do Portal em desenvolvimento local, o redirecionamento para `AdminUI` e `GestorUI` expôs um problema de infraestrutura de frontend:

- o Portal passou a redirecionar corretamente para as portas Vite de cada módulo;
- ao acessar `http://localhost:5174/admin-ui/`, a navegação não chegava ao fluxo de login do Keycloak;
- o mesmo risco estrutural existia para `GestorUI`.

O diagnóstico mostrou que o problema não era o Keycloak local, e sim a configuração de proxy do Vite: rotas de API como `/admin` e `/gestor` estavam capturando indevidamente as próprias rotas das SPAs (`/admin-ui/`, `/gestor-ui/`) por compartilharem o mesmo prefixo textual.

## Problema

Em ambiente local, o Vite deve:

1. servir a SPA na rota base do módulo;
2. encaminhar apenas chamadas de API para o backend Python.

Quando o proxy usa prefixos genéricos como `'/admin'`, qualquer caminho iniciado por esse texto pode ser tratado como API. Isso quebra o bootstrap do frontend e impede o fluxo normal de autenticação OIDC.

## Objetivo

Padronizar os proxies dos frontends Vite para usar match exato por prefixo de API, evitando colisão com as rotas públicas das SPAs.

## Escopo

- `frontend/AdminUI/vite.config.ts`
- `frontend/GestorUI/vite.config.ts`
- `frontend/ClinicoUI/vite.config.ts`
- `frontend/PacienteUI/vite.config.ts`
- `frontend/Portal/vite.config.ts`

## Critérios de aceite

- [ ] Nenhum proxy Vite usa prefixo ambíguo do tipo `'/admin'`, `'/gestor'`, `'/health'` sem delimitação
- [ ] Os proxies passam a usar regex com fronteira de rota, por exemplo `^/admin(?:/|$)`
- [ ] `AdminUI` em `http://localhost:5174/admin-ui/` deixa de ser interceptado pelo proxy `/admin`
- [ ] `GestorUI` em `http://localhost:5175/gestor-ui/` deixa de ser vulnerável ao mesmo problema
- [ ] Os builds dos frontends alterados executam sem erro

## Fora de escopo

- Alterar autenticação do Keycloak
- Alterar rotas do backend Python
- Alterar a lógica do seletor de ambientes do Portal
- Publicar mudanças em staging ou produção
