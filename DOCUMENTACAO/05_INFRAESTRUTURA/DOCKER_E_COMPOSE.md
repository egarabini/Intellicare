# Guia Completo — Docker & Compose (Ambiente Local)

Este guia documenta o uso consolidado da Stack de Desenvolvimento do IntelliCare utilizando o modelo Docker Engine / Docker Compose.

## Inicializando o Sistema

Para obter a arquitetura de 14 microserviços unificada, o projeto emprega o `docker-compose.full.yml`.

### Pré-requisitos
- Ter copiado as chaves de acesso a partir do `.env.example` para seu `.env`.

### 1. Iniciar Infraestrutura de Base
Inicialize os serviços essenciais primários antes para garantir estabilidade da rede local.
```bash
docker compose up -d
```
> Sobe os módulos: **PostgreSQL**, **Redis**, **Prometheus**, **Grafana**.

### 2. Iniciar a Plataforma Completa
Após os bancos estarem ativos e `Healthy`, inicie o backend e frontend:
```bash
docker compose -f docker-compose.full.yml up -d
```

---

## Estrutura do Build Context

**Importante:** Um dos gargalos mais comuns ao criar projetos modulares independentes no docker-compose é o apontamento incorreto do Contexto de Build (O arquivo que roda a cópia primária). 

Para referenciar os builds do Intellicare corretamente e incorporar o `intellicare-core` nos dependentes que não possuem pacotes pré-compilados via PyPI, todo Dockerfile Python possui o padrão root directory local `.`.
Nenhum microsserviço no arquivo yml altera para pasta própria (ex: `context: ./intellicare-grahame` está incorreto).

O arquivo Compose obrigatoriamente contém a sintaxe unificada abaixo para cada container:
```yaml
build:
  context: .
  dockerfile: ./intellicare-nome-modulo/Dockerfile
```

## Solução de Problemas Comuns (Troubleshooting)

### O build está falhando com "COPY failed: file not found in build context"
Conferir sempre o "Build context". Se o `Dockerfile` faz `COPY intellicare-core`, o build context deve ser a raiz — não o diretório do módulo. 

### Erro de Network Address Pool Overlaps
Se você tentar rodar o composer e o docker acusar IP/Network error alegando "Pool overlaps":
Solução recomendada: Execute a quebra forçada da network.
```bash
docker stop $(docker ps -aq)
docker network prune -f 
```
