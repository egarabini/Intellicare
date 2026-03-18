---
tipo: especificacao-tecnica
demanda: DEM-039
titulo: Kestra Workflow CarePlanner
fase: 1
sprint: "4.1"
status: pronto-para-dev
planejador: Claude (PLANEJADOR)
criado: 2026-03-17
---

# DEM-039 — Especificação Técnica

> Localização dos arquivos: `C:\Users\egara\INTELLICARE\`

---

## PRÉ-CONDIÇÕES

- DEM-038 Fases A, B, C e D commitadas e passando todos os testes.
- Container `kestra` rodando localmente (`docker compose ps kestra` = running).
- `KESTRA_URL=http://kestra:8080` presente no `.env`.
- Python 3.11+ com `httpx` disponível (já é dependência do core).

---

## BLOCO 1 — Flows Kestra YAML

**Objetivo:** Criar os dois flows que o Kestra executará para cada tipo de jornada.

### Estrutura de arquivos

```
infra/
  kestra/
    flows/
      careplanner_jornada_basica.yml
      careplanner_jornada_video.yml
    seed_flows.py
```

---

### `infra/kestra/flows/careplanner_jornada_basica.yml`

```yaml
id: careplanner_jornada_basica
namespace: intellicare.careplanner
description: |
  Jornada conversacional básica do IntelliCare CarePlanner.
  Abre uma task no IntelliCare, aguarda a resposta do paciente via
  Rocket.Chat (o IntelliCare resume esta execution quando REPLIED),
  e fecha a jornada.

inputs:
  - id: patient_ref
    type: STRING
    description: "Keycloak ID do paciente (sub do JWT Keycloak)"
  - id: task_type
    type: STRING
    description: "Tipo de jornada: ex. ADESAO, MONITORAMENTO, CHECK_IN"
  - id: template_code
    type: STRING
    description: "Código do template de mensagem a enviar"
    defaults: ""
  - id: template_variables
    type: JSON
    description: "Variáveis para substituição no template"
    defaults: "{}"
  - id: contact_phone_e164
    type: STRING
    description: "Telefone do paciente em formato E.164"
    defaults: ""
  - id: tenant_slug
    type: STRING
    description: "Slug do tenant (ex. alfa, beta)"
  - id: intellicare_base_url
    type: STRING
    description: "URL base do IntelliCare (interno Docker)"
    defaults: "http://intellicare-service:8000"

variables:
  # JWT do tenant armazenado no KV Store do Kestra.
  # Chave: intellicare_jwt_{{ inputs.tenant_slug }}
  # Provisionado manualmente ou via script de seed por tenant.
  tenant_jwt: "{{ kv('intellicare_jwt_' + inputs.tenant_slug) }}"

tasks:
  # ── 1. Abre a task no IntelliCare ──────────────────────────────────────────
  - id: open_task
    type: io.kestra.plugin.core.http.Request
    uri: "{{ inputs.intellicare_base_url }}/careplanner/tasks/open"
    method: POST
    contentType: application/json
    headers:
      Authorization: "Bearer {{ vars.tenant_jwt }}"
    body: |
      {
        "kestra_execution_id": "{{ execution.id }}",
        "patient_ref": "{{ inputs.patient_ref }}",
        "task_type": "{{ inputs.task_type }}",
        "contact": {
          "phone_e164": "{{ inputs.contact_phone_e164 }}",
          "role": "PACIENTE"
        },
        "message": {
          "template_code": "{{ inputs.template_code }}",
          "variables": {{ inputs.template_variables }}
        }
      }
    # IntelliCare retorna 202. Kestra não considera 202 como erro.
    allowFailed: false

  # ── 2. Aguarda resposta do paciente ────────────────────────────────────────
  # O IntelliCare chama POST /api/v1/executions/{execution.id}/resume
  # quando o evento REPLIED chega (process_inbound → kestra.resume_execution).
  # timeout = SLA máximo SENT→EXPIRED (72h). Se estourar, o flow falha
  # e o expiry_worker já terá marcado a task como EXPIRED no IntelliCare.
  - id: wait_for_reply
    type: io.kestra.plugin.core.flow.Pause
    timeout: PT72H
    onResume:
      - id: patient_reply
        type: STRING
        required: true
        description: "Conteúdo da resposta do paciente"

  # ── 3. Fecha a jornada ─────────────────────────────────────────────────────
  - id: close_task
    type: io.kestra.plugin.core.http.Request
    uri: >-
      {{ inputs.intellicare_base_url }}/careplanner/tasks/
      {{- outputs.open_task.body | jq('.correlation_id') | trim -}}
      /close
    method: POST
    contentType: application/json
    headers:
      Authorization: "Bearer {{ vars.tenant_jwt }}"
    body: "{}"

outputs:
  - id: correlation_id
    type: STRING
    value: "{{ outputs.open_task.body | jq('.correlation_id') }}"
  - id: patient_reply
    type: STRING
    value: "{{ outputs.wait_for_reply.onResume.patient_reply }}"
  - id: final_status
    type: STRING
    value: "{{ outputs.close_task.body | jq('.status') }}"

errors:
  - id: handle_timeout
    type: io.kestra.plugin.core.log.Log
    level: WARNING
    message: |
      Jornada {{ outputs.open_task.body | jq('.correlation_id') }} expirou
      por timeout (72h sem resposta). IntelliCare expiry_worker já tratou o EXPIRED.
```

---

### `infra/kestra/flows/careplanner_jornada_video.yml`

```yaml
id: careplanner_jornada_video
namespace: intellicare.careplanner
description: |
  Jornada conversacional com videoconsulta do IntelliCare CarePlanner.
  Após a resposta do paciente, abre automaticamente uma sessão Jitsi
  e envia o link de videoconsulta via Rocket.Chat antes de fechar.

inputs:
  - id: patient_ref
    type: STRING
  - id: task_type
    type: STRING
    defaults: "TELECONSULTA"
  - id: template_code
    type: STRING
    defaults: ""
  - id: template_variables
    type: JSON
    defaults: "{}"
  - id: contact_phone_e164
    type: STRING
    defaults: ""
  - id: clinico_ref
    type: STRING
    description: "Keycloak ID do clínico que conduzirá a videoconsulta"
  - id: tenant_slug
    type: STRING
  - id: intellicare_base_url
    type: STRING
    defaults: "http://intellicare-service:8000"

variables:
  tenant_jwt: "{{ kv('intellicare_jwt_' + inputs.tenant_slug) }}"

tasks:
  - id: open_task
    type: io.kestra.plugin.core.http.Request
    uri: "{{ inputs.intellicare_base_url }}/careplanner/tasks/open"
    method: POST
    contentType: application/json
    headers:
      Authorization: "Bearer {{ vars.tenant_jwt }}"
    body: |
      {
        "kestra_execution_id": "{{ execution.id }}",
        "patient_ref": "{{ inputs.patient_ref }}",
        "task_type": "{{ inputs.task_type }}",
        "contact": {
          "phone_e164": "{{ inputs.contact_phone_e164 }}",
          "role": "PACIENTE"
        },
        "message": {
          "template_code": "{{ inputs.template_code }}",
          "variables": {{ inputs.template_variables }}
        }
      }

  - id: wait_for_reply
    type: io.kestra.plugin.core.flow.Pause
    timeout: PT72H
    onResume:
      - id: patient_reply
        type: STRING
        required: true

  # ── Abre sessão Jitsi e envia link ao paciente via Rocket.Chat ─────────────
  - id: open_video_session
    type: io.kestra.plugin.core.http.Request
    uri: "{{ inputs.intellicare_base_url }}/careplanner/consultations/video"
    method: POST
    contentType: application/json
    headers:
      Authorization: "Bearer {{ vars.tenant_jwt }}"
    body: |
      {
        "correlation_id": "{{ outputs.open_task.body | jq('.correlation_id') | trim }}",
        "clinico_ref": "{{ inputs.clinico_ref }}"
      }

  - id: close_task
    type: io.kestra.plugin.core.http.Request
    uri: >-
      {{ inputs.intellicare_base_url }}/careplanner/tasks/
      {{- outputs.open_task.body | jq('.correlation_id') | trim -}}
      /close
    method: POST
    contentType: application/json
    headers:
      Authorization: "Bearer {{ vars.tenant_jwt }}"
    body: "{}"

outputs:
  - id: correlation_id
    type: STRING
    value: "{{ outputs.open_task.body | jq('.correlation_id') }}"
  - id: patient_reply
    type: STRING
    value: "{{ outputs.wait_for_reply.onResume.patient_reply }}"
  - id: patient_video_url
    type: STRING
    value: "{{ outputs.open_video_session.body | jq('.patient_url') }}"
  - id: clinico_video_url
    type: STRING
    value: "{{ outputs.open_video_session.body | jq('.clinico_url') }}"

errors:
  - id: handle_timeout
    type: io.kestra.plugin.core.log.Log
    level: WARNING
    message: "Jornada de vídeo expirou sem resposta do paciente (72h)."
```

---

## BLOCO 2 — Script de Seed dos Flows

**Objetivo:** Publicar os flows no Kestra de forma idempotente ao iniciar o ambiente.

### `infra/kestra/seed_flows.py`

```python
"""
Provisiona os flows do CarePlanner no Kestra via API.
Idempotente: usa PUT /api/v1/flows (cria ou atualiza).

Uso:
    python infra/kestra/seed_flows.py
    # ou com variáveis de ambiente:
    KESTRA_URL=http://localhost:8080 python infra/kestra/seed_flows.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

KESTRA_URL = os.getenv("KESTRA_URL", "http://localhost:8080").rstrip("/")
FLOWS_DIR = Path(__file__).parent / "flows"

FLOW_FILES = [
    "careplanner_jornada_basica.yml",
    "careplanner_jornada_video.yml",
]


def provision_flows() -> None:
    for filename in FLOW_FILES:
        flow_path = FLOWS_DIR / filename
        if not flow_path.exists():
            print(f"[ERRO] Flow não encontrado: {flow_path}")
            sys.exit(1)

        flow_yaml = flow_path.read_text(encoding="utf-8")

        response = httpx.put(
            f"{KESTRA_URL}/api/v1/flows",
            content=flow_yaml,
            headers={"Content-Type": "application/x-yaml"},
            timeout=30,
        )

        if response.status_code in (200, 201):
            print(f"[OK] {filename} provisionado (HTTP {response.status_code})")
        else:
            print(f"[ERRO] {filename} — HTTP {response.status_code}: {response.text[:200]}")
            sys.exit(1)


if __name__ == "__main__":
    print(f"Kestra URL: {KESTRA_URL}")
    provision_flows()
    print("Todos os flows provisionados com sucesso.")
```

---

## BLOCO 3 — `KestraAdapter.trigger_flow()`

**Objetivo:** Adicionar método que inicia uma nova execution Kestra a partir do
IntelliCare (usado pelo endpoint `/journeys/trigger`).

**Arquivo:** `modules/careplanner/adapters/kestra.py`

Adicionar ao final da classe `KestraAdapter`:

```python
async def trigger_flow(
    self,
    namespace: str,
    flow_id: str,
    inputs: dict | None = None,
) -> dict:
    """Dispara uma nova execution de um flow Kestra.

    Args:
        namespace: Namespace Kestra, ex. 'intellicare.careplanner'.
        flow_id: ID do flow, ex. 'careplanner_jornada_basica'.
        inputs: Dicionário de inputs conforme declarados no flow YAML.

    Returns:
        Objeto execution do Kestra com campos: id, state, namespace, flowId.

    Raises:
        httpx.HTTPStatusError: Em caso de 4xx/5xx do Kestra.
    """
    async with httpx.AsyncClient(
        base_url=self._settings.kestra_url.rstrip("/"),
        timeout=self._settings.kestra_timeout,
    ) as client:
        response = await client.post(
            f"/api/v1/executions/{namespace}/{flow_id}",
            json=inputs or {},
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()
```

---

## BLOCO 4 — Endpoint `POST /careplanner/journeys/trigger`

**Objetivo:** Permitir que o GestorUI/ClinicoUI inicie uma jornada sem precisar
acessar o Kestra diretamente.

**Arquivo:** `modules/careplanner/api/routes.py`

### Novo Pydantic model (adicionar com os demais no topo)

```python
class TriggerJourneyRequest(BaseModel):
    patient_ref: str
    task_type: str
    template_code: str = ""
    template_variables: dict = Field(default_factory=dict)
    contact_phone_e164: str = ""
    flow_id: str = "careplanner_jornada_basica"
    # Opcional — só para careplanner_jornada_video
    clinico_ref: str | None = None
```

### Novo endpoint (adicionar ao final do router)

```python
@router.post("/journeys/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_journey(
    body: TriggerJourneyRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    """Inicia uma nova jornada CarePlanner via Kestra.

    Requer role GESTOR ou CLINICO.
    Retorna o execution_id do Kestra e o correlation_id gerado pelo IntelliCare.
    """
    require_role("GESTOR", "CLINICO")(ctx)
    return await service.trigger_journey(ctx, body)
```

### Novo método em `CareplannerService`

```python
async def trigger_journey(
    self,
    ctx: TenantContext,
    body: "TriggerJourneyRequest",
) -> dict:
    """Dispara um flow Kestra que chamará de volta /tasks/open."""
    inputs: dict = {
        "patient_ref": body.patient_ref,
        "task_type": body.task_type,
        "template_code": body.template_code,
        "template_variables": body.template_variables,
        "contact_phone_e164": body.contact_phone_e164,
        "tenant_slug": ctx.tenant_id,
    }
    if body.clinico_ref:
        inputs["clinico_ref"] = body.clinico_ref

    try:
        execution = await self._kestra.trigger_flow(
            namespace="intellicare.careplanner",
            flow_id=body.flow_id,
            inputs=inputs,
        )
    except Exception as exc:
        logger.error("Falha ao acionar Kestra: %s", exc)
        raise api_error(502, "kestra_unavailable", "Kestra indisponível") from exc

    return {
        "ok": True,
        "execution_id": execution.get("id"),
        "flow_id": body.flow_id,
        "status": "CREATED",
    }
```

**Nota:** O `correlation_id` ainda não existe neste momento — ele só é criado quando
o Kestra chamar `open_task`. O response retorna `execution_id` para rastreio; o
chamador pode buscar o `correlation_id` depois em `GET /careplanner/tasks` filtrando
por `kestra_execution_id` (campo disponível na tabela `care_tasks`).

---

## BLOCO 5 — Testes

**Arquivo:** `packages/intellicare-core/tests/test_careplanner_phase_e.py`

```
test_trigger_flow_sucesso                   — trigger_flow chama POST correto
test_trigger_flow_kestra_indisponivel       — httpx erro → api_error 502
test_trigger_journey_endpoint_202           — POST /journeys/trigger → 202
test_seed_flows_idempotente                 — seed_flows.py com Kestra mockado
```

**Critério:** 4 passed / sem regressão nas suítes A, B, C e D.

---

## Commit Final

```
cd C:\Users\egara\INTELLICARE
git add infra/kestra/ modules/careplanner/adapters/kestra.py modules/careplanner/api/routes.py modules/careplanner/services.py packages/intellicare-core/tests/test_careplanner_phase_e.py docs/demandas/DEM-039_KESTRA_CAREPLANNER/
git commit -F commit_msg.txt
git push origin main
```

Mensagem de commit sugerida:
```
feat(careplanner): DEM-039 Kestra Workflow CarePlanner

- flows YAML: careplanner_jornada_basica + careplanner_jornada_video
- seed_flows.py: provisiona flows via Kestra API (idempotente)
- KestraAdapter.trigger_flow(): dispara nova execution Kestra
- POST /careplanner/journeys/trigger: endpoint para GestorUI/ClinicoUI
- test_careplanner_phase_e.py: 4 testes (trigger_flow, 502, endpoint, seed)
```

---

## Notas de Infra — KV Store Kestra

Antes de testar localmente, provisionar o JWT do tenant `alfa` no KV Store do
Kestra. O KV Store é acessado via UI Kestra (`http://localhost:8080`) em
Namespace → intellicare.careplanner → KV Store, ou via API:

```bash
curl -X PUT http://localhost:8080/api/v1/namespaces/intellicare.careplanner/kv/intellicare_jwt_alfa \
  -H "Content-Type: application/json" \
  -d '"<JWT_DO_GESTOR_ALFA>"'
```

O JWT pode ser obtido logando como `gestor.alfa / Demo@1234` no GestorUI e
copiando o Bearer token dos headers das chamadas à API.
