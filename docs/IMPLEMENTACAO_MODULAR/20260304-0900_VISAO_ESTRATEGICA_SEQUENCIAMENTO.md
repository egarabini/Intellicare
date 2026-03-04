# Visao Estrategica — Sequenciamento Modular IntelliCare
**Data:** 2026-03-04
**Versao:** 1.0.0
**Status:** Ativo

---

## Principio Orientador

> **Do mais simples ao mais sofisticado.**
> Cada modulo entregue gera valor imediato, motivacao para o proximo passo
> e prova de conceito comercial independente.

---

## Mapa de Maturidade dos Modulos

| Modulo | Porta | Estado Atual | Complexidade | Tempo Est. | Valor Comercial |
|--------|-------|-------------|--------------|------------|-----------------|
| **ZILDA** | 8007 | Base implementada, dados publicos | ⭐ Baixa | 1-2 dias | Contexto territorial |
| **PIERRE** | 8009 | Estrutura criada, sem impl. core | ⭐ Baixa | 2-3 dias | Evidencia clinica |
| **MINERVA** | 8008 | Spec OK, upload/parse basico | ⭐⭐ Media | 3-5 dias | Digitalizacao docs |
| **GRAHAME** | 8012 | Endpoints FHIR funcionais | ⭐⭐ Media | 3-5 dias | Interoperabilidade |
| **GERALDA** | 8006 | In-memory, precisa persistencia | ⭐⭐ Media | 5-7 dias | Cuidado longitudinal |
| **COMUNICACAO** | 8005 | 133 testes, deps quebradas | ⭐⭐ Media | 3-4 dias | Canal paciente |
| **DONABEDIAN** | 8003 | Piloto feito, sem API exposta | ⭐⭐ Media | 4-6 dias | Qualidade/auditoria |
| **NISE** | 8013 | Documentado, sem impl. Flowise | ⭐⭐⭐ Alta | 7-10 dias | Chatbot clinico |
| **WANDA** | 8004 | Orquestrador parcial, LangGraph | ⭐⭐⭐ Alta | 10-14 dias | Inteligencia central |

---

## Sequencia Recomendada de Entrega

### ONDA 1 — Quick Wins (Semana 1-2)
Modulos que podem ser finalizados rapidamente, cada um entregavel standalone.

```
ZILDA ∥ PIERRE  →  COMUNICACAO (fix deps)
(paralelo)          (inicia quando qualquer um dos dois terminar)
```

**Por que este sequenciamento:**
- ZILDA e PIERRE nao tem dependencia entre si — rodam em paralelo pelo mesmo dev ou devs distintos
- COMUNICACAO: infra ja pronta, so precisa corrigir dependencias quebradas; inicia apos o primeiro modulo paralelo estar entregue

---

### ONDA 2 — Core Clinico (Semana 2-4)
Modulos com maior valor clinico. **Pode iniciar em paralelo com ONDA 1** — sem dependencia entre ondas.

```
MINERVA ∥ GRAHAME  →  GERALDA
(paralelo)              fase core: independente
                        fase FHIR: depende GRAHAME pronto
```

**Regras de paralelismo:**
- MINERVA e GRAHAME nao tem dependencia entre si — rodam em paralelo
- GERALDA: fase 1 (PostgreSQL) independente, pode comecar junto; fase 3 (FHIR CarePlan) aguarda GRAHAME
- ONDA 2 pode comecar ANTES da ONDA 1 terminar — nenhum modulo da ONDA 2 depende de ZILDA, PIERRE ou COMUNICACAO

---

### Timeline Real (com paralelismo completo)

```
Dia:      1    2    3    4    5    6    7    8    9   10   11   12   13   14
          ─────────────────────────────────────────────────────────────────
ZILDA     ████████
PIERRE    ████████████
MINERVA   ████████████████
GRAHAME   ████████████████
COMUNICAO           ████████████
GERALDA   (fase1)████████████ (fhir)████████████
          ─────────────────────────────────────────────────────────────────
DONABEDI                              ████████████████
NISE                                           ████████████████████
WANDA                                                    ████████████████████
```

> A ONDA 2 pode comecar no Dia 1 junto com ONDA 1.
> A ONDA 3 aguarda GRAHAME + GERALDA funcionais (dados para calcular indicadores).

---

### ONDA 3 — Qualidade e Inteligencia (Semana 4-7)
Modulos que agregam inteligencia sobre o core clinico.

```
DONABEDIAN → NISE → WANDA (integracao completa)
```

**Por que esta ordem:**
- DONABEDIAN: indicadores sobre dados ja persistidos (Grahame/Geralda)
- NISE: chatbot treinado com protocolos do knowledge base
- WANDA: orquestra tudo com LangGraph + MCP (PIERRE + MINERVA)

---

## Criterios de Entrega por Modulo

Cada modulo so e considerado **entregavel** quando:

1. **Health check** `GET /api/v1/health` responde 200 em producao
2. **Testes passando** >= 75% cobertura (ONDA 1) / >= 80% cobertura (ONDAS 2 e 3), 0 falhas criticas
3. **Docker funcionando** `docker compose up` sobe sem erros
4. **Documentacao** ESPECIFICACOES_FUNCIONAIS + TECNICAS + PLANO atualizados
5. **Smoke test** incluido no `scripts/smoke_tests.py`

> **Nota de cobertura:** ONDA 1 usa 75% porque os modulos tem muita interacao com APIs externas
> (DATASUS, PubMed, WAHA) que sao mockadas nos testes. ONDAS 2 e 3 tem logica de negocio
> mais densa (persistencia, FHIR, LangGraph) que justifica o limiar mais alto de 80%.

---

## Dependencias Entre Modulos

```
ZILDA ──────────────────────────────────► standalone
PIERRE ─────────────────────────────────► standalone
COMUNICACAO ─────────────────────────────► Redis (infra)
MINERVA ────────────────────────────────► Ollama (opcional, tem fallback)
GRAHAME ────────────────────────────────► PostgreSQL
GERALDA ────────────────────────────────► PostgreSQL + GRAHAME
DONABEDIAN ─────────────────────────────► GRAHAME + GERALDA (dados)
NISE ───────────────────────────────────► Flowise + COMUNICACAO
WANDA ──────────────────────────────────► TODOS os modulos
```

---

## Modelo Comercial por Modulo

| Modulo | Caso de Uso Comercial | Tipo de Cliente |
|--------|----------------------|-----------------|
| ZILDA | Mapeamento de rede assistencial | Secretarias de saude, gestoras |
| PIERRE | Evidence-based medicine | Hospitais universitarios, AME |
| MINERVA | Digitalizacao de prontuarios fisicos | Clinicas, UBS sem prontuario eletronico |
| GRAHAME | Interoperabilidade FHIR com outros sistemas | Redes hospitalares, planos de saude |
| GERALDA | Gestao de cronicas e adesao terapeutica | APS, NASF, programas de saude |
| COMUNICACAO | Engajamento e lembretes ao paciente | Qualquer estabelecimento |
| DONABEDIAN | Auditoria e acreditacao | Gestoras, operadoras, ANS |
| NISE | Assistente virtual clinico | Telessaude, pronto-atendimento |
| WANDA | Plataforma AI completa | Grandes redes, secretarias estaduais |

---

## Pasta de Cada Modulo

Cada pasta em `docs/IMPLEMENTACAO_MODULAR/<MODULO>/` contem:

```
<MODULO>/
├── YYYYMMDD-HHMM_ESPECIFICACOES_FUNCIONAIS.md   ← O que o modulo faz
├── YYYYMMDD-HHMM_ESPECIFICACOES_TECNICAS.md     ← Como implementar
└── YYYYMMDD-HHMM_PLANO_IMPLEMENTACAO.md         ← Passos e checkpoints
```

---

*Documento gerado em 2026-03-04 — IntelliCare Estrategia Modular v1.0*
