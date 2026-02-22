# PLANO_IMPLEMENTACAO — Fase 1: Estabilizacao

**Versao:** 1.0  
**Data:** 2026-02-19  
**Base:**  
- `ESPECIFICACAO_FUNCIONAL_FASE1_ESTABILIZACAO_v1.0.md`  
- `ESPECIFICACAO_TECNICA_FASE1_ESTABILIZACAO_v1.0.md`

---

## 1. Objetivo do Plano

Executar a estabilizacao da demo local de forma controlada, com evidencias objetivas e entrega dos artefatos exigidos.

---

## 2. Sequencia de Execucao (ordem obrigatoria)

1. Preparar ambiente local e validar pre-requisitos.
2. Subir infraestrutura Docker (Postgres/Redis) e validar health.
3. Validar/ajustar ambientes virtuais dos 6 modulos Python.
4. Subir e validar cada backend individualmente.
5. Subir portal e validar carregamento.
6. Executar subida integrada via `start_demo.bat`.
7. Registrar resultados no checklist e issues conhecidos.

---

## 3. Work Breakdown Structure (WBS)

## WBS-1 — Pre-flight

Tarefas:
- verificar portas livres (5173, 8000, 8001, 8002, 8003, 8004, 8006, 5432, 6379);
- verificar Docker, Node 18+, Python 3.11+;
- validar existencia de arquivos de entrada.

Saida:
- ambiente apto para execucao.

## WBS-2 — Infraestrutura

Tarefas:
- executar `docker-compose up -d`;
- validar `postgres` e `redis` com estado healthy.

Saida:
- CA-001 validado.

## WBS-3 — Ambientes virtuais

Tarefas (por modulo Python da demo):
- criar/ativar ambiente virtual;
- instalar dependencias;
- validar interpretador ativo.

Saida:
- CA-005 validado.

## WBS-4 — Validacao individual de modulos

Tarefas (por modulo):
- iniciar servico pelo entry point local;
- testar `/api/v1/health` ou `/health`;
- executar funcionalidade principal da demo.

Saida:
- CA-004 validado por modulo.

## WBS-5 — Portal

Tarefas:
- iniciar frontend;
- validar `http://localhost:5173`;
- validar navegacao basica entre modulos.

Saida:
- CA-003 validado.

## WBS-6 — Integracao via script

Tarefas:
- executar `start_demo.bat`;
- validar 7 processos ativos;
- conferir ausencia de crash inicial.

Saida:
- CA-002 validado.

## WBS-7 — Encerramento documental

Tarefas:
- preencher `docs/PLANNER-CURSOR/CHECKLIST_ESTABILIZACAO.md`;
- registrar nao bloqueantes em `docs/PLANNER-CURSOR/ISSUES_CONHECIDOS.md`;
- registrar P0/P1/P2 com impacto e workaround.

Saida:
- CA-006 validado.

---

## 4. Cronograma sugerido (5 dias uteis)

| Dia | Foco | Entrega |
|---|---|---|
| D1 | Pre-flight + Infra | WBS-1 e WBS-2 completos |
| D2 | Venv + modulos 1-3 | WBS-3 parcial + WBS-4 parcial |
| D3 | Venv + modulos 4-6 | WBS-3 completo + WBS-4 completo |
| D4 | Portal + execucao integrada | WBS-5 e WBS-6 completos |
| D5 | Correcoes criticas + documentacao | WBS-7 completo |

---

## 5. Matriz de Responsabilidade

| Atividade | Responsavel | Apoio |
|---|---|---|
| Infra Docker | Dev | Arquiteto |
| Ambientes virtuais | Dev | Dono do modulo |
| Validacao funcional | Dev | QA funcional |
| Atualizacao `start_demo.bat` | Dev | Arquiteto |
| Checklist e issues | Dev | QA |

---

## 6. Riscos e Contingencias

1. Dependencia quebrada em modulo especifico  
Contingencia: fix pin de versao no ambiente do modulo e registrar.

2. Conflito de porta  
Contingencia: matar processo conflituoso e rerodar validacao.

3. Script integrado falha mas modulo isolado funciona  
Contingencia: separar falha de orquestracao vs falha de aplicacao e corrigir `start_demo.bat`.

4. Tempo de startup alto gera falso negativo  
Contingencia: retries com timeout progressivo antes de classificar como P0.

---

## 7. Definition of Done (Fase 1)

- Infra healthy (`postgres`, `redis`).
- 6 backends da demo operacionais com health 200.
- Portal acessivel em `http://localhost:5173`.
- `start_demo.bat` validado com 7 processos sem crash inicial.
- `CHECKLIST_ESTABILIZACAO.md` preenchido.
- `ISSUES_CONHECIDOS.md` preenchido (se houver pendencias nao bloqueantes).

---

## 8. Proxima Fase (handoff)

Com Fase 1 concluida:
- iniciar Fase 2 (organizacao Git e release) sem pendencias P0 da demo.
