# Sugestão de proteção IAM nos endpoints WANDA

Recomenda-se proteger endpoints que expõem dados sensíveis, operações administrativas ou execução de fluxos críticos. Exemplos:

## 1. Proteção por autenticação (qualquer usuário autenticado)

```python
from fastapi import Depends
from intellicare_auth import get_current_user

@router.post("/api/v1/aggregate")
async def aggregate_debug(..., user=Depends(get_current_user)):
    ...
```

## 2. Proteção por role (ex: apenas "clinico" ou "admin")

```python
from intellicare_auth.fastapi import require_role

@router.post("/api/v1/workflows/execute")
@require_role("clinico")
async def execute_workflow(...):
    ...
```

## 3. Recomendações de proteção
- Endpoints de execução de workflow, agregação, alertas, eventos e bot devem exigir autenticação.
- Endpoints de administração (ex: /mcp/modules, /traces, /metrics) podem exigir role "admin".
- Endpoints públicos (ex: /health, /info) podem permanecer abertos.

Adapte as proteções conforme o perfil de uso e sensibilidade dos dados.
# 🔐 Segurança IAM (Keycloak)

O WANDA suporta autenticação e autorização centralizadas via Keycloak, usando a biblioteca `intellicare-auth`.

## Como integrar
1. Execute `setup_keycloak.py` em `intellicare-auth` para gerar `keycloak_client_secrets.json`.
2. Adicione a dependência `intellicare-auth` ao requirements.txt.
3. O app já está configurado para usar o middleware de autenticação:

```python
from intellicare_auth.fastapi import configure_auth
configure_auth(app, secrets_path="keycloak_client_secrets.json")
```

4. Para proteger endpoints sensíveis, use:

```python
from intellicare_auth import get_current_user

@router.post("/algum-endpoint-protegido")
async def endpoint(..., user=Depends(get_current_user)):
    ...
```

5. Para proteção por role:

```python
from intellicare_auth.fastapi import require_role

@router.get("/dados-sensiveis")
@require_role("clinico")
async def dados(...):
    ...
```

## Referências
- Veja `INTEGRACAO_SEGURANCA_IAM.md` para plano completo e exemplos
- Consulte a documentação do intellicare-auth para detalhes de configuração

---
