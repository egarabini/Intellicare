---
tipo: plano-execucao
demanda: DEM-039
titulo: Kestra Workflow CarePlanner
status: pendente
dev: CODEX
criado: 2026-03-17
---

# DEM-039 — Plano de Execução

## Estimativa

Tempo estimado: 2h | Complexidade: média

A DEM não altera schema de banco nem lógica de negócio existente.
O maior risco é a sintaxe do Kestra YAML (expressões `jq` e `onResume`)
e a URL de close_task com interpolação de string multi-linha.

---

## STEPs

### STEP-001 — Criar estrutura de diretórios e flows YAML

**Status:** pendente

Ação:
```
mkdir infra\kestra\flows
```

Criar os dois arquivos exatamente como especificado em `02_TECNICA.md` Bloco 1:
- `infra/kestra/flows/careplanner_jornada_basica.yml`
- `infra/kestra/flows/careplanner_jornada_video.yml`

Critério: arquivos criados e válidos YAML (`python -c "import yaml; yaml.safe_load(open('infra/kestra/flows/careplanner_jornada_basica.yml'))"` sem erro).

---

### STEP-002 — Criar seed_flows.py

**Status:** pendente

Ação: Criar `infra/kestra/seed_flows.py` conforme Bloco 2 de `02_TECNICA.md`.

Critério: `python infra/kestra/seed_flows.py --help` não lança ImportError.
Teste funcional adiado para STEP-006 (requer Kestra rodando).

---

### STEP-003 — Adicionar `trigger_flow()` ao KestraAdapter

**Status:** pendente

Arquivo: `modules/careplanner/adapters/kestra.py`

Ação: Adicionar o método `trigger_flow(namespace, flow_id, inputs)` ao final
da classe, conforme Bloco 3 de `02_TECNICA.md`. Não alterar nenhum método
existente (`resume_execution`, `get_execution`, `health_check`).

Critério: `from modules.careplanner.adapters.kestra import KestraAdapter` sem erro;
mypy sem erros novos no arquivo.

---

### STEP-004 — Adicionar endpoint e service method

**Status:** pendente

Arquivos:
- `modules/careplanner/api/routes.py` — adicionar `TriggerJourneyRequest` e
  `POST /journeys/trigger`
- `modules/careplanner/services.py` — adicionar `trigger_journey()`

Seguir exatamente o Bloco 4 de `02_TECNICA.md`.

Atenção: `require_role` em `routes.py` aceita múltiplos argumentos?
Verificar a assinatura de `require_role` em `intellicare_core.auth.jwt`.
Se aceitar apenas uma role, usar `require_role("GESTOR")` e duplicar o
endpoint para CLINICO, ou ajustar conforme a implementação existente.

Critério: `GET /openapi.json` lista o endpoint `/careplanner/journeys/trigger`.

---

### STEP-005 — Criar test_careplanner_phase_e.py

**Status:** pendente

Arquivo: `packages/intellicare-core/tests/test_careplanner_phase_e.py`

4 testes conforme Bloco 5 de `02_TECNICA.md`:

```python
# test_trigger_flow_sucesso
# Mocka httpx.AsyncClient.post retornando {"id": "exec-123", "state": "RUNNING"}
# Chama adapter.trigger_flow("intellicare.careplanner", "careplanner_jornada_basica", {})
# Verifica que retorna {"id": "exec-123", "state": "RUNNING"}

# test_trigger_flow_kestra_indisponivel
# Mocka httpx para lançar httpx.ConnectError
# Chama service.trigger_journey(ctx, body)
# Verifica que levanta HTTPException 502 com detail.code == "kestra_unavailable"

# test_trigger_journey_endpoint_202
# Usa AsyncClient(app=app, base_url="http://test")
# Mock service.trigger_journey retornando {"ok": True, "execution_id": "x", ...}
# POST /careplanner/journeys/trigger com header Authorization válido
# Verifica status 202

# test_seed_flows_idempotente
# Mocka httpx.put retornando Response(200, ...)
# Chama seed_flows.provision_flows() duas vezes
# Verifica que cada call ao PUT é feita exatamente uma vez por arquivo
```

Critério: `pytest packages/intellicare-core/tests/test_careplanner_phase_e.py -v`
→ 4 passed.

---

### STEP-006 — Smoke test local com Kestra real

**Status:** pendente

Ação (manual — executa no terminal do Eduardo):

```bash
# 1. Verificar Kestra rodando
docker compose ps kestra

# 2. Provisionar flows
python infra/kestra/seed_flows.py

# 3. Verificar flows no Kestra UI
# http://localhost:8080 → Flows → intellicare.careplanner
# Deve aparecer: careplanner_jornada_basica, careplanner_jornada_video

# 4. Provisionar JWT do tenant alfa no KV Store
curl -X PUT http://localhost:8080/api/v1/namespaces/intellicare.careplanner/kv/intellicare_jwt_alfa \
  -H "Content-Type: application/json" \
  -d '"<JWT_GESTOR_ALFA>"'

# 5. Disparar jornada básica via endpoint do IntelliCare
curl -X POST http://localhost:9000/careplanner/journeys/trigger \
  -H "Authorization: Bearer <JWT_GESTOR_ALFA>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_ref": "paciente-teste-001",
    "task_type": "CHECK_IN",
    "template_code": "boas_vindas",
    "tenant_slug": "alfa"
  }'
# Esperado: 202 com execution_id

# 6. Verificar no Kestra UI que a execution está PAUSED (aguardando resposta)
# 7. Verificar no DB que a care_task foi criada com status DISPATCHED ou SENT
```

Critério: execution aparece no Kestra UI com status PAUSED; task no IntelliCare
com status DISPATCHED (dispatcher Redis) ou SENT (se RC respondeu).

---

### STEP-007 — Commit

**Status:** pendente

```bash
cd C:\Users\egara\INTELLICARE

# Escrever mensagem em arquivo temporário
echo feat(careplanner): DEM-039 Kestra Workflow CarePlanner > commit_msg.txt
echo. >> commit_msg.txt
echo - flows YAML: careplanner_jornada_basica + careplanner_jornada_video >> commit_msg.txt
echo - seed_flows.py: provisiona flows via Kestra API (idempotente) >> commit_msg.txt
echo - KestraAdapter.trigger_flow(): dispara nova execution Kestra >> commit_msg.txt
echo - POST /careplanner/journeys/trigger: endpoint GestorUI/ClinicoUI >> commit_msg.txt
echo - test_careplanner_phase_e.py: 4 testes >> commit_msg.txt

del .git\index.lock 2>nul

git add infra\kestra\ modules\careplanner\adapters\kestra.py modules\careplanner\api\routes.py modules\careplanner\services.py packages\intellicare-core\tests\test_careplanner_phase_e.py docs\demandas\DEM-039_KESTRA_CAREPLANNER\

git commit -F commit_msg.txt && del commit_msg.txt
git push origin main
```

Critério: push aceito; CI verde.

---

## Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| Sintaxe `jq` no YAML do Kestra inválida | Média | Testar o flow manualmente no Kestra UI antes de commitar |
| `require_role` aceita apenas uma role | Baixa | Verificar assinatura em `intellicare_core.auth.jwt` e ajustar |
| KV Store não persistido entre restarts Docker | Média | Adicionar ao script de seed ou à documentação de setup |
| `onResume` com campo `patient_reply` não serializa corretamente | Baixa | Validar no smoke test com resume manual via API Kestra |
