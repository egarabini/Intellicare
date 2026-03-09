# 🌐 Roteamento de Domínios - IntelliCare

**Data:** 2026-02-26  
**Versão:** 2.0.0  
**Status:** ✅ **DEFINITIVO**

---

## 📋 Visão Geral

O IntelliCare possui **2 domínios principais** com estratégias de roteamento diferentes:

1. **intellicare.ia.br** - Plataforma principal (subdomínios fixos)
2. **saudeplanner.com.br** - White-label multi-tenant (subdomínios dinâmicos)

---

## 🔍 Resposta Direta: Para Onde Vão os Domínios Raiz?

### ❌ **ATUALMENTE NÃO CONFIGURADO**

Se você acessar **sem porta e sem subdomínio**:

| URL | Status Atual | Comportamento |
|-----|--------------|---------------|
| `http://intellicare.ia.br` | ❌ **Não configurado** | Sem rota definida (404 ou timeout) |
| `https://intellicare.ia.br` | ❌ **Não configurado** | Sem rota definida (404 ou timeout) |
| `http://saudeplanner.com.br` | ❌ **Não configurado** | Sem rota definida (404 ou timeout) |
| `https://saudeplanner.com.br` | ❌ **Não configurado** | Sem rota definida (404 ou timeout) |

### ✅ **RECOMENDAÇÃO**

Os domínios raiz **DEVEM** redirecionar para:

| Domínio Raiz | Deve Redirecionar Para | Razão |
|--------------|------------------------|-------|
| `intellicare.ia.br` | `portal.intellicare.ia.br` | Portal principal da plataforma |
| `www.intellicare.ia.br` | `portal.intellicare.ia.br` | Convenção web padrão |
| `saudeplanner.com.br` | `portal.intellicare.ia.br` ou página de marketing | Evitar confusão |
| `www.saudeplanner.com.br` | `portal.intellicare.ia.br` ou página de marketing | Convenção web padrão |

---

## 🏗️ Arquitetura Atual

### 1. intellicare.ia.br (Plataforma Principal)

**Estratégia:** Subdomínios fixos para cada serviço

#### Subdomínios Configurados

| Subdomínio | Destino | Porta Interna | Função |
|------------|---------|---------------|--------|
| `admin.intellicare.ia.br` | intellicare-admin | 8010 | Painel administrativo |
| `portal.intellicare.ia.br` | intellicare-portal | 80 | Portal web (React) |
| `api.intellicare.ia.br/v1/florence` | intellicare-florence | 8001 | API Florence |
| `api.intellicare.ia.br/v1/oswaldo` | intellicare-oswaldo | 8002 | API Oswaldo |
| `api.intellicare.ia.br/v1/donabedian` | intellicare-donabedian | 8003 | API Donabedian |
| `api.intellicare.ia.br/v1/wanda` | intellicare-wanda | 8004 | API Wanda |
| `api.intellicare.ia.br/v1/comunicacao` | intellicare-comunicacao | 8005 | API Comunicacao |
| `auth.intellicare.ia.br` | keycloak | 8080 | Autenticação SSO |
| `traefik.intellicare.ia.br` | traefik | 8080 | Dashboard Traefik |

#### Exemplo de Acesso

```bash
# Portal
https://portal.intellicare.ia.br

# Admin
https://admin.intellicare.ia.br

# API Florence
https://api.intellicare.ia.br/v1/florence/api/v1/health

# Keycloak
https://auth.intellicare.ia.br
```

---

### 2. saudeplanner.com.br (White-Label Multi-Tenant)

**Estratégia:** Subdomínios dinâmicos para tenants + subdomínios fixos para módulos

#### Subdomínios Fixos (Módulos)

| Subdomínio | Destino | Porta Interna | Função |
|------------|---------|---------------|--------|
| `oswaldo.saudeplanner.com.br` | intellicare-oswaldo | 8002 | API Oswaldo |
| `florence.saudeplanner.com.br` | intellicare-florence | 8001 | API Florence |
| `zilda.saudeplanner.com.br` | intellicare-zilda | 8007 | API Zilda |
| `donabedian.saudeplanner.com.br` | intellicare-donabedian | 8003 | API Donabedian |
| `comunicacao.saudeplanner.com.br` | intellicare-comunicacao | 8005 | API Comunicacao |

#### Subdomínios Dinâmicos (White-Label)

**Padrão:** `{tenant}.saudeplanner.com.br` → Portal com `X-Tenant-ID: {tenant}`

| Subdomínio | Destino | Header Injetado | Função |
|------------|---------|-----------------|--------|
| `hospital-abc.saudeplanner.com.br` | intellicare-portal:80 | `X-Tenant-ID: hospital-abc` | Portal white-label |
| `clinica-xyz.saudeplanner.com.br` | intellicare-portal:80 | `X-Tenant-ID: clinica-xyz` | Portal white-label |
| `ubs-centro.saudeplanner.com.br` | intellicare-portal:80 | `X-Tenant-ID: ubs-centro` | Portal white-label |

**Nota:** O frontend lê o header `X-Tenant-ID` ou o hostname para aplicar branding customizado.

#### Exemplo de Acesso

```bash
# Módulo específico
https://oswaldo.saudeplanner.com.br/api/v1/health

# Tenant white-label
https://hospital-abc.saudeplanner.com.br
# → Portal carrega com tema/logo do Hospital ABC

https://clinica-xyz.saudeplanner.com.br
# → Portal carrega com tema/logo da Clínica XYZ
```

---

## 🔧 Configuração Traefik

### Arquivo: `traefik/dynamic/routes-intellicare.yml`

```yaml
http:
  routers:
    admin:
      rule: "Host(`admin.intellicare.ia.br`)"
      service: admin-svc
      
    portal:
      rule: "Host(`portal.intellicare.ia.br`)"
      service: portal-svc
      
    api-florence:
      rule: "Host(`api.intellicare.ia.br`) && PathPrefix(`/v1/florence`)"
      service: florence-svc
```

### Arquivo: `traefik/dynamic/routes-saudeconectada.yml`

```yaml
http:
  routers:
    # Módulos fixos
    sc-oswaldo:
      rule: "Host(`oswaldo.saudeplanner.com.br`)"
      service: oswaldo-svc
      
    # White-label wildcard (prioridade baixa)
    sc-whitelabel:
      rule: "HostRegexp(`{tenant:[a-z0-9_]+}.saudeplanner.com.br`)"
      service: portal-svc
      priority: 1  # Menor prioridade que rotas fixas
```

---

## ⚠️ Problema Atual: Domínios Raiz Não Configurados

### Comportamento Atual

```bash
# ❌ Não funciona (sem rota definida)
curl https://intellicare.ia.br
# → 404 Not Found ou timeout

# ❌ Não funciona (sem rota definida)
curl https://saudeplanner.com.br
# → 404 Not Found ou timeout

# ✅ Funciona (subdomínio configurado)
curl https://portal.intellicare.ia.br
# → 200 OK (Portal React)
```

---

## ✅ Solução Recomendada

### Opção 1: Redirecionar para Portal (Recomendado)

Adicionar rotas de redirecionamento em `routes-intellicare.yml`:

```yaml
http:
  routers:
    # Redirecionar domínio raiz para portal
    root-redirect:
      rule: "Host(`intellicare.ia.br`) || Host(`www.intellicare.ia.br`)"
      entryPoints:
        - websecure
      middlewares:
        - redirect-to-portal
      service: noop@internal
      
  middlewares:
    redirect-to-portal:
      redirectRegex:
        regex: "^https://(?:www\\.)?intellicare\\.ia\\.br/(.*)"
        replacement: "https://portal.intellicare.ia.br/${1}"
        permanent: true
```

### Opção 2: Servir Página de Marketing

Criar serviço de landing page:

```yaml
http:
  routers:
    root-landing:
      rule: "Host(`intellicare.ia.br`) || Host(`www.intellicare.ia.br`)"
      service: landing-svc
      
  services:
    landing-svc:
      loadBalancer:
        servers:
          - url: "http://intellicare-landing:80"
```

---

## 📊 Resumo de Roteamento

| URL | Destino Atual | Recomendação |
|-----|---------------|--------------|
| `intellicare.ia.br` | ❌ Não configurado | ✅ Redirecionar para `portal.intellicare.ia.br` |
| `portal.intellicare.ia.br` | ✅ Portal (React) | ✅ Manter |
| `admin.intellicare.ia.br` | ✅ Admin Panel | ✅ Manter |
| `api.intellicare.ia.br/v1/*` | ✅ APIs (path-based) | ✅ Manter |
| `saudeplanner.com.br` | ❌ Não configurado | ✅ Redirecionar ou landing page |
| `{tenant}.saudeplanner.com.br` | ✅ Portal white-label | ✅ Manter |
| `{module}.saudeplanner.com.br` | ✅ APIs diretas | ✅ Manter |

---

**Criado por:** Augment Agent  
**Data:** 2026-02-26  
**Versão:** 2.0.0  
**Status:** ✅ **DEFINITIVO**

