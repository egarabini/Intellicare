# Especificação — Apresentação V2.0.0 para Palestra

**Data:** 2026-02-22  
**Fonte:** docs/PLANNER-ANTIGRAVITY  
**Destino:** intellicare-apresentacao/versoes/v2_0_0_palestra

---

## 1. Objetivo

Criar apresentação interativa para palestra que mostre aos participantes uma **visão ampla** do avanço IntelliCare, com opção de **aprofundamento** em cada slide via tecla D (Deep Dive).

---

## 2. Público-Alvo

- Participantes da palestra (técnicos, gestores, investidores)
- Nível de detalhe variável: resumo executivo ou aprofundamento técnico conforme interesse

---

## 3. Requisitos de Conteúdo

### 3.1. Fontes de Conteúdo (PLANNER-ANTIGRAVITY)

| Documento | Conteúdo para slides |
|-----------|----------------------|
| `CONTROLE_GERAL.md` | Status dos módulos, prioridades |
| `ROADMAP_PARALELO/20260222-1946_PLANO_MESTRE.md` | Trilhas T1–T5, paralelismo |
| `MULTI_TENANCY/ANALISE_MULTI_TENANCY.md` | 2 camadas, admin, gestor, onboarding |
| `PLANO_DEMO_INVESTIDORES.md` | Pierre, Minerva, Portal, 3 DEVs |
| `MULTI_TENANCY/DESENVOLVIMENTO/F0_*` | TenantContext, JWT, schema isolation |
| `ROADMAP_PARALELO/T1_*` a `T5_*` | Detalhes por trilha |

### 3.2. Regra de Navegação

- **Slide principal:** visão resumida (3–5 bullet points)
- **Tecla D:** abre overlay com detalhamento
- **Overlay:** pode conter texto extenso; ESC ou D novamente fecha
- **Aprofundamento adicional:** se o overlay tiver seção "Ver mais", pode abrir segundo nível (implementação futura)

---

## 4. Estrutura de Slides (10 slides)

### Slide 1 — Título
- **Resumo:** IntelliCare — Uma Visão Além do Tempo
- **Deep Dive:** Mensagem de abertura, próximos passos da palestra

### Slide 2 — O que temos hoje
- **Resumo:** 7 agentes especializados, modularização LEGO, demo funcional
- **Deep Dive:** Arquitetura LEGO, contratos /health, comercialização por módulo

### Slide 3 — Multi-Tenancy: A Evolução
- **Resumo:** 2 camadas (Plataforma + Tenant), schema por tenant, isolamento LGPD
- **Deep Dive:** Fluxo de onboarding, TenantContext, Token Exchange

### Slide 4 — Novos Módulos
- **Resumo:** intellicare-admin (gestão SaaS), intellicare-gestor (admin local)
- **Deep Dive:** F1–F5, provisionamento, RBAC, billing

### Slide 5 — Roadmap Paralelo
- **Resumo:** 5 trilhas (T1 Infra, T2 Multi-Tenancy, T3 Domínios, T4 Hardening, T5 Tooling)
- **Deep Dive:** Dependências, prioridades, cronograma

### Slide 6 — Demo Investidores
- **Resumo:** Pierre (IA), Minerva (MINERVA), Portal (UI) — 3 frentes
- **Deep Dive:** Estratégia 3 DEVs, wow factor, MVP visual

### Slide 7 — TenantContext (F0)
- **Resumo:** Fundação técnica, JWT com tenant_id, schema isolation
- **Deep Dive:** Requisitos RF-F0-001 a RF-F0-006, fluxo de requisição

### Slide 8 — Stack e Arquitetura
- **Resumo:** FastAPI, FHIR R4, Keycloak, Docker, Ollama
- **Deep Dive:** Princípios arquiteturais, zero vendor lock-in

### Slide 9 — Mercado e Oportunidade
- **Resumo:** Saúde digital R$ 47 bi, RNDS/FHIR, modelo SaaS
- **Deep Dive:** Tiers de licenciamento, diferenciais competitivos

### Slide 10 — Fechamento
- **Resumo:** Visão consolidada, convite ao diálogo
- **Deep Dive:** Contato, repositório, próximos passos

---

## 5. Critérios de Aceite

- [ ] 10 slides com conteúdo alinhado a PLANNER-ANTIGRAVITY
- [ ] Cada slide com deep_dive_content preenchido
- [ ] Tecla D abre overlay de detalhamento
- [ ] Narração Wanda opcional (--voz offline/online)
- [ ] Execução via `python main.py --versao v2_0_0_palestra`
- [ ] Documentação em desenvolvimento/V2.0.0-apresentacao
