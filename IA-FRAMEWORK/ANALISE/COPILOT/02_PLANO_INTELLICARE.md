# O que o AIOX pode trazer ao IntelliCare — Plano de Implementação

> Análise realizada por GitHub Copilot em 2026-03-19
> Foco: adaptações práticas, não adoção do framework

---

## Premissa

O IntelliCare é uma **plataforma de saúde em Python/FastAPI** com 7+ módulos, 5 frontends React, e um sistema de demandas (DEM-NNN) já funcional. Não faz sentido adotar o AIOX (Node.js, CLI-first) como framework. O valor está em **extrair 5 padrões de alto impacto** e adaptá-los à realidade do projeto.

---

## 1. Story-Driven DEMs com Contexto Completo

### O que o AIOX faz
O Scrum Master cria stories hiperdetalhadas que contêm TUDO que o dev/agente precisa: contexto, acceptance criteria (Given/When/Then), detalhes de implementação, file list, notas de arquitetura. O dev nunca sai do arquivo de story.

### O que o IntelliCare já tem
Sistema de demandas com 5 documentos (`01_FUNCIONAL.md`, `02_TECNICA.md`, `03_PLANO.md`, `04_DIARIO.md`, `05_FINALIZACAO.md`). Os BRIEFINGs recentes (DEM-044 a DEM-049) já convergem para esse modelo — um único arquivo com tudo.

### O que falta — e o avanço que traz
Os BRIEFINGs atuais são bons mas **não seguem um formato padronizado e verificável**. Adotar o modelo AIOX de acceptance criteria formais (Given/When/Then) + checklist de validação do PO traria:

- **BRIEFINGs auditáveis** — critérios binários de pass/fail por step
- **Menos ambiguidade** — o agente dev (Copilot/Codex) sabe exatamente quando terminou
- **Rastreabilidade** — cada AC mapeia para um teste

### Plano de implementação

| Step | Ação | Esforço |
|------|------|---------|
| 1 | Criar `docs/_templates/tpl_briefing_v2.md` com seções: Contexto, AC (Given/When/Then), Steps com checklist `[ ]`, File List, Quality Gate | 1h |
| 2 | Migrar template de BRIEFING para incluir campo `## Acceptance Criteria` obrigatório | 30min |
| 3 | Criar script `tools/scripts/validate_briefing.py` que verifica: (a) todos os steps têm checklist, (b) AC em formato Given/When/Then, (c) file list presente | 2h |
| 4 | Aplicar no próximo ciclo de DEMs (DEM-050+) e iterar | Contínuo |

**Impacto: ALTO. Esforço: BAIXO.**

---

## 2. Autoridade Exclusiva por Persona na Automação

### O que o AIOX faz
Cada agente tem jurisdição clara: só `@devops` faz git push, só `@architect` decide arquitetura, só `@qa` emite verdicts de qualidade. Isso elimina conflitos e comportamentos imprevisíveis.

### O que o IntelliCare pode adotar
O IntelliCare usa múltiplos agentes (Copilot, Codex, Augment). Definir **regras explícitas** no `AGENTS.md` sobre quem faz o quê:

- **PLANEJADOR** (humano ou agente de planning): cria `01_FUNCIONAL.md` e `02_TECNICA.md`
- **DESENVOLVEDOR** (Copilot/Codex): implementa código, cria `03_PLANO.md`, atualiza `04_DIARIO.md`
- **VALIDADOR** (pytest + lint + build): emite verdict automático
- **Nenhum agente faz deploy sem comando explícito humano** (equivalente à regra "só @devops faz push")

### Plano de implementação

| Step | Ação | Esforço |
|------|------|---------|
| 1 | Adicionar seção `## Autoridades por Persona` ao `AGENTS.md` | 30min |
| 2 | Definir regras de boundary: o que cada agente pode/não pode fazer | 30min |
| 3 | Adicionar guardrail no workflow: "antes de deploy, rodar `tools/scripts/smoke_test.sh`" | Já existe |

**Impacto: MÉDIO. Esforço: MÍNIMO.**

---

## 3. Quality Gates Automatizados por DEM

### O que o AIOX faz
3 camadas: pre-commit (lint+test+typecheck ~30s), PR automation (CodeRabbit ~5m), human review. Viola constituição = bloqueio automático.

### O que o IntelliCare já tem
- `pytest` com testes por módulo
- `QUALITY_SCORE.md` com scorecard (mas todos ⚪ — não avaliados)
- `smoke_test.sh` para verificação pós-deploy
- GitHub Actions workflow (DEM-046) com pytest + build GestorUI + ClinicoUI

### O que falta — e o avanço que traz

O scorecard está vazio e não há **gate automático** que impeça merge de DEM sem testes passando. Implementar gates formais traria disciplina sem overhead:

### Plano de implementação

| Step | Ação | Esforço |
|------|------|---------|
| 1 | Preencher `QUALITY_SCORE.md` com estado real de cada módulo (auditar cobertura, auth, health) | 3h |
| 2 | Criar `tools/scripts/quality_gate.py` que roda: pytest → lint → build check → relata pass/fail | 2h |
| 3 | Integrar `quality_gate.py` no GitHub Actions como step obrigatório antes de merge | 1h |
| 4 | Adicionar badge no README com resultado do último quality gate | 30min |
| 5 | Definir regra: DEM não fecha sem quality gate PASS (atualizar template `05_FINALIZACAO.md`) | 30min |

**Impacto: ALTO. Esforço: MÉDIO.**

---

## 4. Handoff Artifacts entre Agentes de IA

### O que o AIOX faz
Agentes deixam artefatos YAML estruturados em `.aiox/handoffs/` para o próximo agente saber exatamente onde o anterior parou. Permite colaboração assíncrona sem memória compartilhada.

### Aplicação no IntelliCare
O IntelliCare usa 3 agentes de IA (Copilot, Codex, Augment). Quando um agente trabalha em uma DEM e outro continua depois, há **perda de contexto**. Exemplo real: DEM-044 foi implementada por Copilot mas o commit foi esquecido e apareceu no meio da DEM-045 feita pelo Codex.

### Plano de implementação

| Step | Ação | Esforço |
|------|------|---------|
| 1 | Criar convenção: cada DEM terá `HANDOFF.yml` em `docs/demandas/DEM-NNN_NOME/` | 30min |
| 2 | Formato do HANDOFF: `agent`, `status`, `last_commit`, `files_changed`, `pending_actions`, `notes` | Template |
| 3 | Agente que finaliza DEM atualiza HANDOFF antes de parar | Disciplina de prompt |
| 4 | Agente que retoma DEM lê HANDOFF primeiro (adicionar instrução ao `AGENTS.md`) | 30min |

Exemplo de `HANDOFF.yml`:
```yaml
dem: DEM-049
agent: copilot
timestamp: 2026-03-19T10:30:00-03:00
status: committed
commit: 375253a
files_changed:
  - modules/careplanner/adapters/sms.py
  - modules/careplanner/contracts.py
  - modules/careplanner/config.py
  - modules/careplanner/services.py
  - modules/careplanner/api/routes.py
  - infra/docker-compose.yml
  - frontend/GestorUI/src/components/TriggerJourneyModal.tsx
  - packages/intellicare-core/tests/test_careplanner_phase_j.py
tests_passed: 4/4
pending_actions: []
notes: "SMS Channel.SMS adicionado, Jasmin adapter com truncamento 160 chars, webhook reutiliza handle_whatsapp_inbound"
```

**Impacto: ALTO. Esforço: BAIXO.**

---

## 5. Squad Clínico — Agentes Especializados em Saúde

### O que o AIOX faz
Squads são pacotes autocontidos de agentes especializados por domínio. O squad `deep-research` tem 11 agentes baseados em pesquisadores reais (Sackett para EBM, Cochrane para PRISMA/GRADE, Kahneman para viés cognitivo).

### O que o IntelliCare pode criar
Um **squad clínico** com agentes de IA especializados no domínio de saúde, usando a mesma abordagem de "clonar frameworks de decisão de especialistas":

| Agente | Inspiração | Papel no IntelliCare |
|--------|-----------|---------------------|
| `@protocolo` | Guidelines MS/OMS | Valida protocolos clínicos contra evidências |
| `@triagem` | Manchester Triage | Auxilia classificação de risco |
| `@farmacia` | Micromedex/DrugBank | Verifica interações medicamentosas |
| `@epidemio` | DATASUS/SIH/SIM | Análise epidemiológica populacional |
| `@cid` | CID-10/CID-11 | Codificação e classificação de diagnósticos |

Isto converge com os módulos Florence (protocolos RAG) e Oswaldo (análise clínica FHIR) mas eleva para agentes com **raciocínio clínico estruturado**, não apenas busca semântica.

### Plano de implementação

| Step | Ação | Esforço |
|------|------|---------|
| 1 | Criar `docs/design-docs/ADR-004-squad-clinico.md` com decisão e escopo | 2h |
| 2 | Definir prompts de sistema para 2 primeiros agentes (`@protocolo`, `@triagem`) em `docs/squads/` | 4h |
| 3 | Integrar com RAG existente (pgvector + Obsidian vault) — prompt recebe contexto de protocolos | 4h |
| 4 | Expor via endpoint `/api/v1/cuidado/squad/{agent}` no módulo cuidado | 3h |
| 5 | Testar com protocolos DRC, Diabetes, HAS já indexados | 2h |

**Impacto: MUITO ALTO (diferencial de produto). Esforço: ALTO (DEM dedicada).**

---

## Resumo Executivo — Priorização

| # | Iniciativa | Impacto | Esforço | Prioridade |
|---|-----------|---------|---------|------------|
| 1 | Story-Driven DEMs com AC formais | Alto | Baixo | **P0 — Fazer já** |
| 2 | Autoridade por Persona no AGENTS.md | Médio | Mínimo | **P0 — Fazer já** |
| 4 | Handoff Artifacts entre agentes | Alto | Baixo | **P1 — Próximo ciclo** |
| 3 | Quality Gates automatizados | Alto | Médio | **P1 — Próximo ciclo** |
| 5 | Squad Clínico especializado | Muito Alto | Alto | **P2 — DEM dedicada** |

### O que NÃO adotar do AIOX

- **CLI First como dogma** — IntelliCare é plataforma com UI clínica. CLI first se aplica ao tooling, não ao produto.
- **11 personas com nomes e arquétipos** — Overhead desnecessário para time de 1-3 devs.
- **Framework Node.js/markdown-only** — IntelliCare é Python. Usar markdown para docs, não como runtime.
- **Cerimônia SM→PO→Dev→QA por DEM** — Muito pesado para demandas de 1-2h. Manter BRIEFINGs diretos.
- **Constituição formal com processo de emenda** — Prematura para o tamanho do time. As 5 regras do `AGENTS.md` bastam.

---

## Conclusão

O AIOX oferece um modelo maduro de **governança de agentes de IA e engenharia de contexto**. Para o IntelliCare, os 5 padrões acima — especialmente story-driven DEMs, handoff artifacts e o squad clínico — representam avanços concretos que podem ser implementados incrementalmente sem disrupção no fluxo atual. A prioridade é começar pelas mudanças de baixo esforço (P0) e evoluir para o squad clínico como diferencial de produto.
