---
tipo: adr
id: ADR-002
titulo: Módulo (código) ≠ Serviço (runtime)
status: aprovado
data: 2026-03-13
decidido_por: Eduardo (Arquiteto)
tags: [arquitetura, modulos, deploy, runtime]
---

# ADR-002 — Módulo (código) ≠ Serviço (runtime)

## Decisão

**MÓDULO** = unidade de código/desenvolvimento com responsabilidade distinta.
**SERVIÇO** = o que o tenant contratou: conjunto de módulos empacotados rodando
juntos em **1 container** `intellicare-service`.

## Contexto

O projeto V2 tinha 10+ containers (1 por agente). Isso gerava:
- Overhead operacional: 10 health checks, 10 logs, 10 configurações de rede
- Latência extra: chamadas inter-container para funcionalidades simples
- Complexidade de deploy: orquestrar 10 serviços para subir 1 tenant

## Arquitetura aprovada

```
REPOSITÓRIO (código):
  packages/intellicare-core/   → SDK compartilhado
  modules/admin/               → MÓDULO (unidade de desenvolvimento)
  modules/gestor/              → MÓDULO
  modules/cuidado/             → MÓDULO
  modules/florence/            → MÓDULO
  modules/oswaldo/             → MÓDULO
  configs/plans/*.yaml         → define quais módulos cada plano inclui

RUNTIME (servidor):
  Container: intellicare-service  → FastAPI carrega módulos dinamicamente
  Container: postgresql+pgvector
  Container: redis
  Container: keycloak
  Container: ollama (SLM)
  Container: traefik (proxy)
```

## Carregamento dinâmico de módulos

```python
class ModuleLoader:
    def load_for_tenant(self, tenant_config: TenantConfig):
        for module_name in tenant_config.enabled_modules:
            if module_name not in self.modules:
                self.modules[module_name] = import_module(f"modules.{module_name}")

    def route(self, tenant_id: str, module: str, action: str, payload: dict):
        tenant_config = get_tenant_config(tenant_id)
        if module not in tenant_config.enabled_modules:
            raise HTTPException(403, "Módulo não habilitado para este tenant")
        return self.modules[module].execute(action, payload, tenant_id)
```

## Customização por tenant

```
1. CÓDIGO BASE (repo intellicare — padrão para todos)
2. CONFIGURAÇÃO POR VERTICAL (configs/verticals/*.yaml)
3. CONFIGURAÇÃO POR TENANT (tenant_{slug}._admin_config JSONB)
4. OVERLAY EXCLUSIVO (configs/overlays/tenant_{slug}/ — caso extremo)
```

A customização de um tenant nunca afeta os demais.

## Consequências

- 1 Dockerfile em `deploy/` empacota todos os módulos
- Módulos não têm porta própria — são roteados via `intellicare-service`
- WANDA será um módulo carregado quando o plano inclui orquestração (Fase 4+)
- `configs/plans/*.yaml` é a fonte de verdade de quais módulos estão ativos

## Implementação

- `packages/intellicare-core/module_loader/` — DEM-003
- `deploy/Dockerfile` — empacota tudo — DEM-002
