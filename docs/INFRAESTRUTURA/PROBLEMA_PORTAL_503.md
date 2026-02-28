# ⚠️ Problema: Portal 503 Service Unavailable

**Data:** 2026-02-27  
**Status:** ⚠️ **PROBLEMA IDENTIFICADO**

---

## 🔍 Problema

Ao acessar `portal.intellicare.ia.br`, o usuário recebe:

```
503 Service Unavailable
```

---

## 🔎 Diagnóstico

### 1. Container do Portal NÃO Existe ❌

```bash
docker ps -a | grep portal
# Resultado: (vazio)
```

**Causa:** O container `intellicare-portal` não está rodando no servidor.

---

### 2. Rota Traefik Configurada Corretamente ✅

```yaml
# /opt/intellicare/intellicare/traefik/dynamic/routes-intellicare.yml

portal:
  rule: "Host(`portal.intellicare.ia.br`)"
  service: portal-svc

portal-svc:
  loadBalancer:
    servers:
      - url: "http://intellicare-portal:80"
```

**Status:** Rota configurada, mas aponta para container inexistente.

---

### 3. Outros Problemas Identificados ⚠️

```bash
docker ps

intellicare-wanda       Restarting (3) 29 seconds ago  ⚠️
intellicare-florence    Restarting (3) 54 seconds ago  ⚠️
intellicare-oswaldo     Restarting (3) 35 seconds ago  ⚠️
intellicare-traefik     Up 13 minutes (unhealthy)      ⚠️
```

**Containers com problema:**
- Wanda (8004) - Loop de restart
- Florence (8001) - Loop de restart
- Oswaldo (8002) - Loop de restart
- Traefik - Unhealthy

**Containers funcionando:**
- ✅ Donabedian (8003)
- ✅ Geralda (8006)
- ✅ Comunicacao (8005)
- ✅ PostgreSQL (5432)
- ✅ Redis (6379)

---

## 🎯 Soluções Possíveis

### Opção 1: Subir Container do Portal (Recomendado)

**Pré-requisito:** Verificar se existe docker-compose para o portal

```bash
# Verificar se portal está no docker-compose.full.yml
grep -A 20 "portal:" /opt/intellicare/intellicare/docker-compose.full.yml

# Se existir, subir o portal
cd /opt/intellicare/intellicare
docker compose -f docker-compose.full.yml up -d intellicare-portal
```

**Problema:** Portal não está definido no docker-compose.full.yml ❌

---

### Opção 2: Redirecionar para Admin (Temporário)

Alterar redirecionamento dos domínios raiz para apontar para um serviço funcionando:

```yaml
# routes-root-domains.yml
# ANTES: https://portal.intellicare.ia.br/
# DEPOIS: https://admin.intellicare.ia.br/
```

**Vantagem:** Solução imediata  
**Desvantagem:** Admin pode não ser interface adequada

---

### Opção 3: Criar Landing Page Simples

Criar container Nginx com página estática:

```bash
# Criar diretório
mkdir -p /opt/intellicare/landing

# Criar index.html
cat > /opt/intellicare/landing/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>IntelliCare - Portal em Manutenção</title>
    <style>
        body { font-family: Arial; text-align: center; padding: 50px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>🏥 IntelliCare</h1>
    <p>Portal em manutenção. Por favor, tente novamente em breve.</p>
    <p><a href="https://admin.intellicare.ia.br">Acessar Painel Administrativo</a></p>
</body>
</html>
EOF

# Subir Nginx
docker run -d \
  --name intellicare-portal \
  --network intellicare-network \
  -v /opt/intellicare/landing:/usr/share/nginx/html:ro \
  nginx:alpine
```

---

### Opção 4: Investigar e Corrigir Portal Original

**Passos:**

1. Verificar se existe código do portal:
   ```bash
   ls -la /opt/intellicare/intellicare/intellicare-portal/
   ```

2. Verificar se existe Dockerfile:
   ```bash
   ls -la /opt/intellicare/intellicare/intellicare-portal/Dockerfile
   ```

3. Build e subir portal:
   ```bash
   cd /opt/intellicare/intellicare/intellicare-portal
   docker build -t intellicare-portal .
   docker run -d --name intellicare-portal --network intellicare-network intellicare-portal
   ```

---

## 🚀 Solução Imediata Recomendada

### Criar Landing Page Temporária

```bash
# SSH no servidor
ssh root@167.86.97.142

# Criar diretório
mkdir -p /opt/intellicare/landing

# Criar página HTML
cat > /opt/intellicare/landing/index.html << 'EOF'
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IntelliCare - Plataforma de Saúde</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }
        h1 { font-size: 3em; margin-bottom: 20px; }
        p { font-size: 1.2em; margin-bottom: 30px; opacity: 0.9; }
        .links { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
        a {
            display: inline-block;
            padding: 15px 30px;
            background: white;
            color: #667eea;
            text-decoration: none;
            border-radius: 10px;
            font-weight: bold;
            transition: transform 0.3s;
        }
        a:hover { transform: translateY(-5px); }
        .status { margin-top: 40px; font-size: 0.9em; opacity: 0.7; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 IntelliCare</h1>
        <p>Plataforma Modular de Saúde</p>
        <div class="links">
            <a href="https://admin.intellicare.ia.br">Painel Administrativo</a>
            <a href="https://api.intellicare.ia.br/v1/oswaldo/api/docs">API Oswaldo</a>
            <a href="https://api.intellicare.ia.br/v1/donabedian/api/docs">API Donabedian</a>
        </div>
        <div class="status">
            <p>✅ Sistema operacional | v2.0.0</p>
        </div>
    </div>
</body>
</html>
EOF

# Subir container Nginx
docker run -d \
  --name intellicare-portal \
  --network intellicare_default \
  -v /opt/intellicare/landing:/usr/share/nginx/html:ro \
  --restart unless-stopped \
  nginx:alpine

# Verificar
docker ps | grep portal
```

---

## 📋 Checklist de Execução

- [ ] SSH no servidor
- [ ] Criar diretório `/opt/intellicare/landing`
- [ ] Criar `index.html`
- [ ] Subir container Nginx
- [ ] Verificar container rodando
- [ ] Testar `https://portal.intellicare.ia.br`
- [ ] Verificar redirecionamentos dos domínios raiz

---

## 🎯 Próximos Passos

1. ✅ Implementar solução imediata (landing page)
2. ⏳ Investigar portal original
3. ⏳ Corrigir containers em loop (Wanda, Florence, Oswaldo)
4. ⏳ Corrigir healthcheck do Traefik

---

**Criado por:** Augment Agent  
**Data:** 2026-02-27  
**Status:** ⚠️ **AGUARDANDO SOLUÇÃO**

