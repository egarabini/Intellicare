---
tipo: security
atualizado: 2026-03-13
---

# Controles de Segurança — IntelliCare V3

## Autenticação

- **IdP único:** Keycloak (realm `intellicare`)
- **Protocolo:** OAuth 2.0 + OIDC
- **Token:** JWT com claims `tenant_id`, `user_id`, `roles`, `email`
- **Validade:** access token 15min, refresh token 8h
- **Roles:** `PLATFORM_ADMIN`, `TENANT_GESTOR`, `CLINICO`, `PACIENTE`

---

## Multi-tenancy — Isolamento garantido

```python
# Em todo endpoint que acessa dados:
async def get_current_tenant(token: str = Depends(oauth2_scheme)) -> TenantContext:
    payload = decode_jwt(token)
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(401, "tenant_id ausente no token")
    return TenantContext(tenant_id=tenant_id, schema=f"tenant_{tenant_id}")

# TenantAwareSessionFactory garante que TODA query vai para o schema correto:
async with tenant_session(tenant_ctx) as db:
    # db já está no search_path = tenant_{slug}
    results = await db.execute(select(Protocol))
    # Impossível acessar dados de outro tenant
```

Zero possibilidade de acesso cross-tenant via query — o schema PostgreSQL é o boundary.

---

## Segredos — Política

| Ambiente | Como armazenar |
|----------|---------------|
| Desenvolvimento local | `.env` (no `.gitignore`) |
| CI/CD | GitHub Actions Secrets |
| Produção | Variáveis de ambiente no container |

**Nunca:** hardcoded no código, em `.env.example` com valores reais, em logs,
em mensagens de erro expostas ao cliente.

Arquivo `keycloak_client_secrets.json` está explicitamente no `.gitignore`.

---

## Checklist por DEM (pré-conclusão)

Antes de marcar DEM como concluída, verificar:

- [ ] Nenhum secret hardcoded (`grep -r "password\|secret\|key" --include="*.py"`)
- [ ] Todos os endpoints autenticados (exceto `/health` e `/docs`)
- [ ] `tenant_id` validado em toda operação que acessa dados
- [ ] Inputs validados com Pydantic (sem `dict` raw do request)
- [ ] Logs não expõem dados clínicos ou PII
- [ ] `.env` não está no git (`git check-ignore .env`)
- [ ] Migrações testadas (up + down)

---

## LGPD — Considerações

| Dado | Classificação | Retenção | Acesso |
|------|--------------|----------|--------|
| Dados clínicos do paciente | Dado sensível (LGPD Art. 11) | Conforme CFM/Resolução | Apenas CLINICO do tenant |
| Logs de auditoria | Dado pessoal | 5 anos | Apenas PLATFORM_ADMIN e TENANT_GESTOR |
| Dados de billing | Dado pessoal | 5 anos (tributário) | Apenas PLATFORM_ADMIN |

Encerramento de contrato: `pg_dump tenant_{slug}` → entrega ao titular → `DROP SCHEMA CASCADE`.
Sem rastros de dados do tenant após encerramento.

---

## Dependências de segurança

- `python-jose` — validação JWT
- `passlib` — hashing de senhas (quando necessário)
- `httpx` — cliente HTTP com TLS verificado por padrão
- Keycloak (DEM-004) — IdP central, gerenciamento de usuários e grupos
