# Plano de Unificação OpenAPI/Swagger

Data: 2026-02-19

## Objetivo

Criar uma documentação única das APIs internas IntelliCare, mantendo cada módulo com seu OpenAPI local e publicando um catálogo central para consulta.

## Escopo inicial

- Módulos com API mapeada no catálogo:
  - `intellicare-comunicacao`
  - `intellicare-conhecimento`
  - `intellicare-donabedian`
  - `intellicare-florence`
  - `intellicare-geralda`
  - `intellicare-grahame`
  - `intellicare-nise`
  - `intellicare-minerva`
  - `intellicare-oswaldo`
  - `intellicare-superz`
  - `intellicare-wanda`
  - `intellicare-zilda`

## Princípios

- OpenAPI por serviço é a fonte de verdade.
- Catálogo central apenas referencia/compõe os specs.
- Versionamento semântico por módulo (`v1`, `v2`, etc.) e changelog.

## Fase 1: Padronização mínima por módulo

1. Confirmar metadados FastAPI em cada app:
   - `title`
   - `version`
   - `description`
2. Padronizar prefixo de API:
   - preferencialmente `/api/v1`
3. Validar disponibilidade dos endpoints de documentação:
   - `/docs`
   - `/openapi.json`

## Fase 2: Exportação dos specs

1. Subir cada serviço em ambiente local/dev.
2. Coletar `openapi.json` por módulo.
3. Salvar em pasta central:
   - `./docs/openapi/<modulo>.openapi.json`

## Fase 3: Catálogo central

1. Criar índice central com links:
   - nome do módulo
   - URL base do serviço
   - URL de `/docs`
   - URL de `/openapi.json`
2. Publicar este índice no repositório:
   - `./docs/API_PORTAL.md`

## Fase 4: Governança

1. Adicionar checklist de PR para módulos com API:
   - atualizar `version`
   - validar schema OpenAPI
   - atualizar changelog de API
2. Validar compatibilidade em CI:
   - lint OpenAPI
   - diff de breaking changes

## Estrutura recomendada de documentação

- `./docs/API_CATALOG.md` (inventário atual por rota)
- `./docs/API_PORTAL.md` (links de acesso por ambiente)
- `./docs/openapi/*.openapi.json` (snapshots de specs)
- `./docs/API_CHANGELOG.md` (histórico de mudanças)

## Entregáveis imediatos (já disponíveis)

- Inventário por rota: `./docs/API_CATALOG.md`
- Base em CSV:
  - `./docs/LEVANTAMENTO_APIS_INTERNAS.csv`
  - `./docs/LEVANTAMENTO_APIS_INTERNAS_UNICO.csv`

## Próximos passos sugeridos

1. Definir quais módulos entram na primeira onda de publicação de specs.
2. Gerar/commitar `openapi.json` desses módulos.
3. Criar `API_PORTAL.md` com links por ambiente (local/dev/hml/prod).
