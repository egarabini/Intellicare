# 🔌 IntelliCare - Mapeamento Completo de Portas

**Data:** 2026-02-26  
**Versão:** 2.0.0  
**Status:** ✅ **DEFINITIVO**

---

## 📊 Tabela Consolidada de Portas

| Porta | Módulo/Serviço | Tipo | Descrição | Container Port | Arquivo Config |
|-------|----------------|------|-----------|----------------|----------------|
| **8001** | Florence | Backend | RAG + Protocolos Clínicos | 8000 | `.env.full` FLORENCE_PORT |
| **8002** | Oswaldo | Backend | Análise Clínica + FHIR | 8000 | `.env.full` OSWALDO_PORT |
| **8003** | Donabedian | Backend | Qualidade + Indicadores | 8000 | `.env.full` DONABEDIAN_PORT |
| **8004** | Wanda | Backend | Orquestrador IA | 8000 | `.env.full` WANDA_PORT |
| **8005** | Comunicacao | Backend | WhatsApp + Email + SMS | 8000 | `.env.full` COMUNICACAO_PORT |
| **8006** | Geralda | Backend | Gestão + Administrativo | 8000 | `.env.full` GERALDA_PORT |
| **8007** | Zilda | Backend | CNES + DATASUS | 8000 | `.env.full` ZILDA_PORT |
| **8008** | MINERVA/Minerva | Backend | Extração Documentos Médicos | 8008 | `.env.full` MINERVA_PORT |
| **8009** | Pierre | Backend | Scientific Search (PubMed + Tavily) | 8009 | `.env.full` PIERRE_PORT |
| **8010** | Admin | Backend | Administração do Sistema | 8010 | `.env.full` ADMIN_PORT |
| **8011** | Gestor | Backend | Gestão de Módulos Clínicos | 8011 | `.env.full` GESTOR_PORT |
| **8012** | Grahame | Backend | FHIR R4 + CDS Hooks + Terminology | 8000 | `.env.full` GRAHAME_PORT |
| **8013** | Nise | Backend | Chatbot Inteligente + Treinamento | 8000 | `.env.full` NISE_PORT |
| **3001** | Portal | Frontend | Interface Web (React + Vite) | 80 | `.env.full` PORTAL_PORT |
| **5432** | PostgreSQL | Database | Banco de Dados Principal | 5432 | Padrão PostgreSQL |
| **6379** | Redis | Cache | Cache + Pub/Sub | 6379 | Padrão Redis |
| **3000** | Grafana | Monitoring | Dashboards de Monitoramento | 3000 | `.env.full` GRAFANA_PORT |
| **9090** | Prometheus | Monitoring | Métricas do Sistema | 9090 | `.env.full` PROMETHEUS_PORT |
| **587** | SMTP | Email | Servidor de Email (externo) | 587 | Padrão SMTP |

---

## 🔍 Detalhamento por Módulo

### Backend Modules (Porta Externa → Porta Interna)

#### 1. Florence (8001 → 8000)
- **Função:** RAG + Protocolos Clínicos
- **Container:** `intellicare-florence`
- **Healthcheck:** `http://localhost:8000/api/v1/health`
- **Docs:** `http://localhost:8001/api/docs`

#### 2. Oswaldo (8002 → 8000)
- **Função:** Análise Clínica + FHIR
- **Container:** `intellicare-oswaldo`
- **Healthcheck:** `http://localhost:8000/api/v1/health`
- **Docs:** `http://localhost:8002/api/docs`

#### 3. Donabedian (8003 → 8000)
- **Função:** Qualidade + Indicadores
- **Container:** `intellicare-donabedian`
- **Healthcheck:** `http://localhost:8000/api/v1/health`
- **Docs:** `http://localhost:8003/api/docs`

#### 4. Wanda (8004 → 8000)
- **Função:** Orquestrador IA
- **Container:** `intellicare-wanda`
- **Healthcheck:** `http://localhost:8000/api/v1/health`
- **Docs:** `http://localhost:8004/api/docs`

#### 5. Comunicacao (8005 → 8000)
- **Função:** WhatsApp + Email + SMS
- **Container:** `intellicare-comunicacao`
- **Healthcheck:** `http://localhost:8000/api/v1/health`
- **Docs:** `http://localhost:8005/api/docs`
- **Webhook WAHA:** `POST /api/v1/webhooks/waha`

#### 6. Geralda (8006 → 8000)
- **Função:** Gestão + Administrativo
- **Container:** `intellicare-geralda`
- **Healthcheck:** `http://localhost:8000/api/v1/health`
- **Docs:** `http://localhost:8006/api/docs`

#### 7. Zilda (8007 → 8000)
- **Função:** CNES + DATASUS
- **Container:** `intellicare-zilda`
- **Healthcheck:** `http://localhost:8000/api/v1/health`
- **Docs:** `http://localhost:8007/api/docs`

#### 8. MINERVA/Minerva (8008 → 8008)
- **Função:** Extração de Documentos Médicos
- **Container:** `intellicare-minerva`
- **Healthcheck:** `http://localhost:8008/api/v1/health`
- **Docs:** `http://localhost:8008/api/docs`
- **Nota:** Porta interna também é 8008

#### 9. Pierre (8009 → 8009)
- **Função:** Scientific Search (PubMed + Tavily + BVS/BIREME)
- **Container:** `intellicare-pierre`
- **Healthcheck:** `http://localhost:8009/api/v1/health`
- **Docs:** `http://localhost:8009/api/docs`
- **Nota:** Porta interna também é 8009

#### 10. Admin (8010 → 8010)
- **Função:** Administração do Sistema
- **Container:** `intellicare-admin`
- **Healthcheck:** `http://localhost:8010/api/v1/health`
- **Docs:** `http://localhost:8010/api/docs`
- **Nota:** Porta interna também é 8010

#### 11. Gestor (8011 → 8011)
- **Função:** Gestão de Módulos Clínicos
- **Container:** `intellicare-gestor`
- **Healthcheck:** `http://localhost:8011/api/v1/health`
- **Docs:** `http://localhost:8011/api/docs`
- **Nota:** Porta interna também é 8011

#### 12. Grahame (8012 → 8000)
- **Função:** FHIR R4 + CDS Hooks 2.0 + Terminology Service
- **Container:** `intellicare-grahame`
- **Healthcheck:** `http://localhost:8000/api/v1/health`
- **Docs:** `http://localhost:8012/api/docs`
- **Endpoints Especiais:**
  - FHIR Metadata: `GET /api/v1/fhir/metadata`
  - CDS Hooks: `POST /api/v1/cds-hooks`
  - Terminology: `POST /api/v1/fhir/ValueSet/$expand`
  - HL7v2: `POST /api/v1/hl7v2/adt-a04`
  - CCDA Import: `POST /api/v1/fhir/DocumentReference/$ccda-import`
  - Excalidraw: `POST /api/v1/excalidraw/diagrams`

#### 13. Nise (8013 → 8000)
- **Função:** Chatbot Inteligente + Treinamento
- **Container:** `intellicare-nise`
- **Healthcheck:** `http://localhost:8000/api/v1/health`
- **Docs:** `http://localhost:8013/api/docs`
- **Integra com:** Flowise (3000), Ollama (11434), Kestra (8080)

---

### Frontend

#### Portal (3001 → 80)
- **Função:** Interface Web (React + Vite)
- **Container:** `intellicare-portal`
- **URL:** `http://localhost:3001`
- **Build:** Nginx serving static files
- **Variáveis de Ambiente:**
  - `VITE_API_FLORENCE_URL=http://localhost:8001`
  - `VITE_API_OSWALDO_URL=http://localhost:8002`
  - `VITE_API_DONABEDIAN_URL=http://localhost:8003`
  - `VITE_API_WANDA_URL=http://localhost:8004`
  - `VITE_API_COMUNICACAO_URL=http://localhost:8005`
  - `VITE_API_GERALDA_URL=http://localhost:8006`

---

### Infrastructure

#### PostgreSQL (5432 → 5432)
- **Função:** Banco de Dados Principal
- **Container:** `intellicare-postgres`
- **Image:** `postgres:16-alpine`
- **Databases:**
  - `intellicare_db` (principal)
  - `oswaldo` (Oswaldo)
  - `florence` (Florence)
  - `grahame` (Grahame)
  - etc.

#### Redis (6379 → 6379)
- **Função:** Cache + Pub/Sub + Rate Limiting
- **Container:** `intellicare-redis`
- **Image:** `redis:7-alpine`
- **Maxmemory Policy:** `allkeys-lru`

#### Grafana (3000 → 3000)
- **Função:** Dashboards de Monitoramento
- **Container:** `intellicare-grafana`
- **URL:** `http://localhost:3000`
- **Credenciais:** `admin` / `CHANGE_ME` (configurável)

#### Prometheus (9090 → 9090)
- **Função:** Métricas do Sistema
- **Container:** `intellicare-prometheus`
- **URL:** `http://localhost:9090`
- **Scrape Targets:** Todos os módulos backend

---

## ⚠️ Módulos SEM Porta Dedicada

### Apresentacao
- **Tipo:** Aplicação Desktop (Pygame)
- **Função:** Apresentação Interativa com IA
- **Execução:** `python main.py` (local, não dockerizado)
- **Porta:** N/A (não é serviço web)
- **Localização:** `intellicare-apresentacao/`

---

## 🔧 Padrão de Portas

### Convenção Adotada

**Backend Modules:**
- Porta Externa: `800X` (onde X = 1-13)
- Porta Interna: `8000` (padrão FastAPI/uvicorn)
- **Exceções:**
  - MINERVA/Minerva: `8008:8008`
  - Pierre: `8009:8009`
  - Admin: `8010:8010`
  - Gestor: `8011:8011`

**Razão das Exceções:**
- Alguns módulos foram configurados para rodar na mesma porta interna e externa
- Isso facilita debugging e evita confusão em ambientes de desenvolvimento

---

## 📝 Variáveis de Ambiente

### Arquivo: `.env.full`

```bash
# Backend Modules
FLORENCE_PORT=8001
OSWALDO_PORT=8002
DONABEDIAN_PORT=8003
WANDA_PORT=8004
COMUNICACAO_PORT=8005
GERALDA_PORT=8006
ZILDA_PORT=8007
MINERVA_PORT=8008
PIERRE_PORT=8009
ADMIN_PORT=8010
GESTOR_PORT=8011
GRAHAME_PORT=8012
NISE_PORT=8013

# Frontend
PORTAL_PORT=3001

# Infrastructure
POSTGRES_PORT=5432
REDIS_PORT=6379
GRAFANA_PORT=3000
PROMETHEUS_PORT=9090
```

---

## 🎯 Próximos Passos

1. ✅ **Atualizar toda documentação** para refletir este mapeamento
2. ✅ **Validar portas em staging** antes de deploy
3. ✅ **Configurar firewall** para permitir apenas portas necessárias
4. ✅ **Documentar reverse proxy** (Traefik/Nginx) se aplicável

---

---

## 🔍 Verificação de Portas

### Comando para Verificar Portas em Uso

```bash
# Linux/Mac
netstat -tulpn | grep LISTEN | grep -E ':(8001|8002|8003|8004|8005|8006|8007|8008|8009|8010|8011|8012|8013|3001|5432|6379|3000|9090)'

# Windows (PowerShell)
netstat -ano | findstr LISTENING | findstr "8001 8002 8003 8004 8005 8006 8007 8008 8009 8010 8011 8012 8013 3001 5432 6379 3000 9090"

# Docker - Ver portas dos containers
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

### Verificar Conflitos de Porta

```bash
# Verificar se porta está em uso
lsof -i :8001  # Linux/Mac
netstat -ano | findstr :8001  # Windows

# Matar processo usando porta
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows
```

---

## 🚨 Troubleshooting

### Problema: Porta já em uso

**Sintoma:** Container não inicia com erro "port already allocated"

**Solução:**
```bash
# 1. Identificar processo usando a porta
lsof -i :8001

# 2. Parar container conflitante
docker stop <container_name>

# 3. Ou mudar porta no .env
FLORENCE_PORT=8101  # Usar porta alternativa
```

### Problema: Container não responde na porta

**Sintoma:** `curl http://localhost:8001` retorna erro de conexão

**Diagnóstico:**
```bash
# 1. Verificar se container está rodando
docker ps | grep florence

# 2. Ver logs do container
docker logs intellicare-florence

# 3. Verificar healthcheck
docker inspect intellicare-florence | grep -A 10 Health

# 4. Testar porta interna do container
docker exec intellicare-florence curl http://localhost:8000/api/v1/health
```

### Problema: Conflito de portas entre módulos

**Sintoma:** Dois módulos tentando usar a mesma porta

**Solução:**
1. Verificar `.env.full` para duplicações
2. Atualizar `docker-compose.full.yml`
3. Reiniciar containers afetados

---

## 📊 Diagrama de Arquitetura de Portas

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTELLICARE v2.0.0                       │
│                     Mapeamento de Portas                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
├─────────────────────────────────────────────────────────────────┤
│  Portal (3001)          → React + Vite                          │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND MODULES (API)                        │
├─────────────────────────────────────────────────────────────────┤
│  Florence (8001)        → RAG + Protocolos                      │
│  Oswaldo (8002)         → Análise Clínica                       │
│  Donabedian (8003)      → Qualidade                             │
│  Wanda (8004)           → Orquestrador IA                       │
│  Comunicacao (8005)     → WhatsApp + Email                      │
│  Geralda (8006)         → Gestão                                │
│  Zilda (8007)           → CNES + DATASUS                        │
│  MINERVA/Minerva (8008)     → Extração Docs                         │
│  Pierre (8009)          → Scientific Search                     │
│  Admin (8010)           → Administração                         │
│  Gestor (8011)          → Gestão Módulos                        │
│  Grahame (8012)         → FHIR + CDS Hooks                      │
│  Nise (8013)            → Chatbot + Treinamento                 │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE                             │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL (5432)      → Database                              │
│  Redis (6379)           → Cache + Pub/Sub                       │
│  Prometheus (9090)      → Métricas                              │
│  Grafana (3000)         → Dashboards                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Checklist de Validação

### Antes de Deploy

- [ ] Todas as portas estão documentadas em `.env.full`
- [ ] Não há conflitos de portas entre módulos
- [ ] Firewall configurado para permitir portas necessárias
- [ ] Healthchecks funcionando em todas as portas
- [ ] Documentação atualizada

### Após Deploy

- [ ] Todos os containers iniciaram corretamente
- [ ] Todas as portas respondem ao curl/healthcheck
- [ ] Logs não mostram erros de porta
- [ ] Frontend consegue acessar todos os backends
- [ ] Monitoramento (Prometheus/Grafana) funcionando

---

**Criado por:** Augment Agent
**Data:** 2026-02-26
**Versão:** 2.0.0
**Status:** ✅ **DEFINITIVO**

