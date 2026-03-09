# 🏥 IntelliCare - Plataforma Modular de Saúde

**Versão:** 2.0.0  
**Data:** 2026-02-26  
**Status:** ✅ **Produção**

---

## 📋 Visão Geral

IntelliCare é uma plataforma modular de saúde construída com microserviços Python FastAPI + React Portal, usando HL7 FHIR R4 como formato de intercâmbio de dados.

---

## 🏗️ Arquitetura

### Módulos Backend (13 serviços)

| Porta | Módulo | Agente | Função | Mapeamento |
|-------|--------|--------|--------|------------|
| **8001** | Florence | FLORENCE | RAG + Protocolos Clínicos | 8001:8000 |
| **8002** | Oswaldo | OSWALDO | Análise Clínica + FHIR | 8002:8000 |
| **8003** | Donabedian | DONABEDIAN | Qualidade + Indicadores | 8003:8000 |
| **8004** | Wanda | WANDA | **Orquestrador IA** | 8004:8000 |
| **8005** | Comunicacao | — | WhatsApp + Email + SMS | 8005:8000 |
| **8006** | Geralda | GERALDA | Gestão + Administrativo | 8006:8000 |
| **8007** | Zilda | ZILDA | CNES + DATASUS | 8007:8000 |
| **8008** | MINERVA/Minerva | MINERVA | Extração Documentos | 8008:8008 |
| **8009** | Pierre | PIERRE | Scientific Search | 8009:8009 |
| **8010** | Admin | — | Administração Sistema | 8010:8010 |
| **8011** | Gestor | — | Gestão Módulos Clínicos | 8011:8011 |
| **8012** | Grahame | GRAHAME | FHIR R4 + CDS Hooks + HL7v2 + CCDA + Excalidraw | 8012:8000 |
| **8013** | Nise | NISE | Chatbot + Treinamento | 8013:8000 |
| **8014** | Bridge | — | Integrações Externas / Gateway | 8014:8000 |

### Frontend

| Porta | Módulo | Tecnologia | Mapeamento |
|-------|--------|------------|------------|
| **3001** | Portal | React 19 + Vite 7 | 3001:80 |

### Infraestrutura

| Porta | Serviço | Função | Mapeamento |
|-------|---------|--------|------------|
| **5432** | PostgreSQL | Database Principal | 5432:5432 |
| **6379** | Redis | Cache + Pub/Sub | 6379:6379 |
| **3000** | Grafana | Dashboards | 3000:3000 |
| **9090** | Prometheus | Métricas | 9090:9090 |

**Documentação Completa:** [docs/INFRAESTRUTURA/MAPEAMENTO_PORTAS_COMPLETO.md](docs/INFRAESTRUTURA/MAPEAMENTO_PORTAS_COMPLETO.md)

---

## 🚀 Quick Start

### 1. Pré-requisitos

- Docker 24+ e Docker Compose 2.20+
- Python 3.11+
- Node.js 20+ (para frontend)
- Git

### 2. Clonar Repositório

```bash
git clone https://github.com/seu-usuario/intellicare.git
cd intellicare
```

### 3. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas configurações
nano .env
```

### 4. Iniciar Infraestrutura

```bash
# Subir PostgreSQL + Redis + Prometheus + Grafana
docker compose up -d
```

### 5. Iniciar Todos os Serviços

```bash
# Subir todos os 14 backends + portal
docker compose -f docker-compose.full.yml up -d
```

### 6. Verificar Saúde dos Serviços

```bash
# Executar smoke tests
python scripts/smoke_tests.py

# Ou manualmente
curl http://localhost:8001/api/v1/health  # Florence
curl http://localhost:8002/api/v1/health  # Oswaldo
curl http://localhost:8012/api/v1/health  # Grahame
# ... etc
```

### 7. Acessar Portal

```
http://localhost:3001
```

---

## 📚 Documentação

### Principais Documentos

- **[CLAUDE.md](CLAUDE.md)** - Guia completo para desenvolvedores
- **[MAPEAMENTO_PORTAS_COMPLETO.md](docs/INFRAESTRUTURA/MAPEAMENTO_PORTAS_COMPLETO.md)** - Mapeamento definitivo de portas
- **[GUIA_MIGRACAO_PORTAS.md](docs/INFRAESTRUTURA/GUIA_MIGRACAO_PORTAS.md)** - Guia de migração de portas
- **[GUIA_DEPLOY.md](GUIA_DEPLOY.md)** - Guia de deploy em produção

### Documentação por Módulo

Cada módulo tem seu próprio README:
- [intellicare-florence/README.md](intellicare-florence/README.md)
- [intellicare-oswaldo/README.md](intellicare-oswaldo/README.md)
- [intellicare-grahame/README.md](intellicare-grahame/README.md)
- ... etc

---

## 🧪 Testes

### Executar Todos os Testes

```bash
# Smoke tests (verifica se todos os serviços estão up)
python scripts/smoke_tests.py

# Testes de um módulo específico
cd intellicare-oswaldo
make test

# Testes com cobertura
make coverage
```

---

## 🔧 Desenvolvimento

### Executar Módulo Localmente

```bash
# Exemplo: Oswaldo
cd intellicare-oswaldo

# Instalar dependências
make install-dev

# Executar API
python run_api_8002.py

# Ou com uvicorn
uvicorn oswaldo.api.app:app --reload --port 8002
```

### Frontend

```bash
cd intellicare-portal/frontend

# Instalar dependências
npm install

# Dev server
npm run dev  # http://localhost:5173

# Build
npm run build
```

---

## 📊 Monitoramento

- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (admin/CHANGE_ME)
- **Healthchecks:** `http://localhost:800X/api/v1/health`

---

## 🔐 Segurança

- **Keycloak:** Autenticação SSO + SMART-on-FHIR 2.0
- **LGPD:** Conformidade completa (módulo Comunicacao)
- **Hardening:** Imagens Docker distroless, non-root
- **Image Signing:** Cosign para assinatura de imagens

---

## 🌐 Interoperabilidade

- **FHIR R4:** Padrão HL7 FHIR R4
- **HL7v2:** Suporte ADT, ORU, ORM (módulo Grahame)
- **CCDA:** Import de documentos CCDA (módulo Grahame)
- **CDS Hooks 2.0:** Suporte completo (módulo Grahame)
- **Terminology:** $lookup, $expand, $validate, $translate

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Add nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## 📄 Licença

Proprietary - IntelliCare © 2026

---

## 📞 Suporte

- **Documentação:** [docs/](docs/)
- **Issues:** GitHub Issues
- **Email:** suporte@intellicare.com.br

---

**Desenvolvido com ❤️ pela equipe IntelliCare**

