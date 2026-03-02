# V2.0.1 - ADMIN: Módulo de Administração Multi-Tenant

> **Versão:** 2.0.1 | **Data Início:** 2026-02-28 | **Status:** 📋 Planejamento
> **Prioridade:** P0 (Crítica) | **Complexidade:** Alta | **Estimativa:** 30-40 dias

---

## 1. Objetivo

Implementar o módulo **intellicare-admin**, peça fundamental da arquitetura multi-tenant do IntelliCare. Este módulo permitirá:

✅ **Gestão de Empresas (Tenants)**: Cadastro, configuração e provisionamento de organizações
✅ **Controle de Planos e Módulos**: Gerenciar quais módulos cada tenant pode acessar
✅ **Billing e Uso**: Acompanhamento de uso mensal e geração de cobranças
✅ **Administração Global**: Dashboard de monitoramento, auditoria e suporte
✅ **Provisionamento Automatizado**: Criação automática de schemas, Keycloak groups e seed data

---

## 2. Contexto Multi-Tenant

### 2.1 Arquitetura de 2 Camadas

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA PLATAFORMA                        │
│  (Schema: default/platform)                                │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ intellicare-admin│  │ intellicare-portal│               │
│  │  Gestão SaaS     │  │  Login/Routing   │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                    Provisiona & Controla
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      CAMADA TENANT                          │
│  (Schema: tenant_{id} por organização)                     │
│                                                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│  │Gestor│ │Zilda │ │Oswaldo│ │Florence│ │Donabe│ │Wanda │   │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Classificação dos Módulos

| Camada | Módulo | Schema | Responsabilidade |
|--------|--------|--------|------------------|
| **Plataforma** | `intellicare-admin` 🆕 | `default/platform` | **Este módulo** - Gestão SaaS |
| **Plataforma** | `intellicare-portal` | `default` | Login, roteamento JWT → tenant |
| **Tenant** | `intellicare-gestor` | `tenant_{id}` | Gestão de usuários do tenant |
| **Tenant** | `intellicare-zilda` | `tenant_{id}` | CNES, estabelecimentos |
| **Tenant** | `intellicare-oswaldo` | `tenant_{id}` | Períis epidemiológicos |
| **Tenant** | `intellicare-florence` | `tenant_{id}` | Indicadores assistenciais |

---

## 3. Escopo da V2.0.1

### 3.1 O que está INCLUIDO ✅

| Funcionalidade | Descrição |
|----------------|-----------|
| **Cadastro de Tenants** | CRUD completo de empresas/organizações |
| **Provisionamento Automático** | Criar schema DB + Keycloak group + usuário admin |
| **Planos e Módulos** | Gerenciar planos (trial, básico, profissional, enterprise) |
| **Ativação de Módulos** | Controlar quais módulos cada tenant pode acessar |
| **Billing Básico** | Registro de uso mensal e status de pagamento |
| **Monitoramento** | Dashboard com métricas globais e por tenant |
| **Auditoria** | Log de todas as ações administrativas |
| **Impersonação** | Suporte pode acessar contexto de tenant para diagnóstico |

### 3.2 O que NÃO está incluído ❌

| Funcionalidade | Motivo | Versão Futura |
|----------------|--------|---------------|
| Integração Gateway Pagamento | Depende de escolha do gateway | V2.0.2 |
| Relatórios Financeiros Completos | Requer dados reais de uso | V2.0.2 |
| Auto-scaling de Infra | Requer orquestrador Kubernetes | V2.1.x |
| Marketplace de Apps | Requer ecossistema de plugins | V2.2.x |

---

## 4. Fases de Implementação

A V2.0.1 está dividida em **4 fases sequenciais** para permitir entregas incrementais e validação contínua:

| Fase | Nome | Duração | Entregável | Status |
|------|------|---------|------------|--------|
| **Fase 0** | Infraestrutura Multi-Tenant | 5 dias | TenantContext, schemas base | 🔵 Planejado |
| **Fase 1** | Módulo Admin - Core | 12 dias | CRUD Tenants + Provisioning | 🔵 Planejado |
| **Fase 2** | Planos e Billing | 8 dias | Gestão de planos + controle módulos | 🔵 Planejado |
| **Fase 3** | Monitoramento e Auditoria | 5 dias | Dashboard + logs globais | 🔵 Planejado |

**Total estimado: 30 dias**

> [!NOTE]
> As fases podem ser executadas em paralelo com outras trilhas (F4 - Módulos Clínicos, F5 - Tooling) após conclusão da Fase 0.

---

## 5. Dependências

### 5.1 Dependências Técnicas

| Componente | Versão Mínima | Status |
|------------|---------------|--------|
| **PostgreSQL** | 15+ | ✅ Disponível |
| **Keycloak** | 24+ | ✅ Disponível |
| **intellicare-core** | Latest | ✅ Disponível |
| **intellicare-auth** | Latest | ✅ Disponível |
| **Python** | 3.11+ | ✅ Disponível |

### 5.2 Dependências Funcionais

| Item | Status | Observações |
|------|--------|-------------|
| F0 - TenantContext | 🔶 Pendente | Fase 0 da multi-tenancy |
| Schema `platform` | 🔶 Pendente | Será criado na Fase 0 |
| Keycloak Admin API | 🔶 Pendente | Configuração necessária |

---

## 6. Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Falha no provisionamento de schema | Alto | Média | Rollback automatizado + retry |
| Keycloak Admin API mudar versão | Alto | Baixa | Usar cliente Python estável |
| Performance em schema único | Médio | Baixa | Índices otimizados + partitioning |
| Inconsistência billing vs uso real | Médio | Média | Reconciliação diária automatizada |

---

## 7. Critérios de Aceite

### 7.1 Critérios Técnicos

- [ ] Schema `platform` criado e testado
- [ ] API REST completa documentada em OpenAPI
- [ ] Testes unitários com ≥80% de cobertura
- [ ] Testes de integração com Keycloak
- [ ] Migrations idempotentes
- [ ] Logs estruturados em JSON

### 7.2 Critérios Funcionais

- [ ] Super-admin pode criar/editar tenants
- [ ] Provisionamento cria schema + KC + usuário
- [ ] Planos seed inseridos (trial, básico, profissional, enterprise)
- [ ] Ativação/desativação de módulos funciona
- [ ] Billing registra uso mensal
- [ ] Dashboard mostra métricas globais
- [ ] Auditoria registra todas as ações administrativas

### 7.3 Critérios de Performance

- [ ] API responde em <200ms (P95)
- [ ] Provisionamento completo em <30s
- [ ] Dashboard carrega em <2s
- [ ] Suporta 100 tenants simultâneos sem degradação

---

## 8. Entregáveis Finais

| Artefato | Formato | Localização |
|----------|---------|-------------|
| Código Fonte | Python/FastAPI | `intellicare-admin/` |
| Migrations | Alembic | `intellicare-admin/migrations/` |
| Documentação API | OpenAPI 3.0 | `/api/v1/docs` |
| Testes | Pytest | `intellicare-admin/tests/` |
| README | Markdown | `intellicare-admin/README.md` |
| Dockerfile | Docker | `intellicare-admin/Dockerfile` |

---

## 9. Próximos Passos

1. ✅ Validar este planejamento com stakeholder
2. 🔵 Aprovar início da **Fase 0** - Infraestrutura Multi-Tenant
3. 🔵 Atribuir DEV para implementação
4. 🔵 Configurar ambiente de desenvolvimento
5. 🔵 Iniciar implementação seguindo especificações funcionais

---

## 10. Referências

- [ANALISE_MULTI_TENANCY.md](../PLANNER-ANTIGRAVITY/MULTI_TENANCY/ANALISE_MULTI_TENANCY.md)
- [PADRAO_NOMENCLATURA_DOCUMENTOS.md](../NORMAS_E_PADROES/20260221-0714_PADRAO_NOMENCLATURA_DOCUMENTOS.md)
- Especificações F0-F5 em `PLANNER-ANTIGRAVITY/MULTI_TENANCY/DESENVOLVIMENTO/`

---

**Document Owner:** IntelliCare Architecture Team
**Aprovado por:** ___________
**Data Aprovação:** ___________
