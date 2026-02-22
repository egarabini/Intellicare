# Estratégia de Próximos Passos — IntelliCare no Ar

**Data:** 2026-02-19  
**Objetivo:** Colocar o projeto no ar o mais cedo possível, sem erros, em domínio de saúde  
**Contexto:** Evolução rápida, visão avançada, complexidade de 15+ módulos, repositório eduardo/intellicare sem deploy

---

## 1. Princípios da Estratégia

> **Premissa obrigatória (Python):** Sempre executar em ambiente virtual (venv, poetry, conda). O projeto teve problemas recorrentes de compatibilidade de versões de bibliotecas Python; o uso de ambientes virtuais isola dependências por módulo/ambiente.

| Princípio | Aplicação |
|-----------|-----------|
| **Simplicidade primeiro** | Deploy mínimo viável antes de Kubernetes ou orquestração complexa |
| **Zero erros em saúde** | Validação rigorosa antes de cada etapa; testes de fumaça obrigatórios |
| **Incremental** | Um passo de cada vez, com checkpoint de sucesso antes do próximo |
| **Reversível** | Cada decisão deve permitir rollback sem perda de dados |
| **Documentado** | Tudo que for feito deve ser registrado para rastreabilidade |

---

## 2. Visão Geral — 5 Fases

```
FASE 1: Estabilização     → Garantir que o que existe funciona
FASE 2: Organização Git   → Controle de versão e releases
FASE 3: Deploy Mínimo     → Projeto acessível na web
FASE 4: Monitoramento     → Ver e reagir a problemas
FASE 5: Produção Ready    → Auth, LGPD, hardening
```

**Meta de tempo:** Fases 1–3 em 4–6 semanas para ter o projeto no ar.

---

## 3. FASE 1 — Estabilização (Prioridade Máxima)

**Objetivo:** Garantir que todos os serviços da demo sobem e respondem corretamente.

### 3.1 Premissa Obrigatória

**Ambiente virtual Python:** Todos os módulos Python devem ser executados em ambiente virtual (venv, poetry, conda). O projeto teve problemas recorrentes de compatibilidade de versões de bibliotecas; ambientes virtuais isolam dependências.

### 3.2 Checklist de Validação

| # | Ação | Responsável | Critério de sucesso |
|---|------|--------------|---------------------|
| 1.1 | Subir infraestrutura (Postgres, Redis) via `docker-compose up -d` | Dev | Containers healthy |
| 1.2 | Executar `start_demo.bat` e validar os 7 processos | Dev | Todos iniciam sem erro |
| 1.3 | Acessar portal em http://localhost:5173 | Dev | Portal carrega |
| 1.4 | Testar cada módulo na demo (Oswaldo, Florence, Geralda, Nise, Zilda, Grahame) | Dev | Funcionalidades principais respondem |
| 1.5 | Registrar módulos que falham ou têm comportamento inesperado | Dev | Lista de issues conhecidas |
| 1.6 | Corrigir bloqueadores críticos (serviço não sobe, crash) | Dev | Demo 100% funcional localmente |
| 1.7 | Garantir que cada módulo Python use ambiente virtual (venv/poetry) | Dev | Sem conflitos de versão entre módulos |

### 3.3 Entregáveis

- [ ] `docs/PLANNER-CURSOR/CHECKLIST_ESTABILIZACAO.md` — checklist preenchido
- [ ] `docs/PLANNER-CURSOR/ISSUES_CONHECIDOS.md` — lista de problemas não bloqueantes (se houver)
- [ ] Demo local funcionando de ponta a ponta
- [ ] Dev registra em `especificacoes/Fase1/`: ESPECIFICACAO_TECNICA e PLANO_IMPLEMENTACAO
- [ ] Demo local funcionando de ponta a ponta

### 3.4 Prazo sugerido: 1 semana

---

## 4. FASE 2 — Organização Git e Controle de Versão

**Objetivo:** Repositório `eduardo/intellicare` com estratégia clara de branches, tags e releases.

### 4.1 Ações Prioritárias

| # | Ação | Critério de sucesso |
|---|------|---------------------|
| 2.1 | Definir e documentar estratégia de branches | `main` (produção), `develop` (integração), `feature/*` (opcional) |
| 2.2 | Garantir `.gitignore` adequado (venv, __pycache__, .env, node_modules, etc.) | Nenhum arquivo sensível ou gerado versionado |
| 2.3 | Criar `CHANGELOG.md` na raiz | Histórico de mudanças versionado |
| 2.4 | Primeira tag semântica: `v0.1.0-demo` ou `v1.0.0-demo` | Release inicial documentada |
| 2.5 | Documentar processo de release em `docs/PLANNER-CURSOR/PROCESSO_RELEASE.md` | Qualquer dev consegue fazer um release |

### 4.2 Entregáveis

- [ ] `docs/PLANNER-CURSOR/ESTRATEGIA_GIT.md` — branches, tags, fluxo de PR
- [ ] `CHANGELOG.md` na raiz
- [ ] Tag `v0.1.0-demo` (ou similar) criada

### 4.3 Prazo sugerido: 1 semana (pode sobrepor Fase 1)

---

## 5. FASE 3 — Deploy Mínimo Viável

**Objetivo:** Projeto acessível via URL pública (HTTPS), com todos os serviços da demo.

### 5.1 Opções de Deploy (da mais simples à mais complexa)

| Opção | Prós | Contras | Recomendação |
|-------|-----|---------|--------------|
| **A) Docker Compose em VPS** | Controle total, já temos compose | Requer servidor, manutenção | Boa para controle |
| **B) Railway / Render / Fly.io** | Deploy rápido, pouco ops | Custo, limites de recursos | **Recomendado para MVP** |
| **C) Kubernetes** | Escalável, produção | Complexidade alta | Fase posterior |

### 5.2 Ações Prioritárias (independente da opção)

| # | Ação | Critério de sucesso |
|---|------|---------------------|
| 3.1 | Criar `.env.example` com todas as variáveis necessárias | Deploy em máquina limpa funciona |
| 3.2 | Unificar ou orquestrar `start_demo` em um único `docker-compose` (ou script) que levanta tudo | Um comando sobe toda a stack |
| 3.3 | Configurar URLs dos backends no frontend via variáveis de ambiente | Portal aponta para backends corretos em cada ambiente |
| 3.4 | Definir ambiente de staging/homologação | URL de acesso (ex: staging.intellicare.xxx) |
| 3.5 | Configurar HTTPS (Let's Encrypt ou do provedor) | Acesso seguro |
| 3.6 | Smoke tests automatizados (health de cada serviço) | Script que valida deploy |

### 5.3 Orquestração Sugerida

- **Infraestrutura:** Postgres, Redis, Prometheus, Grafana — já no `docker-compose.yml` atual
- **Backends:** 6 módulos (Oswaldo, Florence, Geralda, Nise, Zilda, Grahame) — podem rodar em containers ou processos gerenciados
- **Frontend:** Build estático (Vite) servido por nginx ou CDN
- **Recomendação:** Criar `docker-compose.prod.yml` ou `docker-compose.full.yml` que inclua todos os serviços necessários para a demo completa

### 5.4 Entregáveis

- [ ] `.env.example` completo
- [ ] `docker-compose.full.yml` (ou equivalente) que sobe toda a stack
- [ ] Documento `docs/PLANNER-CURSOR/GUIA_DEPLOY.md`
- [ ] URL de staging acessível e funcional

### 5.5 Prazo sugerido: 2 semanas

---

## 6. FASE 4 — Monitoramento e Observabilidade

**Objetivo:** Ver o que está acontecendo e reagir a falhas.

### 6.1 Ações (Prometheus e Grafana já existem)

| # | Ação | Critério de sucesso |
|---|------|---------------------|
| 4.1 | Validar que Prometheus coleta métricas dos serviços | Dashboard com dados |
| 4.2 | Configurar alertas básicos (serviço down, alta latência) | `alerts.yml` funcional |
| 4.3 | Criar dashboard Grafana mínimo (status dos 6 módulos + portal) | Visão única do sistema |
| 4.4 | Documentar como acessar e interpretar | `docs/PLANNER-CURSOR/GUIA_MONITORAMENTO.md` |

### 6.2 Prazo sugerido: 1 semana (pode ser paralelo à Fase 3)

---

## 7. FASE 5 — Produção Ready (Pós-Deploy)

**Objetivo:** Preparar para uso real com usuários e dados sensíveis.

| # | Ação | Prioridade |
|---|------|------------|
| 5.1 | Implementar intellicare-auth (Keycloak) | Alta — antes de dados reais |
| 5.2 | Revisão LGPD (consentimento, anonimização, auditoria) | Alta |
| 5.3 | Backup automatizado do banco | Alta |
| 5.4 | Política de retenção de dados | Média |
| 5.5 | Testes de integração automatizados | Média |
| 5.6 | CI/CD (GitHub Actions ou similar) | Média |

---

## 8. Priorização Visual — O que fazer AGORA

```
                    URGENTE
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
    │   FASE 1           │    FASE 2         │
    │   Estabilização    │    Git/Releases   │
    │   (esta semana)    │    (esta semana)  │
    │                   │                   │
    └───────────────────┼───────────────────┘
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
    │   FASE 3           │    FASE 4         │
    │   Deploy Mínimo    │    Monitoramento  │
    │   (próximas 2 sem) │    (paralelo)     │
    │                   │                   │
    └───────────────────┼───────────────────┘
                        │
                    FASE 5
                    (após no ar)
```

---

## 9. Ordem de Execução Recomendada

| Semana | Foco | Entregável |
|--------|------|------------|
| **1** | Fase 1 + início Fase 2 | Demo estável + estratégia Git documentada |
| **2** | Fase 2 concluída + início Fase 3 | Tag v0.1.0 + início do deploy |
| **3–4** | Fase 3 | Projeto no ar (staging) |
| **5** | Fase 4 | Monitoramento ativo |
| **6+** | Fase 5 | Auth, LGPD, hardening |

---

## 10. Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Módulo não sobe em ambiente novo | Fase 1 valida localmente; documentar dependências em `.env.example` |
| Conflito de portas em deploy | Usar portas dinâmicas ou reverse proxy (nginx/traefik) |
| Dados sensíveis em repositório | `.env` no `.gitignore`; usar secrets do provedor de deploy |
| Deploy quebra e não sabemos por quê | Fase 4 (monitoramento) antes de declarar "produção" |

---

## 11. Próxima Ação Imediata

**Para o ARQUITETO:** Validar esta estratégia e priorizar se alguma fase deve ser antecipada ou adiada.

**Para o PLANEJADOR:** Após validação, elaborar a primeira **ESPECIFICACAO_FUNCIONAL** — sugerido: **FASE 1 (Estabilização)** — para entrega aos agentes desenvolvedores, com checklist detalhado e critérios de aceite.

**Para os Agentes Desenvolvedores:** Aguardar ESPECIFICACAO_FUNCIONAL aprovada.
