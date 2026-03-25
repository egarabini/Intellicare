# DEM-087 — Especificação Técnica

## Fix 1: JWT Issuer Alignment

### Diagnóstico

O `intellicare-service` usa python-jose / PyJWT para validar tokens. A validação de `iss` (issuer) compara o claim do token com `KEYCLOAK_URL` ou uma variável equivalente configurada em `infra/.env.staging`.

Após o restart forçado do Keycloak durante o troubleshooting do DEM-086, o Keycloak passou a emitir tokens com:
```
"iss": "http://keycloak:8080/realms/intellicare"
```
(URL interna Docker, sem TLS)

Mas o `intellicare-service` provavelmente valida contra:
```
KEYCLOAK_URL=https://auth.intellicare.ia.br
```

### Solução

**Opção A (preferida):** Configurar `KEYCLOAK_ISSUER_URL` separado de `KEYCLOAK_URL`.

No `infra/.env.staging`, adicionar:
```
KEYCLOAK_ISSUER_URL=http://keycloak:8080/realms/intellicare
```

No `intellicare-service` (arquivo `core/security.py` ou equivalente), usar `KEYCLOAK_ISSUER_URL` para validação de `iss` do JWT, mantendo `KEYCLOAK_URL` para redirects e bem-known discovery.

**Opção B (fallback):** Desabilitar validação de issuer no decode JWT (apenas se A não for viável por arquitetura).

### Localização do código

```
intellicare/
  core/
    security.py          ← validação JWT (decode + claims check)
  infra/
    .env.staging         ← KEYCLOAK_ISSUER_URL a adicionar
    docker-compose.yml   ← environment intellicare-service
```

---

## Fix 2: Traefik Routing Identity

### Diagnóstico

As labels Traefik atuais do `intellicare-service` (linha ~429 do `docker-compose.yml`) provavelmente definem:
```yaml
traefik.http.routers.api.rule: Host(`intellicare.ia.br`) && PathPrefix(`/api/`)
```

O `modules/identity/main.py` registra as rotas com prefix `/identity/`. No `main.py` do serviço principal, o módulo é montado em `/identity` — resultando em paths como `/identity/pessoas`.

Para exposição pública, a convenção do projeto é `/api/<módulo>/`. Portanto o path público correto é `/api/identity/*`, que o Traefik precisa rotear para `intellicare-service`.

### Verificação necessária

Confirmar no `main.py` como o módulo identity é montado:

```python
# modules/identity/main.py — Module descriptor
module = Module(
    name="identity",
    prefix="/identity",   ← confirmar este valor
    ...
)
```

Se o loader monta todos os módulos sob `/api/`, o path final é `/api/identity/*` — e basta verificar se a rule Traefik atual já cobre isso com `PathPrefix('/api/')`.

Se o loader monta sem `/api/`, é necessário ajustar o prefix no módulo OU adicionar rule específica no Traefik.

### Fix esperado

**Caso a rule Traefik já cubra `/api/*`:** Só confirmar que o módulo identity usa prefix `/api/identity` no loader.

**Caso contrário:** Adicionar nos labels do `intellicare-service`:
```yaml
- "traefik.http.routers.api-identity.rule=Host(`intellicare.ia.br`) && PathPrefix(`/api/identity`)"
- "traefik.http.routers.api-identity.service=intellicare"
- "traefik.http.routers.api-identity.tls.certresolver=letsencrypt"
```

---

## Testes

```python
# test_infra_identity_fix.py
def test_identity_jwt_local():
    """Token válido → 200 no localhost (não mais 401)"""

def test_identity_traefik_public():
    """POST /api/identity/pessoas público → 200 ou 409 (não mais 405)"""

def test_identity_idempotency_smoke():
    """Criar mesma pessoa 2x via CPF → segundo retorna 200 com mesmo pessoa_id"""
```

Total esperado: 3 testes (smoke + regressão issuer)
