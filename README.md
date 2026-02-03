# 🏥 IntelliCare - Plataforma de Agentes Inteligentes em Saúde Pública

Plataforma completa de **agentes inteligentes baseados em IA** para análise, gestão e otimização de dados de saúde pública no Brasil.

---

## 🎯 Visão Geral

O **IntelliCare** é uma plataforma integrada que combina:
- 🤖 **Agentes Inteligentes** - Análise automatizada de dados de saúde
- 🌐 **Portal Institucional** - Interface web moderna e responsiva
- 🔌 **Backend API** - Gerenciamento de solicitações e integração
- 📧 **Sistema de Emails** - Comunicação profissional e automatizada

---

## 📂 Estrutura do Projeto

```
INTELLICAREREPO/
├── PortalIntellicare/          # Frontend React + TypeScript
├── backend/                    # Backend Node.js + Fastify
├── agentes/                    # Agentes inteligentes Python
├── desenvolvimento/            # Documentação e acompanhamento
│   ├── docs/                   # Especificações técnicas
│   │   ├── README.md
│   │   ├── PortalIntellicare/
│   │   ├── BrazilianHealthDataAgent/
│   │   ├── EmailManagementSystem/
│   │   └── Backend/
│   └── steps/                  # Histórico de desenvolvimento
│       ├── README.md
│       ├── PortalIntellicare/
│       ├── BrazilianHealthDataAgent/
│       ├── EmailManagementSystem/
│       └── Backend/
└── README.md (este arquivo)
```

---

## 🚀 Módulos do Projeto

### 1. 🌐 Portal IntelliCare
**Tecnologia:** React 19 + TypeScript + Vite 7 + Tailwind CSS 4  
**Status:** 🟢 Sprint 1 Completo  
**Versão:** 1.0.0

**Descrição:**  
Portal institucional moderno e responsivo para apresentação da plataforma IntelliCare.

**Recursos:**
- ✅ Home page com hero section e apresentação
- ✅ Catálogo de agentes inteligentes
- ✅ Dashboards públicos
- ✅ Formulários de solicitação de acesso
- ✅ Sistema de acompanhamento de protocolos
- ✅ Design system completo

**Documentação:** [`PortalIntellicare/README.md`](./PortalIntellicare/README.md)

---

### 2. 🔌 Backend API
**Tecnologia:** Node.js 20 + TypeScript + Fastify + Prisma + PostgreSQL  
**Status:** 🟢 MVP Funcional  
**Versão:** 1.0.0

**Descrição:**  
API REST para gerenciamento de solicitações de acesso e integração com agentes.

**Recursos:**
- ✅ CRUD de solicitações (Secretarias e Unidades)
- ✅ Validação de email com tokens
- ✅ Logs e auditoria completa
- ✅ Geração de protocolos únicos
- ✅ Templates de email

**Documentação:** [`backend/README.md`](./backend/README.md)

---

### 3. 🤖 Agentes Inteligentes
**Tecnologia:** Python + LangGraph + LangChain + Agentc  
**Status:** 🟡 Em Desenvolvimento  
**Versão:** Variável por agente

**Descrição:**  
Coleção de agentes especializados para análise de dados de saúde pública.

**Agentes Disponíveis:**
- 🟡 **Brazilian Health Data Agent** (v1.1) - Integração com APIs do MS
- 🟢 **Email Graph Agent** (v1.0) - Gerenciamento de emails (Microsoft)
- 🟢 **Gmail Agent** (v1.0) - Gerenciamento de emails (Google)

**Documentação:** [`agentes/README.md`](./agentes/README.md)

---

### 4. 📧 Email Management System
**Tecnologia:** Python + FastAPI + Celery + Redis + PostgreSQL  
**Status:** 🟡 Documentação Completa  
**Versão:** 1.2

**Descrição:**  
Sistema profissional de gerenciamento de emails com filas assíncronas.

**Recursos:**
- ✅ Envio assíncrono (Celery + Redis)
- ✅ Filas por prioridade (URGENT, NORMAL, LOW)
- ✅ Múltiplos provedores (SMTP, Mailgun, SendGrid)
- ✅ Templates Jinja2 responsivos
- ✅ Logs e auditoria completa
- ✅ Monitoramento (Flower Dashboard)

**Documentação:** [`desenvolvimento/docs/EmailManagementSystem/`](./desenvolvimento/docs/EmailManagementSystem/)

---

## 📚 Documentação

### Estrutura de Documentação

Toda documentação segue padrão versionado em `desenvolvimento/`:

```
desenvolvimento/
├── docs/                       # Especificações técnicas
│   ├── README.md              # Guia de documentação
│   └── [Modulo]/
│       ├── README.md          # Índice do módulo
│       ├── V{x}.{y}-*-EF-*.md    # Especificação Funcional
│       ├── V{x}.{y}-*-ET-*.md    # Especificação Técnica
│       └── V{x}.{y}-*-RESUMO-*.md # Resumo Executivo
│
└── steps/                      # Acompanhamento de desenvolvimento
    ├── README.md              # Guia de steps
    └── [Modulo]/
        ├── V{x}-*-HISTORICO-*.md # Histórico completo
        ├── V{x}-*-PLANO-*.md     # Plano de sprint
        └── V{x}-*-ISSUE-*.md     # Problemas e soluções
```

### Padrão de Nomenclatura

```
V{versão}-{AAAAMMDDHHNN}-{tipo}-{NomeModulo}.md
```

**Exemplo:**
```
V1.2-202502031800-EF-EmailManagementSystem.md
```

**Leia mais:**
- [`desenvolvimento/docs/README.md`](./desenvolvimento/docs/README.md)
- [`desenvolvimento/steps/README.md`](./desenvolvimento/steps/README.md)

---

## 🛠️ Stack Tecnológica

### Frontend
- **React 19** - Biblioteca UI
- **TypeScript** - Tipagem estática
- **Vite 7** - Build tool
- **Tailwind CSS 4** - Framework CSS
- **React Router 7** - Roteamento
- **Framer Motion** - Animações
- **Recharts** - Gráficos

### Backend
- **Node.js 20** - Runtime JavaScript
- **TypeScript** - Tipagem estática
- **Fastify** - Framework web
- **Prisma** - ORM
- **PostgreSQL** - Banco de dados
- **Zod** - Validação

### Agentes & Email
- **Python 3.11+** - Linguagem
- **FastAPI** - API assíncrona
- **Celery** - Filas de tarefas
- **Redis** - Broker e cache
- **LangGraph** - Orquestração de agentes
- **Jinja2** - Templates

### Infraestrutura
- **Docker** - Containerização
- **PostgreSQL** - Banco de dados
- **Redis** - Cache e filas
- **Nginx** - Reverse proxy (produção)

---

## 🚀 Quick Start

### Pré-requisitos
- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- pnpm (gerenciador de pacotes)

### 1. Portal IntelliCare

```bash
cd PortalIntellicare
pnpm install
pnpm dev
# Acesse: http://localhost:3000
```

### 2. Backend API

```bash
cd backend
pnpm install
cp .env.example .env
# Editar .env com credenciais
pnpm prisma migrate dev
pnpm dev
# API: http://localhost:3000/api
```

### 3. Agentes (futuro)

```bash
cd agentes
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Configurar e executar agentes
```

---

## 📊 Status do Projeto

| Módulo | Status | Versão | Última Atualização |
|--------|--------|--------|-------------------|
| Portal IntelliCare | 🟢 Sprint 1 Completo | 1.0.0 | 2025-02-01 |
| Backend API | 🟢 MVP Funcional | 1.0.0 | 2025-01-30 |
| Brazilian Health Data Agent | 🟡 Docs Completa | 1.1 | 2025-02-02 |
| Email Management System | 🟡 Docs Completa | 1.2 | 2025-02-03 |
| Email Graph Agent | 🟢 Funcional | 1.0 | 2025-01-15 |
| Gmail Agent | 🟢 Funcional | 1.0 | 2025-01-15 |

**Legenda:**
- 🟢 Completo/Funcional
- 🟡 Em Desenvolvimento
- 🔵 Planejado
- 🔴 Bloqueado

---

## 🎯 Roadmap

### Q1 2025 (Jan-Mar)
- [x] Portal IntelliCare - Sprint 1 (Home)
- [x] Backend API - MVP
- [x] Documentação Email Management System
- [ ] Portal IntelliCare - Sprint 2 (Agentes)
- [ ] Implementar Brazilian Health Data Agent
- [ ] Implementar Email Management System

### Q2 2025 (Abr-Jun)
- [ ] Portal IntelliCare - Sprint 3 (Dashboards)
- [ ] Painel Administrativo
- [ ] Novos agentes de análise
- [ ] Integração completa dos sistemas

### Q3-Q4 2025 (Jul-Dez)
- [ ] Sistema de recomendações
- [ ] Analytics avançado
- [ ] Mobile app
- [ ] Expansão de agentes

---

## 👥 Equipe

**Desenvolvido pela equipe IntelliCare**

---

## 📝 Licença

Proprietary - © 2025 IntelliCare

---

## 📞 Contato

- **Email:** desenvolvimento@intellicare.com.br
- **Documentação:** Ver `desenvolvimento/docs/`
- **Issues:** Ver `desenvolvimento/steps/`

---

**Última atualização:** 2025-02-03

