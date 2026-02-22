"""Handle /status command — module registry status table (EF-W012)."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def handle_status(
    http_client: Optional[Any],
    module_urls: dict[str, str],
    formatter: Any,
) -> tuple[str, list[dict]]:
    """Return (text, attachments) for the /status command."""
    modules: list[dict[str, Any]] = []

    for name, url in module_urls.items():
        healthy = False
        version = "?"
        if http_client and url:
            try:
                resp = await http_client.get(f"{url}/api/v1/health", timeout=5.0)
                if resp.status_code == 200:
                    healthy = True
                    data = resp.json()
                    version = data.get("version", "?")
            except Exception as exc:
                logger.debug("Health check failed for %s: %s", name, exc)
        modules.append({"name": name, "healthy": healthy, "version": version})

    attachments = formatter.status_table(modules)
    return "Status dos módulos IntelliCare:", attachments
