# 📋 BRIEFING — Fix Módulos Unhealthy no Servidor

**Data:** 2026-02-22  
**Prazo:** 30 minutos  
**Prioridade:** 🟡 Média  
**Servidor:** `167.86.97.142` — `root`

---

## 🎯 Problema

Os containers estão rodando mas marcados como **unhealthy**. Causas prováveis:
1. Imagens antigas (antes da correção dos Dockerfiles — T4-F2)
2. Healthchecks apontando para `/health` ao invés de `/api/v1/health`
3. Falta de `curl` dentro dos containers

> [!IMPORTANT]
> As correções já existem no código (Dockerfiles + docker-compose.full.yml). Só precisa **rebuild + redeploy**.

---

## 📝 Passo a Passo

### 1. Conectar ao servidor

```bash
ssh root@167.86.97.142
cd /opt/intellicare/intellicare
```

### 2. Garantir que o código está atualizado

```bash
git pull origin main
```

Se o repo não estiver configurado com git, copiar do Windows:
```powershell
# Do Windows (PowerShell):
$s = "root@167.86.97.142"
$r = "/opt/intellicare/intellicare"

# Docker compose atualizado
scp docker-compose.full.yml ${s}:${r}/

# Dockerfiles de cada módulo
scp intellicare-florence\Dockerfile ${s}:${r}/intellicare-florence/
scp intellicare-oswaldo\Dockerfile ${s}:${r}/intellicare-oswaldo/
scp intellicare-donabedian\Dockerfile ${s}:${r}/intellicare-donabedian/
scp intellicare-wanda\Dockerfile ${s}:${r}/intellicare-wanda/
scp intellicare-comunicacao\Dockerfile ${s}:${r}/intellicare-comunicacao/
scp intellicare-geralda\Dockerfile ${s}:${r}/intellicare-geralda/

# Core e Auth (dependências internas)
scp -r intellicare-core ${s}:${r}/intellicare-core/
scp -r intellicare-auth ${s}:${r}/intellicare-auth/
```

### 3. No servidor — Rebuild das imagens

```bash
cd /opt/intellicare/intellicare

# Parar módulos (manter postgres, redis, traefik)
docker-compose -f docker-compose.full.yml stop \
  florence oswaldo donabedian wanda comunicacao geralda portal

# Rebuild forçado (--no-cache garante imagens limpas)
docker-compose -f docker-compose.full.yml build --no-cache \
  florence oswaldo donabedian wanda comunicacao geralda portal

# Subir novamente
docker-compose -f docker-compose.full.yml up -d \
  florence oswaldo donabedian wanda comunicacao geralda portal
```

### 4. Aguardar e verificar

```bash
# Aguardar 60s para healthchecks rodarem
sleep 60

# Status dos containers
docker-compose -f docker-compose.full.yml ps

# Verificar se curl existe dentro de cada container
for svc in florence oswaldo donabedian wanda comunicacao geralda; do
  echo "--- $svc ---"
  docker-compose -f docker-compose.full.yml exec $svc curl -s http://localhost:8000/api/v1/health 2>/dev/null || echo "FALHOU"
done
```

### 5. Smoke test

```bash
bash scripts/smoke_test.sh
```

---

## 🔍 Troubleshooting

### Se um módulo continua unhealthy:

```bash
# Ver logs do módulo
docker-compose -f docker-compose.full.yml logs --tail=50 florence

# Entrar no container
docker-compose -f docker-compose.full.yml exec florence bash

# Dentro do container, testar manualmente:
curl http://localhost:8000/api/v1/health
python -c "import intellicare_core; print('core OK')"
python -c "import intellicare_auth; print('auth OK')"
```

### Portas internas dos módulos:

| Módulo | Porta interna | Healthcheck |
|---|---|---|
| florence | 8001 | `curl http://localhost:8001/api/v1/health` |
| oswaldo | 8002 | `curl http://localhost:8002/api/v1/health` |
| donabedian | 8003 | `curl http://localhost:8003/api/v1/health` |
| wanda | 8004 | `curl http://localhost:8004/api/v1/health` |
| comunicacao | 8005 | `curl http://localhost:8005/api/v1/health` |
| geralda | 8006 | `curl http://localhost:8006/api/v1/health` |

### Se o problema é a URL do banco:

Verificar se o `.env` tem as variáveis corretas:
```bash
grep DATABASE .env
# Deve ter algo como:
# DATABASE_URL=postgresql+asyncpg://intellicare_admin:SENHA@postgres:5432/intellicare_db
```

> [!WARNING]
> Se a senha do banco tem caracteres especiais (`@`, `#`, `%`), ela precisa estar URL-encoded no `.env`.

---

## 🏁 Critério de Conclusão

```bash
docker-compose -f docker-compose.full.yml ps
```

Todos os módulos devem mostrar **(healthy)**:
- ✅ florence → healthy
- ✅ oswaldo → healthy
- ✅ donabedian → healthy
- ✅ wanda → healthy
- ✅ comunicacao → healthy
- ✅ geralda → healthy
- ✅ portal → healthy (ou running)
- ✅ traefik → healthy
