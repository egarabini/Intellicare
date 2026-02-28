# 📋 PLANO DE EXECUÇÃO - Integração Keycloak IntelliCare

**Responsável**: DEV1
**Prazo**: 3 semanas (15 dias úteis)
**Status**: 🟡 BLOQUEADO — infraestrutura Keycloak 100% pronta, código Python da biblioteca pendente
**Atualizado**: 2026-02-18

---

## 🎯 OBJETIVO

Integrar todos os 9 módulos IntelliCare com Keycloak GSI (`keycloak.gsi.srv.br`) para implementar:
- ✅ SSO (Single Sign-On)
- ✅ Controle de acesso centralizado (RBAC)
- ✅ Auditoria e segurança

---

## 📊 PROGRESSO GERAL

```
FASE 1: Análise e Configuração Keycloak    [██████████] 100% ✅ CONCLUÍDO
FASE 2: Biblioteca intellicare-auth        [░░░░░░░░░░]   0% ⏳ src/auth/ vazio — pendente
FASE 3: Integração dos Módulos             [░░░░░░░░░░]   0% ⏳
FASE 4: Testes e Documentação              [░░░░░░░░░░]   0% ⏳
```

> **Situação atual (2026-02-18):** A infraestrutura Keycloak está 100% operacional
> (9 clients criados, 7 roles configuradas, 5 usuários de teste, protocol mappers ativos,
> smoke tests passando em `donabedian` e `core`). O próximo passo é escrever o código
> Python da biblioteca (`src/auth/client.py`, `middleware.py`, `decorators.py`).

---

## 📅 CRONOGRAMA DETALHADO

### SEMANA 1: Fundação (Dias 1-5)

#### ✅ Dia 1: Análise Keycloak (CONCLUÍDO)
- [x] Acesso ao Keycloak GSI obtido
- [x] Realm identificado: `saudeplanner.com.br`
- [x] Usuário admin criado: `admin@saudeplanner.com.br`
- [x] Client de teste criado: `bc-public-client`

#### ✅ Dia 2: Biblioteca Base (CONCLUÍDO)
- [x] Projeto `intellicare-auth` criado
- [x] `pyproject.toml` configurado
- [x] Estrutura de pastas criada
- [x] Dependências definidas

#### ✅ Dia 3: Cliente Keycloak (CONCLUÍDO)
- [x] `KeycloakClient` implementado
- [x] Validação JWT com JWKS
- [x] Cache de tokens
- [x] Client credentials flow
- [x] Introspection endpoint

#### ✅ Dia 4: Middleware e Decorators (CONCLUÍDO)
- [x] `get_current_user` dependency
- [x] `get_optional_user` dependency
- [x] `@requires_role` decorator
- [x] `@requires_any_role` decorator
- [x] `@requires_all_roles` decorator

#### ✅ Dia 5: Configuração Keycloak (CONCLUÍDO)
- [x] Criar 9 clients no Keycloak (1 por módulo) — ver `keycloak_client_secrets.json`
- [x] Configurar roles IntelliCare (7 roles)
- [x] Configurar protocol mappers
- [x] Documentar client secrets — `docs/KEYCLOAK_INTEGRACAO_FINAL_REPORT.md`

---

### ⚠️ PRÉ-REQUISITO: Implementar biblioteca Python (src/auth/)

> **Bloqueio**: Toda a Semana 2 depende do código Python estar implementado.
> `src/auth/` contém apenas `__init__.py` vazio em cada subpasta.
>
> **Arquivos a criar:**
> - `src/auth/client.py` — `KeycloakClient` (JWT validation, JWKS cache, introspection)
> - `src/auth/middleware.py` — FastAPI middleware
> - `src/auth/decorators.py` — `@requires_role`, `@requires_any_role`, `@requires_all_roles`
> - `src/auth/dependencies.py` — `get_current_user`, `get_optional_user`
> - `src/auth/config.py` — `AuthSettings` (pydantic-settings)
> - `src/auth/exceptions.py` — `AuthenticationError`, `AuthorizationError`

### SEMANA 2: Integração Inicial (Dias 6-10) — BLOQUEADA

#### Dia 6: Módulo Piloto - intellicare-core
- [ ] ~~Instalar `intellicare-auth`~~ → **implementar biblioteca primeiro**
- [ ] Configurar variáveis de ambiente
- [ ] Proteger endpoints de exemplo
- [ ] Testar com token

#### Dia 7: intellicare-donabedian
- [ ] Instalar biblioteca
- [ ] Proteger endpoints críticos
- [ ] Aplicar roles (admin, doctor, nurse)
- [ ] Testes de integração

#### Dia 8: intellicare-wanda
- [ ] Integrar autenticação
- [ ] Proteger endpoints de orquestração
- [ ] Testar discovery com auth
- [ ] Documentar

#### Dia 9: intellicare-oswaldo
- [ ] Integrar biblioteca
- [ ] Proteger endpoints de análise
- [ ] Roles para profissionais de saúde
- [ ] Testes

#### Dia 10: intellicare-florence
- [ ] Integração completa
- [ ] Proteção de endpoints clínicos
- [ ] Testes com múltiplas roles

---

### SEMANA 3: Expansão e Finalização (Dias 11-15) — BLOQUEADA

#### Dia 11-12: Módulos Restantes
- [ ] intellicare-zilda (CNES/territorial)
- [ ] intellicare-geralda (care plans)
- [ ] intellicare-comunicacao (Rocket.Chat — **nota**: Matrix descontinuado)
- [ ] intellicare-portal (React + keycloak-js)

#### Dia 13: Testes de Integração
- [ ] Testes end-to-end multi-módulo
- [ ] Testes de SSO (login único)
- [ ] Testes de performance (latência)
- [ ] Testes de segurança

#### Dia 14: Documentação
- [ ] Guia do desenvolvedor
- [ ] Manual do administrador
- [ ] Runbooks de operação
- [ ] FAQ para usuários

#### Dia 15: Deploy e Validação
- [ ] Deploy em staging
- [ ] Validação com time
- [ ] Ajustes finais
- [ ] Go-live

---

## 🔧 CONFIGURAÇÃO KEYCLOAK

### Clients Criados ✅

| Client ID | Porta real | Status Keycloak | Código integrado |
|-----------|-----------|-----------------|-----------------|
| `intellicare-core` | 8000 | ✅ Criado | ⏳ Pendente |
| `intellicare-wanda` | 8007 | ✅ Criado | ⏳ Pendente |
| `intellicare-florence` | 8002 | ✅ Criado | ⏳ Pendente |
| `intellicare-oswaldo` | 8001 | ✅ Criado | ⏳ Pendente |
| `intellicare-zilda` | 8003 | ✅ Criado | ⏳ Pendente |
| `intellicare-geralda` | 8006 | ✅ Criado | ⏳ Pendente |
| `intellicare-donabedian` | 8004 | ✅ Criado | ⏳ Pendente |
| `intellicare-portal` | 3000 | ✅ Criado | ⏳ Pendente |
| `intellicare-comunicacao` | 8005 | ✅ Criado | ⏳ Pendente |

> Secrets disponíveis em `keycloak_client_secrets.json` (não commitar).

### Roles a Configurar

```
intellicare_admin
├── intellicare_hospital_admin
├── intellicare_doctor
├── intellicare_nurse
├── intellicare_nutritionist
├── intellicare_care_coordinator
└── intellicare_patient
```

---

## 📦 ENTREGÁVEIS

### Código
- [x] Estrutura do projeto `intellicare-auth` (pyproject.toml, pytest.ini, alembic.ini)
- [x] Scripts Keycloak (setup, create_users, assign_roles, verify_secrets — 10+ scripts)
- [ ] Código Python da biblioteca (`src/auth/client.py`, `middleware.py`, `decorators.py`, etc.)
- [ ] 9 módulos integrados
- [ ] Testes unitários (>90% cobertura)
- [ ] Testes de integração

### Documentação
- [x] README.md da biblioteca (especificação da API)
- [x] `docs/KEYCLOAK_INTEGRACAO_FINAL_REPORT.md` — relatório completo de configuração
- [x] `docs/REPLICACAO_KEYCLOAK_COMPLETA.md` — guia de replicação
- [x] `SETUP_COMPLETO.md` — log de setup
- [ ] Manual do administrador
- [ ] Troubleshooting guide

### Infraestrutura
- [ ] 9 clients configurados no Keycloak
- [ ] Roles e mappers configurados
- [ ] Secrets armazenados com segurança
- [ ] Monitoramento configurado

---

## 🎯 PRÓXIMOS PASSOS IMEDIATOS

1. **Implementar `src/auth/client.py`** — `KeycloakClient`: validação JWT (JWKS), cache, introspection
2. **Implementar `src/auth/dependencies.py`** — `get_current_user`, `get_optional_user` para FastAPI
3. **Implementar `src/auth/decorators.py`** — `@requires_role`, `@requires_any_role`
4. **Escrever testes unitários** (mocks para Keycloak — sem dependência de serviço real)
5. **Testar com módulo piloto** (`intellicare-core` ou `intellicare-donabedian`)
6. **Expandir para os 9 módulos**

---

**Atualizado**: 2026-02-18
**Status**: Keycloak ✅ operacional | Biblioteca Python ⏳ pendente | Integração ⏳ pendente

