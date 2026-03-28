# DEM-095 — Plano de Implementação

> **Status:** Concluido
> **Data:** 2026-03-28
> **Responsável:** Codex

## Objetivo

Eliminar colisões entre rotas de SPA e rotas de API no `server.proxy` dos frontends Vite, preservando o comportamento correto de desenvolvimento local com múltiplas portas.

## Plano executado

### Fase 1 — proxies Vite

1. **Diagnóstico do problema no AdminUI**
   - Validar se o Keycloak local estava disponível
   - Verificar o `AuthProvider` do `AdminUI`
   - Confirmar que a falha ocorria antes do fluxo de autenticação

2. **Isolamento da causa**
   - Levantar o `AdminUI` local
   - Observar erro interno no Vite ao acessar `/admin-ui/`
   - Confirmar que `/admin-ui/` estava sendo indevidamente capturado pelo proxy `/admin`

3. **Correção imediata**
   - Ajustar `frontend/AdminUI/vite.config.ts`
   - Ajustar `frontend/GestorUI/vite.config.ts` pelo mesmo risco estrutural

4. **Padronização transversal**
   - Aplicar o mesmo padrão regex exato em `ClinicoUI`, `PacienteUI` e `Portal`
   - Uniformizar a configuração para evitar regressões futuras

5. **Validação**
   - Executar build dos módulos afetados
   - Confirmar que a raiz `/admin-ui/` passou a responder corretamente no dev server

6. **Publicação**
   - Criar commit único com os `vite.config.ts`
   - Publicar em `origin/main`

### Fase 2 — logout para o Portal

1. **Diagnóstico complementar**
   - Validar o comportamento do botão `Sair` nos módulos autenticados
   - Confirmar que o logout encerrava a sessão, mas não retornava ao Portal

2. **Definição da regra**
   - em dev local, após logout, voltar para `http://localhost:5176/`
   - em domínio oficial, após logout, voltar para `https://intellicare.ia.br/`

3. **Implementação**
   - criar helper compartilhado `frontend/shared/authUrls.ts`
   - substituir `post_logout_redirect_uri` baseado na origem atual por `getPortalUrl()`

4. **Validação**
   - executar build dos módulos autenticados
   - garantir integridade dos imports compartilhados

5. **Publicação**
   - criar commit separado da Fase 2
   - publicar em `origin/main`

### Fase 3 — contrato explícito de Portal URL

1. **Diagnóstico do erro residual**
   - reproduzir `invalid redirect uri` no logout
   - confirmar desalinhamento entre frontend e redirect permitido no Keycloak

2. **Definir contrato de configuração**
   - frontend usa `VITE_PORTAL_URL`
   - infraestrutura/provisionamento usa `PORTAL_URL`

3. **Implementação**
   - atualizar helper compartilhado para priorizar `VITE_PORTAL_URL`
   - adicionar a variável aos `.env` locais e de produção dos frontends
   - registrar `PORTAL_URL` em `infra/.env.example`
   - atualizar `setup_keycloak.py` para provisionar redirects e origins com `PORTAL_URL`

4. **Validação**
   - rebuild dos módulos autenticados
   - reexecutar `setup_keycloak.py` local com `PORTAL_URL=http://localhost:5176`

5. **Publicação**
   - criar commit dedicado da Fase 3
   - publicar em `origin/main`

## Resultado esperado

- frontends locais continuam acessíveis em suas portas Vite dedicadas;
- APIs continuam sendo proxyadas corretamente;
- rotas de SPA deixam de ser sequestradas por prefixos ambíguos de proxy.
- logout dos módulos autenticados retorna ao Portal de forma consistente.
- redirect pós-logout passa a ser contrato explícito de configuração entre frontend e Keycloak.
