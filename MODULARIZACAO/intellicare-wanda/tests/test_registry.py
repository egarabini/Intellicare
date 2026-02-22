"""Testes do ModuleRegistry."""

import pytest
import respx
import httpx

from wanda.discovery.models import ModuleStatus
from wanda.discovery.registry import ModuleRegistry


@pytest.fixture
def small_registry():
    return ModuleRegistry(
        module_urls={
            "mod-a": "http://mod-a:8000",
            "mod-b": "http://mod-b:8000",
        },
        timeout_seconds=2,
    )


class TestDiscover:
    @respx.mock
    @pytest.mark.asyncio
    async def test_discover_all_online(self, small_registry):
        respx.get("http://mod-a:8000/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "mod-a", "version": "1.0.0",
                "capabilities": ["cap1"], "description": "Module A",
            })
        )
        respx.get("http://mod-a:8000/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://mod-b:8000/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "mod-b", "version": "2.0.0",
                "capabilities": ["cap2"],
            })
        )
        respx.get("http://mod-b:8000/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )

        modules = await small_registry.discover()
        assert len(modules) == 2
        assert small_registry.online_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_discover_one_offline(self, small_registry):
        respx.get("http://mod-a:8000/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "mod-a", "version": "1.0.0", "capabilities": [],
            })
        )
        respx.get("http://mod-a:8000/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://mod-b:8000/api/v1/info").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        modules = await small_registry.discover()
        assert len(modules) == 2
        assert small_registry.online_count == 1

        online = small_registry.get_online_modules()
        assert len(online) == 1
        assert online[0].name == "mod-a"

    @respx.mock
    @pytest.mark.asyncio
    async def test_discover_degraded(self, small_registry):
        respx.get("http://mod-a:8000/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "mod-a", "version": "1.0.0", "capabilities": [],
            })
        )
        respx.get("http://mod-a:8000/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "degraded"})
        )
        respx.get("http://mod-b:8000/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "mod-b", "version": "1.0.0", "capabilities": [],
            })
        )
        respx.get("http://mod-b:8000/api/v1/health").mock(
            side_effect=httpx.TimeoutException("timeout")
        )

        modules = await small_registry.discover()
        # mod-a: degraded (health says degraded), mod-b: degraded (health timeout)
        assert modules[0].status == ModuleStatus.DEGRADED
        assert modules[1].status == ModuleStatus.DEGRADED
        # Both still count as "online" (not OFFLINE)
        assert small_registry.online_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_discover_all_offline(self, small_registry):
        respx.get("http://mod-a:8000/api/v1/info").mock(
            side_effect=httpx.ConnectError("refused")
        )
        respx.get("http://mod-b:8000/api/v1/info").mock(
            side_effect=httpx.ConnectError("refused")
        )

        modules = await small_registry.discover()
        assert small_registry.online_count == 0


class TestCallModule:
    @respx.mock
    @pytest.mark.asyncio
    async def test_call_get(self, small_registry):
        # First discover
        respx.get("http://mod-a:8000/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "mod-a", "version": "1.0.0", "capabilities": [],
            })
        )
        respx.get("http://mod-a:8000/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://mod-b:8000/api/v1/info").mock(
            side_effect=httpx.ConnectError("refused")
        )
        await small_registry.discover()

        # Then call
        respx.get("http://mod-a:8000/api/v1/diseases").mock(
            return_value=httpx.Response(200, json={"data": ["CKD", "DM2"]})
        )

        resp = await small_registry.call_module("mod-a", "/api/v1/diseases")
        assert resp.success
        assert resp.data == {"data": ["CKD", "DM2"]}

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_post(self, small_registry):
        respx.get("http://mod-a:8000/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "mod-a", "version": "1.0.0", "capabilities": [],
            })
        )
        respx.get("http://mod-a:8000/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://mod-b:8000/api/v1/info").mock(
            side_effect=httpx.ConnectError("refused")
        )
        await small_registry.discover()

        respx.post("http://mod-a:8000/api/v1/analyze").mock(
            return_value=httpx.Response(200, json={"result": "ok"})
        )

        resp = await small_registry.call_module(
            "mod-a", "/api/v1/analyze", method="POST", payload={"query": "test"}
        )
        assert resp.success

    @pytest.mark.asyncio
    async def test_call_unknown_module(self, small_registry):
        resp = await small_registry.call_module("unknown", "/api/v1/test")
        assert not resp.success
        assert "nao encontrado" in resp.error

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_offline_module(self, small_registry):
        respx.get("http://mod-a:8000/api/v1/info").mock(
            side_effect=httpx.ConnectError("refused")
        )
        respx.get("http://mod-b:8000/api/v1/info").mock(
            side_effect=httpx.ConnectError("refused")
        )
        await small_registry.discover()

        resp = await small_registry.call_module("mod-a", "/api/v1/test")
        assert not resp.success
        assert "offline" in resp.error

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_timeout(self, small_registry):
        respx.get("http://mod-a:8000/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "mod-a", "version": "1.0.0", "capabilities": [],
            })
        )
        respx.get("http://mod-a:8000/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://mod-b:8000/api/v1/info").mock(
            side_effect=httpx.ConnectError("refused")
        )
        await small_registry.discover()

        respx.get("http://mod-a:8000/api/v1/slow").mock(
            side_effect=httpx.TimeoutException("timeout")
        )

        resp = await small_registry.call_module("mod-a", "/api/v1/slow")
        assert not resp.success
        assert "Timeout" in resp.error


class TestProperties:
    @respx.mock
    @pytest.mark.asyncio
    async def test_get_module(self, small_registry):
        respx.get("http://mod-a:8000/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "mod-a", "version": "1.0.0", "capabilities": ["cap1"],
            })
        )
        respx.get("http://mod-a:8000/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://mod-b:8000/api/v1/info").mock(
            side_effect=httpx.ConnectError("refused")
        )
        await small_registry.discover()

        m = small_registry.get_module("mod-a")
        assert m is not None
        assert m.version == "1.0.0"
        assert small_registry.get_module("nope") is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_modules_with_capability(self, small_registry):
        respx.get("http://mod-a:8000/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "mod-a", "version": "1.0.0", "capabilities": ["cap1", "cap2"],
            })
        )
        respx.get("http://mod-a:8000/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get("http://mod-b:8000/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "mod-b", "version": "1.0.0", "capabilities": ["cap2", "cap3"],
            })
        )
        respx.get("http://mod-b:8000/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        await small_registry.discover()

        cap2_mods = small_registry.get_modules_with_capability("cap2")
        assert len(cap2_mods) == 2

        cap1_mods = small_registry.get_modules_with_capability("cap1")
        assert len(cap1_mods) == 1
        assert cap1_mods[0].name == "mod-a"

        cap99 = small_registry.get_modules_with_capability("cap99")
        assert len(cap99) == 0

    @pytest.mark.asyncio
    async def test_last_discovery_none(self, small_registry):
        assert small_registry.last_discovery is None
