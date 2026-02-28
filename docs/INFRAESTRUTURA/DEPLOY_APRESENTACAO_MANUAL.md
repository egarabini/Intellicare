# Deploy Manual: apresentacao.intellicare.ia.br

## Método Alternativo: Docker Compose

Como a conexão SSH está com problemas, vamos usar uma abordagem via Docker Compose que pode ser aplicada através do painel de controle do servidor ou FileZilla.

---

## Passo 1: Criar arquivo docker-compose para apresentacao

Crie o arquivo `/opt/intellicare/intellicare/intellicare-apresentacao/docker-compose.yml` com o seguinte conteúdo:

```yaml
version: '3.8'

services:
  apresentacao:
    image: nginx:alpine
    container_name: intellicare-apresentacao
    volumes:
      - ./apresentacao/web:/usr/share/nginx/html:ro
    networks:
      - modularizacao_intellicare-network
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.apresentacao.rule=Host(`apresentacao.intellicare.ia.br`)"
      - "traefik.http.routers.apresentacao.entrypoints=websecure"
      - "traefik.http.routers.apresentacao.tls.certresolver=letsencrypt"
      - "traefik.http.services.apresentacao.loadbalancer.server.port=80"
      - "traefik.http.routers.apresentacao.middlewares=frontend-chain@file"

networks:
  modularizacao_intellicare-network:
    external: true
```

---

## Passo 2: Iniciar o serviço

Via terminal SSH (quando conseguir conectar):

```bash
cd /opt/intellicare/intellicare/intellicare-apresentacao
docker-compose up -d
```

Ou via Portainer (se disponível):
1. Acesse Portainer
2. Vá em "Stacks"
3. Clique em "Add Stack"
4. Cole o conteúdo do docker-compose.yml
5. Defina o nome: `intellicare-apresentacao`
6. Clique em "Deploy"

---

## Passo 3: Verificar

```bash
docker ps --filter name=apresentacao
docker logs intellicare-apresentacao
```

---

## Vantagens desta Abordagem

1. ✅ **Labels Traefik no próprio container** - não precisa editar `routes-intellicare.yml`
2. ✅ **Auto-discovery** - Traefik detecta automaticamente via Docker labels
3. ✅ **Certificado SSL automático** - Let's Encrypt via `certresolver=letsencrypt`
4. ✅ **Fácil de gerenciar** - pode usar Portainer ou Docker Compose

---

## Teste Final

Após deploy, aguarde 30-60 segundos e teste:

```bash
curl -I https://apresentacao.intellicare.ia.br
```

Ou abra no navegador: **https://apresentacao.intellicare.ia.br**

