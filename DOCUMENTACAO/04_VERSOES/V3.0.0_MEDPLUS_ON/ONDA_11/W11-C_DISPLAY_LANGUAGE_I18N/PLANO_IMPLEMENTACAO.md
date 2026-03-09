# W11-C — Display language overrides (i18n) — Plano de Implementação

**Workstream:** W11-C
**Estimativa:** 7 dias
**Responsável:** DEV1 (execução DEV2 em 2026-02-25)
**Status Atual:** ✅ Concluído

---

## Ordem de Execução

| # | Task | Dias | Depende |
|---|------|------|---------|
| 1 | accept_language parser (RFC 7231) | 1 | — |
| 2 | DisplayResolver (designation por language) | 2 | 1 |
| 3 | Integrar em $lookup e $validate-code | 1 | 2 |
| 4 | Integrar em $expand e $translate | 1 | 2 |
| 5 | Testes + documentação | 2 | 3-4 |

---

## Passo a Passo

### Passo 1: accept_language parser
- Função parse_accept_language(header) -> List[str]
- Ordenar por q-value
- Tratar pt-BR, pt, en, etc.

### Passo 2: DisplayResolver
- resolve_display(concept, languages) -> str
- concept pode ter display e designation[]
- Buscar designation.language in languages
- Fallback para concept.display

### Passo 3: $lookup e $validate-code
- Extrair Accept-Language do request
- Ao retornar display: usar DisplayResolver
- Passar languages para LookupService

### Passo 4: $expand e $translate
- $expand: para cada conceito no resultado, resolver display
- $translate: para match, resolver display no idioma
- Garantir que response inclua display correto

### Passo 5: Testes
- test_accept_language_parser
- test_display_resolver_pt_br
- test_display_resolver_fallback
- test_lookup_with_accept_language
- test_expand_with_accept_language

---

## Checklist de Entrega

- [x] Accept-Language parseado corretamente
- [x] DisplayResolver funcional
- [x] $lookup retorna display no idioma
- [x] $validate-code retorna display no idioma
- [x] $expand retorna displays no idioma
- [x] $translate retorna match display no idioma
- [x] Fallback para default quando idioma não disponível
- [x] Testes passando

---

## Evidências de Execução (2026-02-25)

### Implementação
- Parser RFC7231:
  - `intellicare-grahame/grahame/utils/accept_language.py`
- Resolver de display por idioma:
  - `intellicare-grahame/grahame/services/display_resolver.py`
- Integração nas operações de Terminology:
  - `intellicare-grahame/grahame/api/routes/terminology_routes.py`

### Cobertura funcional
- `Accept-Language` aplicado em:
  - `CodeSystem/$lookup`
  - `CodeSystem/$validate-code`
  - `ValueSet/$expand`
  - `ValueSet/$validate-code`
  - `ConceptMap/$translate`
- Fallback para display padrão quando não há designation no idioma solicitado.

### Testes
- Arquivo:
  - `intellicare-grahame/tests/test_onda11_terminology.py`
- Resultado validado junto da suíte de regressão da ONDA 10:
  - `14 passed`
