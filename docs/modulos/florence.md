---
tipo: nota-modulo
modulo: florence
porto: 8001
fase: 3
sprint: "3.x"
status: pendente
dem_principal: TBD
score_v2: "1/10"
tags: [fase-3, florence, rag, protocolos]
---

# Módulo: florence

**Responsabilidade:** Biblioteca especializada de protocolos clínicos via RAG.
V2: score 1/10 (existia só no nome). V3: reconstruída do zero.

---

## Distinção em relação ao módulo `cuidado`

| `cuidado` | `florence` |
|-----------|-----------|
| Fluxo clínico (o que fazer com o protocolo) | Biblioteca especializada (onde buscar o protocolo) |
| Interface para o profissional | Fonte de conhecimento para o cuidado |
| RAG genérico por tenant | Protocolos por programa, especialidade, vertical |

Florence é a **biblioteca**. Cuidado é o **fluxo**. Em runtime, são módulos
separados mas `cuidado` pode delegar buscas especializadas a `florence`.

---

## O que entrega

- Base de protocolos clínicos especializados (SBEM, MS, CFM, SBC)
- Busca semântica por programa e especialidade
- Referências rastreáveis (fonte + data de publicação + versão)
- Pipeline de atualização de protocolos (re-ingestão automática)

## Dependências

- [[decisoes/ADR-003-rag-slm-pgvector]]
- Módulo cuidado funcional (DEM-013)
- Pipeline ingest_docs.py (DEM-002)
- Protocolos indexados (DEM-014)
