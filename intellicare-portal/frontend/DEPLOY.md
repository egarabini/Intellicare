# IntelliCare Portal - Deploy Guide

## 📋 Visão Geral

O IntelliCare Portal é a interface web do sistema IntelliCare, construída com:
- **React 18** + **TypeScript**
- **Vite** (build tool)
- **Nginx** (servidor web em produção)
- **Docker** (containerização)

---

## 🔧 Configuração de Ambiente

### Variáveis de Ambiente

O frontend utiliza variáveis de ambiente com prefixo `VITE_*` que são injetadas durante o build.

#### Desenvolvimento Local

1. Copie o arquivo de exemplo:
```bash
cp .env.example .env.local
```

2. Edite `.env.local` com as URLs dos backends:
```bash
VITE_API_FLORENCE_URL=http://localhost:8001
VITE_API_OSWALDO_URL=http://localhost:8002
VITE_API_DONABEDIAN_URL=http://localhost:8003
VITE_API_WANDA_URL=http://localhost:8004
VITE_API_COMUNICACAO_URL=http://localhost:8005
VITE_API_GERALDA_URL=http://localhost:8006
```

#### Produção

As variáveis são passadas como **build arguments** no Docker:

```bash
docker build \
  --build-arg VITE_API_FLORENCE_URL=https://api.intellicare.com/florence \
  --build-arg VITE_API_OSWALDO_URL=https://api.intellicare.com/oswaldo \
  --build-arg VITE_API_DONABEDIAN_URL=https://api.intellicare.com/donabedian \
  --build-arg VITE_API_WANDA_URL=https://api.intellicare.com/wanda \
  --build-arg VITE_API_COMUNICACAO_URL=https://api.intellicare.com/comunicacao \
  --build-arg VITE_API_GERALDA_URL=https://api.intellicare.com/geralda \
  --build-arg VITE_APP_VERSION=0.1.0-demo \
  -t intellicare-portal:latest .
```

---

## 🚀 Deploy

### Opção 1: Docker Compose (Recomendado)

Use o `docker-compose.full.yml` na raiz do projeto:

```bash
# Na raiz do projeto ./
docker-compose -f docker-compose.full.yml up -d portal
```

### Opção 2: Docker Build Manual

```bash
# Build
docker build -t intellicare-portal:latest .

# Run
docker run -d \
  --name intellicare-portal \
  -p 3001:80 \
  intellicare-portal:latest
```

### Opção 3: Desenvolvimento Local (sem Docker)

```bash
# Instalar dependências
pnpm install

# Rodar em modo desenvolvimento
pnpm dev

# Build para produção
pnpm build

# Preview do build
pnpm preview
```

---

## 📁 Estrutura de Arquivos

```
frontend/
├── Dockerfile              # Multi-stage build (node + nginx)
├── nginx.conf              # Configuração do Nginx
├── .env.example            # Template de variáveis de ambiente
├── DEPLOY.md               # Este arquivo
├── src/
│   ├── config/
│   │   ├── env.ts          # Carrega variáveis VITE_*
│   │   └── modules.ts      # Registro de módulos backend
│   ├── services/           # Clientes HTTP para backends
│   ├── components/         # Componentes React
│   └── pages/              # Páginas da aplicação
└── dist/                   # Build de produção (gerado)
```

---

## 🔒 Segurança

O `nginx.conf` inclui headers de segurança:
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

---

## 📊 Performance

### Otimizações Implementadas

1. **Gzip Compression**: Ativado para text/css, text/javascript, application/json
2. **Cache de Assets**: 1 ano para JS/CSS/fonts/images
3. **No-cache para HTML**: Garante que index.html sempre busca a versão mais recente
4. **Code Splitting**: Chunks separados para react, ui, forms, charts

### Health Check

Endpoint disponível em `/health`:
```bash
curl http://localhost:3001/health
# Resposta: healthy
```

---

## 🐛 Troubleshooting

### Problema: Variáveis de ambiente não estão sendo aplicadas

**Solução**: Variáveis `VITE_*` são injetadas no **build time**, não em runtime. Você precisa rebuildar a imagem Docker com os novos valores.

### Problema: CORS errors ao chamar backends

**Solução**: Verifique se as URLs dos backends estão corretas e acessíveis. Em produção, use um reverse proxy (Nginx/Traefik) para evitar CORS.

### Problema: 404 ao recarregar página em rota diferente de /

**Solução**: O `nginx.conf` já está configurado com `try_files $uri $uri/ /index.html` para suportar SPA routing.

---

## 📝 Notas

- **Build Args vs Runtime Env**: Vite injeta variáveis no build, então mudanças requerem rebuild
- **HTTPS**: Em produção, use um reverse proxy (Nginx/Traefik) na frente para terminar SSL
- **Logs**: Nginx logs estão em `/var/log/nginx/` dentro do container

---

**Versão**: 0.1.0-demo  
**Última atualização**: 2026-02-20

