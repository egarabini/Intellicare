# FASE2_ADMIN - Módulo de Administração da Plataforma

**Status**: 🟡 Em Planejamento
**Data Início**: 2026-03-02
**Prioridade**: 🚨 ALTA
**Responsável**: IntelliCare Team

---

## 📋 Visão Geral

A **FASE2_ADMIN** implementa o módulo **intellicare-admin**, componente crítico da arquitetura multi-tenant da plataforma IntelliCare. Este módulo permite:

- ✅ **Gestão de Tenants**: Cadastro, configuração e provisionamento de organizações
- ✅ **Controle de Acesso**: Apenas usuários com role **PLATFORM_ADMIN** podem acessar
- ✅ **Planos e Módulos**: Gerenciar quais módulos cada tenant pode acessar
- ✅ **Billing**: Acompanhamento de uso mensal e geração de cobranças
- ✅ **Monitoramento**: Dashboard global com métricas da plataforma
- ✅ **Auditoria**: Log completo de ações administrativas
- ✅ **Suporte**: Impersonação de tenants para diagnóstico

### Arquitetura de Segurança

```
┌────────────────────────────────────────────────────────────┐
│  CAMADA PLATAFORMA (Schema: platform)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  intellicare-admin (PORT 8010)                      │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ 🔒 PROTEGIDO - PLATFORM_ADMIN ONLY             │  │  │
│  │  │ - POST /api/v1/admin/tenants                  │  │  │
│  │  │ - GET /api/v1/admin/dashboard                 │  │  │
│  │  │ - POST /api/v1/admin/support/impersonate      │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

---

## 📁 Documentos da Fase

### Especificações

| Documento | Descrição | Status |
|-----------|-----------|--------|
| [20260302-1400_ESPECIFICACAO_FUNCIONAL.md](./20260302-1400_ESPECIFICACAO_FUNCIONAL.md) | Requisitos funcionais, casos de uso, atores | 🟢 Completo |
| [20260302-1405_ESPECIFICACAO_TECNICA.md](./20260302-1405_ESPECIFICACAO_TECNICA.md) | Stack técnico, arquitetura, API design | 🟢 Completo |
| [20260302-1410_PLANO_IMPLEMENTACAO.md](./20260302-1410_PLANO_IMPLEMENTACAO.md) | Cronograma, fases, recursos, riscos | 🟢 Completo |
| [PASSOS_IMPLEMENTACAO.md](./PASSOS_IMPLEMENTACAO.md) | Checklist passo a passo | 🟢 Completo |

---

## 🎯 Objetivos da Fase

### Objetivos Principais

1. **Implementar API REST** para administração da plataforma
2. **Garantir acesso exclusivo** a usuários PLATFORM_ADMIN
3. **Criar sistema de provisionamento** automático de tenants
4. **Estabelecer controle de planos** e billing básico
5. **Implementar auditoria completa** de ações administrativas

### Critérios de Sucesso

- [ ] API REST completa documentada em OpenAPI
- [ ] Apenas PLATFORM_ADMIN pode acessar endpoints
- [ ] Provisionamento cria schema + Keycloak + usuário em <30s
- [ ] Planos podem ser gerenciados (CRUD)
- [ ] Billing registra uso mensal
- [ ] Dashboard mostra métricas globais
- [ ] Auditoria registra todas as ações
- [ ] PLATFORM_SUPPORT pode impersonar tenants
- [ ] Testes com ≥80% de cobertura
- [ ] Deploy em staging funcionando

---

## 📅 Cronograma

| Fase | Nome | Duração | Status |
|------|------|---------|--------|
| Fase 0 | Pré-Implementação | 2 dias | 🔵 Planejado |
| Fase 1 | Core - CRUD Tenants | 5 dias | 🔵 Planejado |
| Fase 2 | Autenticação e Segurança | 3 dias | 🔵 Planejado |
| Fase 3 | Provisionamento | 5 dias | 🔵 Planejado |
| Fase 4 | Planos e Módulos | 3 dias | 🔵 Planejado |
| Fase 5 | Billing Básico | 4 dias | 🔵 Planejado |
| Fase 6 | Monitoramento | 3 dias | 🔵 Planejado |
| Fase 7 | Auditoria | 3 dias | 🔵 Planejado |
| Fase 8 | Suporte - Impersonação | 2 dias | 🔵 Planejado |
| Fase 9 | Testes E2E e Documentação | 3 dias | 🔵 Planejado |

**Total**: 33 dias úteis (~7 semanas)

---

## 🔗 Dependências

### Dependências Técnicas

| Componente | Versão Mínima | Status |
|------------|---------------|--------|
| PostgreSQL | 15+ | ✅ Disponível |
| Keycloak | 24+ | ✅ Disponível (FASE0_KEYCLOAK) |
| intellicare-core | Latest | ✅ Disponível (FASE1_CORE) |
| intellicare-auth | Latest | ✅ Disponível (FASE0_KEYCLOAK) |
| Python | 3.11+ | ✅ Disponível |
| Redis | 7+ | ✅ Disponível |

### Dependências Funcionais

| Item | Status | Observações |
|------|--------|-------------|
| Role PLATFORM_ADMIN | ✅ | Definido no realm bemcuidar |
| Role PLATFORM_SUPPORT | ✅ | Definido no realm bemcuidar |
| Schema platform | 🔶 | Será criado na Fase 0 |
| Client intellicare-admin | 🔶 | Será criado na Fase 0 |

---

## 🚀 Como Começar

### 1. Revisar Documentação

Leia os documentos nesta ordem:

1. **ESPECIFICACAO_FUNCIONAL.md** - Entender o que precisa ser construído
2. **ESPECIFICACAO_TECNICA.md** - Entender como será construído
3. **PLANO_IMPLEMENTACAO.md** - Entender o cronograma e fases
4. **PASSOS_IMPLEMENTACAO.md** - Seguir checklist de implementação

### 2. Configurar Ambiente

```bash
# Clonar repositório (se ainda não tem)
git clone https://github.com/egarabini/Intellicare.git
cd Intellicare

# Ir para módulo admin
cd intellicare-admin

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependências
pip install -e ".[dev]"
```

### 3. Seguir PASSOS_IMPLEMENTACAO.md

Comece pela **Fase 0: Pré-Implementação** e siga o checklist passo a passo.

---

## 📊 Status Atual

### Progresso Geral

```
████████████████████████████████████████████████████
  Planejamento     [████████████████████████] 100%
  Implementação    [░░░░░░░░░░░░░░░░░░░░░░░]   0%
  Testes           [░░░░░░░░░░░░░░░░░░░░░░░]   0%
  Deploy           [░░░░░░░░░░░░░░░░░░░░░░░]   0%
```

### Fases Concluídas

- ✅ Planejamento completo
- ✅ Especificações aprovadas

### Próximos Passos

1. 🔲 Atribuir desenvolvedor
2. 🔲 Iniciar Fase 0 - Pré-Implementação
3. 🔲 Seguir cronograma

---

## 📞 Suporte

### Dúvidas sobre Implementação

- Consultar **ESPECIFICACAO_TECNICA.md** para detalhes técnicos
- Consultar **PASSOS_IMPLEMENTACAO.md** para checklist
- Abrir issue no GitHub para blockers

### Dúvidas sobre Negócio

- Consultar **ESPECIFICACAO_FUNCIONAL.md** para casos de uso
- Consultar **PLANO_IMPLEMENTACAO.md** para cronograma

---

## 📝 Notas

- Seguir **PADRAO_NOMENCLATURA_DOCUMENTOS.md** para novos documentos
- Todos os commits devem seguir padrão de mensagens
- Todo código deve passar por `ruff check` e `mypy`
- Testes devem ter cobertura ≥80%

---

**FASE2_ADMIN v1.0.0**
**Data**: 2026-03-02
**Responsável**: IntelliCare Team
**Status**: 🟡 Pronto para Início da Implementação
