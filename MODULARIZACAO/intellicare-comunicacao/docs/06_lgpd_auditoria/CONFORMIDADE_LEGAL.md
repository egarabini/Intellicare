# Conformidade Legal LGPD - Módulo Comunicação

## 📋 Visão Geral

Este documento mapeia as funcionalidades do módulo **intellicare-comunicacao** aos artigos da **Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018)**, demonstrando conformidade legal.

---

## 🏛️ Bases Legais para Tratamento de Dados (Art. 7º)

### Art. 7º, I - Consentimento do Titular

**Texto Legal**:
> "mediante o fornecimento de consentimento pelo titular"

**Implementação**:
- ✅ **CommunicationPreference.consent_given**: Flag de consentimento
- ✅ **CommunicationPreference.consent_given_at**: Timestamp de concessão
- ✅ **CommunicationPreference.consent_version**: Versão do termo aceito
- ✅ **CommunicationPreference.consent_expires_at**: Data de expiração
- ✅ **ConsentLogEntry**: Histórico imutável de consentimento
- ✅ **PreferencesService.grant_consent()**: Conceder consentimento
- ✅ **PreferencesService.withdraw_consent()**: Revogar consentimento

**Código**:
```python
# comunicacao/lgpd/preferences_service.py
async def grant_consent(self, patient_id: str, version: str) -> CommunicationPreference:
    """Concede consentimento para comunicações."""
    # Registra consentimento com timestamp e versão
    # Cria entrada imutável em consent_log
```

---

### Art. 7º, II - Cumprimento de Obrigação Legal

**Texto Legal**:
> "para o cumprimento de obrigação legal ou regulatória pelo controlador"

**Implementação**:
- ✅ **LegalBasis.LEGAL_OBLIGATION**: Base legal para obrigações regulatórias
- ✅ **AuditTrailService**: Retenção de 5 anos (requisito legal)

**Exemplo**: Notificações obrigatórias do SUS, alertas de farmacovigilância.

---

### Art. 7º, VII - Tutela da Saúde

**Texto Legal**:
> "para a tutela da saúde, exclusivamente, em procedimento realizado por profissionais de saúde, serviços de saúde ou autoridade sanitária"

**Implementação**:
- ✅ **LegalBasis.HEALTH_PROTECTION**: Base legal para proteção da saúde
- ✅ **LGPDComplianceService**: Override para severidade HIGH em clinical_alert
- ✅ **Keycloak Integration**: Autenticação de profissionais de saúde

**Código**:
```python
# comunicacao/lgpd/compliance_service.py
if severity == "HIGH" and category in {"clinical_alert", "escalation"}:
    return LGPDDecision(
        allowed=True,
        legal_basis=LegalBasis.HEALTH_PROTECTION,
        reason="Alerta clínico de alta prioridade - Art. 7º, VII LGPD",
        override_applied=True,
    )
```

---

### Art. 7º, VIII - Proteção ao Interesse Público

**Texto Legal**:
> "quando necessário para atender aos interesses legítimos do controlador ou de terceiro, exceto no caso de prevalecerem direitos e liberdades fundamentais do titular"

**Implementação**:
- ✅ **LegalBasis.PUBLIC_INTEREST**: Base legal para interesse público (SUS)

**Exemplo**: Campanhas de vacinação, alertas epidemiológicos.

---

## 🏥 Tratamento de Dados Sensíveis de Saúde (Art. 11)

### Art. 11, II, f - Proteção da Vida

**Texto Legal**:
> "para a proteção da vida ou da incolumidade física do titular ou de terceiro"

**Implementação**:
- ✅ **LegalBasis.VITAL_PROTECTION**: Base legal para proteção da vida
- ✅ **LGPDComplianceService**: Override para severidade CRITICAL
- ✅ **Override ignora**: Consentimento, quiet hours, opt-out

**Código**:
```python
# comunicacao/lgpd/compliance_service.py
if severity == "CRITICAL":
    return LGPDDecision(
        allowed=True,
        legal_basis=LegalBasis.VITAL_PROTECTION,
        reason="Alerta crítico - proteção da vida (Art. 7º, VII + Art. 11, II, f)",
        override_applied=True,
    )
```

**Exemplo**: Alerta de parada cardíaca, reação alérgica grave, risco de morte iminente.

---

## 👤 Direitos do Titular (Art. 18)

### Art. 18, I - Confirmação de Tratamento

**Texto Legal**:
> "confirmação da existência de tratamento"

**Implementação**:
- ✅ **GET /api/v1/lgpd/preferences/{patient_id}**: Consultar preferências
- ✅ **GET /api/v1/lgpd/audit**: Consultar audit trail

---

### Art. 18, II - Acesso aos Dados

**Texto Legal**:
> "acesso aos dados"

**Implementação**:
- ✅ **DataSubjectService.export_data()**: Exportação completa de dados
- ✅ **GET /api/v1/lgpd/export/{patient_id}**: Endpoint de exportação
- ✅ **Formatos**: JSON e FHIR R4

**Código**:
```python
# comunicacao/lgpd/data_subject_service.py
async def export_data(self, patient_id: str, format: str = "json") -> dict:
    """Exporta todos os dados do paciente (Art. 18, II)."""
    # Retorna: preferências, consentimento, histórico de comunicações
```

---

### Art. 18, III - Correção de Dados

**Texto Legal**:
> "correção de dados incompletos, inexatos ou desatualizados"

**Implementação**:
- ✅ **PreferencesService.update_preferences()**: Atualizar preferências
- ✅ **PUT /api/v1/lgpd/preferences/{patient_id}**: Endpoint de atualização

---

### Art. 18, IV - Anonimização

**Texto Legal**:
> "anonimização, bloqueio ou eliminação de dados desnecessários, excessivos ou tratados em desconformidade"

**Implementação**:
- ✅ **DataSubjectService.anonymize()**: Anonimização de dados
- ✅ **POST /api/v1/lgpd/anonymize/{patient_id}**: Endpoint de anonimização
- ✅ **HashChainManager**: Pseudonimização em audit trail

**Código**:
```python
# comunicacao/lgpd/data_subject_service.py
async def anonymize(self, patient_id: str) -> dict:
    """Anonimiza dados do paciente (Art. 18, IV)."""
    # Remove preferências, mantém audit trail pseudonimizado
```

---

### Art. 18, V - Portabilidade

**Texto Legal**:
> "portabilidade dos dados a outro fornecedor de serviço ou produto, mediante requisição expressa"

**Implementação**:
- ✅ **FHIRCommunicationBuilder**: Exportação em formato FHIR R4 (padrão internacional)
- ✅ **GET /api/v1/lgpd/export/{patient_id}?format=fhir**: Exportação FHIR

---

### Art. 18, VI - Eliminação

**Texto Legal**:
> "eliminação dos dados pessoais tratados com o consentimento do titular"

**Implementação**:
- ✅ **DataSubjectService.anonymize()**: Eliminação via anonimização
- ✅ **Audit Trail**: Mantido por 5 anos (requisito legal), mas pseudonimizado

---

### Art. 18, IX - Revogação do Consentimento

**Texto Legal**:
> "revogação do consentimento"

**Implementação**:
- ✅ **PreferencesService.withdraw_consent()**: Revogar consentimento
- ✅ **DELETE /api/v1/lgpd/consent/{patient_id}**: Endpoint de revogação
- ✅ **ConsentLogEntry**: Histórico imutável de revogações

---

## 🔒 Segurança e Integridade (Art. 46)

### Art. 46 - Medidas de Segurança

**Texto Legal**:
> "Os agentes de tratamento devem adotar medidas de segurança, técnicas e administrativas aptas a proteger os dados pessoais"

**Implementação**:

#### 1. **Hash Chain (Blockchain Simplificado)**
- ✅ **SHA-256**: Algoritmo criptográfico robusto
- ✅ **Imutabilidade**: Triggers bloqueiam UPDATE/DELETE
- ✅ **Integridade**: Qualquer adulteração quebra a cadeia
- ✅ **Verificação**: Endpoint `/api/v1/lgpd/verify-chain`

#### 2. **Pseudonimização**
- ✅ **recipient_hash**: Hash do recipient_id
- ✅ **patient_hash**: Hash do patient_id
- ✅ **Salt configurável**: `LGPD_ANONYMIZATION_HASH_SALT`

#### 3. **Controle de Acesso**
- ✅ **Keycloak SSO**: Autenticação centralizada
- ✅ **RBAC**: Roles específicas (data_protection_officer, audit_read)
- ✅ **Audit Trail**: Rastreamento de todos os acessos

#### 4. **Retenção de Dados**
- ✅ **5 anos**: Audit trail (requisito legal)
- ✅ **Expiração**: Consentimento expira após 365 dias (configurável)

---

## 📊 Relatório de Conformidade

| Artigo LGPD | Requisito | Status | Implementação |
|-------------|-----------|--------|---------------|
| Art. 7º, I | Consentimento | ✅ | PreferencesService, ConsentLogEntry |
| Art. 7º, II | Obrigação Legal | ✅ | LegalBasis.LEGAL_OBLIGATION |
| Art. 7º, VII | Tutela da Saúde | ✅ | LegalBasis.HEALTH_PROTECTION, HIGH override |
| Art. 7º, VIII | Interesse Público | ✅ | LegalBasis.PUBLIC_INTEREST |
| Art. 11, II, f | Proteção da Vida | ✅ | LegalBasis.VITAL_PROTECTION, CRITICAL override |
| Art. 18, I | Confirmação | ✅ | GET /api/v1/lgpd/preferences |
| Art. 18, II | Acesso | ✅ | DataSubjectService.export_data() |
| Art. 18, III | Correção | ✅ | PreferencesService.update_preferences() |
| Art. 18, IV | Anonimização | ✅ | DataSubjectService.anonymize() |
| Art. 18, V | Portabilidade | ✅ | FHIR R4 export |
| Art. 18, VI | Eliminação | ✅ | DataSubjectService.anonymize() |
| Art. 18, IX | Revogação | ✅ | PreferencesService.withdraw_consent() |
| Art. 46 | Segurança | ✅ | Hash chain, pseudonimização, RBAC |

---

## 📚 Referências

- **LGPD**: Lei nº 13.709/2018
- **FHIR R4**: https://hl7.org/fhir/R4/
- **Keycloak**: https://www.keycloak.org/
- **PostgreSQL Triggers**: Imutabilidade de audit trail

