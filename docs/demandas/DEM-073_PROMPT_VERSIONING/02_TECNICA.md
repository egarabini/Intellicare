---
tipo: especificacao-tecnica
demanda: DEM-073
titulo: Prompt Versioning
---

# DEM-073 — Especificação Técnica

## Mapa de mudanças

| Arquivo | Tipo | O que muda |
|---------|------|-----------|
| `db/migrations/017_prompt_templates.py` | **Novo** | Tabela `prompt_templates` com suporte a versionamento |
| `packages/intellicare-core/intellicare_core/shared/llm.py` | Modificar | `get_active_prompt()` — busca no banco antes de fallback hardcoded |
| `modules/florence/services.py` | Modificar | Substituir strings hardcoded por `get_active_prompt("florence_soap")` |
| `modules/oswaldo/services.py` | Modificar | Substituir strings hardcoded por `get_active_prompt("oswaldo_prescription")`, `get_active_prompt("oswaldo_cid10")` |
| `modules/admin/routes.py` | Modificar | Endpoints CRUD para `prompt_templates` |
| `modules/admin/services.py` | Modificar | `list_prompts()`, `get_prompt_versions()`, `save_new_version()`, `activate_version()` |
| `modules/admin/schemas.py` | Modificar | `PromptTemplateOut`, `PromptVersionOut`, `PromptUpdateIn` |
| `frontend/AdminUI/src/pages/PromptsPage.tsx` | **Novo** | Página "Prompts IA" — lista + editor + histórico de versões |
| `tests/test_prompt_versioning.py` | **Novo** | 4+ testes automatizados |

---

## Migration 017 — `prompt_templates`

```sql
-- platform.prompt_templates
CREATE TABLE platform.prompt_templates (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        TEXT NOT NULL,          -- ex: "florence_soap", "oswaldo_prescription"
    version     INTEGER NOT NULL,        -- auto-incremental por slug
    content     TEXT NOT NULL,           -- o template completo do prompt
    description TEXT,                    -- nota do gestor (ex: "Adaptado para cardiologia")
    is_active   BOOLEAN NOT NULL DEFAULT FALSE,
    created_by  TEXT,                    -- email do gestor que criou
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_prompt_slug_version UNIQUE (slug, version)
);

-- Índice para busca rápida do ativo
CREATE INDEX idx_prompt_templates_active ON platform.prompt_templates (slug, is_active)
    WHERE is_active = TRUE;
```

**Regra de negócio**: somente uma versão pode ser `is_active = TRUE` por slug. Enforçado via trigger ou service.

**Seeds iniciais** (migration insere prompts hardcoded como versão 1, active):
- `florence_soap` — prompt atual do Florence em `services.py`
- `oswaldo_prescription` — prompt atual do Oswaldo prescriptions
- `oswaldo_cid10` — prompt atual do Oswaldo CID-10 search

---

## `shared/llm.py` — `get_active_prompt()`

```python
from functools import lru_cache
from typing import Optional

_prompt_cache: dict[str, str] = {}
_CACHE_TTL_SECONDS = 60  # invalida a cada 1 minuto

def get_active_prompt(slug: str, fallback: str) -> str:
    """
    Busca o prompt ativo no banco (tabela platform.prompt_templates).
    Em caso de falha (DB indisponível, slug não encontrado), usa fallback hardcoded.
    Cache em memória com TTL de 60s para não bater no banco a cada chamada LLM.

    Args:
        slug: Identificador do prompt (ex: "florence_soap")
        fallback: String hardcoded usada se banco não disponível

    Returns:
        Conteúdo do prompt ativo
    """
    # Verificar cache
    cached = _get_from_cache(slug)
    if cached:
        return cached

    try:
        with get_platform_session() as session:
            row = session.execute(
                text("SELECT content FROM platform.prompt_templates WHERE slug = :slug AND is_active = TRUE"),
                {"slug": slug}
            ).fetchone()

        if row:
            _set_cache(slug, row.content)
            return row.content
        else:
            # Slug não cadastrado ainda — usar fallback silenciosamente
            return fallback
    except Exception:
        # Banco indisponível — degradar graciosamente
        logger.warning(f"prompt_templates unavailable for slug={slug}, using hardcoded fallback")
        return fallback
```

**Padrão de uso nos services:**

```python
# Antes (hardcoded):
SOAP_PROMPT = """Você é Florence, assistente clínica..."""

# Depois (com versionamento):
from intellicare_core.shared.llm import get_active_prompt

SOAP_PROMPT_FALLBACK = """Você é Florence, assistente clínica..."""  # mantido como fallback

def get_soap_suggestion(encounter_data: dict) -> str:
    prompt = get_active_prompt("florence_soap", fallback=SOAP_PROMPT_FALLBACK)
    # ... chamar LLM com prompt
```

---

## API Admin — Endpoints

```
GET  /admin/prompts
     → Lista slugs únicos com versão ativa e data de criação
     → PromptTemplateOut[]

GET  /admin/prompts/{slug}/versions
     → Lista todas as versões do slug com is_active
     → PromptVersionOut[]

GET  /admin/prompts/{slug}/active
     → Retorna conteúdo da versão ativa
     → PromptVersionOut

POST /admin/prompts/{slug}/versions
     Body: { content: str, description: str }
     → Cria nova versão (NÃO ativa automaticamente)
     → PromptVersionOut (nova versão criada)

POST /admin/prompts/{slug}/versions/{version}/activate
     → Ativa versão específica, desativa todas as outras do slug
     → 204 No Content

POST /admin/prompts/{slug}/versions/{version}/activate
     + invalida cache em memória de get_active_prompt()
```

---

## Schemas

```python
class PromptVersionOut(BaseModel):
    id: UUID
    slug: str
    version: int
    content: str
    description: str | None
    is_active: bool
    created_by: str | None
    created_at: datetime

class PromptTemplateOut(BaseModel):
    slug: str
    active_version: int
    active_since: datetime
    total_versions: int

class PromptUpdateIn(BaseModel):
    content: str
    description: str | None = None
```

---

## Frontend — `PromptsPage.tsx`

Estrutura da página AdminUI:

```
┌─ Prompts IA ──────────────────────────────────────────────────────┐
│                                                                    │
│  florence_soap          v4  ●  Ativo  [última edição: 20/03/2026] │
│  oswaldo_prescription   v2  ●  Ativo  [última edição: 15/03/2026] │
│  oswaldo_cid10          v1  ●  Ativo  [última edição: 21/03/2026] │
│                                                                    │
│  [ Clique em um prompt para editar ]                               │
└───────────────────────────────────────────────────────────────────┘

┌─ florence_soap — Versão 4 (ativa) ───────────────────────────────┐
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Você é Florence, assistente clínica especializada em...    │  │
│  │ [textarea editável com fonte monospace]                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│  Descrição: [_________________________________]                    │
│                               [Salvar nova versão]                 │
│                                                                    │
│  Histórico de versões:                                            │
│  v4 ● ATIVO   20/03/2026  "Adaptado cardiologia"  [Ativar]       │
│  v3   20/02/2026  "Tom mais conciso"              [Ativar]        │
│  v2   15/01/2026  "Primeira revisão clínica"      [Ativar]        │
│  v1   01/01/2026  "Versão inicial (migrada)"      [Ativar]        │
└───────────────────────────────────────────────────────────────────┘
```

Comportamento:
- "Salvar nova versão" cria versão sem ativar (gestor pode revisar antes)
- "Ativar" aplica imediatamente — próxima chamada ao LLM usa o novo prompt
- Versão ativa exibe badge verde "●  ATIVO"
- Textarea: `Textarea` Mantine com `minRows={15}`, `font-family: monospace`

---

## Invalidação de cache

Quando `activate_version()` é chamado no service, deve também invalidar o cache em memória:

```python
def activate_version(slug: str, version: int, db) -> None:
    # 1. Desativar todas as versões do slug
    db.execute(
        text("UPDATE platform.prompt_templates SET is_active = FALSE WHERE slug = :slug"),
        {"slug": slug}
    )
    # 2. Ativar a versão solicitada
    db.execute(
        text("UPDATE platform.prompt_templates SET is_active = TRUE WHERE slug = :slug AND version = :version"),
        {"slug": slug, "version": version}
    )
    db.commit()
    # 3. Invalidar cache
    invalidate_prompt_cache(slug)
```

---

## Slugs gerenciados (seeds migration 017)

| Slug | Módulo | Descrição |
|------|--------|-----------|
| `florence_soap` | Florence | Geração de nota SOAP clínica |
| `florence_free_text` | Florence | Nota em texto livre |
| `oswaldo_prescription` | Oswaldo | Geração de prescrição |
| `oswaldo_cid10` | Oswaldo | Sugestão de CID-10 por sintomas |

---

## Dependências

- PostgreSQL `platform` schema — já existente (schema de plataforma, não de tenant)
- Alembic migration 017 — sem dependência de tenant individual
- Sem dependência de packages externos novos
