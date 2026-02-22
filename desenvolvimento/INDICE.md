# 📑 Índice Geral - Projeto IntelliCare

Navegação rápida para toda a documentação e código do projeto.

---

## ⭐ Acesso Rápido

| Documento | Descrição |
|-----------|-----------|
| [ControleVersao.md](./ControleVersao.md) | **Visão consolidada de todas as versões** |
| [HISTORICO-ProjetoIntelliCare](./steps/V1.0-202502031900-HISTORICO-ProjetoIntelliCare.md) | Documento fundacional do projeto |
| [docs/README.md](./docs/README.md) | Guia de especificações |
| [steps/README.md](./steps/README.md) | Guia de acompanhamento |

---

## 🗂️ Estrutura de Navegação

### 📚 Documentação Técnica (`docs/`)

```
docs/
├── README.md ........................... Guia de documentação
│
├── PortalIntellicare/
│   └── README.md ....................... Índice do módulo
│
├── Backend/
│   └── README.md ....................... Índice do módulo
│
├── BrazilianHealthDataAgent/
│   ├── README.md ....................... Índice do módulo
│   ├── V1.1-*-EF-*.md .................. Especificação Funcional
│   ├── V1.1-*-ET-*.md .................. Especificação Técnica
│   ├── V1.1-*-RESUMO-*.md .............. Resumo Executivo
│   ├── API-VALIDATION-CHECKLIST.md ..... Checklist de validação
│   └── CHANGELOG.md .................... Histórico de versões
│
└── EmailManagementSystem/
    ├── README.md ....................... Índice do módulo
    ├── V1.2-*-EF-*.md .................. Especificação Funcional
    ├── V1.2-*-ET-*.md .................. Especificação Técnica
    └── V1.2-*-RESUMO-*.md .............. Resumo Executivo
```

### 📊 Acompanhamento (`steps/`)

```
steps/
├── README.md ........................... Guia de steps
├── V1.0-*-HISTORICO-ProjetoIntelliCare.md  Documento fundacional
│
├── PortalIntellicare/
│   └── V1.0-*-HISTORICO-*.md ........... Histórico de desenvolvimento
│
├── Backend/
│   └── V1-*-PLANO-Backend-Database.md .. Plano de desenvolvimento
│
├── BrazilianHealthDataAgent/
│   └── (aguardando implementação)
│
└── EmailManagementSystem/
    └── (aguardando implementação)
```

---

## 🚀 Acesso Rápido por Módulo

### 🌐 Portal IntelliCare

| Tipo | Link | Descrição |
|------|------|-----------|
| 📁 Código | [`../../PortalIntellicare/`](../PortalIntellicare/) | Código-fonte React |
| 📖 README | [`../../PortalIntellicare/README.md`](../PortalIntellicare/README.md) | Guia do módulo |
| 📄 Docs | [`docs/PortalIntellicare/`](./docs/PortalIntellicare/) | Especificações |
| 📊 Steps | [`steps/PortalIntellicare/`](./steps/PortalIntellicare/) | Histórico |

**Status:** 🟢 Sprint 1 Completo  
**Versão:** 1.0.0

---

### 🔌 Backend API

| Tipo | Link | Descrição |
|------|------|-----------|
| 📁 Código | [`../../backend/`](../backend/) | Código-fonte Node.js |
| 📖 README | [`../../backend/README.md`](../backend/README.md) | Guia do módulo |
| 📄 Docs | [`docs/Backend/`](./docs/Backend/) | Especificações |
| 📊 Steps | [`steps/Backend/`](./steps/Backend/) | Planejamento |

**Status:** 🟢 MVP Funcional
**Versão:** 1.0.0

---

### 🤖 Agentes Inteligentes

| Tipo | Link | Descrição |
|------|------|-----------|
| 📁 Código | [`../../agentes/`](../agentes/) | Código-fonte Python |
| 📖 README | [`../../agentes/README.md`](../agentes/README.md) | Guia do módulo |

**Status:** 🟡 Em Desenvolvimento

#### Brazilian Health Data Agent

| Tipo | Link | Descrição |
|------|------|-----------|
| 📖 README | [`docs/BrazilianHealthDataAgent/README.md`](./docs/BrazilianHealthDataAgent/README.md) | Índice completo |
| 📋 Resumo | [`docs/BrazilianHealthDataAgent/V1.1-*-RESUMO-*.md`](./docs/BrazilianHealthDataAgent/) | Visão geral |
| 📄 EF | [`docs/BrazilianHealthDataAgent/V1.1-*-EF-*.md`](./docs/BrazilianHealthDataAgent/) | Requisitos |
| 🔧 ET | [`docs/BrazilianHealthDataAgent/V1.1-*-ET-*.md`](./docs/BrazilianHealthDataAgent/) | Implementação |
| ✅ Checklist | [`docs/BrazilianHealthDataAgent/API-VALIDATION-CHECKLIST.md`](./docs/BrazilianHealthDataAgent/API-VALIDATION-CHECKLIST.md) | Validação |

**Status:** 🟡 Documentação Completa  
**Versão:** 1.1

---

### 📧 Email Management System

| Tipo | Link | Descrição |
|------|------|-----------|
| 📖 README | [`docs/EmailManagementSystem/README.md`](./docs/EmailManagementSystem/README.md) | Índice completo |
| 📋 Resumo | [`docs/EmailManagementSystem/V1.2-*-RESUMO-*.md`](./docs/EmailManagementSystem/) | Visão geral |
| 📄 EF | [`docs/EmailManagementSystem/V1.2-*-EF-*.md`](./docs/EmailManagementSystem/) | Requisitos |
| 🔧 ET | [`docs/EmailManagementSystem/V1.2-*-ET-*.md`](./docs/EmailManagementSystem/) | Implementação |

**Status:** 🟡 Documentação Completa  
**Versão:** 1.2

---

## 📖 Guias de Leitura

### Para Desenvolvedores

**Novo no projeto?**
1. Leia [`../README.md`](../README.md) - Visão geral do IntelliCare
2. Leia [`docs/README.md`](./docs/README.md) - Entenda a estrutura de docs
3. Escolha um módulo e leia seu README
4. Leia RESUMO → EF → ET do módulo

**Implementando um módulo?**
1. Leia EF para entender requisitos
2. Leia ET para implementação
3. Crie HISTORICO em `steps/[Modulo]/`
4. Atualize status no README do módulo

---

### Para Gestores

**Avaliando o projeto?**
1. Leia [`../README.md`](../README.md) - Visão geral
2. Leia RESUMO de cada módulo
3. Consulte status em [`steps/README.md`](./steps/README.md)

**Acompanhando progresso?**
1. Verifique tabela de status em [`../README.md`](../README.md)
2. Leia HISTORICO em `steps/[Modulo]/`
3. Consulte próximos passos nos READMEs

---

### Para Novos Membros

**Onboarding:**
1. [`../README.md`](../README.md) - Entenda o projeto
2. [`docs/README.md`](./docs/README.md) - Estrutura de documentação
3. [`steps/README.md`](./steps/README.md) - Como acompanhar desenvolvimento
4. README de cada módulo - Detalhes específicos
5. RESUMO de cada módulo - Visão rápida

---

## 🔍 Busca Rápida

### Por Tipo de Documento

| Tipo | Onde Encontrar | Propósito |
|------|---------------|-----------|
| **README** | Raiz de cada módulo | Guia geral do módulo |
| **RESUMO** | `docs/[Modulo]/V*-RESUMO-*.md` | Visão executiva rápida |
| **EF** | `docs/[Modulo]/V*-EF-*.md` | Requisitos funcionais |
| **ET** | `docs/[Modulo]/V*-ET-*.md` | Implementação técnica |
| **HISTORICO** | `steps/[Modulo]/V*-HISTORICO-*.md` | Progresso do desenvolvimento |
| **PLANO** | `steps/[Modulo]/V*-PLANO-*.md` | Planejamento de sprint |
| **ISSUE** | `steps/[Modulo]/V*-ISSUE-*.md` | Problemas e soluções |

---

### Por Status

| Status | Módulos |
|--------|---------|
| 🟢 **Completo** | Portal (Sprint 1), Backend API |
| 🟡 **Em Desenvolvimento** | Brazilian Health Data Agent, Email Management System |
| 🔵 **Planejado** | Portal (Sprint 2+), Novos Agentes |

---

## 📊 Métricas do Projeto

### Documentação

- **Total de Módulos:** 4
- **Documentos EF:** 3
- **Documentos ET:** 3
- **Documentos RESUMO:** 2
- **READMEs:** 8+

### Código

- **Linhas de Código (estimado):**
  - Portal: ~15.000 linhas (TypeScript/React)
  - Backend: ~3.000 linhas (TypeScript/Node.js)
  - Agentes: ~2.000 linhas (Python)

---

## 🔗 Links Úteis

### Documentação Externa

- [React 19 Docs](https://react.dev/)
- [TypeScript Docs](https://www.typescriptlang.org/docs/)
- [Fastify Docs](https://fastify.dev/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Celery Docs](https://docs.celeryq.dev/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)

### Ferramentas

- [Prisma Studio](https://www.prisma.io/studio) - GUI do banco de dados
- [Flower](https://flower.readthedocs.io/) - Monitoramento Celery
- [Vite](https://vitejs.dev/) - Build tool

---

**Última atualização:** 2025-02-03  
**Mantido por:** Equipe IntelliCare

