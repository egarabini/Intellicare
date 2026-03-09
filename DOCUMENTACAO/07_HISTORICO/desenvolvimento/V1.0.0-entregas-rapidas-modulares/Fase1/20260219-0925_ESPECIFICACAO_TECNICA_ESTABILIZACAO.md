# ESPECIFICACAO_TECNICA — Fase 1: Estabilizacao

**Versao:** 1.0  
**Data:** 2026-02-19  
**Status:** Aprovada para execucao  
**Base funcional:** `ESPECIFICACAO_FUNCIONAL_FASE1_ESTABILIZACAO_v1.0.md`

---

## 1. Objetivo Tecnico

Garantir subida confiavel da demo local (6 backends + portal), com infraestrutura dependente (Postgres/Redis), isolamento de dependencias Python por modulo e validacoes minimas de funcionamento por endpoint de health e fluxo principal.

---

## 2. Arquitetura de Execucao da Fase

## 2.1 Componentes

- Infraestrutura compartilhada: Docker Compose (`postgres`, `redis`).
- Backends da demo:
  - Oswaldo (8002)
  - Florence (8001)
  - Geralda (8006)
  - Nise (8000)
  - Zilda (8003)
  - Grahame (8004)
- Frontend/portal:
  - Portal Vite/React (5173)
- Orquestracao:
  - `start_demo.bat` (alvo principal no Windows)

## 2.2 Modelo de isolamento de dependencias

Cada modulo Python deve executar em ambiente virtual proprio:
- opcao preferencial: `python -m venv .venv`
- alternativa permitida: poetry/conda

Regras:
- proibido compartilhar `site-packages` global;
- instalacao de dependencias sempre dentro do ambiente do modulo;
- evidenciar ambiente ativo antes da subida do servico.

---

## 3. Contratos Tecnicos de Validacao

## 3.1 Contrato de infraestrutura

- `docker-compose up -d` deve finalizar sem erro.
- Containers `postgres` e `redis` devem estar `healthy`.

## 3.2 Contrato de processo por modulo

Para cada backend:
- processo inicia sem excecao fatal;
- porta alvo abre e aceita conexao;
- endpoint de health retorna HTTP 200.

## 3.3 Contrato do portal

- `npm run dev` inicia sem erro;
- `http://localhost:5173` responde;
- paginas dos modulos da demo carregam.

---

## 4. Matriz de Validacao Tecnica

| Modulo | Porta | Entry point esperado | Health esperado |
|---|---:|---|---|
| Oswaldo | 8002 | `python -m src.oswaldo.api.main` (ou equivalente local) | `/api/v1/health` ou `/health` |
| Florence | 8001 | `python run_api_8001.py` | `/api/v1/health` ou `/health` |
| Geralda | 8006 | `python run_api_8006.py` | `/api/v1/health` ou `/health` |
| Nise | 8000 | `python run_api_lite.py` | `/api/v1/health` ou `/health` |
| Zilda | 8003 | `python run_api_lite.py` | `/api/v1/health` ou `/health` |
| Grahame | 8004 | `python run_api_lite.py` | `/api/v1/health` ou `/health` |
| Portal | 5173 | `npm run dev` | `/` carregando UI |

---

## 5. Telemetria e Evidencias Minimas

Para cada modulo validar e registrar:
- comando executado;
- timestamp de inicio;
- URL testada;
- status HTTP;
- resultado final (`OK`, `P0`, `P1`, `P2`).

Arquivos de saida obrigatorios:
- `docs/PLANNER-CURSOR/CHECKLIST_ESTABILIZACAO.md`
- `docs/PLANNER-CURSOR/ISSUES_CONHECIDOS.md`

---

## 6. Tratamento de Falhas

Categorias:
- `P0`: bloqueia demo (servico nao sobe, crash, sem health)
- `P1`: sobe com degradacao relevante (funcao principal quebrada)
- `P2`: nao bloqueante (mensagem, UX, warning sem impacto funcional)

Politica:
- corrigir obrigatoriamente P0 na fase;
- P1 corrigir se baixo custo, senao registrar;
- P2 registrar para backlog.

---

## 7. Requisitos de Script de Inicializacao

`start_demo.bat` deve:
- considerar inicializacao de infraestrutura;
- iniciar os 7 processos sem concorrencia conflituosa;
- emitir logs claros de sucesso/falha por modulo;
- refletir uso de ambientes virtuais por modulo (direto ou via precondicao documentada).

---

## 8. Criterios Tecnicos de Conclusao

1. Infra em estado healthy.
2. 6 backends ativos com health 200.
3. Portal ativo em `http://localhost:5173`.
4. Checklist preenchido e versionado.
5. Issues conhecidas registradas com prioridade e impacto.
6. Sem dependencia Python global para execucao da demo.
