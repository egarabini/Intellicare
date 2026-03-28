# ADR-005 - Separacao de Infraestrutura: VPS-DATA e VPS-STORAGE

## Status
Accepted

## Contexto

Durante o ciclo de validacao de staging de 2026-03, identificamos tres problemas recorrentes
no modelo atual de infraestrutura local de desenvolvimento:

1. **Banco de dados volatil em dev**: o PostgreSQL rodando via Docker Desktop em Windows
   perde dados ao reiniciar volumes, forçando re-seeds frequentes e perdendo estado de teste.

2. **Carga no notebook de desenvolvimento**: Docker Desktop (WSL2) + VS2022 + todos os servicos
   IntelliCare + PostgreSQL competem por RAM e CPU no mesmo host. Com a inclusao futura de
   pgvector para busca semantica dos agentes, esse cenario se torna inviavel.

3. **Isolamento para times remotos**: com a evolucao prevista para equipes de 3+ desenvolvedores
   remotos, cada dev precisaria de um banco local independente e vazio, sem possibilidade de
   compartilhar estado de testes ou seeds de dados.

Alem disso, o VPS 161.97.141.186 ja possui Keycloak instalado e operacional para outro projeto,
tornando trivial a adicao do realm `intellicare` sem custo de setup adicional.

## Decisao

Separar banco de dados e storage em VPSes dedicados, compartilhados pelos ambientes
`develop` e `staging`:

### VPS-DATA (161.97.141.186 — 4 CPU / 8 GB RAM / 400 GB SSD)
- **PostgreSQL 16** com os bancos:
  - `intellicare_develop`, `intellicare_staging`
  - `evolution_develop`, `evolution_staging`
  - `kestra_develop`, `kestra_staging`
  - `listmonk_develop`, `listmonk_staging`
- **Keycloak 24** — realm `intellicare` adicionado ao Keycloak existente
  - realm `intellicare` (dev) e realm `intellicare-staging` (staging)

### VPS-STORAGE (173.249.49.39 — 2 CPU / 2 GB RAM / 600 GB SSD)
- **MinIO** com os buckets:
  - `uploads-develop`, `uploads-staging`
  - `backups`
  - `obsidian-vault`

### O que permanece nos VPSes de aplicacao
- `intellicare-service` (FastAPI)
- Traefik
- Redis (latencia minima com a aplicacao — nao migra)
- Kestra worker
- Frontends compilados (static via FastAPI)

## Topologia resultante

```
Notebook dev (Windows)
└── VS2022 / Python → conecta via TCP a VPS-DATA e VPS-STORAGE
    → DB_URL=postgresql://...@161.97.141.186:5432/intellicare_develop
    → MINIO_URL=http://173.249.49.39:9000
    → KEYCLOAK_URL=https://auth-data.intellicare.ia.br (realm intellicare)

VPS-APP-STAGING → conecta a VPS-DATA e VPS-STORAGE
    → DB_URL=postgresql://...@161.97.141.186:5432/intellicare_staging
    → MINIO_URL=http://173.249.49.39:9000
    → KEYCLOAK_URL=https://auth.intellicare.ia.br (realm intellicare)
```

## Segurança

- Portas 5432 (PostgreSQL) e 9000/9001 (MinIO) no VPS-DATA e VPS-STORAGE devem aceitar
  conexoes **somente dos IPs dos VPSes de aplicacao e dos IPs dos desenvolvedores**.
  Nunca expostas publicamente na internet.
- Acesso administrativo aos VPSes exclusivamente via SSH com chave.
- Credenciais de banco por ambiente (usuarios separados: `intellicare_dev`, `intellicare_staging`).
- Developers acessam o banco de dev via SSH tunnel se necessario:
  `ssh -L 5432:localhost:5432 user@161.97.141.186`

## Consequências

**Positivas:**
- Banco de dados persistente e compartilhado para todos os desenvolvedores
- Maquinas de dev rodam apenas codigo — sem containers pesados de banco
- pgvector com performance nativa Linux (sem overhead WSL2)
- Seeds e cargas de teste preservadas entre reinicios de aplicacao
- Keycloak compartilhado elimina configuracao repetida de realm por dev
- Arquitetura de dev/staging reflete topologia de producao real

**Negativas / riscos:**
- Dependencia de rede: dev requer conexao com a internet para acessar o banco
- VPS-STORAGE com 2 GB RAM esta no limite minimo do MinIO — requer configuracao de
  limite de heap (`deploy.resources.limits.memory: 1G` no compose)
- VPS-DATA e ponto unico de falha para dev e staging — aceitavel para esses ambientes

## DEM de execucao

A implementacao desta ADR sera realizada via `DEM-INF-002_INFRA_DATA_STORAGE`, a ser
criada quando Eduardo iniciar a execucao. Esta ADR serve como decisao arquitetural
registrada; a infraestrutura atual nao e alterada ate a DEM ser aberta e executada.

## Data
2026-03-28

## Autor
ARQUITETO (Eduardo Garabini)
