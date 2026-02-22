# 📚 IntelliCare - Índice de Documentação

Este arquivo serve como ponto de entrada para toda a documentação do projeto IntelliCare.

---

## 🗂️ Organização da Documentação

A documentação está organizada por assunto na pasta [`docs/`](docs/):

### 📁 Estrutura Principal

| Pasta | Descrição | Link |
|-------|-----------|------|
| **API_OPENAPI** | Catálogo de APIs, levantamentos e plano de unificação OpenAPI | [`docs/API_OPENAPI/`](docs/API_OPENAPI/) |
| **ARQUITETURA_E_DADOS** | Visão geral, estratégias de schema e especificações técnicas | [`docs/ARQUITETURA_E_DADOS/`](docs/ARQUITETURA_E_DADOS/) |
| **PLANOS_E_ESTRATEGIA** | Planos de implementação e estratégias de execução | [`docs/PLANOS_E_ESTRATEGIA/`](docs/PLANOS_E_ESTRATEGIA/) |
| **RELATORIOS_E_ANDAMENTO** | Relatórios de progresso, andamento e retrospectivas | [`docs/RELATORIOS_E_ANDAMENTO/`](docs/RELATORIOS_E_ANDAMENTO/) |
| **GOVERNANCA** | Índices e documentos de governança documental | [`docs/GOVERNANCA/`](docs/GOVERNANCA/) |
| **HISTORICO** | Documentos históricos e análises legadas | [`docs/HISTORICO/`](docs/HISTORICO/) |
| **NORMAS_E_PADROES** | Normas e padrões oficiais de documentação | [`docs/NORMAS_E_PADROES/`](docs/NORMAS_E_PADROES/) |
| **SERVIDORES** | Configurações e guias de deploy de servidores | [`docs/SERVIDORES/`](docs/SERVIDORES/) |

### 📁 Planejamento (Organização Própria)

| Pasta | Descrição | Link |
|-------|-----------|------|
| **PLANNER-CURSOR** | Especificações, desenvolvimento e controle do planejador | [`docs/PLANNER-CURSOR/`](docs/PLANNER-CURSOR/) |
| **PLANNER-ANTIGRAVITY** | Controle geral, diário de bordo e fluxos de trabalho | [`docs/PLANNER-ANTIGRAVITY/`](docs/PLANNER-ANTIGRAVITY/) |

---

## 🚀 Guias Rápidos

### Deploy e Configuração

| Documento | Descrição | Localização |
|-----------|-----------|-------------|
| **Guia de Deploy Geral** | Instruções gerais de deploy (local, staging, produção) | [`GUIA_DEPLOY.md`](GUIA_DEPLOY.md) |
| **Servidor Homologação** | Configuração completa do servidor Contabo | [`docs/SERVIDORES/SERVIDOR_HOMOLOGACAO_CONTABO.md`](docs/SERVIDORES/SERVIDOR_HOMOLOGACAO_CONTABO.md) |
| **Quick Start Homologação** | Deploy rápido em 5 minutos | [`docs/SERVIDORES/SERVIDOR_HOMOLOGACAO_README.md`](docs/SERVIDORES/SERVIDOR_HOMOLOGACAO_README.md) |

### Arquitetura e Dados

| Documento | Descrição | Localização |
|-----------|-----------|-------------|
| **Visão Geral** | Arquitetura LEGO e visão do sistema | [`docs/ARQUITETURA_E_DADOS/20260209-1944_VISAO.md`](docs/ARQUITETURA_E_DADOS/20260209-1944_VISAO.md) |
| **Modularização** | Estratégia de modularização | [`docs/ARQUITETURA_E_DADOS/20260209-1945_MODULARIZACAO.md`](docs/ARQUITETURA_E_DADOS/20260209-1945_MODULARIZACAO.md) |
| **Database Schemas** | Estratégia de schemas PostgreSQL | [`docs/ARQUITETURA_E_DADOS/20260210-0550_ESTRATEGIA_DATABASE_SCHEMAS.md`](docs/ARQUITETURA_E_DADOS/20260210-0550_ESTRATEGIA_DATABASE_SCHEMAS.md) |

### APIs e Integrações

| Documento | Descrição | Localização |
|-----------|-----------|-------------|
| **Catálogo de APIs** | Inventário completo de APIs | [`docs/API_OPENAPI/20260219-0810_API_CATALOG.md`](docs/API_OPENAPI/20260219-0810_API_CATALOG.md) |
| **Plano Unificação OpenAPI** | Estratégia de padronização | [`docs/API_OPENAPI/20260219-0811_PLANO_UNIFICACAO_OPENAPI.md`](docs/API_OPENAPI/20260219-0811_PLANO_UNIFICACAO_OPENAPI.md) |

### Normas e Padrões

| Documento | Descrição | Localização |
|-----------|-----------|-------------|
| **Padrão de Nomenclatura** | Convenções de nomenclatura de documentos | [`docs/NORMAS_E_PADROES/20260221-0714_PADRAO_NOMENCLATURA_DOCUMENTOS.md`](docs/NORMAS_E_PADROES/20260221-0714_PADRAO_NOMENCLATURA_DOCUMENTOS.md) |
| **README Normas** | Índice de normas e padrões | [`docs/NORMAS_E_PADROES/README.md`](docs/NORMAS_E_PADROES/README.md) |

---

## 🔧 Arquivos de Configuração

### Variáveis de Ambiente

| Arquivo | Descrição | Localização |
|---------|-----------|-------------|
| `.env.example` | Template geral com todas as variáveis | [`.env.example`](.env.example) |
| `.env.homologacao` | Configuração para servidor de homologação | [`.env.homologacao`](.env.homologacao) |

### Docker

| Arquivo | Descrição | Localização |
|---------|-----------|-------------|
| `docker-compose.full.yml` | Stack completa (infra + backends + frontend) | [`docker-compose.full.yml`](docker-compose.full.yml) |

### Scripts

| Script | Descrição | Localização |
|--------|-----------|-------------|
| `deploy_homologacao.sh` | Deploy automático para homologação | [`scripts/deploy_homologacao.sh`](scripts/deploy_homologacao.sh) |
| `smoke_tests.sh` | Testes de validação pós-deploy | [`scripts/smoke_tests.sh`](scripts/smoke_tests.sh) |

---

## 📊 Relatórios e Andamento

### Últimos Relatórios

| Data | Documento | Descrição |
|------|-----------|-----------|
| 2026-02-15 | [Retrospectiva Agentes](docs/RELATORIOS_E_ANDAMENTO/20260215-1627_RETROSPECTIVA_AGENTES_INTELLICARE.md) | Retrospectiva completa dos 9 agentes |
| 2026-02-12 | [Resumo Executivo](docs/RELATORIOS_E_ANDAMENTO/20260212-1202_RESUMO_EXECUTIVO_DIA_12FEB.md) | Resumo executivo do dia 12/02 |
| 2026-02-12 | [Fase 2.5 Replicação](docs/RELATORIOS_E_ANDAMENTO/20260212-0800_RESUMO_FASE_2_5_REPLICACAO.md) | Resumo da Fase 2.5 |

---

## 🎯 Por Onde Começar?

### Se você é...

#### 👨‍💻 Desenvolvedor
1. Leia: [`docs/ARQUITETURA_E_DADOS/20260209-1944_VISAO.md`](docs/ARQUITETURA_E_DADOS/20260209-1944_VISAO.md)
2. Configure ambiente: [`GUIA_DEPLOY.md`](GUIA_DEPLOY.md) (seção Deploy Local)
3. Explore APIs: [`docs/API_OPENAPI/20260219-0810_API_CATALOG.md`](docs/API_OPENAPI/20260219-0810_API_CATALOG.md)

#### 🏗️ DevOps / Infraestrutura
1. Leia: [`docs/SERVIDORES/README.md`](docs/SERVIDORES/README.md)
2. Configure servidor: [`docs/SERVIDORES/SERVIDOR_HOMOLOGACAO_CONTABO.md`](docs/SERVIDORES/SERVIDOR_HOMOLOGACAO_CONTABO.md)
3. Execute deploy: [`scripts/deploy_homologacao.sh`](scripts/deploy_homologacao.sh)

#### 📋 Gestor de Projeto
1. Leia: [`docs/PLANNER-CURSOR/VISAO_PLANEJADOR.md`](docs/PLANNER-CURSOR/VISAO_PLANEJADOR.md)
2. Acompanhe: [`docs/RELATORIOS_E_ANDAMENTO/`](docs/RELATORIOS_E_ANDAMENTO/)
3. Planeje: [`docs/PLANOS_E_ESTRATEGIA/`](docs/PLANOS_E_ESTRATEGIA/)

#### 🏛️ Arquiteto de Software
1. Leia: [`docs/ARQUITETURA_E_DADOS/20260209-1945_MODULARIZACAO.md`](docs/ARQUITETURA_E_DADOS/20260209-1945_MODULARIZACAO.md)
2. Entenda schemas: [`docs/ARQUITETURA_E_DADOS/20260210-0550_ESTRATEGIA_DATABASE_SCHEMAS.md`](docs/ARQUITETURA_E_DADOS/20260210-0550_ESTRATEGIA_DATABASE_SCHEMAS.md)
3. Revise APIs: [`docs/API_OPENAPI/20260219-0811_PLANO_UNIFICACAO_OPENAPI.md`](docs/API_OPENAPI/20260219-0811_PLANO_UNIFICACAO_OPENAPI.md)

---

## 🔍 Buscar Documentação

### Por Assunto

- **APIs:** [`docs/API_OPENAPI/`](docs/API_OPENAPI/)
- **Arquitetura:** [`docs/ARQUITETURA_E_DADOS/`](docs/ARQUITETURA_E_DADOS/)
- **Deploy:** [`docs/SERVIDORES/`](docs/SERVIDORES/) + [`GUIA_DEPLOY.md`](GUIA_DEPLOY.md)
- **Normas:** [`docs/NORMAS_E_PADROES/`](docs/NORMAS_E_PADROES/)
- **Planejamento:** [`docs/PLANNER-CURSOR/`](docs/PLANNER-CURSOR/)
- **Progresso:** [`docs/RELATORIOS_E_ANDAMENTO/`](docs/RELATORIOS_E_ANDAMENTO/)

### Por Data

Os documentos seguem o padrão: `YYYYMMDD-HHMM_TITULO.md`

Exemplo: `20260221-0714_PADRAO_NOMENCLATURA_DOCUMENTOS.md`

---

## 📞 Suporte

- **Documentação Geral:** [`docs/README.md`](docs/README.md)
- **Governança:** [`docs/GOVERNANCA/`](docs/GOVERNANCA/)
- **GitHub:** https://github.com/eduardo/intellicare

---

**Última atualização:** 2026-02-21  
**Versão:** 0.1.0-demo

