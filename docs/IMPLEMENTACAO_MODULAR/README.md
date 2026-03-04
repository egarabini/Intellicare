# IMPLEMENTACAO MODULAR — IntelliCare

**Data:** 2026-03-04
**Versao:** 1.0.0

---

## Visao Geral

Este diretorio contem a documentacao estrategica de implementacao modular do IntelliCare.
Cada modulo e desenvolvivel e entregavel de forma independente.

O principio orientador e: **do mais simples ao mais sofisticado**.
Cada entrega gera valor imediato e motivacao para o proximo passo.

---

## Documento Central

[20260304-0900_VISAO_ESTRATEGICA_SEQUENCIAMENTO.md](./20260304-0900_VISAO_ESTRATEGICA_SEQUENCIAMENTO.md)

Leia este documento primeiro. Ele define:
- Mapa de maturidade de todos os modulos
- Sequencia de entrega em 3 ondas
- Dependencias entre modulos
- Modelo comercial por modulo

---

## Sequencia de Desenvolvimento

### ONDA 1 — Quick Wins (Semana 1-2)

> ZILDA e PIERRE rodam em **paralelo**. COMUNICACAO inicia quando qualquer um dos dois terminar.

| Modulo | Tempo Est. | Complexidade | Paralelo? | Pasta |
|--------|-----------|--------------|-----------|-------|
| **ZILDA** — CNES + DATASUS | 1-2 dias | Baixa | ✅ com PIERRE | [ZILDA/](./ZILDA/) |
| **PIERRE** — Pesquisa Cientifica | 2-3 dias | Baixa | ✅ com ZILDA | [PIERRE/](./PIERRE/) |
| **COMUNICACAO** — Fix deps | 3-4 dias | Media | Apos ZILDA ou PIERRE | [COMUNICACAO/](./COMUNICACAO/) |

### ONDA 2 — Core Clinico (Semana 2-4)

| Modulo | Tempo Est. | Complexidade | Pasta |
|--------|-----------|--------------|-------|
| **MINERVA** — OCR + Documentos | 3-5 dias | Media | [MINERVA/](./MINERVA/) |
| **GRAHAME** — FHIR R4 Hardening | 3-5 dias | Media | [GRAHAME/](./GRAHAME/) |
| **GERALDA** — Planos de Cuidado | 5-7 dias | Media | [GERALDA/](./GERALDA/) |

### ONDA 3 — Qualidade e Inteligencia (Semana 4-7)

| Modulo | Tempo Est. | Complexidade | Pasta |
|--------|-----------|--------------|-------|
| **DONABEDIAN** — Indicadores | 4-6 dias | Media | [DONABEDIAN/](./DONABEDIAN/) |
| **NISE** — Chatbot Clinico | 7-10 dias | Alta | [NISE/](./NISE/) |
| **WANDA** — Orquestrador IA | 10-14 dias | Alta | [WANDA/](./WANDA/) |

---

## Estrutura de Cada Modulo

```
<MODULO>/
├── YYYYMMDD-HHMM_ESPECIFICACOES_FUNCIONAIS.md  ← O que faz
├── YYYYMMDD-HHMM_ESPECIFICACOES_TECNICAS.md    ← Como implementar
└── YYYYMMDD-HHMM_PLANO_IMPLEMENTACAO.md        ← Passos + checklist
```

---

## Criterio Universal de Entrega

Um modulo e considerado entregavel quando:
1. `GET /api/v1/health` → 200 OK em producao
2. `pytest -q` → 0 falhas, **>= 75% cobertura (ONDA 1)** / **>= 80% (ONDAS 2 e 3)**
3. `docker compose up` → container healthy
4. Incluido no `scripts/smoke_tests.py`
5. Documentacao atualizada

---

*IntelliCare — Implementacao Modular — 2026-03-04*
