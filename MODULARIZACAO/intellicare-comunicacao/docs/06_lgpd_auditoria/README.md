# D6 - LGPD/Auditoria

## 📋 Visão Geral

O domínio **D6 - LGPD/Auditoria** implementa conformidade com a **Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018)** para o módulo de comunicação do IntelliCare.

---

## 🎯 Objetivos

1. ✅ **Conformidade Legal**: Atender todos os requisitos da LGPD
2. ✅ **Transparência**: Rastreabilidade completa de comunicações
3. ✅ **Segurança**: Proteção de dados pessoais sensíveis de saúde
4. ✅ **Direitos do Titular**: Facilitar exercício de direitos (Art. 18)
5. ✅ **Auditoria**: Trilha imutável para fiscalização

---

## 🏗️ Arquitetura

```
D6 - LGPD/Auditoria
├── Compliance (Conformidade)
│   ├── LGPDComplianceService
│   ├── PreferencesService
│   └── DataSubjectService
├── Audit Trail (Trilha de Auditoria)
│   ├── AuditTrailService
│   ├── HashChainManager
│   └── FHIRCommunicationBuilder
├── Integration (Integração)
│   └── LGPDComplianceAdapter (D6 ↔ D1)
└── API (Endpoints REST)
    └── 15 endpoints LGPD
```

---

## 📦 Componentes

### 1. Compliance Service

**Arquivo**: `comunicacao/lgpd/compliance_service.py`

**Responsabilidades**:
- ✅ Verificar conformidade LGPD antes de enviar comunicação
- ✅ Determinar base legal (Art. 7º e 11)
- ✅ Aplicar overrides para CRITICAL/HIGH
- ✅ Validar consentimento e expiração
- ✅ Verificar quiet hours e opt-out

**Principais Métodos**:
- `check_compliance()`: Verificação principal
- `determine_legal_basis()`: Determina base legal
- `check_quiet_hours()`: Valida horários silenciosos

---

### 2. Preferences Service

**Arquivo**: `comunicacao/lgpd/preferences_service.py`

**Responsabilidades**:
- ✅ CRUD de preferências de comunicação
- ✅ Gerenciar consentimento (grant/withdraw)
- ✅ Opt-in/opt-out por canal
- ✅ Configurar quiet hours

**Principais Métodos**:
- `get_preferences()`: Buscar preferências
- `update_preferences()`: Atualizar preferências
- `grant_consent()`: Conceder consentimento
- `withdraw_consent()`: Revogar consentimento
- `opt_out_channel()`: Desabilitar canal
- `opt_in_channel()`: Habilitar canal

---

### 3. Audit Trail Service

**Arquivo**: `comunicacao/audit/audit_service.py`

**Responsabilidades**:
- ✅ Logar todas as comunicações
- ✅ Logar decisões LGPD
- ✅ Gerenciar hash chain (blockchain simplificado)
- ✅ Pseudonimizar IDs de pacientes
- ✅ Verificar integridade da cadeia

**Principais Métodos**:
- `log_communication()`: Logar comunicação
- `log_lgpd_decision()`: Logar decisão LGPD
- `verify_chain_integrity()`: Verificar integridade

---

### 4. Data Subject Service

**Arquivo**: `comunicacao/lgpd/data_subject_service.py`

**Responsabilidades**:
- ✅ Exportar dados do paciente (Art. 18, II)
- ✅ Anonimizar dados (Art. 18, IV)
- ✅ Fornecer histórico de consentimento
- ✅ Fornecer histórico de comunicações

**Principais Métodos**:
- `export_data()`: Exportar dados (JSON/FHIR)
- `anonymize()`: Anonimizar dados
- `get_consent_history()`: Histórico de consentimento
- `get_communication_history()`: Histórico de comunicações

---

### 5. LGPD Compliance Adapter

**Arquivo**: `comunicacao/routing/lgpd_adapter.py`

**Responsabilidades**:
- ✅ Integrar D6 com D1 (Routing Engine)
- ✅ Implementar protocolo `LGPDComplianceGateway`
- ✅ Converter formatos entre D1 e D6
- ✅ Logar decisões em audit trail

---

## 🗄️ Banco de Dados

### Tabelas (3)

1. **communication_preferences** (16 colunas)
   - Preferências de comunicação por paciente
   - Consentimento e expiração
   - Quiet hours
   - Opt-in/opt-out por canal (6 canais)

2. **consent_log** (6 colunas)
   - Histórico imutável de consentimento
   - Append-only (triggers bloqueiam UPDATE/DELETE)

3. **audit_trail** (21 colunas)
   - Trilha imutável de comunicações
   - Hash chain (SHA-256)
   - Pseudonimização de IDs
   - Append-only (triggers bloqueiam UPDATE/DELETE)

### Índices (11)

- 1 índice em `communication_preferences`
- 2 índices em `consent_log`
- 6 índices em `audit_trail`
- 2 índices UNIQUE para integridade

### Triggers (5)

- `prevent_audit_trail_update/delete`: Imutabilidade
- `prevent_consent_log_update/delete`: Imutabilidade
- `update_communication_preferences_updated_at`: Auto-update

---

## 🌐 API Endpoints (15)

### Preferences (5)
- `GET /api/v1/lgpd/preferences/{patient_id}`: Buscar preferências
- `PUT /api/v1/lgpd/preferences/{patient_id}`: Atualizar preferências
- `PUT /api/v1/lgpd/preferences/{patient_id}/quiet-hours`: Configurar quiet hours
- `POST /api/v1/lgpd/preferences/{patient_id}/opt-out/{channel}`: Opt-out
- `POST /api/v1/lgpd/preferences/{patient_id}/opt-in/{channel}`: Opt-in

### Consent (3)
- `POST /api/v1/lgpd/consent/{patient_id}`: Conceder consentimento
- `DELETE /api/v1/lgpd/consent/{patient_id}`: Revogar consentimento
- `GET /api/v1/lgpd/consent/{patient_id}/history`: Histórico

### Audit (3)
- `GET /api/v1/lgpd/audit`: Listar audit trail
- `GET /api/v1/lgpd/audit/intent/{intent_id}`: Audit por intent
- `GET /api/v1/lgpd/audit/patient/{patient_id}`: Audit por paciente

### Data Subject Rights (2)
- `GET /api/v1/lgpd/export/{patient_id}`: Exportar dados (JSON/FHIR)
- `POST /api/v1/lgpd/anonymize/{patient_id}`: Anonimizar dados

### Compliance (2)
- `GET /api/v1/lgpd/compliance-report`: Relatório de conformidade
- `GET /api/v1/lgpd/verify-chain`: Verificar integridade da hash chain

---

## 📚 Documentação

1. **CONFORMIDADE_LEGAL.md**: Mapeamento de artigos LGPD para features
2. **GUIA_DPO.md**: Guia operacional para DPO
3. **TERMO_CONSENTIMENTO.md**: Template de termo de consentimento
4. **INTEGRACAO_D1.md**: Guia de integração com Routing Engine

---

## 🧪 Testes

### Unit Tests (3 arquivos)
- `tests/test_lgpd_compliance.py`: LGPDComplianceService (18 testes)
- `tests/test_lgpd_preferences.py`: PreferencesService (10 testes)
- `tests/test_lgpd_audit.py`: AuditTrailService (8 testes)

### Integration Tests (1 arquivo)
- `tests/integration/test_d6_lgpd_integration.py`: D6 ↔ D1 (3 testes)

**Total**: 39 testes

**Cobertura Target**: ≥90% (requisito regulatório)

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
LGPD_CONSENT_EXPIRATION_DAYS=365
LGPD_ANONYMIZATION_HASH_SALT=your-secret-salt-here
```

---

## 📊 Estatísticas

| Métrica | Valor |
|---------|-------|
| **Linhas de Código** | ~2,562 |
| **Arquivos Criados** | 17 |
| **Serviços** | 4 |
| **API Endpoints** | 15 |
| **Tabelas** | 3 |
| **Triggers** | 5 |
| **Índices** | 11 |
| **Testes** | 39 |
| **Documentos** | 4 |

---

## 🚀 Como Usar

Ver: `INTEGRACAO_D1.md`

---

## 📞 Suporte

**DPO**: dpo@intellicare.com.br  
**Equipe Técnica**: dev@intellicare.com.br

