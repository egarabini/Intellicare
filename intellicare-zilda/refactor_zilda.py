import os
import re

base_dir = r"c:\Users\egara\INTELLICARE\intellicare-zilda\zilda"

def refactor_cnes_client():
    filepath = os.path.join(base_dir, "engine", "cnes_client.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add ctx to get_unit_types
    content = content.replace("def get_unit_types(self) -> list[HealthUnitType]:", "def get_unit_types(self, ctx: Any = None) -> list[HealthUnitType]:")
    content = content.replace('cache_key = "unit_types"', 'tenant_prefix = f"tenant:{ctx.tenant_id}:" if ctx and hasattr(ctx, "tenant_id") else ""\n        cache_key = f"{tenant_prefix}unit_types"')

    # 2. Add ctx to search_establishments
    content = content.replace("        offset: int = 0,\n    ) -> list[HealthEstablishment]:", "        offset: int = 0,\n        ctx: Any = None,\n    ) -> list[HealthEstablishment]:")
    content = content.replace('cache_key = f"establishments:{hash(frozenset(params.items()))}"', 'tenant_prefix = f"tenant:{ctx.tenant_id}:" if ctx and hasattr(ctx, "tenant_id") else ""\n        cache_key = f"{tenant_prefix}establishments:{hash(frozenset(params.items()))}"')

    # 3. Add ctx to get_establishment_by_cnes
    content = content.replace("def get_establishment_by_cnes(self, cnes_code: str) -> HealthEstablishment | None:", "def get_establishment_by_cnes(self, cnes_code: str, ctx: Any = None) -> HealthEstablishment | None:")
    content = content.replace('cache_key = f"establishment:{cnes_code}"', 'tenant_prefix = f"tenant:{ctx.tenant_id}:" if ctx and hasattr(ctx, "tenant_id") else ""\n        cache_key = f"{tenant_prefix}establishment:{cnes_code}"')

    # 4. Add ctx to get_health_regions
    content = content.replace("        offset: int = 0,\n    ) -> list[HealthRegion]:", "        offset: int = 0,\n        ctx: Any = None,\n    ) -> list[HealthRegion]:")
    content = content.replace('cache_key = f"regions:{hash(frozenset(params.items()))}"', 'tenant_prefix = f"tenant:{ctx.tenant_id}:" if ctx and hasattr(ctx, "tenant_id") else ""\n        cache_key = f"{tenant_prefix}regions:{hash(frozenset(params.items()))}"')

    # 5. Add ctx to validate_cnes
    content = content.replace("def validate_cnes(self, cnes_code: str) -> CnesValidation:", "def validate_cnes(self, cnes_code: str, ctx: Any = None) -> CnesValidation:")
    content = content.replace("establishment = self.get_establishment_by_cnes(digits)", "establishment = self.get_establishment_by_cnes(digits, ctx=ctx)")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def refactor_territorial():
    filepath = os.path.join(base_dir, "engine", "territorial.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. get_territorial_summary
    content = content.replace("        limit: int = 100,\n    ) -> TerritorialSummary:", "        limit: int = 100,\n        ctx: Any = None,\n    ) -> TerritorialSummary:")
    content = content.replace("active_only=True,\n            limit=limit,\n        )", "active_only=True,\n            limit=limit,\n            ctx=ctx,\n        )")
    content = content.replace("if state_code:\n            regions = self._client.get_health_regions(state_code=state_code)", "if state_code:\n            regions = self._client.get_health_regions(state_code=state_code, ctx=ctx)")

    # 2. find_nearby_establishments
    content = content.replace("        limit: int = 20,\n    ) -> list[HealthEstablishment]:", "        limit: int = 20,\n        ctx: Any = None,\n    ) -> list[HealthEstablishment]:")
    content = content.replace("active_only=True,\n            limit=limit,\n        )", "active_only=True,\n            limit=limit,\n            ctx=ctx,\n        )")

    # 3. get_region_context
    content = content.replace("def get_region_context(self, city_code: str, state_code: str) -> dict[str, Any]:", "def get_region_context(self, city_code: str, state_code: str, ctx: Any = None) -> dict[str, Any]:")
    content = content.replace("regions = self._client.get_health_regions(state_code=state_code)", "regions = self._client.get_health_regions(state_code=state_code, ctx=ctx)")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def refactor_app():
    filepath = os.path.join(base_dir, "api", "app.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Add imports
    import_stmt = "\nfrom fastapi import Depends\nfrom zilda.api.auth import get_tenant_context, check_module_active\n"
    content = content.replace("from fastapi import FastAPI, HTTPException, Query", import_stmt + "from fastapi import FastAPI, HTTPException, Query")

    # define depends string
    depends_str = ", ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-zilda'))"

    routes = {
        "def health() -> dict[str, Any]:": "()",
        "def info() -> dict[str, Any]:": "()",
        "def unit_types() -> list[dict[str, str]]:": "()",
        "def validate_cnes(request: CnesValidateRequest) -> dict[str, Any]:": "(request)",
        "def get_establishment(cnes_code: str) -> dict[str, Any]:": "(cnes_code)"
    }
    for old, params in routes.items():
        if old in content:
            new = old.replace(")", depends_str + ")")
            content = content.replace(old, new)
    
    # query routes
    content = content.replace("offset: int = Query(0, ge=0),\n    ) -> list[dict[str, Any]]:", f"offset: int = Query(0, ge=0),\n        ctx: Any = Depends(get_tenant_context),\n        _check: Any = Depends(check_module_active('intellicare-zilda'))\n    ) -> list[dict[str, Any]]:")
    content = content.replace("limit: int = Query(100, ge=1, le=100),\n    ) -> dict[str, Any]:", f"limit: int = Query(100, ge=1, le=100),\n        ctx: Any = Depends(get_tenant_context),\n        _check: Any = Depends(check_module_active('intellicare-zilda'))\n    ) -> dict[str, Any]:")
    content = content.replace('def region_context(city_code: str, state_code: str = Query(..., description="Codigo UF")) -> dict[str, Any]:', f'def region_context(city_code: str, state_code: str = Query(..., description="Codigo UF"), ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active("intellicare-zilda"))) -> dict[str, Any]:')
    content = content.replace("async def analyze(request: AnalyzeRequest) -> dict[str, Any]:", f"async def analyze(request: AnalyzeRequest, ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-zilda'))) -> dict[str, Any]:")

    # method calls inside the endpoints:
    content = content.replace("types = client.get_unit_types()", "types = client.get_unit_types(ctx=ctx)")
    
    content = content.replace("""        results = client.search_establishments(
            state_code=state_code,
            city_code=city_code,
            unit_type_code=unit_type_code,
            active_only=active_only,
            limit=limit,
            offset=offset,
        )""", """        results = client.search_establishments(
            state_code=state_code,
            city_code=city_code,
            unit_type_code=unit_type_code,
            active_only=active_only,
            limit=limit,
            offset=offset,
            ctx=ctx,
        )""")

    content = content.replace("est = client.get_establishment_by_cnes(cnes_code)", "est = client.get_establishment_by_cnes(cnes_code, ctx=ctx)")
    content = content.replace("result = client.validate_cnes(request.cnes_code)", "result = client.validate_cnes(request.cnes_code, ctx=ctx)")
    
    content = content.replace("""        regions = client.get_health_regions(
            state_code=state_code,
            limit=limit,
            offset=offset,
        )""", """        regions = client.get_health_regions(
            state_code=state_code,
            limit=limit,
            offset=offset,
            ctx=ctx,
        )""")

    content = content.replace("""        summary = engine.get_territorial_summary(
            state_code=state_code,
            city_code=city_code,
            limit=limit,
        )""", """        summary = engine.get_territorial_summary(
            state_code=state_code,
            city_code=city_code,
            limit=limit,
            ctx=ctx,
        )""")
    
    content = content.replace("return engine.get_region_context(city_code=city_code, state_code=state_code)", "return engine.get_region_context(city_code=city_code, state_code=state_code, ctx=ctx)")
    
    # analyze router changes 
    content = content.replace("""                    found = client.search_establishments(
                        state_code=parameters.get("state_code"),
                        city_code=parameters.get("city_code"),
                        unit_type_code=parameters.get("unit_type_code"),
                        active_only=True,
                        limit=int(parameters.get("limit", 20)),
                    )""", """                    found = client.search_establishments(
                        state_code=parameters.get("state_code"),
                        city_code=parameters.get("city_code"),
                        unit_type_code=parameters.get("unit_type_code"),
                        active_only=True,
                        limit=int(parameters.get("limit", 20)),
                        ctx=ctx,
                    )""")

    content = content.replace("""                summary = engine.get_territorial_summary(
                    state_code=state_code,
                    city_code=city_code,
                    limit=int(parameters.get("limit", 100)),
                )""", """                summary = engine.get_territorial_summary(
                    state_code=state_code,
                    city_code=city_code,
                    limit=int(parameters.get("limit", 100)),
                    ctx=ctx,
                )""")

    content = content.replace("context = engine.get_region_context(city_code=city_code, state_code=state_code)", "context = engine.get_region_context(city_code=city_code, state_code=state_code, ctx=ctx)")
    
    content = content.replace("""                nearby = engine.find_nearby_establishments(
                    city_code=str(parameters.get("city_code", "")),
                    unit_type_code=parameters.get("unit_type_code"),
                    limit=int(parameters.get("limit", 20)),
                )""", """                nearby = engine.find_nearby_establishments(
                    city_code=str(parameters.get("city_code", "")),
                    unit_type_code=parameters.get("unit_type_code"),
                    limit=int(parameters.get("limit", 20)),
                    ctx=ctx,
                )""")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    refactor_cnes_client()
    refactor_territorial()
    refactor_app()
    print("Zilda refatorado com sucesso")
