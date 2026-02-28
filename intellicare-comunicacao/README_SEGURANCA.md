# Integração IAM/Keycloak (intellicare-auth)

Este módulo utiliza autenticação centralizada via Keycloak, integrada pelo pacote `intellicare-auth`.

## Como funciona
- Todos os endpoints sensíveis exigem autenticação JWT (Bearer Token).
- Endpoints administrativos exigem role específica (ex: `admin`).
- O middleware é configurado no FastAPI app principal.

## Exemplo de uso

```python
from intellicare_auth.fastapi import configure_auth, get_current_user, require_role
from fastapi import FastAPI, Depends

app = FastAPI()
configure_auth(app)

@app.post("/api/v1/send", dependencies=[Depends(get_current_user)])
async def send_message(...):
    ...

@app.get("/api/v1/intents", dependencies=[Depends(require_role("admin"))])
async def list_intents():
    ...
```

## Variáveis de ambiente necessárias
- KEYCLOAK_ADMIN_URL
- KEYCLOAK_TARGET_REALM
- (ver README principal)

## Testando endpoints protegidos

```bash
# Obtenha um token JWT válido via Keycloak
export TOKEN=eyJhbGciOi...

# Envie requisição autenticada
curl -H "Authorization: Bearer $TOKEN" http://localhost:8005/api/v1/send -d '{"channel": "rocketchat", ...}'
```

## Referências
- [intellicare-auth no PyPI](https://pypi.org/project/intellicare-auth/)
- [Documentação Keycloak](https://www.keycloak.org/docs/latest/)
