# Integração LGPD (D6) com Routing Engine (D1)

## 📋 Visão Geral

Este documento descreve como integrar o **LGPDComplianceService** (D6) com o **RoutingEngine** (D1) usando o **LGPDComplianceAdapter**.

---

## 🔌 Arquitetura da Integração

```
┌─────────────────────────────────────────────────────────────┐
│                      RoutingEngine (D1)                      │
│                                                               │
│  1. create_intent()                                          │
│  2. process_intent()                                         │
│      ├─ resolve_recipient()                                  │
│      ├─ check_compliance() ◄─────────────┐                  │
│      ├─ match_rules()                     │                  │
│      ├─ render_content()                  │                  │
│      └─ dispatch()                        │                  │
└───────────────────────────────────────────┼──────────────────┘
                                            │
                                            │
                    ┌───────────────────────▼──────────────────┐
                    │   LGPDComplianceAdapter (D6 ↔ D1)       │
                    │                                          │
                    │  • Implementa LGPDComplianceGateway     │
                    │  • Converte formatos D1 ↔ D6            │
                    │  • Loga decisões em audit trail         │
                    └───────────────────────┬──────────────────┘
                                            │
                    ┌───────────────────────▼──────────────────┐
                    │   LGPDComplianceService (D6)             │
                    │                                          │
                    │  • check_compliance()                    │
                    │  • determine_legal_basis()               │
                    │  • check_quiet_hours()                   │
                    │  • check_consent()                       │
                    └──────────────────────────────────────────┘
```

---

## 🚀 Como Usar

### 1. Criar Adapter com Sessão do Banco

```python
from sqlalchemy.ext.asyncio import AsyncSession
from comunicacao.routing.lgpd_adapter import LGPDComplianceAdapter
from comunicacao.lgpd.config import LGPDConfig

# Obter sessão do banco
async with get_db_session() as db:
    # Criar adapter
    lgpd_adapter = LGPDComplianceAdapter(
        db=db,
        config=LGPDConfig.from_env(),  # Opcional
    )
```

### 2. Usar Adapter no RoutingEngine

```python
from comunicacao.routing.engine import RoutingEngine
from comunicacao.routing.lgpd_adapter import LGPDComplianceAdapter

# Criar RoutingEngine com adapter
engine = RoutingEngine(
    routing_store=routing_store,
    template_store=template_store,
    rule_matcher=rule_matcher,
    recipient_resolver=recipient_resolver,
    lgpd_gateway=lgpd_adapter,  # ◄── Usar adapter ao invés de DefaultLGPDGateway
    dispatcher_manager=dispatcher_manager,
)

# Processar intent (compliance check automático)
intent = await engine.create_intent(intent_create)
result = await engine.process_intent(intent.id)
```

### 3. Verificar Compliance Manualmente

```python
# Verificar se pode enviar por canal específico
decision = await lgpd_adapter.can_send(
    patient_id="PAT-12345",
    channel="rocketchat",
    intent_type="clinical_alert",
    severity="HIGH",
)

if decision.allowed:
    print(f"✅ Permitido - {decision.reason}")
    if decision.override_applied:
        print(f"⚠️  Override aplicado - Base legal: {decision.legal_basis}")
else:
    print(f"❌ Bloqueado - {decision.reason}")
    if decision.defer_until:
        print(f"⏰ Adiado até: {decision.defer_until}")
```

---

## 📊 Fluxo de Verificação LGPD

```
┌─────────────────────────────────────────────────────────────┐
│ 1. RoutingEngine.process_intent()                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. LGPDComplianceAdapter.check_compliance()                 │
│    • Extrai patient_id                                      │
│    • Determina canal preferencial                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. LGPDComplianceService.check_compliance()                 │
│    ├─ Busca preferências do paciente                        │
│    ├─ Verifica CRITICAL (sempre permitido)                  │
│    ├─ Verifica HIGH (permitido com base legal)              │
│    ├─ Verifica consentimento                                │
│    ├─ Verifica expiração                                    │
│    ├─ Verifica opt-out do canal                             │
│    └─ Verifica quiet hours                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. AuditTrailService.log_lgpd_decision()                    │
│    • Cria AuditEntry com hash chain                         │
│    • Pseudonimiza patient_id                                │
│    • Registra base legal e override                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Retorna decisão para RoutingEngine                       │
│    • allowed: True/False                                    │
│    • legal_basis: CONSENT, VITAL_PROTECTION, etc.           │
│    • reason: Descrição da decisão                           │
│    • override_applied: True se CRITICAL/HIGH                │
│    • defer_until: Timestamp se em quiet hours               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Bases Legais LGPD

O adapter mapeia automaticamente as bases legais:

| Severidade | Categoria | Base Legal | Artigo LGPD |
|------------|-----------|------------|-------------|
| CRITICAL | Qualquer | VITAL_PROTECTION | Art. 7º, VII + Art. 11, II, f |
| HIGH | clinical_alert, escalation | HEALTH_PROTECTION | Art. 7º, VII |
| Outros | Com consentimento | CONSENT | Art. 7º, I |
| Outros | Obrigação legal | LEGAL_OBLIGATION | Art. 7º, II |
| Outros | Interesse público (SUS) | PUBLIC_INTEREST | Art. 7º, VIII |

---

## 📝 Audit Trail Automático

Todas as decisões LGPD são automaticamente registradas em audit trail:

```python
# Exemplo de AuditEntry criado automaticamente
{
    "id": "uuid-...",
    "intent_id": "intent-123",
    "patient_hash": "sha256-...",  # Pseudonimizado
    "status": "blocked_lgpd",
    "legal_basis": "consent",
    "lgpd_override": False,
    "lgpd_reason": "Paciente não concedeu consentimento",
    "severity": "MEDIUM",
    "channel": "rocketchat",
    "previous_hash": "sha256-...",  # Hash chain
    "entry_hash": "sha256-...",
    "created_at": "2026-02-18T10:30:00Z"
}
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# LGPD Configuration
LGPD_CRITICAL_OVERRIDE_ENABLED=true
LGPD_HIGH_ALERT_OVERRIDE_ENABLED=true
LGPD_BLOCK_WITHOUT_CONSENT=true
LGPD_DEFAULT_QUIET_HOURS_START=22:00
LGPD_DEFAULT_QUIET_HOURS_END=07:00
LGPD_AUDIT_RETENTION_YEARS=5
LGPD_CONSENT_VERSION=1.0
LGPD_ANONYMIZATION_HASH_SALT=your-secret-salt-here
```

---

## 🧪 Testes

```python
import pytest
from comunicacao.routing.lgpd_adapter import LGPDComplianceAdapter

@pytest.mark.asyncio
async def test_lgpd_adapter_critical_override(db_session):
    """Testa que CRITICAL sempre é permitido."""
    adapter = LGPDComplianceAdapter(db=db_session)
    
    decision = await adapter.can_send(
        patient_id="PAT-123",
        channel="rocketchat",
        intent_type="clinical_alert",
        severity="CRITICAL",
    )
    
    assert decision.allowed is True
    assert decision.override_applied is True
    assert decision.legal_basis == "vital_protection"
```

---

## 📚 Referências

- **D1 - Engine de Roteamento**: `docs/01_engine_roteamento/`
- **D6 - LGPD/Auditoria**: `docs/06_lgpd_auditoria/`
- **LGPDComplianceService**: `comunicacao/lgpd/compliance_service.py`
- **AuditTrailService**: `comunicacao/audit/audit_service.py`
- **LGPDComplianceAdapter**: `comunicacao/routing/lgpd_adapter.py`

