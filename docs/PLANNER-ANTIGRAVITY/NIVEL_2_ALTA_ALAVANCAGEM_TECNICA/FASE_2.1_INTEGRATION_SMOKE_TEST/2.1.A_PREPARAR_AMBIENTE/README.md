# 2.1.A - Preparar Ambiente (Full Stack)

**Data de início:** 2026-02-24
**Responsável:** DEV2
**Status:** ✅ CONCLUÍDO

## Objetivo

Garantir que o `docker compose -f docker-compose.full.yml up -d --build` consiga compilar todas as imagens do stack completo.

## Ações executadas

- Correções de context/build no `docker-compose.full.yml` (módulos `ocr`, `pierre`, `admin`, `nise`).
- Ajustes de Dockerfile para resolver dependências locais entre módulos.
- Alinhamento de dependências Python em `intellicare-admin`, `intellicare-gestor`, `intellicare-grahame`.
- Ajuste de build do portal para smoke (`vite build` no lugar de `tsc -b && vite build`).

## Resultado

- ✅ Todas as imagens principais do stack foram compiladas com sucesso.
- ✅ `docker compose ... up -d --build` avançou até criação dos containers.
- ⚠️ Persistem falhas de runtime em parte dos serviços (registradas em 2.1.B).

## Log

- `20260224-0950_PREPARACAO_AMBIENTE.md`
