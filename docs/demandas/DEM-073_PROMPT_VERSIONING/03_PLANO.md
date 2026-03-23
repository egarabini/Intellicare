---
tipo: plano-execucao
demanda: DEM-073
titulo: Prompt Versioning
status: em-execucao
dev: CODEX
criado: 2026-03-21
---

# DEM-073 — Plano de Execução

## Estimativa

Tempo estimado: ~4h | Complexidade: média

O núcleo técnico é simples (migration + cache layer), mas requer disciplina: os prompts hardcoded devem ser preservados como fallback em todos os services — nunca removidos. A PromptsPage requer atenção ao UX de versionamento.

---

## Ordem de execução

### Bloco 1 — Migration e seeds (45min)
1. Criar migration `017_prompt_templates.py` com tabela `platform.prompt_templates`
2. Extrair prompts hardcoded atuais de `florence/services.py` e `oswaldo/services.py`
3. Inserir como seeds (versão 1, `is_active = TRUE`) na migration
4. Rodar migration — confirmar tabela criada e seeds inseridos

### Bloco 2 — Camada shared/llm.py (45min)
5. Implementar `get_active_prompt(slug, fallback)` com cache em memória (TTL 60s)
6. Implementar `invalidate_prompt_cache(slug)`
7. Testar `get_active_prompt` isolado: com slug válido, slug inválido e simulando falha de DB

### Bloco 3 — Integração nos services (45min)
8. Atualizar `florence/services.py`:
   - Manter strings hardcoded como `*_FALLBACK` no topo do arquivo
   - Substituir uso direto por `get_active_prompt(slug, fallback=*_FALLBACK)`
9. Repetir para `oswaldo/services.py` (2 slugs: prescription e cid10)
10. Rodar suite de testes existente — sem regressões

### Bloco 4 — Admin API (45min)
11. Criar endpoints em `admin/routes.py` (GET list, GET versions, POST new version, POST activate)
12. Implementar `admin/services.py`: `list_prompts()`, `get_prompt_versions()`, `save_new_version()`, `activate_version()`
13. `activate_version()` deve chamar `invalidate_prompt_cache()` após commit

### Bloco 5 — Frontend AdminUI (45min)
14. Criar `PromptsPage.tsx`:
    - Lista de slugs com versão ativa
    - Seleção de slug → abre painel lateral
    - Textarea editável (monospace, minRows=15)
    - Botão "Salvar nova versão"
    - Tabela de histórico de versões com botão "Ativar"
15. Adicionar rota `/admin/prompts` no router AdminUI
16. Adicionar item "Prompts IA" no menu lateral (ícone `IconBrain` Mantine)

### Bloco 6 — Testes (30min)
17. Criar `tests/test_prompt_versioning.py`:
    - `test_get_active_prompt_returns_db_content()` — verifica que o conteúdo do banco é retornado
    - `test_get_active_prompt_fallback_on_db_error()` — simula falha de DB → fallback hardcoded
    - `test_save_new_version_does_not_auto_activate()` — nova versão criada não é ativa
    - `test_activate_version_switches_active()` — ativar v2 desativa v1
    - (bonus) `test_cache_invalidated_after_activate()` — cache limpo após troca de versão

---

## Gotcha — Preservar fallbacks hardcoded

**Nunca remover** os prompts hardcoded dos `services.py`. Eles são o fallback de segurança em dois cenários:
1. DB temporariamente indisponível
2. Ambiente de desenvolvimento local sem migration 017 rodada

Padrão obrigatório:

```python
# ✅ CORRETO
SOAP_PROMPT_FALLBACK = """..."""  # mantido, usado como fallback

def suggest_soap(data):
    prompt = get_active_prompt("florence_soap", fallback=SOAP_PROMPT_FALLBACK)

# ❌ ERRADO
def suggest_soap(data):
    prompt = get_active_prompt("florence_soap")  # sem fallback — vai quebrar se DB cair
```

---

## Gotcha — Cache e múltiplos workers Uvicorn

O cache em memória (`_prompt_cache: dict`) é **por processo**. Com Uvicorn rodando com `--workers 4`, cada worker tem seu próprio cache. Isso é aceitável para esta DEM — a inconsistência máxima é de 60s entre workers.

**Não** implementar cache Redis para esta DEM (over-engineering). Se Marie/DEM-074 exigir consistência perfeita, migrar o cache para Redis naquele momento.

---

## Gotcha — Seeds na migration vs. seed script

Os seeds de prompts vão **dentro da migration 017** (usando `op.execute()`), não em script separado. Isso garante que CODEX aplica a migration e já tem os prompts no banco — sem etapa manual.

```python
# 017_prompt_templates.py
def upgrade():
    op.execute("""
        INSERT INTO platform.prompt_templates (slug, version, content, is_active, description)
        VALUES
            ('florence_soap', 1, $PROMPT$...conteúdo atual...$PROMPT$, TRUE, 'Versão inicial (migrada do código)'),
            ('oswaldo_prescription', 1, $PROMPT$...conteúdo atual...$PROMPT$, TRUE, 'Versão inicial (migrada do código)'),
            ...
    """)
```

---

## Entrega

```
feat(shared): prompt versioning — prompt_templates table, get_active_prompt(), AdminUI PromptsPage
```
Hash → enviar para o ARQUITETO fechar DEM-073.
