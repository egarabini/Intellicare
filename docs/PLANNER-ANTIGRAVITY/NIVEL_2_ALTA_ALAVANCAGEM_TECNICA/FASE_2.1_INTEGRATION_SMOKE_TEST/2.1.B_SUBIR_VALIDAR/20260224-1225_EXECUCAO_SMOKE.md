# LOG - 2.1.B Subir e Validar

## 2026-02-24 12:25

### Smoke test consolidado

Comando:

```powershell
$env:PYTHONUTF8='1'
python scripts\smoke_tests.py --json docs\PLANNER-ANTIGRAVITY\NIVEL_2_ALTA_ALAVANCAGEM_TECNICA\FASE_2.1_INTEGRATION_SMOKE_TEST\2.1.B_SUBIR_VALIDAR\20260224-1225_SMOKE_REPORT.json
```

Resultado:

- Total: 16
- Saudáveis: 10
- Com problemas: 6
- Taxa de sucesso: 62.5%

### Serviços com problema e evidência

1. `admin`
- Estado: `Created`
- Evidência: falha ao iniciar processo com `exec: "uvicorn": executable file not found in $PATH`

2. `comunicacao`
- Estado: `Restarting`
- Evidência: `ModuleNotFoundError: No module named 'psycopg2'`

3. `gestor`
- Estado: `Restarting`
- Evidência: `ModuleNotFoundError: No module named 'redis'`

4. `grahame`
- Estado: `Restarting`
- Evidência: `ModuleNotFoundError: No module named 'redis'`

5. `pierre`
- Estado: `Up (unhealthy)`
- Evidência: `ModuleNotFoundError: No module named 'intellicare_core'`

6. `oswaldo`
- Estado: `Restarting`
- Evidência: `sqlalchemy.exc.MissingGreenlet` no startup e health retornando `HTTP 404`

### Observações

- `portal` passou a subir após ajuste de build para `vite build`.
- `nise` e `wanda` passaram a subir e ficaram `healthy`.
