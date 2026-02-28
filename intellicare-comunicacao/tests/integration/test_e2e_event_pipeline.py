from __future__ import annotations

import json
import os
import time
import uuid
from urllib import request as urllib_request

import pytest


ENABLE_E2E = os.getenv("INTELLICARE_ENABLE_E2E", "false").lower() == "true"


@pytest.mark.e2e
@pytest.mark.skipif(not ENABLE_E2E, reason="INTELLICARE_ENABLE_E2E!=true")
def test_e2e_redis_alert_to_matrix_pipeline() -> None:
    redis = pytest.importorskip("redis")

    base_url = os.getenv("INTELLICARE_E2E_BASE_URL", "http://localhost:8010")
    redis_url = os.getenv("INTELLICARE_E2E_REDIS_URL", "redis://localhost:6379")
    stream_prefix = os.getenv("INTELLICARE_E2E_STREAM_PREFIX", "intellicare")
    alert_type = os.getenv("INTELLICARE_E2E_ALERT_TYPE", "alert.created")
    expected_outcome = os.getenv("INTELLICARE_E2E_EXPECT_OUTCOME", "routed_ok").strip().lower()
    room_id = os.getenv("INTELLICARE_E2E_ROOM_ID", "").strip()
    assert room_id, "Defina INTELLICARE_E2E_ROOM_ID para executar o E2E"
    assert expected_outcome in {"routed_ok", "routed_error"}

    patient_id = f"e2e-{uuid.uuid4().hex[:8]}"
    stream = f"{stream_prefix}:{alert_type}"

    _http_post(f"{base_url}/api/v1/events/metrics/reset")

    _http_post(f"{base_url}/api/v1/events/consumer/start")

    _http_post(
        f"{base_url}/api/v1/links/patient-room",
        payload={"patient_id": patient_id, "room_id": room_id},
    )

    client = redis.Redis.from_url(redis_url, decode_responses=True)
    data = {
        "module": "intellicare-oswaldo",
        "patient_id": patient_id,
        "severity": "alta",
        "message": "E2E alerta de teste",
        "alert_type": "e2e-alert",
        "correlation_id": f"corr-{uuid.uuid4().hex[:8]}",
    }
    client.xadd(
        stream,
        {
            "type": alert_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "data": json.dumps(data, ensure_ascii=False),
        },
    )

    deadline = time.time() + 45
    outcome_reached = False
    last_payload: dict | None = None
    while time.time() < deadline:
        metrics = _http_get_json(f"{base_url}/api/v1/events/metrics")
        last_payload = metrics
        same_patient = (metrics.get("last_event") or {}).get("patient_id") == patient_id
        if expected_outcome == "routed_ok" and metrics.get("routed_ok", 0) >= 1 and same_patient:
            outcome_reached = True
            break
        if expected_outcome == "routed_error" and metrics.get("routed_error", 0) >= 1 and same_patient:
            outcome_reached = True
            break
        time.sleep(2)

    assert outcome_reached, (
        f"E2E nao atingiu outcome esperado ({expected_outcome}) no prazo. "
        f"metrics={last_payload}"
    )


def _http_post(url: str, payload: dict | None = None, timeout: int = 10) -> dict:
    body: bytes | None = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib_request.Request(url=url, method="POST", data=body, headers=headers)
    with urllib_request.urlopen(req, timeout=timeout) as response:
        assert response.status == 200
        content = response.read()
    return json.loads(content.decode("utf-8")) if content else {}


def _http_get_json(url: str, timeout: int = 10) -> dict:
    with urllib_request.urlopen(url, timeout=timeout) as response:
        assert response.status == 200
        return json.loads(response.read().decode("utf-8"))
