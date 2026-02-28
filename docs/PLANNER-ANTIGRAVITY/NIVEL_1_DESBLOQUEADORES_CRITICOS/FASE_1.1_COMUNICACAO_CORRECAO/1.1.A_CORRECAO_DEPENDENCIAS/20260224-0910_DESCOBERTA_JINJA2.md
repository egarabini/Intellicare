# Descoberta do Erro Real - 2026-02-24 09:10

## Problema Identificado

O erro **NÃO era** `email-validator` (que já estava no pyproject.toml).

O erro real é: **`ModuleNotFoundError: No module named 'jinja2'`**

## Rastro do Erro

```
comunicacao\channels\email\templates.py:1: in <module>
    from jinja2 import Environment, FileSystemLoader, select_autoescape, DictLoader
E   ModuleNotFoundError: No module named 'jinja2'
```

## 11 Arquivos de Teste Afetados

Todos os testes que importam `comunicacao.api.app` falham porque o app não consegue carregar o `email_routes`, que depende de `jinja2`.

## Solução

Adicionar `jinja2` ao `pyproject.toml` e instalar.

## Próximo Passo

Verificar se `jinja2` está no pyproject.toml e instalá-lo.
