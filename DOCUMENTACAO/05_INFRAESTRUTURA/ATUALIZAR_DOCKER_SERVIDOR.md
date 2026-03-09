# Atualização do Docker no Servidor de Produção

**Data:** 2026-03-01
**Status:** ⚠️ **CRÍTICO** - Atualização necessária
**Problema:** API do Docker muito antiga (1.24, mínimo requerido: 1.43+)

---

## Diagnóstico

### Erro Detectado
```
Error response from daemon: client version 1.24 is too old.
Minimum supported API version is 1.44
```

### Causa
O cliente Docker no servidor está muito desatualizado e não é mais compatível com as versões mais recentes do Docker Engine.

### Impacto
- Impossível executar comandos `docker` no servidor
- Deploy automatizado falhando
- Gerenciamento de containers comprometido

---

## Versões Mínimas Requeridas

| Componente | Versão Mínima | Recomendada |
|------------|---------------|-------------|
| Docker Engine | 24.0.0+ (API 1.43+) | 25.0.0+ (API 1.44+) |
| Docker Compose | 2.20.0+ | 2.24.0+ |
| Linux Kernel | 4.19+ | 5.10+ |
| Sistema Operacional | - | Ubuntu 20.04+, Debian 11+, Rocky Linux 8+ |

---

## Plano de Atualização

### Opção 1: Script Automatizado (RECOMENDADO)

```bash
# 1. Copiar script para o servidor
scp scripts/server/UPDATE_DOCKER_SERVER.sh root@<IP-DO-SERVIDOR>:/tmp/

# 2. Executar script
ssh root@<IP-DO-SERVIDOR>
bash /tmp/UPDATE_DOCKER_SERVER.sh
```

**O que o script faz:**
1. ✅ Backup automático de todas as configurações
2. ✅ Atualiza Docker para versão mais recente
3. ✅ Atualiza Docker Compose
4. ✅ Reinicia os containers
5. ✅ Verifica saúde dos serviços

### Opção 2: Manual

#### Debian/Ubuntu

```bash
# 1. Remover versão antiga
sudo apt-get remove docker docker-engine docker.io containerd runc

# 2. Atualizar repositório e instalar dependências
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 3. Adicionar chave GPG oficial do Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 4. Configurar repositório
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Instalar Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. Habilitar e iniciar
sudo systemctl enable docker
sudo systemctl start docker
```

#### CentOS/RHEL/Rocky Linux

```bash
# 1. Remover versão antiga
sudo yum remove docker docker-client docker-client-latest docker-common \
    docker-latest docker-latest-logrotate docker-logrotate docker-engine

# 2. Instalar dependências
sudo yum install -y yum-utils

# 3. Adicionar repositório do Docker
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 4. Instalar Docker Engine
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 5. Habilitar e iniciar
sudo systemctl enable docker
sudo systemctl start docker
```

---

## Diagnóstico Pré-Atualização

Antes de atualizar, execute o diagnóstico:

```bash
# Copiar script para o servidor
scp scripts/server/diagnose_docker.sh root@<IP-DO-SERVIDOR>:/tmp/

# Executar diagnóstico
ssh root@<IP-DO-SERVIDOR>
bash /tmp/diagnose_docker.sh
```

**O diagnóstico verifica:**
- ✅ Versão do Docker e API
- ✅ Versão do Docker Compose
- ✅ Versão do Kernel Linux
- ✅ Sistema Operacional
- ✅ Status do serviço Docker
- ✅ Status dos containers IntelliCare
- ✅ Rede Docker

---

## Pós-Atualização

### 1. Verificar Nova Versão

```bash
docker --version
docker version --format '{{.Server.APIVersion}}'
docker compose version
```

### 2. Reiniciar Containers

```bash
cd /opt/intellicare/intellicare
docker-compose -f docker-compose.full.yml up -d
```

### 3. Verificar Saúde dos Containers

```bash
# Ver status
docker ps

# Ver logs se houver problemas
docker logs <container-name> --tail 50
```

### 4. Testar Funcionalidade

```bash
# Testar API Gateway
curl -I https://api.intellicare.ia.br/v1/oswaldo/api/v1/health

# Testar Portal
curl -I https://portal.intellicare.ia.br

# Testar Grafana
curl -I https://grafana.intellicare.ia.br
```

---

## Estratégia de Rollback

Se algo der errado:

```bash
# 1. Parar containers
docker-compose -f docker-compose.full.yml down

# 2. Desinstalar versão nova
sudo apt-get remove docker-ce docker-ce-cli containerd.io

# 3. Reinstalar versão antiga (se disponível)
# OU
# Restaurar do backup criado pelo script

# 4. Reiniciar containers
docker-compose -f docker-compose.full.yml up -d
```

**Nota:** O script de atualização cria automaticamente um backup em:
```
/opt/intellicare/backups/docker-update-<timestamp>/
```

---

## Problemas Conhecidos

### Containers em "Restarting" (Estado Atual)

Os seguintes containers estão reiniciando continuamente:
- `intellicare-wanda`
- `intellicare-florence`
- `intellicare-oswaldo`
- `intellicare-traefik` (unhealthy)

**Possíveis causas:**
1. Versão antiga do Docker
2. Configuração incorreta
3. Dependências faltando
4. Problemas de rede

**Após atualizar o Docker:**
```bash
# Investigar logs
docker logs intellicare-wanda --tail 50
docker logs intellicare-florence --tail 50
docker logs intellicare-oswaldo --tail 50
docker logs intellicare-traefik --tail 50

# Ver configurarções
docker inspect <container-name>

# Tentar reiniciar manualmente
docker restart <container-name>
```

---

## Links Úteis

- [Documentação Oficial Docker - Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Documentação Oficial Docker - Debian](https://docs.docker.com/engine/install/debian/)
- [Documentação Oficial Docker - CentOS](https://docs.docker.com/engine/install/centos/)
- [Docker Compose Install](https://docs.docker.com/compose/install/)
- [Docker API Version History](https://docs.docker.com/engine/api/#api-version-matrix)

---

## Checklist de Atualização

### Pré-Atualização
- [ ] Executar diagnóstico (`diagnose_docker.sh`)
- [ ] Fazer backup manual de configurações críticas
- [ ] Documentar containers rodando
- [ ] Avisar equipe sobre manutenção

### Atualização
- [ ] Executar script de atualização (`UPDATE_DOCKER_SERVER.sh`)
- [ ] Verificar nova versão do Docker
- [ ] Verificar nova versão do Docker Compose
- [ ] Reiniciar containers
- [ ] Verificar saúde dos containers

### Pós-Atualização
- [ ] Testar endpoints críticos
- [ ] Verificar logs de erros
- [ ] Testar deploy automatizado
- [ ] Documentar mudanças
- [ ] Atualizar documentação

---

## Suporte

Em caso de problemas:

1. **Ver logs:** `docker logs <container> --tail 50`
2. **Ver diagnóstico:** `bash scripts/server/diagnose_docker.sh`
3. **Consultar documentação:** `docs/INFRAESTRUTURA/`
4. **Ver backup:** `/opt/intellicare/backups/docker-update-<timestamp>/`

---

**Última atualização:** 2026-03-01
**Responsável:** IntelliCare DevOps Team
