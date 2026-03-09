# Scripts Keycloak — IntelliCare

## assign-his-adapter-role

Atribui a role **HIS_ADAPTER** ao service account do client `intellicare-bridge-dev`.

O import do realm via JSON não atribui roles a service accounts automaticamente.

### Automático (Docker Compose)

O serviço `keycloak-init` no `docker-compose.keycloak.yml` executa o script automaticamente após o Keycloak ficar saudável:

```bash
docker compose -f docker-compose.keycloak.yml up -d
# keycloak-init roda após keycloak ficar healthy e atribui HIS_ADAPTER
```

### Manual (quando Keycloak já está rodando)

**Python** (funciona em qualquer SO, sem dependências extras):

```bash
cd intellicare-auth/keycloak/scripts
python assign-his-adapter-role.py
```

**Windows (PowerShell):**

```powershell
cd intellicare-auth\keycloak\scripts
.\assign-his-adapter-role.ps1
```

Com parâmetros:

```powershell
.\assign-his-adapter-role.ps1 -KeycloakUrl "http://localhost:8080" -AdminPassword "sua-senha"
```

Variáveis de ambiente: `KEYCLOAK_URL`, `KEYCLOAK_ADMIN`, `KEYCLOAK_ADMIN_PASSWORD`, `KEYCLOAK_REALM`

### Linux/macOS (Bash)

```bash
chmod +x assign-his-adapter-role.sh
./assign-his-adapter-role.sh
```

Requer `curl` e `jq`. Variáveis: `KEYCLOAK_URL`, `KEYCLOAK_ADMIN`, `KEYCLOAK_ADMIN_PASSWORD`, `KEYCLOAK_REALM`

### Dentro do container Keycloak

```bash
docker exec -it keycloak-intellicare /bin/bash
# Dentro do container (se tiver curl e jq):
KEYCLOAK_URL=http://localhost:8080 ./assign-his-adapter-role.sh
```

Ou execute do host apontando para a porta exposta (ex: `http://localhost:8080`).
