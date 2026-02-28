# FASE 1.1.B - Correção de Testes Falhando - intellicare-comunicacao

**Data de início:** 2026-02-24 09:15
**Responsável:** DEV2
**Prioridade:** 🔴 BLOQUEADOR
**Status:** 🔄 EM ANDAMENTO

## Contexto

Após a FASE 1.1.A (correção de dependências), ainda temos **2 erros de coleta** e precisamos executar a suite completa para identificar os **4 testes falhando** mencionados no roadmap.

## Objetivo

1. Resolver os 2 erros de coleta restantes
2. Executar `pytest -q` para identificar testes falhando
3. Corrigir os 4 testes com falha conhecida

## Testes com Falha Conhecida (do Roadmap)

| Teste | Erro | Ação |
|-------|------|------|
| `test_sms/test_dispatcher.py::test_get_status` | `sqlalchemy.exc.ArgumentError` | Verificar setup da sessão no fixture |
| `test_sms/test_providers.py::test_twilio_send` | `TypeError: 'coroutine'` | Adicionar `await` ou marcar teste como `async` |
| `test_sms/test_providers.py::test_zenvia_send` | `TypeError: 'coroutine'` | Idem |
| `test_whatsapp/test_webhook.py::test_handle_status_update` | `sqlalchemy.exc.ArgumentError` | Verificar fixture de sessão |

## Tarefas

- [ ] ⚙️ Resolver 2 erros de coleta restantes (import errors)
- [ ] 🧪 Executar suite completa: `pytest -q`
- [ ] ⚙️ Inspecionar fixtures em `tests/conftest.py`
- [ ] ⚙️ Para testes async: garantir `@pytest.mark.asyncio` + `async def test_...`
- [ ] 🧪 Meta: `pytest -q` → **≥ 80% cobertura, 0 falhas**

## Log de Progresso

### 2026-02-24 09:15 - Início da FASE 1.1.B
- Criada estrutura de pastas para documentação
- Próximo passo: Investigar os 2 erros de coleta restantes
