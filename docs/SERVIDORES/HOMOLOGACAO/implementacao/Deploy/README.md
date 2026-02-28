# Deploy — Versões e Módulos

Pastas para cada deploy de versão ou módulo, seguindo `docs/NORMAS_E_PADROES/20260221-0714_PADRAO_NOMENCLATURA_DOCUMENTOS.md`.

---

## Padrão de nomenclatura

| Tipo | Formato da pasta | Exemplo |
|------|------------------|---------|
| **Deploy de versão** | `YYYYMMDD-HHMM_DEPLOY_VX.Y.Z` | `20260221-1430_DEPLOY_V1.0.0` |
| **Deploy de módulo** | `YYYYMMDD-HHMM_DEPLOY_MODULO_<NOME>` | `20260221-1500_DEPLOY_MODULO_FLORENCE` |

---

## Regras

1. **YYYYMMDD-HHMM**: data e hora do deploy (24h).
2. **TITULO**: maiúsculas, `_` entre palavras, sem acentos.
3. Cada pasta deve conter:
   - `README.md` — resumo do deploy
   - `YYYYMMDD-HHMM_RELATORIO_EXECUCAO.md` — log da execução (opcional)

---

## Exemplos de pastas (criar ao executar deploy)

```
20260221-1430_DEPLOY_V1.0.0/
20260221-1500_DEPLOY_MODULO_FLORENCE/
20260222-0900_DEPLOY_V1.1.0/
```
