---
tipo: briefing-completo
demanda: DEM-051
titulo: Observabilidade Multicanal — Healthcheck + Grafana por Canal
dev: DEV-2
estimativa: 2.5h
prerequisito: DEM-047/048/049 commitadas
---

# DEM-051 — Observabilidade Multicanal

## Contexto

O CarePlanner tem 4 canais ativos mas o Grafana só mostra métricas agregadas.
Se o Evolution API cair silenciosamente, o gestor não sabe — só descobre quando
uma jornada falha. Esta DEM adiciona visibilidade operacional por canal.

## Arquivos a modificar/criar

| Arquivo | Tipo |
|---------|------|
| `modules/careplanner/api/routes.py` | Modificar — endpoint `/health/adapters` |
| `modules/careplanner/services.py` | Modificar — método `health_check_adapters()` |
| `modules/careplanner/metrics.py` | Modificar — label `channel` nas métricas |
| `infra/grafana/provisioning/dashboards/careplanner-overview.json` | Modificar — 4 novos panels |

---

## STEP-001 — Endpoint `GET /health/adapters`

Em `modules/careplanner/api/routes.py`:

```python
@router.get("/health/adapters", status_code=200)
async def adapters_health(
    service: CareplannerService = Depends(get_service),
) -> dict:
    """Retorna status de conectividade de cada adapter de canal."""
    return await service.health_check_adapters()
```

---

## STEP-002 — `health_check_adapters()` em `services.py`

```python
async def health_check_adapters(self) -> dict[str, str]:
    results = {}

    # RocketChat
    try:
        await self._rc.login_bot()
        results["rocketchat"] = "ok"
    except Exception:
        results["rocketchat"] = "degraded"

    # Evolution API (WhatsApp)
    try:
        client = await self._whatsapp._get_client()
        r = await client.get(f"/instance/connectionState/{self._settings.evolution_instance_name}")
        state = r.json().get("instance", {}).get("state", "unknown")
        results["whatsapp"] = "ok" if state == "open" else f"degraded:{state}"
    except Exception:
        results["whatsapp"] = "degraded"

    # Listmonk (Email)
    try:
        client = await self._email._get_client()
        r = await client.get("/api/health")
        results["email"] = "ok" if r.status_code == 200 else "degraded"
    except Exception:
        results["email"] = "degraded"

    # Jasmin (SMS)
    try:
        client = await self._sms._get_client()
        r = await client.get(
            "/send",
            params={
                "username": self._settings.jasmin_username,
                "password": self._settings.jasmin_password,
                "to": "0", "from": "TEST", "content": "ping",
            }
        )
        # Jasmin retorna "Error" para número inválido mas conexão está OK
        results["sms"] = "ok" if "Error" in r.text or r.status_code == 200 else "degraded"
    except Exception:
        results["sms"] = "degraded"

    return results
```

---

## STEP-003 — Label `channel` nas métricas existentes

Em `modules/careplanner/metrics.py`, adicionar `channel` como label nas
métricas de dispatch:

```python
# ANTES:
careplanner_dispatch_total = Counter(
    "careplanner_dispatch_total",
    "Total de mensagens despachadas",
    ["tenant_slug", "status"],
)

# DEPOIS:
careplanner_dispatch_total = Counter(
    "careplanner_dispatch_total",
    "Total de mensagens despachadas",
    ["tenant_slug", "status", "channel"],   # <- novo label
)
```

Atualizar todos os `.labels(...)` que chamam essa métrica em `services.py`
e `dispatcher.py` para incluir `channel=task.channel.value`.

⚠️ Buscar todas as chamadas: `grep -rn "careplanner_dispatch_total.labels" modules/`

---

## STEP-004 — 4 novos panels no Grafana

Editar `infra/grafana/provisioning/dashboards/careplanner-overview.json`.
Adicionar ao final do array `panels` (incrementar `id` a partir do último existente):

**Panel 1 — Disparos por Canal (stacked bar):**
```json
{
  "title": "Disparos por Canal",
  "type": "barchart",
  "options": {"stacking": "normal"},
  "targets": [{
    "expr": "sum by (channel) (increase(careplanner_dispatch_total[1h]))",
    "legendFormat": "{{channel}}"
  }]
}
```

**Panel 2 — Taxa de Falha por Canal:**
```json
{
  "title": "Taxa de Falha por Canal (%)",
  "type": "timeseries",
  "targets": [{
    "expr": "sum by (channel) (rate(careplanner_dispatch_total{status='FAILED'}[5m])) / sum by (channel) (rate(careplanner_dispatch_total[5m])) * 100",
    "legendFormat": "{{channel}}"
  }]
}
```

**Panel 3 — Latência p95 por Canal:**
```json
{
  "title": "Latência p95 Dispatch→Sent por Canal",
  "type": "timeseries",
  "targets": [{
    "expr": "histogram_quantile(0.95, sum by (channel, le) (rate(careplanner_dispatch_to_sent_seconds_bucket[5m])))",
    "legendFormat": "p95 {{channel}}"
  }]
}
```

**Panel 4 — Status dos Adapters (stat):**
```json
{
  "title": "Health Adapters",
  "type": "stat",
  "description": "Atualizar manualmente via /health/adapters — integração futura com blackbox_exporter",
  "options": {"colorMode": "background"},
  "targets": [{
    "expr": "up{job=~'careplanner.*'}",
    "legendFormat": "{{job}}"
  }]
}
```

---

## STEP-005 — Testes

```python
# packages/intellicare-core/tests/test_careplanner_health.py
@pytest.mark.asyncio
async def test_health_adapters_returns_all_channels(client, gestor_token):
    resp = await client.get(
        "/api/v1/careplanner/health/adapters",
        headers={"Authorization": f"Bearer {gestor_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"rocketchat", "whatsapp", "email", "sms"}
    # Em CI todos os adapters estarão degraded — verificar estrutura, não valor
    for v in body.values():
        assert isinstance(v, str)
```

---

## STEP-006 — Commit

```
feat(careplanner): DEM-051 healthcheck adapters + label channel no Grafana
```
