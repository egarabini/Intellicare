# Correção dos Testes SMS Providers - 2026-02-24 09:37

## Problema Identificado

```
TypeError: 'coroutine' object is not subscriptable
RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
```

## Causa Raiz

No teste, temos:
```python
mock_response = AsyncMock()
mock_response.json.return_value = {...}
```

Isso cria uma coroutine quando chamamos `mock_response.json()`, e `.return_value` tenta acessar algo que não existe.

## Solução

Usar `return_value` diretamente em vez de `.json.return_value`:

```python
# ANTES (ERRADO):
mock_response.json.return_value = {"sid": "SM123456"}
mock_response.raise_for_status = AsyncMock()

# DEPOIS (CORRETO):
mock_response.json.return_value = AsyncMock(return_value={"sid": "SM123456"})
mock_response.raise_for_status = AsyncMock(return_value=None)
```

Ou, mais simples, usar `MagicMock()` para métodos síncronos:

```python
# SOLUÇÃO MAIS SIMPLES:
mock_response = MagicMock()  # Não AsyncMock para response
mock_response.json.return_value = {"sid": "SM123456"}
mock_response.raise_for_status.return_value = None
```

## Arquivos a Corrigir

1. `tests/test_sms/test_providers.py`
   - `test_twilio_send` (linha 56-61)
   - `test_zenvia_send` (linha 105-109)
