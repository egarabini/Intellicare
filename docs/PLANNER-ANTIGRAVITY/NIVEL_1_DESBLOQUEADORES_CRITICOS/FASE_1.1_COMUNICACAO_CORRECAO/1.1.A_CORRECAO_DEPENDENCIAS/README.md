# FASE 1.1.A - Correção de Dependências - intellicare-comunicacao

**Data de início:** 2026-02-24
**Responsável:** DEV2
**Prioridade:** 🔴 BLOQUEADOR
**Status:** 🔄 EM ANDAMENTO

## Contexto

O módulo `intellicare-comunicacao` tem 11 arquivos de teste falhando na coleta com:
```
ModuleNotFoundError: No module named 'email_validator'
```

## Objetivo

Adicionar a dependência `email-validator` ao `pyproject.toml` e verificar que todos os testes são coletados sem erros.

## Tarefas

- [ ] ⚙️ Adicionar `email-validator>=2.1.0` ao `pyproject.toml`
- [ ] ⚙️ Re-executar `pip install -e ".[dev]"` no venv
- [ ] 🧪 Verificar coleta: `pytest --co -q` deve mostrar **0 errors**

## Arquivos Afetados

- `intellicare-comunicacao/pyproject.toml` - adicionar dependência

## Log de Progresso

### 2026-02-24 09:06 - Início da FASE 1.1.A
- Criada estrutura de pastas para documentação
- Próximo passo: Verificar pyproject.toml atual
