# Docker Network Troubleshooting - IntelliCare

## Problema: Pool Overlaps

Erro ao criar rede:
```
failed to create network intellicare_intellicare-network: Error response from daemon: invalid pool request: Pool overlaps with other one on this address space
```

## Causa

Já existe uma rede Docker com o mesmo nome ou com sobreposição de endereços IP.

## Solução

### 1. Listar redes existentes

```bash
docker network ls
```

### 2. Verificar detalhes da rede conflitante

```bash
docker network inspect intellicare_intellicare-network
```

### 3. Remover redes antigas/conflitantes

```bash
# Remover rede específica
docker network rm intellicare_intellicare-network

# Remover todas as redes intellicare
docker network ls | grep "intellicare" | awk '{print $1}' | xargs -r docker network rm

# Forçar remoção se houver containers conectados
docker network rm -f intellicare_intellicare-network
```

### 4. Parar containers que estão usando a rede

```bash
docker-compose -f docker-compose.full.yml down
```

### 5. Criar rede limpa

```bash
docker network create intellicare-network --driver bridge --subnet 172.20.0.0/16
```

### 6. Iniciar containers novamente

```bash
docker-compose -f docker-compose.full.yml up -d
```

## Script Automatizado de Limpeza

Adicionado ao `clean_and_rebuild.sh`:

```bash
# Remover redes antigas intellicare
echo "Removing old intellicare networks..."
docker network ls | grep "intellicare.*network" | awk '{print $1}' | xargs -r docker network rm -f 2>/dev/null || true
```

## Prevenção

Sempre executar `docker-compose down` antes de recriar redes.

## Diagnóstico Completo

```bash
# Ver todas as redes
docker network ls

# Ver redes em uso
docker network ls --filter type=custom

# Ver containers conectados a cada rede
docker network inspect intellicare_intellicare-network --format='{{range .Containers}}{{.Name}} {{end}}'
```

## Rede IntelliCare Padrão

- **Nome:** `intellicare-network` (sem prefixo duplicado)
- **Driver:** bridge
- **Subnet:** 172.20.0.0/16 (ou definida pelo Docker)
- **Gateway:** 172.20.0.1

## Documentação de Referência

- Docker Networks: https://docs.docker.com/engine/reference/commandline/network/
- Docker Compose Networks: https://docs.docker.com/compose/networking/
