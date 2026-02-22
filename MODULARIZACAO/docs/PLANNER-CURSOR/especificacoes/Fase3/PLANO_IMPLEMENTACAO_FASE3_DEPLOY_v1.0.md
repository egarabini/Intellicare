# PLANO_IMPLEMENTACAO — Fase 3: Deploy Mínimo Viável

**Versão:** 1.0  
**Data:** 2026-02-20  
**Status:** Aprovado para execução  
**Referência:** `ESPECIFICACAO_TECNICA_FASE3_DEPLOY_v1.0.md`  
**Estimativa Total:** ~6 horas

---

## 1. Visão Geral

Este plano detalha a implementação da Fase 3 - Deploy Mínimo Viável, dividida em 6 fases sequenciais.

---

## 2. Fases de Implementação

### Fase 3.1 - Criar .env.example (1 hora)

**Objetivo:** Documentar todas as variáveis de ambiente necessárias

**Tarefas:**
1. Analisar cada módulo backend para identificar variáveis
2. Criar `.env.example` na raiz de MODULARIZACAO
3. Documentar cada variável com comentários
4. Incluir valores de exemplo (não credenciais reais)

**Entregáveis:**
- `MODULARIZACAO/.env.example` (~150 linhas)

**Comandos:**
```bash
cd MODULARIZACAO
# Criar arquivo .env.example
# Documentar variáveis de:
# - PostgreSQL (host, port, user, password, database)
# - Redis (host, port, password)
# - Cada backend (port, database_url, configurações específicas)
# - Frontend (VITE_API_* URLs)
# - Monitoring (Prometheus, Grafana)
# - Deployment (environment, log_level, domain)
```

**Validação:**
- [ ] Arquivo criado
- [ ] Todas as variáveis documentadas
- [ ] Comentários explicativos presentes
- [ ] Valores de exemplo (não credenciais reais)

---

### Fase 3.2 - Criar docker-compose.full.yml (1.5 horas)

**Objetivo:** Orquestração unificada de toda a stack

**Tarefas:**
1. Criar `docker-compose.full.yml` que extends `docker-compose.yml`
2. Adicionar serviço para cada backend (6 serviços)
3. Adicionar serviço para frontend (portal)
4. Configurar rede compartilhada
5. Definir health checks para cada serviço
6. Configurar restart policies
7. Definir dependências entre serviços

**Entregáveis:**
- `MODULARIZACAO/docker-compose.full.yml` (~300 linhas)

**Estrutura:**
```yaml
version: "3.9"

services:
  # Infraestrutura (extends docker-compose.yml)
  postgres: ...
  redis: ...
  prometheus: ...
  grafana: ...
  
  # Backend Services
  florence:
    build: ./intellicare-florence
    ports: ["8001:8000"]
    environment: ...
    depends_on: [postgres, redis]
    healthcheck: ...
  
  oswaldo: ...
  donabedian: ...
  wanda: ...
  comunicacao: ...
  geralda: ...
  
  # Frontend
  portal:
    build: ./intellicare-portal/frontend
    ports: ["3001:80"]
    environment: ...
    depends_on: [florence, oswaldo, ...]
```

**Validação:**
- [ ] Arquivo criado
- [ ] Todos os 6 backends incluídos
- [ ] Frontend incluído
- [ ] Health checks configurados
- [ ] Dependências corretas
- [ ] Teste: `docker-compose -f docker-compose.full.yml config` (valida sintaxe)

---

### Fase 3.3 - Configurar Frontend (1 hora)

**Objetivo:** Frontend usa variáveis de ambiente para URLs dos backends

**Tarefas:**
1. Criar `intellicare-portal/frontend/.env.example`
2. Atualizar código do frontend para usar `import.meta.env.VITE_*`
3. Criar `Dockerfile` para build do frontend
4. Criar `nginx.conf` para servir frontend
5. Testar build local

**Entregáveis:**
- `intellicare-portal/frontend/.env.example`
- `intellicare-portal/frontend/Dockerfile`
- `intellicare-portal/frontend/nginx.conf`
- Código atualizado para usar variáveis

**Dockerfile:**
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_FLORENCE_URL
ARG VITE_API_OSWALDO_URL
ARG VITE_API_DONABEDIAN_URL
ARG VITE_API_WANDA_URL
ARG VITE_API_COMUNICACAO_URL
ARG VITE_API_GERALDA_URL
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Validação:**
- [ ] `.env.example` criado
- [ ] Código usa `import.meta.env.VITE_*`
- [ ] Dockerfile criado
- [ ] nginx.conf criado
- [ ] Build local funciona: `docker build -t portal-test .`

---

### Fase 3.4 - Criar Script de Smoke Tests (1.5 horas)

**Objetivo:** Script automatizado para validar health de todos os serviços

**Tarefas:**
1. Criar `MODULARIZACAO/scripts/smoke_tests.py`
2. Implementar verificação de health para cada backend
3. Implementar verificação de portal
4. Implementar verificação de PostgreSQL
5. Implementar verificação de Redis
6. Gerar relatório JSON + console output
7. Adicionar opção `--url` para testar ambiente remoto

**Entregáveis:**
- `MODULARIZACAO/scripts/smoke_tests.py` (~200 linhas)

**Estrutura:**
```python
import requests
import sys
import json
from datetime import datetime

SERVICES = {
    "florence": "http://localhost:8001/health",
    "oswaldo": "http://localhost:8002/health",
    "donabedian": "http://localhost:8003/health",
    "wanda": "http://localhost:8004/health",
    "comunicacao": "http://localhost:8005/health",
    "geralda": "http://localhost:8006/health",
    "portal": "http://localhost:3001",
}

def check_service(name, url):
    try:
        response = requests.get(url, timeout=5)
        return {
            "status": "OK" if response.status_code == 200 else "FAIL",
            "response_time_ms": int(response.elapsed.total_seconds() * 1000)
        }
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}

def main():
    results = {}
    for name, url in SERVICES.items():
        results[name] = check_service(name, url)
    
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "OK" if all(r["status"] == "OK" for r in results.values()) else "FAIL",
        "services": results
    }
    
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["status"] == "OK" else 1)

if __name__ == "__main__":
    main()
```

**Validação:**
- [ ] Script criado
- [ ] Verifica todos os 6 backends
- [ ] Verifica portal
- [ ] Gera relatório JSON
- [ ] Exit code correto (0=OK, 1=FAIL)
- [ ] Teste: `python scripts/smoke_tests.py`

---

### Fase 3.5 - Criar GUIA_DEPLOY.md (1 hora)

**Objetivo:** Documentação completa do processo de deploy

**Tarefas:**
1. Criar `MODULARIZACAO/docs/PLANNER-CURSOR/GUIA_DEPLOY.md`
2. Documentar pré-requisitos
3. Documentar deploy local
4. Documentar deploy em VPS
5. Documentar configuração HTTPS
6. Documentar smoke tests
7. Documentar troubleshooting
8. Documentar rollback

**Entregáveis:**
- `GUIA_DEPLOY.md` (~400 linhas)

**Seções:**
1. Pré-requisitos
2. Deploy Local (Desenvolvimento)
3. Deploy em VPS (Staging/Produção)
4. Configuração HTTPS (Let's Encrypt)
5. Smoke Tests
6. Troubleshooting
7. Rollback
8. FAQ

**Validação:**
- [ ] Documento criado
- [ ] Todas as seções presentes
- [ ] Comandos exatos documentados
- [ ] Screenshots/exemplos incluídos
- [ ] Novo dev consegue seguir sem ambiguidade

---

### Fase 3.6 - Validação Final (30 min)

**Objetivo:** Validar todos os requisitos e critérios de aceite

**Tarefas:**
1. Validar RF-001 a RF-007
2. Validar CA-001 a CA-006
3. Testar deploy local completo
4. Executar smoke tests
5. Criar relatório de execução

**Checklist de Validação:**
- [ ] RF-001: `.env.example` lista todas as variáveis
- [ ] RF-002: Um comando sobe toda a stack
- [ ] RF-003: Frontend usa variáveis de ambiente
- [ ] RF-004: Projeto acessível via URL (local)
- [ ] RF-005: Smoke tests validam todos os serviços
- [ ] RF-006: GUIA_DEPLOY.md permite deploy reproduzível
- [ ] RF-007: Infraestrutura disponível
- [ ] CA-001: Deploy funciona em máquina limpa
- [ ] CA-002: Script de deploy sobe toda a stack
- [ ] CA-003: Portal carrega e módulos respondem
- [ ] CA-004: HTTPS configurado (documentado)
- [ ] CA-005: Smoke tests reportam OK/FALHA
- [ ] CA-006: Novo dev consegue seguir GUIA_DEPLOY.md

**Entregáveis:**
- `RELATORIO_EXECUCAO_FASE3_2026-02-20.md`

---

## 3. Dependências entre Fases

```
3.1 (.env.example)
  ↓
3.2 (docker-compose.full.yml) ← depende de 3.1
  ↓
3.3 (Frontend config) ← depende de 3.1
  ↓
3.4 (Smoke tests) ← depende de 3.2, 3.3
  ↓
3.5 (GUIA_DEPLOY.md) ← depende de 3.1, 3.2, 3.3, 3.4
  ↓
3.6 (Validação) ← depende de todas as anteriores
```

---

## 4. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Variáveis de ambiente incompletas | Média | Alto | Revisar cada módulo individualmente |
| Docker build falha | Baixa | Médio | Testar build de cada serviço isoladamente |
| Health checks não funcionam | Média | Médio | Implementar health checks simples primeiro |
| Documentação ambígua | Média | Alto | Pedir feedback de outro dev |

---

## 5. Estimativa de Tempo

| Fase | Estimativa | Complexidade |
|------|------------|--------------|
| 3.1 - .env.example | 1 hora | Baixa |
| 3.2 - docker-compose.full.yml | 1.5 horas | Média |
| 3.3 - Frontend config | 1 hora | Média |
| 3.4 - Smoke tests | 1.5 horas | Média |
| 3.5 - GUIA_DEPLOY.md | 1 hora | Baixa |
| 3.6 - Validação | 30 min | Baixa |
| **Total** | **~6 horas** | - |

---

## 6. Próximos Passos (Pós-Fase 3)

- **Fase 4:** Monitoramento avançado (alertas, dashboards)
- **Fase 5:** Produção ready (auth, LGPD, hardening)
- **CI/CD:** GitHub Actions para deploy automatizado

---

## 7. Histórico de Alterações

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 2026-02-20 | Versão inicial |

