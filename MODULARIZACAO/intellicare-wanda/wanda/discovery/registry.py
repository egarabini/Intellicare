"""Module registry — discovers and manages IntelliCare module instances via HTTP."""

import time
from datetime import datetime
from typing import Optional

import httpx

from wanda.discovery.models import ModuleInfo, ModuleResponse, ModuleStatus


class ModuleRegistry:
    """Discovers and manages IntelliCare module instances."""

    def __init__(
        self,
        module_urls: dict[str, str],
        timeout_seconds: int = 5,
    ):
        self._module_urls = module_urls
        self._timeout = timeout_seconds
        self._modules: dict[str, ModuleInfo] = {}
        self._last_discovery: Optional[datetime] = None
        self._circuit_breaker_manager = None
        self._retry_policy = None
        self._timeout_manager = None
        self._fallback_manager = None

    def configure_resilience(
        self,
        circuit_breaker_manager=None,
        retry_policy=None,
        timeout_manager=None,
        fallback_manager=None,
    ) -> None:
        self._circuit_breaker_manager = circuit_breaker_manager
        self._retry_policy = retry_policy
        self._timeout_manager = timeout_manager
        self._fallback_manager = fallback_manager

    @property
    def has_resilience(self) -> bool:
        return any(
            item is not None
            for item in (
                self._circuit_breaker_manager,
                self._retry_policy,
                self._timeout_manager,
                self._fallback_manager,
            )
        )

    async def discover(self) -> list[ModuleInfo]:
        """Query /api/v1/info from each configured module. Returns list of discovered modules."""
        discovered = []

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for name, base_url in self._module_urls.items():
                module = await self._probe_module(client, name, base_url)
                self._modules[name] = module
                discovered.append(module)

        self._last_discovery = datetime.now()
        return discovered

    async def _probe_module(
        self, client: httpx.AsyncClient, name: str, base_url: str
    ) -> ModuleInfo:
        """Probe a single module for info and health."""
        module = ModuleInfo(name=name, base_url=base_url)

        # Try /api/v1/info
        try:
            resp = await client.get(f"{base_url}/api/v1/info")
            if resp.status_code == 200:
                data = resp.json()
                module.version = data.get("version", "")
                module.description = data.get("description", "")
                module.capabilities = data.get("capabilities", [])
                module.status = ModuleStatus.ONLINE
                module.last_check = datetime.now()
        except (httpx.RequestError, httpx.TimeoutException):
            module.status = ModuleStatus.OFFLINE

        # If info succeeded, also check health
        if module.status == ModuleStatus.ONLINE:
            try:
                resp = await client.get(f"{base_url}/api/v1/health")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") != "healthy":
                        module.status = ModuleStatus.DEGRADED
            except (httpx.RequestError, httpx.TimeoutException):
                module.status = ModuleStatus.DEGRADED

        return module

    async def call_module(
        self,
        module_name: str,
        endpoint: str,
        method: str = "GET",
        payload: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> ModuleResponse:
        """Call a specific endpoint on a module."""
        module = self._modules.get(module_name)
        if not module:
            return ModuleResponse(
                module_name=module_name,
                endpoint=endpoint,
                status_code=0,
                error=f"Modulo {module_name} nao encontrado no registry",
            )

        if module.status == ModuleStatus.OFFLINE:
            return ModuleResponse(
                module_name=module_name,
                endpoint=endpoint,
                status_code=0,
                error=f"Modulo {module_name} esta offline",
            )

        url = f"{module.base_url}{endpoint}"
        start = time.monotonic()

        async def _http_call() -> ModuleResponse:
            timeout_seconds = self._timeout
            if self._timeout_manager is not None:
                timeout_seconds = self._timeout_manager.get_timeout(module_name.replace("intellicare-", ""), "analyze")
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                if method.upper() == "POST":
                    resp = await client.post(url, json=payload)
                else:
                    resp = await client.get(url, params=params)
                duration = (time.monotonic() - start) * 1000
                response = ModuleResponse(
                    module_name=module_name,
                    endpoint=endpoint,
                    status_code=resp.status_code,
                    data=resp.json() if resp.status_code < 400 else {},
                    error=resp.text if resp.status_code >= 400 else "",
                    duration_ms=duration,
                )
                if response.status_code >= 500:
                    raise RuntimeError(response.error or f"HTTP {response.status_code}")
                return response

        async def _attempt() -> ModuleResponse:
            if self._circuit_breaker_manager is None:
                return await _http_call()
            breaker = self._circuit_breaker_manager.get(module_name)
            return await breaker.call(_http_call)

        try:
            if self._retry_policy is not None:
                return await self._retry_policy.execute_with_retry(_attempt, policy_name="default")
            return await _attempt()
        except httpx.TimeoutException:
            duration = (time.monotonic() - start) * 1000
            if self._fallback_manager is not None:
                fallback = await self._fallback_manager.get_fallback(module_name, query="", patient_id=None)
                return ModuleResponse(
                    module_name=module_name,
                    endpoint=endpoint,
                    status_code=503,
                    data={"fallback": fallback},
                    error="Timeout na chamada ao modulo",
                    duration_ms=duration,
                )
            return ModuleResponse(
                module_name=module_name,
                endpoint=endpoint,
                status_code=0,
                error="Timeout na chamada ao modulo",
                duration_ms=duration,
            )
        except httpx.RequestError as e:
            duration = (time.monotonic() - start) * 1000
            if self._fallback_manager is not None:
                fallback = await self._fallback_manager.get_fallback(module_name, query="", patient_id=None)
                return ModuleResponse(
                    module_name=module_name,
                    endpoint=endpoint,
                    status_code=503,
                    data={"fallback": fallback},
                    error=str(e),
                    duration_ms=duration,
                )
            return ModuleResponse(
                module_name=module_name,
                endpoint=endpoint,
                status_code=0,
                error=str(e),
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            if self._fallback_manager is not None:
                fallback = await self._fallback_manager.get_fallback(module_name, query="", patient_id=None)
                return ModuleResponse(
                    module_name=module_name,
                    endpoint=endpoint,
                    status_code=503,
                    data={"fallback": fallback},
                    error=str(e),
                    duration_ms=duration,
                )
            return ModuleResponse(
                module_name=module_name,
                endpoint=endpoint,
                status_code=503,
                error=str(e),
                duration_ms=duration,
            )

    def get_online_modules(self) -> list[ModuleInfo]:
        """Return all modules that are online or degraded."""
        return [
            m
            for m in self._modules.values()
            if m.status in (ModuleStatus.ONLINE, ModuleStatus.DEGRADED)
        ]

    def get_module(self, name: str) -> Optional[ModuleInfo]:
        """Get a specific module by name."""
        return self._modules.get(name)

    def get_modules_with_capability(self, capability: str) -> list[ModuleInfo]:
        """Find modules that have a specific capability."""
        return [
            m
            for m in self._modules.values()
            if capability in m.capabilities and m.status != ModuleStatus.OFFLINE
        ]

    @property
    def total_modules(self) -> int:
        return len(self._modules)

    @property
    def online_count(self) -> int:
        return len(self.get_online_modules())

    @property
    def last_discovery(self) -> Optional[datetime]:
        return self._last_discovery
