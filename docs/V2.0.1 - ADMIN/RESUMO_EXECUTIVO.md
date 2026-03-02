# V2.0.1 - ADMIN: Resumo Executivo do Planejamento

> **Status:** 📋 Planejamento Completo | **Data:** 2026-02-28
> **Próximo Passo:** Validar com stakeholder e iniciar Fase 0

---

## 📋 Visão Geral

**Objetivo:** Implementar o módulo **intellicare-admin**, fundação da arquitetura multi-tenant do IntelliCare.

**Importância:** Sem este módulo, não é possível ter múltiplas organizações (tenants) usando a plataforma.

---

## 🎯 O Que Será Entregue

### Funcionalidades Principais

| Funcionalidade | Descrição | Prioridade |
|----------------|-----------|------------|
| **Cadastro de Tenants** | CRUD de empresas/hospitais | P0 |
| **Provisionamento Automático** | Criar schema DB + Keycloak + admin user | P0 |
| **Planos e Módulos** | Controlar quais módulos cada tenant acessa | P0 |
| **Monitoramento** | Dashboard com métricas globais | P1 |
| **Auditoria** | Log de todas as ações administrativas | P1 |
| **Impersonação** | Suporte pode acessar contexto de tenant | P2 |

### Planos Disponíveis

| Plano | Preço | Usuários | SMS/mês | Módulos |
|-------|-------|----------|---------|---------|
| **Trial** | Grátis | 5 | 100 | Zilda, Florence |
| **Básico** | R$ 497 | 20 | 500 | + Oswaldo, Geralda |
| **Profissional** | R$ 1.497 | 100 | 2.000 | + Donabedian, Comunicação, Grahame |
| **Enterprise** | R$ 2.997 | Ilimitado | 10.000 | + Wanda IA |

---

## 📅 Estrutura em 4 Fases

| Fase | Nome | Duração | Status | Entregável |
|------|------|---------|--------|-----------|
| **Fase 0** | Infraestrutura Multi-Tenant | 5 dias | 🔵 Planejado | TenantContext, schemas base |
| **Fase 1** | Módulo Admin - Core | 12 dias | 🔵 Planejado | CRUD Tenants + Provisioning |
| **Fase 2** | Planos e Billing | 8 dias | 🔵 Planejado | Gestão planos + controle módulos |
| **Fase 3** | Monitoramento e Auditoria | 5 dias | 🔵 Planejado | Dashboard + logs globais |

**Total Estimado:** 30 dias

---

## 🏗️ Arquitetura Multi-Tenant

### Duas Camadas de Governança

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
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │
│  │Gestor│ │Zilda │ │Oswaldo│ │Florence│ │Donabe│            │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Documentos Criados

### V2.0.1 - ADMIN/

| Arquivo | Descrição | Status |
|---------|-----------|--------|
| `README.md` | Visão geral da versão | ✅ Criado |
| `FASE1_CORE/20260228-0930_ESPECIFICACAO_FUNCIONAL.md` | Requisitos detalhados da Fase 1 | ✅ Criado |
| `FASE1_CORE/20260228-0930_PLANO_IMPLEMENTACAO.md` | Tarefas técnicas da Fase 1 | ✅ Criado |

### A Criar (Validação aprovada)

- [ ] `FASE0_TENANT_CONTEXT/` - Infraestrutura base
- [ ] `FASE2_PLANOS_BILLING/` - Planos e controle de módulos
- [ ] `FASE3_MONITORAMENTO/` - Dashboard e auditoria

---

## ✅ Critérios de Aceite

### Técnicos
- [ ] Schema `platform` criado e testado
- [ ] API REST documentada em OpenAPI
- [ ] Testes com ≥80% de cobertura
- [ ] Provisionamento <30s

### Funcionais
- [ ] Criar tenant funciona
- [ ] Provisionamento cria tudo automaticamente
- [ ] Planos seed inseridos
- [ ] Ativação/desativação de módulos funciona
- [ ] Monitoramento registra métricas

---

## 🚀 Próximos Passos

1. **Validação** 👈 Você aprova este planejamento?
2. **Atribuir DEV** - Qual desenvolvedor vai implementar?
3. **Iniciar Fase 0** - Criar infraestrutura base multi-tenant
4. **Configurar ambiente** - Setup de desenvolvimento
5. **Kickoff Fase 1** - Iniciar implementação do módulo admin

---

## 📊 Estimativa de Esforço

| Fase | Dias | DEV(s) |
|------|------|---------|
| Fase 0 - TenantContext | 5 | 1 DEV |
| Fase 1 - Admin Core | 12 | 1 DEV |
| Fase 2 - Planos/Billing | 8 | 1 DEV |
| Fase 3 - Monitoring | 5 | 1 DEV |
| **TOTAL** | **30 dias** | **1-2 DEV(s)** |

> Nota: Fases podem rodar em paralelo com outras trilhas após Fase 0.

---

## ⚠️ Riscos Identificados

| Risco | Impacto | Plano de Mitigação |
|-------|---------|-------------------|
| Falha no provisionamento | Alto | Rollback automatizado + retry |
| Keycloak mudar API | Alto | Usar cliente Python estável |
| Performance schema único | Médio | Índices otimizados |
| Inconsistência billing | Médio | Reconciliação diária |

---

## 🎯 Sucesso!

Após implementação da V2.0.1:

✅ Plataforma pronta para ter múltiplos tenants
✅ Operadores podem gerenciar empresas via interface admin
✅ Provisionamento 100% automatizado
✅ Base sólida para escalar para centenas de organizações
✅ Próximo passo: F4 - Adaptar módulos clínicos para multi-tenant

---

**Aprovado por:** ___________
**Data:** ___________
**Assinatura:** ___________
