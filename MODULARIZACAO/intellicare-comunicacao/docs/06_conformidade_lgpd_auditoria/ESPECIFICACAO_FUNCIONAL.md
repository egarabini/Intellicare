# Domínio 6 — Conformidade LGPD e Auditoria
## Especificação Funcional Detalhada

**Identificadores**: EF-COM-050, EF-COM-051  
**Prioridade Global**: CRÍTICA (regulatória)  
**Sprint**: S4–S5 (paralelo com D4)  
**Dependências**: D1 (delivery_results), D5 (consolidação)  
**Dependentes**: D7 (dashboards de conformidade)

---

## 1. OBJETIVO

Implementar a camada de conformidade com a LGPD (Lei Geral de Proteção de Dados — Lei nº 13.709/2018) e auditoria completa de todas as comunicações, incluindo:

1. **Preferências de comunicação do paciente** (opt-in/opt-out por canal)
2. **Horários silenciosos** (quiet hours — não perturbar)
3. **Exceção para alertas CRITICAL** conforme Art. 7º, VII LGPD (tutela da saúde)
4. **Trilha de auditoria imutável** de todas as comunicações
5. **Exportação FHIR Communication** para interoperabilidade
6. **Consentimento rastreável** com timestamp e metadados
7. **Direito de acesso** (Art. 18) — exportação de dados do paciente
8. **Direito de eliminação** (Art. 18, VI) — anonimização de dados

**Contexto Legal**: No SUS, a base legal para processamento de dados de saúde é o Art. 7º, VII (tutela da saúde) e Art. 11, II, f (proteção da vida). Alertas CRITICAL podem ser enviados mesmo sem consentimento explícito.

---

## 2. CONTEXTO ARQUITETURAL

```
┌────────────────────────────────────────────────────────────────────┐
│                    intellicare-comunicacao                          │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │              RoutingEngine (D1)                           │     │
│  │                                                          │     │
│  │  ANTES de rotear, consulta:                              │     │
│  │  ┌──────────────────────────────┐                        │     │
│  │  │ LGPDComplianceService        │                        │     │
│  │  │ ├── can_send(patient, channel)?                       │     │
│  │  │ ├── is_quiet_hours(patient)?                          │     │
│  │  │ └── is_critical_override(severity)?                   │     │
│  │  └──────────────────────────────┘                        │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │              AuditTrailService                            │     │
│  │                                                          │     │
│  │  DEPOIS de cada comunicação:                             │     │
│  │  ├── Registra audit_entry (imutável)                     │     │
│  │  ├── Hash chain (integridade)                            │     │
│  │  └── Gera FHIR Communication (se aplicável)             │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │              DataSubjectService                           │     │
│  │                                                          │     │
│  │  Direitos do titular (Art. 18 LGPD):                     │     │
│  │  ├── export_data(patient_id) → JSON/FHIR                │     │
│  │  ├── anonymize(patient_id)                              │     │
│  │  └── consent_log(patient_id)                            │     │
│  └──────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────┘
```

---

## 3. EF-COM-050 — Preferências LGPD do Paciente

### 3.1 Modelo de Consentimento

```python
from enum import Enum
from datetime import datetime, time
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class ConsentStatus(str, Enum):
    """Status do consentimento."""
    GRANTED = "granted"             # Consentimento concedido
    REVOKED = "revoked"             # Consentimento revogado
    PENDING = "pending"             # Aguardando resposta
    NOT_APPLICABLE = "not_applicable"  # Canal não aplicável (ex: sem telefone)


class LegalBasis(str, Enum):
    """Base legal LGPD para envio de comunicação."""
    CONSENT = "consent"                    # Art. 7, I — consentimento
    HEALTH_PROTECTION = "health_protection"  # Art. 7, VII — tutela da saúde
    LIFE_PROTECTION = "life_protection"    # Art. 11, II, f — proteção da vida
    LEGAL_OBLIGATION = "legal_obligation"  # Art. 7, II — obrigação legal
    PUBLIC_INTEREST = "public_interest"    # Art. 7, III — políticas públicas (SUS)


class CommunicationPreference(BaseModel):
    """Preferências de comunicação de um paciente."""
    
    id: UUID = Field(default_factory=uuid4)
    patient_id: str
    
    # Consentimento por canal
    channel_preferences: List[ChannelPreference]
    
    # Horários silenciosos
    quiet_hours_enabled: bool = True
    quiet_hours_start: time = time(22, 0)      # 22:00
    quiet_hours_end: time = time(7, 0)          # 07:00
    quiet_hours_timezone: str = "America/Sao_Paulo"
    
    # Exceções
    allow_critical_anytime: bool = True         # CRITICAL ignora quiet hours
    
    # Preferências de idioma
    preferred_language: str = "pt-BR"
    
    # Contato preferido
    preferred_channel: Optional[str] = "whatsapp"  # Canal favorito
    
    # Metadata de consentimento
    consent_given_at: Optional[datetime]
    consent_given_via: Optional[str]             # "portal", "whatsapp", "presencial"
    consent_version: str = "1.0"                 # Versão do termo de consentimento
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChannelPreference(BaseModel):
    """Preferência de um canal específico."""
    
    channel: str                              # "whatsapp", "sms", "email", "push"
    status: ConsentStatus = ConsentStatus.PENDING
    
    # Detalhes
    contact_value: Optional[str]              # +5511999..., email@..., etc.
    verified: bool = False                    # Contato verificado?
    
    # Tipos de comunicação permitidos
    allow_alerts: bool = True                 # Alertas clínicos
    allow_reminders: bool = True              # Lembretes (consulta, medicação)
    allow_teleconsult: bool = True            # Convites de teleconsulta
    allow_educational: bool = True            # Material educativo
    allow_surveys: bool = False               # Pesquisas de satisfação (default: off)
    
    # Histórico
    status_changed_at: Optional[datetime]
    status_changed_reason: Optional[str]      # "patient_request", "system_error", etc.
```

### 3.2 LGPDComplianceService

```python
class LGPDComplianceService:
    """
    Serviço de conformidade LGPD.
    
    Consultado pelo RoutingEngine ANTES de enviar qualquer comunicação.
    """
    
    def __init__(self, db: AsyncSession, config: LGPDConfig):
        self._db = db
        self._config = config
    
    async def can_send(
        self,
        patient_id: str,
        channel: str,
        intent_type: str,
        severity: str
    ) -> LGPDDecision:
        """
        Decide se uma comunicação pode ser enviada.
        
        Lógica de decisão:
        
        1. Se severity == CRITICAL:
           → PERMITIDO (Art. 7, VII — tutela da saúde)
           → legal_basis = HEALTH_PROTECTION
           → Registrar que foi enviado sem consentimento
        
        2. Se severity == HIGH e intent_type == CLINICAL_ALERT:
           → PERMITIDO (Art. 11, II, f — proteção da vida)
           → legal_basis = LIFE_PROTECTION
           → Mas respeitar quiet hours se possível (agendar)
        
        3. Para demais:
           → Buscar CommunicationPreference do paciente
           → Verificar consent do canal
           → Verificar tipo de comunicação permitido
           → Verificar quiet hours
           → Se consent == REVOKED → BLOQUEADO
           → Se consent == PENDING → BLOQUEADO (exceto CRITICAL/HIGH)
           → Se quiet hours → ADIADO (colocar na fila para envio pós-quiet)
        """
        # 1. Override para CRITICAL
        if severity == "CRITICAL":
            return LGPDDecision(
                allowed=True,
                legal_basis=LegalBasis.HEALTH_PROTECTION,
                reason="Art. 7, VII LGPD — tutela da saúde em procedimento por profissionais da área de saúde",
                override_applied=True
            )
        
        # 2. Override para HIGH + alerta clínico
        if severity == "HIGH" and intent_type in ["clinical_alert", "lab_critical"]:
            return LGPDDecision(
                allowed=True,
                legal_basis=LegalBasis.LIFE_PROTECTION,
                reason="Art. 11, II, f LGPD — proteção da vida do titular",
                override_applied=True,
                respect_quiet_hours=True  # Tentar respeitar, mas enviar de todo modo
            )
        
        # 3. Buscar preferências
        prefs = await self._get_preferences(patient_id)
        if not prefs:
            # Sem preferências registradas → BLOQUEAR (princípio da cautela)
            return LGPDDecision(
                allowed=False,
                legal_basis=None,
                reason="Preferências de comunicação não registradas. Consentimento necessário.",
                override_applied=False
            )
        
        # 4. Verificar consent do canal
        channel_pref = self._find_channel_pref(prefs, channel)
        if not channel_pref or channel_pref.status == ConsentStatus.REVOKED:
            return LGPDDecision(
                allowed=False,
                legal_basis=None,
                reason=f"Consentimento revogado para canal {channel}",
                override_applied=False
            )
        
        if channel_pref.status == ConsentStatus.PENDING:
            return LGPDDecision(
                allowed=False,
                legal_basis=None,
                reason=f"Consentimento pendente para canal {channel}",
                override_applied=False
            )
        
        # 5. Verificar tipo de comunicação
        if not self._is_comm_type_allowed(channel_pref, intent_type):
            return LGPDDecision(
                allowed=False,
                legal_basis=None,
                reason=f"Tipo de comunicação '{intent_type}' não autorizado pelo paciente",
                override_applied=False
            )
        
        # 6. Verificar quiet hours
        if await self._is_quiet_hours(prefs):
            return LGPDDecision(
                allowed=False,
                legal_basis=LegalBasis.CONSENT,
                reason="Horário silencioso ativo. Comunicação será adiada.",
                override_applied=False,
                defer_until=self._next_active_time(prefs)
            )
        
        # 7. Consentimento OK
        return LGPDDecision(
            allowed=True,
            legal_basis=LegalBasis.CONSENT,
            reason="Consentimento válido",
            override_applied=False
        )
    
    async def _is_quiet_hours(self, prefs: CommunicationPreference) -> bool:
        """Verifica se estamos em horário silencioso do paciente."""
        if not prefs.quiet_hours_enabled:
            return False
        
        import pytz
        tz = pytz.timezone(prefs.quiet_hours_timezone)
        now = datetime.now(tz).time()
        
        start = prefs.quiet_hours_start
        end = prefs.quiet_hours_end
        
        if start <= end:
            return start <= now <= end
        else:
            # Horário que cruza meia-noite (ex: 22:00 - 07:00)
            return now >= start or now <= end
    
    def _is_comm_type_allowed(self, pref: ChannelPreference, intent_type: str) -> bool:
        """Verifica se o tipo de comunicação é permitido no canal."""
        mapping = {
            "clinical_alert": pref.allow_alerts,
            "lab_result": pref.allow_alerts,
            "medication_reminder": pref.allow_reminders,
            "teleconsult_invite": pref.allow_teleconsult,
            "teleconsult_reminder": pref.allow_reminders,
            "educational_content": pref.allow_educational,
            "satisfaction_survey": pref.allow_surveys,
        }
        return mapping.get(intent_type, pref.allow_alerts)


class LGPDDecision(BaseModel):
    """Resultado da decisão de conformidade LGPD."""
    allowed: bool
    legal_basis: Optional[LegalBasis]
    reason: str
    override_applied: bool = False        # True se usou exceção CRITICAL
    respect_quiet_hours: bool = False     # True se deve tentar respeitar quiet hours
    defer_until: Optional[datetime] = None  # Se adiado, quando enviar


class LGPDConfig(BaseModel):
    """Configuração de conformidade LGPD."""
    
    # Alertas CRITICAL sempre enviados
    critical_override_enabled: bool = True
    
    # Alertas HIGH enviados com base legal de proteção à vida
    high_alert_override_enabled: bool = True
    
    # Pacientes sem consentimento: bloquear tudo exceto CRITICAL
    block_without_consent: bool = True
    
    # Quiet hours padrão (se paciente não definiu)
    default_quiet_hours_start: str = "22:00"
    default_quiet_hours_end: str = "07:00"
    
    # Retenção de dados
    audit_retention_years: int = 5         # Manter audit por 5 anos (requisito legal)
    delivery_retention_days: int = 365     # Delivery results por 1 ano
    
    # Consentimento
    consent_version: str = "1.0"
    consent_renewal_days: int = 365        # Renovar consentimento anualmente
```

### 3.3 Integração com RoutingEngine (D1)

O RoutingEngine deve consultar `LGPDComplianceService.can_send()` **antes** de enviar cada comunicação:

```python
# No RoutingEngine (D1), adicionar ao fluxo:

async def route(self, intent: CommunicationIntent) -> RoutingResult:
    # ... (passos 1-4 existentes)
    
    # 5. LGPD Compliance Check (NOVO)
    if intent.patient_id:
        lgpd_decision = await self._lgpd.can_send(
            patient_id=intent.patient_id,
            channel=step.channel,
            intent_type=intent.intent_type,
            severity=intent.severity
        )
        
        if not lgpd_decision.allowed:
            if lgpd_decision.defer_until:
                # Agendar envio para depois do quiet hours
                await self._scheduler.schedule_delivery(
                    intent, step, send_at=lgpd_decision.defer_until
                )
                delivery.status = "deferred"
                delivery.deferred_until = lgpd_decision.defer_until
            else:
                # Bloqueado por LGPD
                delivery.status = "blocked_lgpd"
                delivery.lgpd_reason = lgpd_decision.reason
            
            # Registrar na auditoria
            await self._audit.log_lgpd_decision(intent, lgpd_decision)
            continue  # Tentar próximo canal se cascading
        
        # Registrar base legal usada
        delivery.legal_basis = lgpd_decision.legal_basis
        delivery.lgpd_override = lgpd_decision.override_applied
    
    # ... (continuar com envio)
```

### 3.4 API Endpoints — Preferências

```yaml
# ── Preferências do Paciente ──
GET /api/v1/lgpd/preferences/{patient_id}
  Description: Retorna preferências de comunicação do paciente
  Auth: Keycloak (patient (own), doctor, care_coordinator, admin)
  Response 200: CommunicationPreference

PUT /api/v1/lgpd/preferences/{patient_id}
  Description: Atualiza preferências de comunicação
  Auth: Keycloak (patient (own), admin)
  Body: CommunicationPreference (parcial)
  Response 200: CommunicationPreference
  Note: Cada alteração gera entrada no consent_log

POST /api/v1/lgpd/preferences/{patient_id}/opt-in
  Description: Opt-in em um canal específico
  Auth: Keycloak (patient (own), admin)
  Body: { channel: str, contact_value: Optional[str] }
  Response 200: { status: "granted", channel: str }

POST /api/v1/lgpd/preferences/{patient_id}/opt-out
  Description: Opt-out de um canal específico
  Auth: Keycloak (patient (own), admin)
  Body: { channel: str, reason: Optional[str] }
  Response 200: { status: "revoked", channel: str }

POST /api/v1/lgpd/preferences/{patient_id}/opt-out-all
  Description: Opt-out de todos os canais (exceto CRITICAL)
  Auth: Keycloak (patient (own), admin)
  Body: { reason: Optional[str] }
  Response 200: { revoked_channels: List[str], note: "Alertas CRITICAL continuarão sendo enviados conforme Art. 7, VII LGPD" }

PUT /api/v1/lgpd/preferences/{patient_id}/quiet-hours
  Description: Configurar horários silenciosos
  Auth: Keycloak (patient (own), admin)
  Body: { enabled: bool, start: str, end: str, timezone: str }
  Response 200: CommunicationPreference
```

### 3.5 Consent Log

```python
class ConsentLogEntry(BaseModel):
    """Registro de consentimento (imutável)."""
    
    id: UUID = Field(default_factory=uuid4)
    patient_id: str
    
    # O que mudou
    action: str                          # "opt_in" | "opt_out" | "update_preferences" | "initial_consent"
    channel: Optional[str]               # Canal afetado (ou null se geral)
    
    # Estado
    previous_status: Optional[str]
    new_status: str
    
    # Detalhes
    reason: Optional[str]                # Motivo do opt-out
    consent_version: str                 # Versão do termo
    legal_basis: LegalBasis              # Base legal
    
    # Quem
    performed_by: str                    # user_id (paciente ou admin)
    performed_via: str                   # "portal" | "whatsapp" | "sms" | "presencial" | "api"
    ip_address: Optional[str]
    user_agent: Optional[str]
    
    # Quando (imutável)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 4. EF-COM-051 — Trilha de Auditoria

### 4.1 Descrição Funcional

Todas as comunicações devem ter uma trilha de auditoria imutável que permite:

1. **Rastrear** quem enviou o quê, para quem, quando e por quê
2. **Provar conformidade** em caso de auditoria regulatória
3. **Verificar integridade** via hash chain (detectar adulteração)
4. **Exportar** no formato FHIR Communication
5. **Reter** por no mínimo 5 anos (requisito legal)

### 4.2 AuditTrailService

```python
class AuditTrailService:
    """
    Serviço de trilha de auditoria para comunicações.
    
    Cada comunicação gera uma entrada de audit imutável.
    Hash chain garante integridade (semelhante a blockchain simplificado).
    """
    
    def __init__(self, db: AsyncSession):
        self._db = db
    
    async def log_communication(
        self,
        intent: CommunicationIntent,
        delivery: DeliveryResult,
        lgpd_decision: LGPDDecision,
    ) -> AuditEntry:
        """
        Registra comunicação na trilha de auditoria.
        
        Chamado APÓS cada tentativa de envio (sucesso ou falha).
        
        Fluxo:
        1. Buscar hash do último audit entry (para chain)
        2. Criar AuditEntry com todos os dados
        3. Calcular hash do entry atual (SHA-256)
        4. Salvar entry (INSERT ONLY — nunca UPDATE)
        5. Se aplicável, gerar FHIR Communication
        """
        # 1. Hash chain
        previous_hash = await self._get_last_hash()
        
        # 2. Criar entry
        entry = AuditEntry(
            # Comunicação
            intent_id=str(intent.id) if hasattr(intent, 'id') else None,
            delivery_id=str(delivery.id) if delivery else None,
            
            # O quê
            intent_type=intent.intent_type,
            template_name=intent.template_name,
            channel=delivery.channel if delivery else "none",
            
            # Para quem (pseudonimizado)
            recipient_type=intent.recipient_type,
            recipient_hash=self._hash_recipient(intent.recipient_id),
            patient_hash=self._hash_recipient(intent.patient_id) if intent.patient_id else None,
            
            # Resultado
            status=delivery.status if delivery else "blocked",
            error_message=delivery.error_message if delivery and delivery.status == "failed" else None,
            
            # LGPD
            legal_basis=lgpd_decision.legal_basis.value if lgpd_decision.legal_basis else None,
            lgpd_override=lgpd_decision.override_applied,
            lgpd_reason=lgpd_decision.reason,
            consent_status=lgpd_decision.consent_status if hasattr(lgpd_decision, 'consent_status') else None,
            
            # Severidade
            severity=intent.severity,
            
            # Fonte
            source_module=intent.source_module,
            source_event_id=intent.source_event_id,
            
            # Hash chain
            previous_hash=previous_hash,
        )
        
        # 3. Calcular hash
        entry.entry_hash = self._calculate_hash(entry)
        
        # 4. Salvar
        await self._save(entry)
        
        return entry
    
    async def log_lgpd_decision(
        self,
        intent: CommunicationIntent,
        decision: LGPDDecision,
    ) -> AuditEntry:
        """
        Registra decisão LGPD (quando comunicação é bloqueada ou adiada).
        """
        previous_hash = await self._get_last_hash()
        
        entry = AuditEntry(
            intent_type=intent.intent_type,
            channel="none",
            recipient_type=intent.recipient_type,
            recipient_hash=self._hash_recipient(intent.recipient_id),
            status="blocked_lgpd" if not decision.allowed else "deferred",
            legal_basis=decision.legal_basis.value if decision.legal_basis else None,
            lgpd_override=decision.override_applied,
            lgpd_reason=decision.reason,
            severity=intent.severity,
            source_module=intent.source_module,
            previous_hash=previous_hash,
        )
        
        entry.entry_hash = self._calculate_hash(entry)
        await self._save(entry)
        
        return entry
    
    def _calculate_hash(self, entry: AuditEntry) -> str:
        """
        Calcula SHA-256 do entry para integridade.
        
        Inclui: previous_hash + intent_type + channel + recipient_hash + 
                status + legal_basis + severity + created_at
        """
        import hashlib
        
        data = (
            f"{entry.previous_hash or ''}"
            f"{entry.intent_type}"
            f"{entry.channel}"
            f"{entry.recipient_hash}"
            f"{entry.status}"
            f"{entry.legal_basis or ''}"
            f"{entry.severity}"
            f"{entry.created_at.isoformat()}"
        )
        
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _hash_recipient(self, recipient_id: Optional[str]) -> Optional[str]:
        """
        Pseudonimiza recipient_id para auditoria.
        
        Usa HMAC-SHA256 com secret key para que o hash seja determinístico
        mas não reversível sem a chave.
        """
        if not recipient_id:
            return None
        
        import hmac
        return hmac.new(
            self._config.hmac_secret.encode(),
            recipient_id.encode(),
            "sha256"
        ).hexdigest()[:16]
    
    async def verify_chain_integrity(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ChainVerificationResult:
        """
        Verifica integridade da hash chain.
        
        Retorna:
        - total_entries: int
        - verified: int
        - broken_at: Optional[int] (ID do entry onde a chain quebra)
        - is_valid: bool
        """
        entries = await self._get_entries_range(start_date, end_date)
        
        for i, entry in enumerate(entries):
            if i == 0:
                continue
            
            expected_previous = entries[i-1].entry_hash
            if entry.previous_hash != expected_previous:
                return ChainVerificationResult(
                    total_entries=len(entries),
                    verified=i,
                    broken_at=entry.id,
                    is_valid=False,
                    error=f"Chain broken at entry {entry.id}: expected previous_hash={expected_previous}, got={entry.previous_hash}"
                )
        
        return ChainVerificationResult(
            total_entries=len(entries),
            verified=len(entries),
            broken_at=None,
            is_valid=True
        )
    
    async def export_fhir_communication(self, audit_entry: AuditEntry) -> Dict:
        """
        Gera recurso FHIR Communication a partir de uma entrada de audit.
        
        Referência: https://hl7.org/fhir/communication.html
        """
        return {
            "resourceType": "Communication",
            "id": str(audit_entry.id),
            "status": self._map_fhir_status(audit_entry.status),
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/communication-category",
                    "code": "notification",
                    "display": "Notification"
                }]
            }],
            "medium": [{
                "coding": [{
                    "system": "http://intellicare.gsi.srv.br/fhir/communication-medium",
                    "code": audit_entry.channel,
                    "display": audit_entry.channel.title()
                }]
            }],
            "subject": {
                "reference": f"Patient/{audit_entry.patient_hash}",
                "display": f"Patient (pseudonymized: {audit_entry.patient_hash})"
            } if audit_entry.patient_hash else None,
            "sent": audit_entry.created_at.isoformat(),
            "payload": [{
                "contentString": f"[{audit_entry.intent_type}] Template: {audit_entry.template_name}"
            }],
            "extension": [
                {
                    "url": "http://intellicare.gsi.srv.br/fhir/lgpd-legal-basis",
                    "valueString": audit_entry.legal_basis or "none"
                },
                {
                    "url": "http://intellicare.gsi.srv.br/fhir/lgpd-override",
                    "valueBoolean": audit_entry.lgpd_override
                },
                {
                    "url": "http://intellicare.gsi.srv.br/fhir/severity",
                    "valueString": audit_entry.severity
                },
                {
                    "url": "http://intellicare.gsi.srv.br/fhir/audit-hash",
                    "valueString": audit_entry.entry_hash
                }
            ]
        }


class AuditEntry(BaseModel):
    """Entrada de auditoria (IMUTÁVEL — apenas INSERT, nunca UPDATE)."""
    
    id: UUID = Field(default_factory=uuid4)
    
    # Comunicação
    intent_id: Optional[str]
    delivery_id: Optional[str]
    
    # O quê
    intent_type: str
    template_name: Optional[str]
    channel: str
    
    # Para quem (pseudonimizado)
    recipient_type: str
    recipient_hash: Optional[str]         # HMAC-SHA256 pseudonimizado
    patient_hash: Optional[str]           # HMAC-SHA256 pseudonimizado
    
    # Resultado
    status: str                           # "sent", "delivered", "read", "failed", "blocked_lgpd", "deferred"
    error_message: Optional[str]
    
    # LGPD
    legal_basis: Optional[str]
    lgpd_override: bool = False
    lgpd_reason: Optional[str]
    consent_status: Optional[str]
    
    # Severidade
    severity: str
    
    # Fonte
    source_module: Optional[str]
    source_event_id: Optional[str]
    
    # Hash chain
    previous_hash: Optional[str]
    entry_hash: Optional[str]
    
    # Timestamp (imutável)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChainVerificationResult(BaseModel):
    """Resultado da verificação de integridade."""
    total_entries: int
    verified: int
    broken_at: Optional[UUID]
    is_valid: bool
    error: Optional[str] = None
```

### 4.3 DataSubjectService (Direitos do Titular)

```python
class DataSubjectService:
    """
    Implementa direitos do titular de dados (Art. 18 LGPD).
    """
    
    def __init__(self, db: AsyncSession, audit_service: AuditTrailService):
        self._db = db
        self._audit = audit_service
    
    async def export_patient_data(self, patient_id: str) -> PatientDataExport:
        """
        Art. 18, II — Acesso aos dados.
        
        Exporta todos os dados de comunicação do paciente em formato estruturado.
        
        Inclui:
        1. Preferências de comunicação
        2. Histórico de consentimento
        3. Todas as comunicações enviadas/recebidas
        4. Teleconsultas
        5. FHIR Communications
        
        Dados sensíveis são incluídos (o paciente tem direito a ver seus dados).
        """
        prefs = await self._get_preferences(patient_id)
        consent_log = await self._get_consent_log(patient_id)
        communications = await self._get_communications(patient_id)
        teleconsults = await self._get_teleconsults(patient_id)
        
        return PatientDataExport(
            patient_id=patient_id,
            export_date=datetime.utcnow(),
            preferences=prefs,
            consent_history=consent_log,
            communications=communications,
            teleconsults=teleconsults,
            fhir_communications=[
                await self._audit.export_fhir_communication(c) 
                for c in communications
            ]
        )
    
    async def anonymize_patient(self, patient_id: str, reason: str, performed_by: str) -> AnonymizationResult:
        """
        Art. 18, VI — Eliminação dos dados.
        
        Nota: Em saúde, a eliminação total muitas vezes não é possível
        devido a obrigações legais de retenção. A anonimização é a alternativa.
        
        Fluxo:
        1. Verificar se há obrigação legal de retenção (prontuário: 20 anos, CFM)
        2. Se retenção obrigatória → anonimizar em vez de deletar
        3. Anonimizar:
           a. CommunicationPreference → deletar contact_value, manter canal/status
           b. delivery_results → substituir recipient_id por hash
           c. teleconsult_sessions → substituir patient_name e phone
           d. audit_entries → já pseudonimizados (recipient_hash)
           e. consent_log → manter (prova legal)
        4. Registrar na auditoria: "data_anonymization"
        """
        # Verificar retenção legal
        has_legal_hold = await self._check_legal_hold(patient_id)
        
        if has_legal_hold:
            # Anonimizar em vez de deletar
            result = await self._anonymize(patient_id)
        else:
            # Deletar dados operacionais, manter audit (pseudonimizado)
            result = await self._delete_operational(patient_id)
        
        # Registrar na auditoria
        await self._audit.log_anonymization(patient_id, reason, performed_by, result)
        
        return result
    
    async def get_consent_history(self, patient_id: str) -> List[ConsentLogEntry]:
        """Art. 18, VII — Informação sobre compartilhamento."""
        return await self._get_consent_log(patient_id)
    
    async def get_data_processing_report(self, patient_id: str) -> DataProcessingReport:
        """
        Art. 18, I — Confirmação da existência de tratamento.
        
        Gera relatório de como os dados do paciente foram processados:
        - Quantas comunicações enviadas
        - Quais canais usados
        - Qual base legal
        - Quem acessou (pseudonimizado)
        """


class PatientDataExport(BaseModel):
    """Exportação de dados do paciente."""
    patient_id: str
    export_date: datetime
    preferences: Optional[CommunicationPreference]
    consent_history: List[ConsentLogEntry]
    communications: List[Dict]            # Resumo das comunicações
    teleconsults: List[Dict]              # Resumo das teleconsultas
    fhir_communications: List[Dict]       # FHIR Communication resources
    format: str = "json"                  # "json" | "fhir_bundle"


class AnonymizationResult(BaseModel):
    """Resultado da anonimização."""
    patient_id: str
    records_anonymized: int
    records_deleted: int
    records_retained: int                  # Mantidos por obrigação legal
    has_legal_hold: bool
    completed_at: datetime
```

### 4.4 API Endpoints

```yaml
# ── Preferências LGPD ──
GET /api/v1/lgpd/preferences/{patient_id}
PUT /api/v1/lgpd/preferences/{patient_id}
POST /api/v1/lgpd/preferences/{patient_id}/opt-in
POST /api/v1/lgpd/preferences/{patient_id}/opt-out
POST /api/v1/lgpd/preferences/{patient_id}/opt-out-all
PUT /api/v1/lgpd/preferences/{patient_id}/quiet-hours

# ── Direitos do Titular ──
GET /api/v1/lgpd/data-export/{patient_id}
  Description: Exporta dados do paciente (Art. 18, II)
  Auth: Keycloak (patient (own), admin, data_protection_officer)
  Response 200: PatientDataExport

POST /api/v1/lgpd/anonymize/{patient_id}
  Description: Anonimiza dados do paciente (Art. 18, VI)
  Auth: Keycloak (admin, data_protection_officer)
  Body: { reason: str }
  Response 200: AnonymizationResult

GET /api/v1/lgpd/consent-history/{patient_id}
  Description: Histórico de consentimento (Art. 18, VII)
  Auth: Keycloak (patient (own), admin)
  Response 200: List[ConsentLogEntry]

GET /api/v1/lgpd/processing-report/{patient_id}
  Description: Relatório de processamento (Art. 18, I)
  Auth: Keycloak (patient (own), admin, data_protection_officer)
  Response 200: DataProcessingReport

# ── Auditoria ──
GET /api/v1/audit/entries
  Description: Lista entradas de auditoria
  Auth: Keycloak (admin, auditor, data_protection_officer)
  Query: start_date, end_date, channel, severity, status, page, page_size
  Response 200: { items: List[AuditEntry], total: int }

GET /api/v1/audit/entry/{entry_id}
  Description: Detalhes de uma entrada
  Auth: Keycloak (admin, auditor)
  Response 200: AuditEntry

POST /api/v1/audit/verify-integrity
  Description: Verificar integridade da hash chain
  Auth: Keycloak (admin, auditor, data_protection_officer)
  Body: { start_date: Optional[str], end_date: Optional[str] }
  Response 200: ChainVerificationResult

GET /api/v1/audit/fhir/{entry_id}
  Description: Exporta entrada como FHIR Communication
  Auth: Keycloak (admin, auditor)
  Response 200: FHIR Communication resource

GET /api/v1/audit/fhir-bundle
  Description: Exporta bundle de FHIR Communications
  Auth: Keycloak (admin, auditor)
  Query: patient_id, start_date, end_date
  Response 200: FHIR Bundle

# ── Relatórios de Conformidade ──
GET /api/v1/lgpd/compliance-report
  Description: Relatório de conformidade LGPD
  Auth: Keycloak (admin, data_protection_officer)
  Query: period (month|quarter|year)
  Response 200: {
    total_communications: int,
    by_legal_basis: Dict[str, int],
    critical_overrides: int,
    blocked_by_lgpd: int,
    opt_out_rate: float,
    consent_coverage: float,        # % de pacientes com consentimento
    chain_integrity: bool,
    pending_anonymizations: int
  }
```

---

## 5. SCHEMA SQL

```sql
-- Migration: 2026_02_15_0006_create_lgpd_audit_tables.py
-- Schema: comunicacao_operacional

-- Preferências de comunicação do paciente
CREATE TABLE comunicacao_operacional.communication_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR(200) NOT NULL UNIQUE,
    
    -- Quiet hours
    quiet_hours_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    quiet_hours_start TIME NOT NULL DEFAULT '22:00',
    quiet_hours_end TIME NOT NULL DEFAULT '07:00',
    quiet_hours_timezone VARCHAR(50) NOT NULL DEFAULT 'America/Sao_Paulo',
    
    -- Exceções
    allow_critical_anytime BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Preferências
    preferred_language VARCHAR(10) NOT NULL DEFAULT 'pt-BR',
    preferred_channel VARCHAR(20) DEFAULT 'whatsapp',
    
    -- Consentimento
    consent_given_at TIMESTAMPTZ,
    consent_given_via VARCHAR(50),
    consent_version VARCHAR(10) NOT NULL DEFAULT '1.0',
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prefs_patient ON comunicacao_operacional.communication_preferences(patient_id);

-- Preferências por canal
CREATE TABLE comunicacao_operacional.channel_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    preference_id UUID NOT NULL REFERENCES comunicacao_operacional.communication_preferences(id) ON DELETE CASCADE,
    
    channel VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    contact_value VARCHAR(300),          -- Será anonimizado se solicitado
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    
    allow_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    allow_reminders BOOLEAN NOT NULL DEFAULT TRUE,
    allow_teleconsult BOOLEAN NOT NULL DEFAULT TRUE,
    allow_educational BOOLEAN NOT NULL DEFAULT TRUE,
    allow_surveys BOOLEAN NOT NULL DEFAULT FALSE,
    
    status_changed_at TIMESTAMPTZ,
    status_changed_reason TEXT,
    
    UNIQUE(preference_id, channel)
);

-- Log de consentimento (IMUTÁVEL — apenas INSERT)
CREATE TABLE comunicacao_operacional.consent_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR(200) NOT NULL,
    
    action VARCHAR(50) NOT NULL,
    channel VARCHAR(20),
    
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    
    reason TEXT,
    consent_version VARCHAR(10) NOT NULL,
    legal_basis VARCHAR(50) NOT NULL,
    
    performed_by VARCHAR(200) NOT NULL,
    performed_via VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- SEM updated_at — IMUTÁVEL
);

CREATE INDEX idx_consent_patient ON comunicacao_operacional.consent_log(patient_id);
CREATE INDEX idx_consent_created ON comunicacao_operacional.consent_log(created_at);

-- Trilha de auditoria (IMUTÁVEL — apenas INSERT)
CREATE TABLE comunicacao_operacional.audit_trail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Comunicação
    intent_id VARCHAR(200),
    delivery_id VARCHAR(200),
    
    -- O quê
    intent_type VARCHAR(50) NOT NULL,
    template_name VARCHAR(200),
    channel VARCHAR(20) NOT NULL,
    
    -- Para quem (pseudonimizado)
    recipient_type VARCHAR(50) NOT NULL,
    recipient_hash VARCHAR(64),
    patient_hash VARCHAR(64),
    
    -- Resultado
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    
    -- LGPD
    legal_basis VARCHAR(50),
    lgpd_override BOOLEAN NOT NULL DEFAULT FALSE,
    lgpd_reason TEXT,
    consent_status VARCHAR(20),
    
    -- Severidade
    severity VARCHAR(20) NOT NULL,
    
    -- Fonte
    source_module VARCHAR(50),
    source_event_id VARCHAR(200),
    
    -- Hash chain (integridade)
    previous_hash VARCHAR(64),
    entry_hash VARCHAR(64) NOT NULL,
    
    -- Timestamp (imutável)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- SEM updated_at — IMUTÁVEL
);

-- Indexes para auditoria
CREATE INDEX idx_audit_created ON comunicacao_operacional.audit_trail(created_at);
CREATE INDEX idx_audit_patient ON comunicacao_operacional.audit_trail(patient_hash);
CREATE INDEX idx_audit_channel ON comunicacao_operacional.audit_trail(channel);
CREATE INDEX idx_audit_severity ON comunicacao_operacional.audit_trail(severity);
CREATE INDEX idx_audit_status ON comunicacao_operacional.audit_trail(status);
CREATE INDEX idx_audit_legal ON comunicacao_operacional.audit_trail(legal_basis);
CREATE INDEX idx_audit_hash ON comunicacao_operacional.audit_trail(entry_hash);

-- Particionamento por ano para retenção (opcional mas recomendado para volume)
-- ALTER TABLE comunicacao_operacional.audit_trail
-- PARTITION BY RANGE (created_at);

-- Proteção contra UPDATE/DELETE na trilha de auditoria
-- (implementar via trigger ou política de segurança)
CREATE OR REPLACE FUNCTION comunicacao_operacional.prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit trail entries cannot be modified or deleted';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_audit_update
BEFORE UPDATE OR DELETE ON comunicacao_operacional.audit_trail
FOR EACH ROW
EXECUTE FUNCTION comunicacao_operacional.prevent_audit_modification();

CREATE TRIGGER trg_prevent_consent_update
BEFORE UPDATE OR DELETE ON comunicacao_operacional.consent_log
FOR EACH ROW
EXECUTE FUNCTION comunicacao_operacional.prevent_audit_modification();
```

---

## 6. ESTRUTURA DE CÓDIGO

```
comunicacao/
├── lgpd/
│   ├── __init__.py
│   ├── compliance_service.py          # LGPDComplianceService
│   ├── preferences_service.py         # CRUD de CommunicationPreference
│   ├── consent_service.py             # ConsentLogEntry management
│   ├── data_subject_service.py        # DataSubjectService (direitos Art. 18)
│   ├── config.py                      # LGPDConfig
│   └── models.py                      # Todos os models LGPD
├── audit/
│   ├── __init__.py
│   ├── audit_service.py               # AuditTrailService
│   ├── hash_chain.py                  # Hash chain logic
│   ├── fhir_communication.py          # FHIR Communication builder
│   ├── verification.py                # Chain integrity verification
│   └── models.py                      # AuditEntry, ChainVerificationResult
├── api/
│   ├── lgpd_routes.py                 # Endpoints de preferências e direitos
│   └── audit_routes.py                # Endpoints de auditoria
└── tests/
    ├── test_lgpd/
    │   ├── test_compliance_service.py
    │   ├── test_preferences.py
    │   ├── test_consent_log.py
    │   └── test_data_subject.py
    └── test_audit/
        ├── test_audit_service.py
        ├── test_hash_chain.py
        ├── test_fhir_export.py
        └── test_verification.py
```

---

## 7. TESTES ESPERADOS

```
test_lgpd/
├── test_compliance_service.py
│   ├── test_critical_always_allowed
│   ├── test_critical_uses_health_protection_basis
│   ├── test_high_alert_allowed_life_protection
│   ├── test_revoked_consent_blocks_medium
│   ├── test_pending_consent_blocks_low
│   ├── test_quiet_hours_defers_medium
│   ├── test_quiet_hours_not_affect_critical
│   ├── test_no_preferences_blocks
│   ├── test_opted_out_channel_blocked
│   ├── test_surveys_not_allowed_by_default
│   └── test_educational_allowed_if_opted_in
├── test_preferences.py
│   ├── test_create_preferences
│   ├── test_opt_in_channel
│   ├── test_opt_out_channel
│   ├── test_opt_out_all_keeps_critical
│   ├── test_set_quiet_hours
│   ├── test_quiet_hours_crossing_midnight
│   └── test_update_creates_consent_log
├── test_consent_log.py
│   ├── test_log_created_on_opt_in
│   ├── test_log_created_on_opt_out
│   ├── test_log_immutable
│   └── test_log_contains_metadata
└── test_data_subject.py
    ├── test_export_patient_data
    ├── test_export_includes_fhir
    ├── test_anonymize_patient
    ├── test_anonymize_keeps_audit_pseudonymized
    ├── test_consent_history
    └── test_processing_report

test_audit/
├── test_audit_service.py
│   ├── test_log_communication_creates_entry
│   ├── test_entry_is_immutable
│   ├── test_recipient_pseudonymized
│   ├── test_hash_chain_maintained
│   └── test_lgpd_decision_logged
├── test_hash_chain.py
│   ├── test_consecutive_entries_linked
│   ├── test_tampered_entry_detected
│   ├── test_missing_entry_detected
│   ├── test_first_entry_has_no_previous
│   └── test_hash_deterministic
├── test_fhir_export.py
│   ├── test_fhir_communication_valid
│   ├── test_fhir_bundle_valid
│   ├── test_fhir_contains_lgpd_extension
│   └── test_fhir_status_mapping
└── test_verification.py
    ├── test_verify_intact_chain
    ├── test_verify_broken_chain
    └── test_verify_empty_range
```

---

## 8. CONFIGURAÇÃO

```bash
# LGPD
LGPD_CRITICAL_OVERRIDE=true
LGPD_HIGH_ALERT_OVERRIDE=true
LGPD_BLOCK_WITHOUT_CONSENT=true
LGPD_DEFAULT_QUIET_START=22:00
LGPD_DEFAULT_QUIET_END=07:00
LGPD_CONSENT_VERSION=1.0
LGPD_CONSENT_RENEWAL_DAYS=365

# Audit
AUDIT_RETENTION_YEARS=5
AUDIT_HMAC_SECRET=<segredo_forte_para_pseudonimizacao>

# FHIR
FHIR_BASE_URL=http://intellicare.gsi.srv.br/fhir
```

---

## 9. ENTREGÁVEIS DO DEV

1. **Especificação Técnica**: Diagramas de decisão LGPD
2. **Plano de Implementação**: Compliance → Preferences → Audit → DataSubject → FHIR
3. **Código**: Todos os serviços com testes ≥ 90% (criticalidade regulatória)
4. **Migrations**: Tabelas + triggers de proteção
5. **Documentação Legal**: Mapeamento artigos LGPD → funcionalidades
6. **Termo de Consentimento**: Template do termo para ser apresentado ao paciente
7. **Relatório de Conformidade**: Template do relatório para DPO

**Prazo estimado**: 2 sprints (S4 + S5)

**NOTA IMPORTANTE**: Este domínio tem criticidade regulatória. O código deve ser revisado por um especialista em proteção de dados antes de ir para produção.
