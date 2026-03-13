"""
Carregamento dinamico de modulos por tenant.
"""

from __future__ import annotations

import importlib
import logging

from fastapi import FastAPI

from intellicare_core.contracts.base import BaseModule, TenantContext
from intellicare_core.contracts.errors import api_error

logger = logging.getLogger(__name__)

AVAILABLE_MODULES: dict[str, str] = {
    "admin": "modules.admin.main",
    "gestor": "modules.gestor.main",
    "cuidado": "modules.cuidado.main",
    "florence": "modules.florence.main",
    "oswaldo": "modules.oswaldo.main",
}


class ModuleLoader:
    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self._loaded: dict[str, BaseModule] = {}

    def load(self, module_name: str) -> BaseModule:
        if module_name in self._loaded:
            return self._loaded[module_name]

        if module_name not in AVAILABLE_MODULES:
            raise ValueError(f"Modulo '{module_name}' nao existe em AVAILABLE_MODULES")

        import_path = AVAILABLE_MODULES[module_name]
        try:
            module = importlib.import_module(import_path)
        except ImportError as exc:
            raise ImportError(
                f"Nao foi possivel importar modulo '{module_name}' de '{import_path}': {exc}"
            ) from exc

        module_class = getattr(module, "Module", None)
        if module_class is None or not issubclass(module_class, BaseModule):
            raise TypeError(
                f"'{import_path}' deve expor uma classe 'Module' que herda de BaseModule"
            )

        instance = module_class()
        self.app.include_router(instance.get_router(), prefix=f"/{module_name}", tags=[module_name])
        self._loaded[module_name] = instance
        logger.info("Modulo '%s' v%s carregado.", module_name, instance.version)
        return instance

    def load_for_tenant(self, enabled_modules: list[str]) -> None:
        for module_name in enabled_modules:
            if module_name in AVAILABLE_MODULES:
                self.load(module_name)

    def is_enabled(self, module_name: str, ctx: TenantContext) -> bool:
        _ = ctx
        return module_name in self._loaded

    def get(self, module_name: str) -> BaseModule:
        if module_name not in self._loaded:
            raise api_error(404, "module_not_loaded", f"Modulo '{module_name}' nao esta carregado")
        return self._loaded[module_name]

    @property
    def loaded_modules(self) -> list[str]:
        return list(self._loaded.keys())
