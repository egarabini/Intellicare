# INTEGRAÇÃO DE SEGURANÇA IAM — INTELLICARE-AUTH/KEYCLOAK

## Objetivo
Integrar autenticação e autorização centralizadas (IAM) via Keycloak, usando a biblioteca intellicare-auth, em todos os módulos do ecossistema IntelliCare.

---

## Status Atual
- Biblioteca intellicare-auth pronta e funcional
- Nenhum módulo ainda utiliza Keycloak
- Próximos passos definidos em STATUS.md

---

## Plano de Integração

### 1. Provisionamento Keycloak
- Executar `setup_keycloak.py` para gerar `keycloak_client_secrets.json` com credenciais de cada módulo
- Validar configuração de realms, clients e roles conforme documentação

### 2. Integração Piloto
- Integrar intellicare-auth no módulo Donabedian como piloto
- Testar autenticação (login, token JWT), autorização (roles, scopes) e refresh
- Corrigir eventuais divergências de escopo/fluxo

### 3. Expansão para Wanda e Core
- Integrar nos módulos Wanda e Core, validando fluxos de autenticação e autorização
- Documentar exemplos de uso e pontos de integração

### 4. Rollout para demais módulos
- Replicar integração nos demais módulos (total 9)
- Garantir cobertura de testes e documentação

---

## Pontos de Atenção
- Todos os endpoints sensíveis devem exigir autenticação JWT
- Roles e scopes devem ser validados conforme perfil do usuário
- Tokens e segredos nunca devem ser expostos em logs ou frontends
- Atualizar README/DEVLOG de cada módulo com instruções de uso

---

## Referências
- `./intellicare-auth/` — biblioteca e scripts de setup
- `./intellicare-donabedian/` — piloto de integração
- `./intellicare-wanda/` — integração prioritária
- `STATUS.md` — cronograma e próximos passos

---

*Prioridade: Alta — conforme documento 05*
*Responsável: GitHub Copilot — 17/02/2026*
