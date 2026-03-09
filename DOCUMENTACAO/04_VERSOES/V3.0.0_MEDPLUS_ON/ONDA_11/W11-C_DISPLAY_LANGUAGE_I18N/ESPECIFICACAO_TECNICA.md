# W11-C — Display language overrides (i18n) — Especificação Técnica

**Workstream:** W11-C
**Módulo:** `intellicare-grahame` (Terminology)
**Data:** 2026-02-24

---

## 1. Fluxo

```
Request com Accept-Language: pt-BR, pt;q=0.9, en;q=0.8
    │
    ▼
Parse Accept-Language -> ["pt-BR", "pt", "en"]
    │
    ▼
Para cada conceito/código:
  - Buscar designation onde designation.language in ["pt-BR", "pt", "en"]
  - Ordem de preferência
  - Se encontrado: usar designation.value como display
  - Senão: usar concept.display (default)
```

---

## 2. Estrutura CodeSystem.concept.designation

```json
{
  "concept": [
    {
      "code": "A09",
      "display": "Diarrhea and gastroenteritis",
      "designation": [
        { "language": "pt-BR", "value": "Diarreia e gastroenterite" },
        { "language": "es", "value": "Diarrea y gastroenteritis" }
      ]
    }
  ]
}
```

---

## 3. Algoritmo de seleção

1. Parse Accept-Language (RFC 7231)
2. Ordenar por q-value (maior primeiro)
3. Para cada language na lista:
   - Buscar designation com language exato ou language-REGION (ex: pt-BR -> pt)
4. Fallback: concept.display

---

## 4. Endpoints afetados

- CodeSystem/$lookup
- CodeSystem/$validate-code
- ValueSet/$expand
- ConceptMap/$translate
- Opcional: GET/POST recursos com _elements=display para Coding

---

## 5. Estrutura de Código

```
intellicare-grahame/
├── grahame/
│   ├── utils/
│   │   └── accept_language.py   # NOVO — parse Accept-Language
│   └── services/
│       └── terminology/
│           └── display_resolver.py  # NOVO — resolver display por idioma
```

---

## 6. Variáveis de Ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| DEFAULT_DISPLAY_LANGUAGE | pt-BR | Idioma padrão quando Accept-Language ausente |
| I18N_DISPLAY_ENABLED | true | Habilitar override de display |
