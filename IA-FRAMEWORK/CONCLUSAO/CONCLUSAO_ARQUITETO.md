# Conclusão do Arquiteto — Framework AIOX × IntelliCare V3

> Autor: ARQUITETO (Planejador IntelliCare)
> Data: 2026-03-19
> Base: Análises de ANTIGRAVITY, CODEX, COPILOT, CURSOR e GEMINI

---

## 1. O que é o AIOX — síntese em uma linha

Um sistema de engenharia de software orientado a agentes de IA, onde a qualidade do
**artefato** (documento, story, handoff) é o mecanismo de controle — não o talento
individual do agente.

---

## 2. O que os 5 agentes convergiram

Lendo as 10 análises sem exceção, há **5 pontos em que todos concordam**:

| Ponto | Consenso |
|-------|----------|
| Memória operacional (`patterns`, `gotchas`, `digests`) | Implementar — alto valor, baixo custo |
| Quality gates formais por demanda | Implementar — já temos CI/CD, falta o gate por DEM |
| Handoff estruturado entre agentes | Implementar — resolve perda de contexto real |
| Executor Matrix (Worker/Agent/Hybrid/Human) | Implementar — crítico para CarePlanner multi-canal |
| Adoption story: absorver padrões, NÃO copiar o framework | Unânime — CLI-first, Node.js e burocracia de squads não se aplicam |

---

## 3. Minha avaliação como arquiteto do IntelliCare

### 3.1 O que os agentes acertaram

**CODEX** foi o mais cirúrgico: identificou que nosso maior ganho não é "criar squads",
é institucionalizar memória útil, contexto de brownfield, gates objetivos e separação
entre automação determinística e decisão assistida. Concordo inteiramente.

**COPILOT** trouxe o insight mais concreto: o nosso sistema de DEMs (`01_FUNCIONAL`,
`02_TECNICA`, `03_PLANO`) **já é** story-driven development. O que falta são acceptance
criteria formais (Given/When/Then) e um HANDOFF.yml por entrega. Custo: horas, não semanas.

**CURSOR** foi o mais rigoroso no ponto da saúde: qualquer adoção precisa incorporar
critérios clínicos (segurança do paciente, rastreabilidade, FHIR) — frameworks genéricos
de "quality gate de software" não bastam quando o output influencia conduta clínica.

### 3.2 O que os agentes subestimaram

**O problema mais urgente que temos não é arquitetural — é de contexto perdido entre entregas.**

Nos últimos sprints, já tivemos:
- DEM-044: commit esquecido, hash trocado com DEM-046, regressão descoberta tarde
- DEM-050: `CareplannerService.__init__` mudou em DEM-047/048/049 e fixtures das Phases B/C/E
  não foram atualizadas — causou regressão que bloqueou o commit de DEM-050
- Staging deploy: commits existiam só nas máquinas locais dos devs, não no GitHub

Todos esses problemas têm a **mesma causa raiz**: ausência de memória operacional
e handoffs explícitos. O AIOX chama isso de `patterns.md`, `gotchas.md` e
`session-digests`. Nós não precisamos de squads para resolver isso — precisamos de
**3 arquivos e uma disciplina**.

### 3.3 O que descarto do AIOX para nosso contexto atual

**Squad Clínico Tier 0/1/2/3 (ANTIGRAVITY):** A visão é correta e o destino final
está certo, mas o momento é prematuro. Os módulos `florence` e `oswaldo` ainda não
têm cobertura de testes suficiente nem documentação de contratos que sustente um
sistema de roteamento clínico robusto. Construir o "departamento de inteligência
clínica" em cima de alicerces não consolidados vai produzir mais bugs clínicos, não menos.

**11 personas com nomes, arquétipos e jurisdição absoluta:** Somos 1 arquiteto + 4 devs
+ agentes de IA. A formalização de personas agrega burocracia sem ganho proporcional.
O que temos no `AGENTS.md` e `PLANEJADOR.md` é suficiente como controle de autoridade.

**CLI-first como filosofia de produto:** IntelliCare é uma plataforma clínica. O
profissional de saúde usa UI. CLI é tooling de desenvolvimento — não é o produto.

---

## 4. Minha conclusão: 3 camadas de adoção

### Camada 1 — Engenharia de Processo (imediato, ~1 DEM-INF)

**O que:** Memória operacional + handoffs estruturados + quality gate por DEM.

**Por quê primeiro:** Resolve dor real que já ocorreu múltiplas vezes. Custo mínimo.
Impacto imediato nos próximos sprints.

**Entregas concretas:**

```
docs/
├── patterns/
│   ├── README.md             — índice + regra: toda DEM que gerar padrão reutilizável registra aqui
│   ├── backend-modules.md    — repository → service → router, migrations, seeds
│   ├── frontend-pages.md     — hooks + pages + Mantine 7, NativeSelect vs Select
│   └── workers-webhooks.md   — adapter pattern, retry exponencial, HMAC, Redis dispatch
├── gotchas/
│   ├── README.md
│   ├── careplanner.md        — channel enum, fixtures CareplannerService, cross-tenant phone lookup
│   ├── staging-deploy.md     — git push antes do deploy, letsencrypt dirty, .env.staging secrets
│   └── keycloak-auth.md      — VITE_KEYCLOAK_URL, redirect_uri, roles no JWT
└── digests/
    └── README.md             — formato mínimo de digest por DEM/sprint
```

**Quality gate:** Adicionar checklist `## ✅ Quality Gate` ao template `05_FINALIZACAO.md`
(ou ao BRIEFING.md) com itens blocking vs warning. Uma DEM não fecha sem o gate.

**HANDOFF.yml:** Arquivo simples em cada pasta de DEM. O dev que entrega preenche;
o próximo dev lê antes de começar. Resolve exatamente o problema DEM-044/DEM-050.

---

### Camada 2 — Governança de Automações (próximo ciclo, 1 DEM dedicada)

**O que:** Executor Matrix + atualização do AGENTS.md.

**Por quê:** O CarePlanner agora tem 4 canais, 3 workers, Kestra, Evolution API, Listmonk,
Jasmin. Antes de avançar para funcionalidades clínicas com IA, precisamos ter clareza
sobre onde cada tipo de trabalho acontece.

**Entregável:** `docs/design-docs/ADR-003-execution-matrix.md`

```
Módulo         | Tipo de executor
---------------|------------------------------------------
Migrations     | Worker — 100% determinístico
Adapters (RC/WA/Email/SMS) | Worker — chamada HTTP estruturada
Kestra flows   | Worker — orquestração por YAML
Dispatcher     | Worker — lógica de roteamento por enum
Expiry worker  | Worker — cron determinístico
Templates CarePlanner | Worker — seed com fallback idempotente
Notificações SSE/WS | Worker — pub/sub Redis estruturado
----
AIAssistant (draft de conduta) | Hybrid — LLM sugere, clínico revisa
Encounter summary              | Hybrid — LLM rascunha, clínico aprova
Florence RAG (busca protocolo) | Agent — semântico, resultado informativo
Oswaldo (análise FHIR)         | Agent — semântico com auditoria
Triagem de risco (futuro)      | Human gate — NUNCA automático sem aprovação
```

---

### Camada 3 — Squad Clínico (futuro, quando Camada 1 estiver estável)

**O que:** Pipeline de inteligência clínica com HITL, inspirado no AIOX Deep Research
Squad mas adaptado para saúde regulada.

**Por quê depois:** Depende de florence e oswaldo estabilizados, de testes de integração
robustos, e de uma base de contratos FHIR documentada. Sem Camada 1, qualquer alucinação
clínica vai ser difícil de rastrear.

**Quando:** Após DEM-INF de Engenharia de Processo entregue e um sprint completo
rodando com `patterns`, `gotchas` e HANDOFF.yml funcionando.

**Visão:** Cada paciente não fala com um chatbot genérico — aciona uma borda de
inteligência clínica que roteia, pesquisa protocolo, gera rascunho e submete ao clínico
antes de qualquer output chegar ao canal (WhatsApp/Email/SMS).

---

## 5. O que temos hoje vs o que o AIOX tem

| Conceito AIOX | IntelliCare hoje | Gap |
|--------------|-----------------|-----|
| Story-driven development | ✅ Sistema DEMs com 01/02/03_PLANO | Falta AC formal Given/When/Then |
| Planejador/Arquiteto | ✅ PLANEJADOR.md + sessão de trabalho | — |
| Agentes de dev | ✅ DEV-1/2/CODEX/DEV-3/4 | Falta HANDOFF.yml |
| Quality gates | ⚠️ CI/CD existe, gate por DEM não | Criar checklist no template |
| Memory layer | ❌ Não existe | Criar docs/patterns + gotchas |
| Session digests | ❌ Não existe | Criar docs/digests |
| Executor Matrix | ❌ Implícito, não documentado | Documentar em ADR |
| Squad Clínico | ❌ florence/oswaldo existem mas não orquestrados | Camada 3 (futuro) |
| Brownfield map por DEM | ⚠️ Parcial nos BRIEFINGs | Formalizar 00_CONTEXTO.md |
| Constituição formal | ⚠️ AGENTS.md básico | Expandir autoridades |

---

## 6. Recomendação executiva

**Prioridade 1 (próxima DEM-INF):** Criar `docs/patterns/`, `docs/gotchas/` e
template de HANDOFF.yml. Levar 1 sprint para preencher com o conhecimento que já
existe implicitamente na nossa cabeça.

**Prioridade 2 (DEM seguinte):** `docs/design-docs/ADR-003-execution-matrix.md` +
quality gate formal no template de demanda.

**Prioridade 3 (quando p1 e p2 estiverem rodando):** Discutir Squad Clínico como
próxima fronteira estratégica do produto — não como overhead de processo, mas como
diferencial competitivo real da plataforma.

---

## 7. Uma frase para resumir

> O AIOX nos confirma que já estamos no caminho certo — DEMs bem especificadas, devs
> com autonomia guiada, arquiteto como orquestrador. O salto é transformar o conhecimento
> que hoje vive na memória de sessão em artefatos persistentes que sobrevivem entre
> sprints e entre agentes. Isso é low-cost, high-impact, e desbloqueará a Camada 3
> (Squad Clínico) de forma segura quando chegar a hora.
