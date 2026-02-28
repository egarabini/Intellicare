"""W11-A tests for websocket token refresh helpers."""

from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import time

import pytest
from fastapi.websockets import WebSocketState

_WS_HANDLER_PATH = (
    Path(__file__).resolve().parents[1] / "comunicacao" / "subscriptions" / "ws_handler.py"
)
_SPEC = importlib.util.spec_from_file_location("ws_handler_under_test", _WS_HANDLER_PATH)
ws_handler = importlib.util.module_from_spec(_SPEC)
assert _SPEC is not None and _SPEC.loader is not None
_SPEC.loader.exec_module(ws_handler)


class _FakeWebSocket:
    def __init__(self) -> None:
        self.client_state = WebSocketState.CONNECTED
        self.sent: list[dict] = []
        self.closed: tuple[int, str] | None = None

    async def send_json(self, data: dict) -> None:
        self.sent.append(data)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)


def _jwt_with_exp(exp: int, iss: str | None = None) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).decode().rstrip("=")
    payload_obj = {"exp": exp}
    if iss:
        payload_obj["iss"] = iss
    payload = base64.urlsafe_b64encode(json.dumps(payload_obj).encode()).decode().rstrip("=")
    return f"Bearer {header}.{payload}.sig"


def test_parse_and_validate_token_success():
    token = _jwt_with_exp(int(time.time()) + 600)
    parsed = ws_handler._parse_and_validate_token(token)
    assert parsed["ok"] is True
    assert float(parsed["exp"]) > time.time()


def test_parse_and_validate_token_expired():
    token = _jwt_with_exp(int(time.time()) - 60)
    parsed = ws_handler._parse_and_validate_token(token)
    assert parsed["ok"] is False
    assert "expired" in str(parsed["error"]).lower()


@pytest.mark.asyncio
async def test_refresh_required_emitted():
    ws = _FakeWebSocket()
    context = {
        "token_exp": float(time.time() + 120),
        "refresh_required_sent": False,
        "last_refresh_ts": 0.0,
        "token": "x",
    }
    should_close = await ws_handler._enforce_token_lifecycle(ws, context)
    assert should_close is False
    assert any(m.get("type") == "refresh-required" for m in ws.sent)


@pytest.mark.asyncio
async def test_connection_closed_when_expired():
    ws = _FakeWebSocket()
    context = {
        "token_exp": float(time.time() - 1),
        "refresh_required_sent": False,
        "last_refresh_ts": 0.0,
        "token": "x",
    }
    should_close = await ws_handler._enforce_token_lifecycle(ws, context)
    assert should_close is True
    assert ws.closed is not None
    assert ws.closed[0] == 4001
