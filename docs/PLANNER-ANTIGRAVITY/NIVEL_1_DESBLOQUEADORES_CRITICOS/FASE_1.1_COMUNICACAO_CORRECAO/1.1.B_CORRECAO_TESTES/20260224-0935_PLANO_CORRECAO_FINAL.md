# Plano de Correção Final - FASE 1.1.B

**Data:** 2026-02-24 09:35
**Objetivo:** Corrigir os 9 testes falhando e atingir 80% cobertura

## Ordem de Prioridade

### 1. Testes SMS (Mencionados no Roadmap) - 3 testes
- `test_sms/test_dispatcher.py::test_get_status`
- `test_sms/test_providers.py::test_twilio_send`
- `test_sms/test_providers.py::test_zenvia_send`

**Erro Comum:** `TypeError: 'coroutine'` - falta `await` ou marcação `async`

### 2. Teste WhatsApp (Mencionado no Roadmap) - 1 teste
- `test_whatsapp/test_webhook.py::test_handle_status_update`

**Erro:** `sqlalchemy.exc.ArgumentError` - fixture de sessão

### 3. Testes Jinja2 - 2 testes
- `test_email/test_template_engine.py::test_format_date_filter`
- `test_email/test_template_engine.py::test_format_datetime_filter`

**Erro:** Filtros não registrados no Jinja2 Environment

### 4. Testes Push - 3 testes
- `test_push/test_dispatcher.py::test_send_to_web_subscription`
- `test_push/test_dispatcher.py::test_send_no_subscriptions`
- `test_push/test_dispatcher.py::test_send_to_multiple_devices`

**Erro:** `AssertionError` - lógica incompleta

## Log de Execução

### 2026-02-24 09:35 - Início das correções
Próximo: Verificar test_sms/test_providers.py
