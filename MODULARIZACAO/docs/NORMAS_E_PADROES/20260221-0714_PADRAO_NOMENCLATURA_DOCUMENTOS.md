# Padrao de Nomenclatura de Documentos

Data: 2026-02-21

## Objetivo

Padronizar nomes de arquivos de documentacao para que a ordem cronologica seja visivel ao listar diretorios.

## Padrao obrigatorio

`YYYYMMDD-HHMM_TITULO.md`

Onde:
- `YYYYMMDD`: data no formato ano, mes, dia
- `HHMM`: hora e minuto (24h)
- `TITULO`: titulo curto em maiusculas, com `_` entre palavras
- extensao: `.md`

## Regras

1. Nao usar espacos no nome do arquivo.
2. Nao usar acentos ou caracteres especiais no `TITULO`.
3. Usar `_` para separar palavras no `TITULO`.
4. A fase nao precisa aparecer no nome do arquivo quando ja estiver no caminho do diretorio.
5. Ao criar nova versao de documento, gerar novo arquivo com novo timestamp.

## Exemplos

- `20260219-0923_ESPECIFICACAO_FUNCIONAL.md`
- `20260219-0925_ESPECIFICACAO_TECNICA.md`
- `20260219-0929_PLANO_IMPLEMENTACAO.md`
- `20260220-1846_RELATORIO_EXECUCAO.md`

## Beneficio esperado

Com esse padrao, a listagem por nome ja representa a sequencia temporal de criacao/evolucao dos documentos.
