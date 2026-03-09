# ONDA_11 — Refinamentos

**Data:** 2026-02-24
**Status:** ✅ Concluída (W11-A + W11-B + W11-C)
**Filosofia:** Refinamentos de segurança, terminologia e internacionalização

---

## Visão Geral

A ONDA_11 implementa refinamentos identificados na análise de gap:

1. **WS Token Refresh** — Renovação de token em conexões WebSocket longas
2. **Terminology ($lookup, $validate-code)** — Operações de CodeSystem
3. **Display language overrides (i18n)** — Tradução de conceitos codificados

---

## Objetivos por Workstream

### W11-A — WS Token Refresh (5 dias)
Renovação automática de token em conexões WebSocket para sessões longas (ex: médicos em plantão).
Status de execução (2026-02-25): ✅ Concluída por DEV2

### W11-B — Terminology ($lookup, $validate-code) (7 dias)
Operações CodeSystem/$lookup e CodeSystem/$validate-code conforme FHIR R4.
Status de execução (2026-02-25): ✅ Concluída por DEV2

### W11-C — Display language overrides (i18n) (7 dias)
Override de display em conceitos codificados conforme idioma preferido (Accept-Language).
Status de execução (2026-02-25): ✅ Concluída por DEV2

---

## Estrutura de Documentação

```
ONDA_11/
├── README.md
├── W11-A_WS_TOKEN_REFRESH/
│   ├── ESPECIFICACAO_FUNCIONAL.md
│   ├── ESPECIFICACAO_TECNICA.md
│   ├── PLANO_IMPLEMENTACAO.md
│   └── DIARIO_EXECUCAO.md
├── W11-B_TERMINOLOGY_LOOKUP_VALIDATE/
│   ├── ESPECIFICACAO_FUNCIONAL.md
│   ├── ESPECIFICACAO_TECNICA.md
│   ├── PLANO_IMPLEMENTACAO.md
│   └── DIARIO_EXECUCAO.md
└── W11-C_DISPLAY_LANGUAGE_I18N/
    ├── ESPECIFICACAO_FUNCIONAL.md
    ├── ESPECIFICACAO_TECNICA.md
    ├── PLANO_IMPLEMENTACAO.md
    └── DIARIO_EXECUCAO.md
```

---

## Pré-requisitos

- ONDAS 1-10
- WebSocket subscriptions (W1-B)
- Terminology Service (W5-C)
