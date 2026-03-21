# DEM-056 — Executor Matrix ADR (Camada 2 IA-FRAMEWORK)

> **Dev:** CODEX
> **Estimativa:** ~2h
> **Dependência:** DEM-INF Memória Operacional (7f708fb), IA-FRAMEWORK/CONCLUSAO/CONCLUSAO_ARQUITETO.md

---

## Contexto

A CONCLUSAO_ARQUITETO.md definiu 3 camadas de adoção do IA-FRAMEWORK:

- **Camada 1** ✅ Concluída (7f708fb) — `docs/patterns/` + `docs/gotchas/` + HANDOFF.yml
- **Camada 2** → Esta DEM — Executor Matrix como ADR formal
- **Camada 3** → DEM futura — Clinical Squad (florence+oswaldo)

A Executor Matrix classifica cada componente automatizável do IntelliCare em uma
das 4 categorias do framework:

| Categoria | Definição |
|---|---|
| **Worker** | Execução autônoma, sem supervisão humana. Reversível ou idempotente. |
| **Agent** | Execução autônoma com consequência externa (envia mensagem, altera dado). Requer auditoria. |
| **Hybrid** | Inicia automaticamente, mas requer aprovação humana em algum ponto do fluxo. |
| **Human** | Deve ser executado por humano. Automatização proibida ou inviável no momento. |

---

## Entrega

Um único arquivo `docs/adr/ADR-001-executor-matrix.md` seguindo o formato
[MADR](https://adr.github.io/madr/) adaptado ao IntelliCare.

---

## Estrutura do ADR

### STEP-001 — Criar diretório e arquivo

```
docs/
└── adr/
    ├── README.md          (índice dos ADRs — criar junto)
    └── ADR-001-executor-matrix.md
```

### STEP-002 — Conteúdo obrigatório do ADR-001

O arquivo deve conter as seguintes seções com conteúdo real (não placeholder):

#### Cabeçalho
```markdown
# ADR-001 — Executor Matrix: Governança de Automação IntelliCare

- **Status:** Accepted
- **Data:** 2026-03-28
- **Decisores:** ARQUITETO (Eduardo Garabini)
- **Contexto técnico:** IntelliCare V3 — FastAPI + Celery/Redis + 4 canais CarePlanner
```

#### Contexto e Problema
Descrever: o IntelliCare tem workers, adapters, agents LLM e ações humanas misturados
sem classificação formal. Sem essa classificação, é difícil decidir o que pode ser
automatizado de forma segura e o que precisa de supervisão.

#### Decisão
Adotar a Executor Matrix como critério formal de classificação, revisada a cada sprint
pelo ARQUITETO.

#### Classificação Atual dos Componentes

Preencher a tabela completa com os componentes reais do IntelliCare V3:

```markdown
| Componente | Módulo | Categoria | Justificativa |
|---|---|---|---|
| `dispatcher_worker` | careplanner | Agent | Envia mensagem real para paciente via 3 canais externos |
| `expiry_worker` | careplanner | Worker | Marca tasks como EXPIRED — reversível via admin |
| `seed_flows.py` | careplanner | Worker | Idempotente, não tem efeito externo |
| `seed_templates()` | careplanner | Worker | Idempotente, só escrita interna |
| `EmailAdapter.send()` | careplanner | Agent | Envia email real — irreversível |
| `WhatsAppAdapter.send()` | careplanner | Agent | Envia mensagem WA — irreversível |
| `SMSAdapter.send()` | careplanner | Agent | Envia SMS real — irreversível e cobrado |
| `RocketChatAdapter.send()` | careplanner | Agent | Envia para canal RC — reversível por moderação |
| `notify_clinico_replied()` | careplanner | Worker | Notificação interna, sem canal externo |
| `notify_task_expired()` | careplanner | Worker | Notificação interna, sem canal externo |
| `generate_journey_report()` | careplanner | Worker | Geração on-demand, sem efeito externo |
| `trigger_flow()` (Kestra) | careplanner | Hybrid | Dispara workflow externo, precisa de correlation_id válido |
| `AIAssistant` (ClinicoUI) | clínico | Hybrid | Sugere texto ao clínico — humano revisa antes de salvar |
| Deploy VPS (`staging_update.sh`) | infra | Human | Requer SSH e decisão humana sobre timing |
| Escaneio QR WhatsApp | infra | Human | Requer ação física do operador |
| Criação de tenant | admin | Human | Decisão comercial — não automatizável |
| Emissão de certificado SSL | infra | Worker | Traefik/Let's Encrypt automático e idempotente |
```

> **Instrução:** adicionar todos os componentes conhecidos. Não inventar componentes
> que não existem no código. Consultar `docs/patterns/workers-webhooks.md` e
> `docs/patterns/backend-modules.md` como fonte.

#### Consequências
- Positivas: clareza sobre o que pode ser automatizado com segurança
- Negativas: overhead de revisão a cada nova DEM que introduz automação
- Risco: classificação desatualizada se não revisada

#### Critério de revisão
"A cada DEM que introduz novo worker, adapter ou automação, o dev deve propor a
classificação na seção de entrega do BRIEFING. O ARQUITETO confirma no code review."

#### Exemplo de uso futuro
"Florence (DEM-055) introduz `FlorenceNoteEditor` — classificação proposta: **Hybrid**
(sugere texto, humano decide salvar). Se no futuro Florence auto-salvar notas, reclassificar
para Agent e adicionar log de auditoria obrigatório."

### STEP-003 — README.md do diretório adr/

```markdown
# ADRs — IntelliCare V3

Architectural Decision Records seguindo o formato MADR.

| ADR | Título | Status |
|-----|--------|--------|
| [ADR-001](ADR-001-executor-matrix.md) | Executor Matrix: Governança de Automação | Accepted |
```

---

## Critérios de Aceite

- [ ] `docs/adr/ADR-001-executor-matrix.md` criado com todas as seções preenchidas
- [ ] Tabela de componentes tem no mínimo 15 linhas com componentes reais do IntelliCare
- [ ] Nenhuma linha da tabela com "TODO" ou "a definir"
- [ ] `docs/adr/README.md` com índice
- [ ] ADR referencia a CONCLUSAO_ARQUITETO.md como contexto

---

## Nota de Escopo

Este ADR é **documental** — não altera código. Mas tem impacto direto nos próximos
BRIEFINGs: toda DEM que introduzir automação deve agora propor a classificação da
Executor Matrix na seção de entrega. O ARQUITETO revisa e confirma antes do aceite.
