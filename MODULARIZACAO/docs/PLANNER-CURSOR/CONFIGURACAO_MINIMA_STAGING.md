# Configuração Mínima para Homologação (Staging)

**Data:** 2026-02-20  
**Objetivo:** Deploy funcional e apresentável para demonstração — não produção  
**Escopo:** 6 backends da demo + portal + infraestrutura essencial

---

## 1. Visão Geral

Para um ambiente de **homologação (staging)** que demonstre o IntelliCare de forma funcional e apresentável, a configuração mínima inclui:

| Componente | Quantidade | Observação |
|------------|------------|------------|
| **Infraestrutura** | Postgres + Redis | Obrigatório |
| **Backends** | 6 módulos (Nise, Florence, Oswaldo, Zilda, Grahame, Geralda) | Demo principal |
| **Frontend** | Portal React (build estático) | Servido por nginx ou similar |
| **Monitoramento** | Prometheus + Grafana | Opcional para staging (reduz custo) |

---

## 2. Recursos de Hardware (Mínimo)

### 2.1 VPS / Servidor dedicado

| Recurso | Mínimo | Recomendado para staging |
|---------|--------|---------------------------|
| **vCPUs** | 2 | 4 |
| **RAM** | 4 GB | 8 GB |
| **Disco** | 30 GB | 50 GB SSD |
| **Rede** | 1 IP pública | 1 IP pública |

**Estimativa de uso por serviço:**

| Serviço | RAM aprox. | CPU |
|---------|------------|-----|
| PostgreSQL | 256–512 MB | Baixo |
| Redis | 128–512 MB | Baixo |
| 6 backends Python (Uvicorn) | 1,5–3 GB total | Médio |
| Portal (nginx servindo estático) | ~50 MB | Muito baixo |
| Prometheus (opcional) | 256–512 MB | Baixo |
| Grafana (opcional) | 256 MB | Baixo |

### 2.2 Plataformas PaaS (Railway, Render, Fly.io)

- **Railway:** ~$5–20/mês para staging (depende de serviços)
- **Render:** Free tier limitado; paid ~$7/serviço
- **Fly.io:** Free tier generoso; paid conforme uso

---

## 3. Portas e Serviços

### 3.1 Portas expostas (demo)

| Porta | Serviço | Uso |
|-------|---------|-----|
| **80** | nginx / reverse proxy | HTTP (redirecionar para 443) |
| **443** | nginx / reverse proxy | HTTPS — acesso ao portal |
| **5432** | PostgreSQL | Interno (não expor publicamente) |
| **6379** | Redis | Interno (não expor publicamente) |
| **8000** | Nise | Backend — via reverse proxy |
| **8001** | Florence | Backend — via reverse proxy |
| **8002** | Oswaldo | Backend — via reverse proxy |
| **8003** | Zilda | Backend — via reverse proxy |
| **8004** | Grahame | Backend — via reverse proxy |
| **8006** | Geralda | Backend — via reverse proxy |

**Recomendação:** Backends acessíveis via reverse proxy (nginx/traefik) em subpaths ou subdomínios, sem expor portas 8000–8006 diretamente.

### 3.2 Exemplo de URLs em staging

```
https://staging.intellicare.xxx/           → Portal
https://staging.intellicare.xxx/api/nise/  → Nise (proxy para :8000)
https://staging.intellicare.xxx/api/florence/ → Florence (proxy para :8001)
...
```

Ou subdomínios:
```
https://portal.staging.intellicare.xxx
https://nise.staging.intellicare.xxx
https://florence.staging.intellicare.xxx
...
```

---

## 4. Variáveis de Ambiente (Mínimo)

### 4.1 Infraestrutura (compartilhada)

```env
# PostgreSQL
INTELLICARE_DATABASE_URL=postgresql+asyncpg://intellicare_admin:SENHA@postgres:5432/intellicare_db
# ou para conexão direta: postgresql+asyncpg://user:pass@localhost:5432/intellicare_db

# Redis
REDIS_URL=redis://redis:6379/0
# ou: redis://localhost:6379/0
```

### 4.2 Por backend (6 módulos)

Cada módulo precisa de:
- `INTELLICARE_DATABASE_URL` ou `DATABASE_URL` (apontando para o mesmo Postgres)
- `REDIS_URL` (quando o módulo usa Redis)
- Schema específico quando aplicável (ex.: `oswaldo_operacional`, `florence_operacional`)

**Módulos da demo e dependências:**

| Módulo | Postgres | Redis | Observação |
|--------|----------|-------|------------|
| Nise | Sim | Sim (opcional) | Orquestração |
| Florence | Sim | Sim (cache) | Lab |
| Oswaldo | Sim | Opcional | Cuidado crônico |
| Zilda | Sim | Opcional | Saúde pública |
| Grahame | Sim (FHIR) | Não | Interop |
| Geralda | Sim | Opcional | Atenção primária |

### 4.3 Frontend (build time)

Variáveis **VITE_*** são injetadas no build. Para staging:

```env
VITE_OSWALDO_URL=https://staging.intellicare.xxx/api/oswaldo
VITE_FLORENCE_URL=https://staging.intellicare.xxx/api/florence
VITE_ZILDA_URL=https://staging.intellicare.xxx/api/zilda
VITE_GERALDA_URL=https://staging.intellicare.xxx/api/geralda
VITE_NISE_URL=https://staging.intellicare.xxx/api/nise
VITE_GRAHAME_URL=https://staging.intellicare.xxx/api/grahame
VITE_API_URL=https://staging.intellicare.xxx/api
```

**Importante:** O portal usa `modules.ts` que referencia `VITE_OSWALDO_URL`, `VITE_FLORENCE_URL`, etc. Ajustar conforme a estrutura de URLs do staging. Verificar mapeamento de portas em `start_demo.bat` (Oswaldo=8002, Florence=8001, etc.) e alinhar com `modules.ts`.

---

## 5. Stack Mínima para Staging

### 5.1 Obrigatório

| Componente | Versão | Função |
|------------|--------|--------|
| **Docker** | 20+ | Orquestração de containers |
| **Docker Compose** | 2.x | Compose file |
| **PostgreSQL** | 15 | Banco de dados |
| **Redis** | 7 | Cache/eventos |
| **Python** | 3.11+ | Backends (ou containers) |
| **Node.js** | 18+ | Build do frontend |
| **nginx** (ou Caddy) | — | Reverse proxy + HTTPS + servir estático |

### 5.2 Opcional para staging (reduz custo)

| Componente | Quando incluir |
|------------|----------------|
| Prometheus | Se quiser métricas básicas |
| Grafana | Se quiser dashboards |
| Certbot/Let's Encrypt | HTTPS automático |

---

## 6. Configuração Mínima por Opção

### Opção A: VPS com Docker Compose (controle total)

1. **Servidor:** 4 vCPUs, 8 GB RAM, 50 GB SSD
2. **Docker Compose** com:
   - postgres, redis
   - 6 backends (imagens ou build local)
   - nginx (reverse proxy + static)
3. **HTTPS:** Let's Encrypt via certbot ou nginx
4. **Custo:** ~$20–40/mês (DigitalOcean, Linode, AWS Lightsail, etc.)

### Opção B: Plataforma PaaS (menos ops)

1. **Postgres:** Serviço gerenciado (Railway, Render, Supabase)
2. **Redis:** Serviço gerenciado (Railway, Upstash)
3. **Backends:** 6 serviços (containers ou runtimes)
4. **Frontend:** Static site (Vercel, Netlify, ou mesmo na PaaS)
5. **Custo:** ~$30–80/mês dependendo da plataforma

### Opção C: Híbrido (custo mínimo)

1. **Postgres + Redis:** Docker Compose em VPS pequena (2 GB RAM)
2. **Backends + Portal:** Railway ou Render (free tier onde possível)
3. **Custo:** ~$10–20/mês

---

## 7. Checklist de Configuração Mínima

- [ ] Postgres 15 com banco `intellicare_db` e usuário configurado
- [ ] Redis 7 acessível
- [ ] Migrations executadas (`init-db.sql` ou Alembic)
- [ ] 6 backends com variáveis de ambiente corretas
- [ ] Portal buildado com `VITE_*` apontando para URLs de staging
- [ ] Reverse proxy configurado (nginx/Caddy) com HTTPS
- [ ] Portas 80/443 abertas no firewall
- [ ] Smoke test: portal carrega, cada módulo responde em /health

---

## 8. Resumo Executivo

| Item | Configuração mínima staging |
|------|-----------------------------|
| **Hardware** | 4 vCPUs, 8 GB RAM, 50 GB |
| **Infra** | Postgres 15 + Redis 7 |
| **Aplicações** | 6 backends + portal (build estático) |
| **Rede** | HTTPS (443), reverse proxy |
| **Variáveis** | DATABASE_URL, REDIS_URL, VITE_* (URLs dos backends) |
| **Custo estimado** | $20–50/mês (VPS) ou $30–80/mês (PaaS) |

**Objetivo:** Ambiente funcional e apresentável para demonstração, sem requisitos de produção (HA, backup automatizado, etc.).
