# FASE 2.5.1: CUSTOMIZAÇÃO DE MODELOS
## Guia Prático para Cada Domínio

---

## 📋 Estrutura Base para Todos os Módulos

Cada módulo segue este padrão em `src/{module}/models/__init__.py`:

```python
"""
{Module} Models
IntelliCare Module
"""

from .base import BaseModel
from .domain_models import *

__all__ = [
    # Importar todos os modelos aqui
]
```

---

## 1️⃣ Florence (Análise Clínica)

### Arquivo: `intellicare-florence/src/florence/models/`

**Modelos a Criar**:

```python
# models/clinical_analysis.py
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class ClinicalAnalysis(BaseModel):
    """Análise Clínica de um Paciente"""
    __tablename__ = "clinical_analyses"
    
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    analysis_type = Column(String, nullable=False)  # ex: "Lab", "Image", "Physical"
    analysis_date = Column(DateTime, default=datetime.utcnow)
    result = Column(String, nullable=False)
    value = Column(Float)
    unit = Column(String)
    normal_range_min = Column(Float)
    normal_range_max = Column(Float)
    interpretation = Column(String)  # "Normal", "High", "Low"
    
    # Relacionamentos
    patient = relationship("Patient", back_populates="analyses")
    indicators = relationship("DiagnosisIndicator", back_populates="analysis")

class DiagnosisIndicator(BaseModel):
    """Indicadores de Diagnóstico"""
    __tablename__ = "diagnosis_indicators"
    
    clinical_analysis_id = Column(String, ForeignKey("clinical_analyses.id"), nullable=False)
    indicator_name = Column(String, nullable=False)
    indicator_value = Column(Float, nullable=False)
    severity = Column(String)  # "Low", "Medium", "High"
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    analysis = relationship("ClinicalAnalysis", back_populates="indicators")

class ClinicalMetric(BaseModel):
    """Métricas Clínicas Agregadas"""
    __tablename__ = "clinical_metrics"
    
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    metric_type = Column(String)  # "BMI", "BP", "HR", etc
    metric_value = Column(Float)
    measurement_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String)  # "Stable", "Improving", "Declining"

class TreatmentOutcome(BaseModel):
    """Desfechos de Tratamento"""
    __tablename__ = "treatment_outcomes"
    
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    treatment_id = Column(String)
    outcome_date = Column(DateTime, default=datetime.utcnow)
    outcome_type = Column(String)  # "Improved", "Stable", "Worsened"
    improvement_percentage = Column(Float)
    notes = Column(String)

class LabResults(BaseModel):
    """Resultados de Laboratório"""
    __tablename__ = "lab_results"
    
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    test_name = Column(String)
    test_date = Column(DateTime, default=datetime.utcnow)
    result_value = Column(String)
    reference_range = Column(String)
    status = Column(String)  # "Positive", "Negative", "Normal"
```

**Schemas** (`schemas/clinical_analysis.py`):
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ClinicalAnalysisCreate(BaseModel):
    patient_id: str
    analysis_type: str
    result: str
    value: Optional[float] = None
    interpretation: Optional[str] = None

class ClinicalAnalysisResponse(BaseModel):
    id: str
    patient_id: str
    analysis_type: str
    analysis_date: datetime
    result: str
    interpretation: Optional[str]
```

**API Routes** (`api/routes/clinical.py`):
```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/clinical", tags=["Clinical"])

@router.post("/analysis", status_code=status.HTTP_201_CREATED)
async def create_clinical_analysis(
    analysis: ClinicalAnalysisCreate,
    db: Session = Depends(get_db)
):
    """Criar nova análise clínica"""
    db_analysis = ClinicalAnalysis(**analysis.dict())
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis

@router.get("/analysis/{analysis_id}")
async def get_clinical_analysis(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """Obter análise clínica específica"""
    return db.query(ClinicalAnalysis).filter(
        ClinicalAnalysis.id == analysis_id
    ).first()

@router.get("/patient/{patient_id}/analyses")
async def get_patient_analyses(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """Listar todas as análises de um paciente"""
    return db.query(ClinicalAnalysis).filter(
        ClinicalAnalysis.patient_id == patient_id
    ).all()
```

---

## 2️⃣ Oswaldo (Gestão de Pacientes)

### Arquivo: `intellicare-oswaldo/src/oswaldo/models/`

**Modelos a Criar**:

```python
# models/patient_management.py
from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Patient(BaseModel):
    """Registro Principal do Paciente"""
    __tablename__ = "patients"
    
    name = Column(String, nullable=False)
    date_of_birth = Column(DateTime)
    email = Column(String, unique=True)
    phone = Column(String)
    cpf = Column(String, unique=True)
    gender = Column(String)  # "M", "F", "Other"
    blood_type = Column(String)
    allergies = Column(String)
    chronic_conditions = Column(String)
    registration_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Active")  # Active, Inactive, Discharged
    
    # Relacionamentos
    registration = relationship("PatientRegistration", back_populates="patient", uselist=False)
    medical_history = relationship("MedicalHistory", back_populates="patient")
    insurance = relationship("InsuranceInfo", back_populates="patient")
    emergency_contacts = relationship("EmergencyContact", back_populates="patient")

class PatientRegistration(BaseModel):
    """Dados de Registração do Paciente"""
    __tablename__ = "patient_registrations"
    
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, unique=True)
    registration_number = Column(String, unique=True)
    registration_date = Column(DateTime, default=datetime.utcnow)
    facility_id = Column(String)
    attending_physician = Column(String)
    
    patient = relationship("Patient", back_populates="registration")

class MedicalHistory(BaseModel):
    """Histórico Médico do Paciente"""
    __tablename__ = "medical_histories"
    
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    condition = Column(String)
    diagnosis_date = Column(DateTime)
    status = Column(String)  # "Active", "Inactive", "Resolved"
    notes = Column(String)
    
    patient = relationship("Patient", back_populates="medical_history")

class InsuranceInfo(BaseModel):
    """Informações de Seguro"""
    __tablename__ = "insurance_info"
    
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, unique=True)
    insurance_provider = Column(String)
    policy_number = Column(String)
    coverage_type = Column(String)  # "Private", "Public", "Mixed"
    expiry_date = Column(DateTime)
    
    patient = relationship("Patient", back_populates="insurance")

class EmergencyContact(BaseModel):
    """Contatos de Emergência"""
    __tablename__ = "emergency_contacts"
    
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    name = Column(String)
    relationship = Column(String)
    phone = Column(String)
    email = Column(String)
    priority = Column(Integer, default=1)  # 1 = Primary, 2 = Secondary
    
    patient = relationship("Patient", back_populates="emergency_contacts")
```

---

## 3️⃣ Zilda (Epidemiologia)

### Arquivo: `intellicare-zilda/src/zilda/models/`

**Modelos a Criar**:

```python
# models/epidemiology.py
from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

class EpidemicEvent(BaseModel):
    """Evento Epidemiológico"""
    __tablename__ = "epidemic_events"
    
    event_name = Column(String, nullable=False)
    disease_type = Column(String)  # ex: "COVID-19", "Dengue"
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    location = Column(String)
    severity = Column(String)  # "Low", "Medium", "High", "Critical"
    reported_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String)  # "Ongoing", "Resolved", "Monitoring"
    
    case_reports = relationship("CaseReport", back_populates="event")

class CaseReport(BaseModel):
    """Relatório de Caso"""
    __tablename__ = "case_reports"
    
    epidemic_event_id = Column(String, ForeignKey("epidemic_events.id"), nullable=False)
    patient_id = Column(String)
    case_date = Column(DateTime, default=datetime.utcnow)
    symptom_onset = Column(DateTime)
    confirmed = Column(Boolean, default=False)
    severity = Column(String)  # "Mild", "Moderate", "Severe"
    outcome = Column(String)  # "Recovered", "Deceased", "Hospitalized"
    location = Column(String)
    
    event = relationship("EpidemicEvent", back_populates="case_reports")

class EpidemicIndicator(BaseModel):
    """Indicadores Epidemiológicos"""
    __tablename__ = "epidemic_indicators"
    
    event_id = Column(String, ForeignKey("epidemic_events.id"))
    indicator_name = Column(String)  # "Incidence", "Prevalence", "R-value"
    indicator_value = Column(Float)
    measurement_date = Column(DateTime, default=datetime.utcnow)
    population_at_risk = Column(Integer)

class PopulationMetrics(BaseModel):
    """Métricas Populacionais"""
    __tablename__ = "population_metrics"
    
    region = Column(String, nullable=False)
    total_population = Column(Integer)
    disease_type = Column(String)
    affected_count = Column(Integer)
    mortality_rate = Column(Float)
    recovery_rate = Column(Float)
    measurement_date = Column(DateTime, default=datetime.utcnow)
```

---

## 4️⃣ Geralda (Notas Clínicas)

### Arquivo: `intellicare-geralda/src/geralda/models/`

**Modelos a Criar**:

```python
# models/clinical_notes.py
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

class ClinicalNote(BaseModel):
    """Nota Clínica"""
    __tablename__ = "clinical_notes"
    
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    encounter_date = Column(DateTime, default=datetime.utcnow)
    note_type = Column(String)  # "Progress", "Assessment", "Discharge"
    content = Column(Text)
    author = Column(String)
    reviewed_by = Column(String)
    reviewed_date = Column(DateTime)
    status = Column(String)  # "Draft", "Finalized", "Reviewed"
    
    patient_id_fk = relationship("Patient")
    attachments = relationship("NoteAttachment", back_populates="note")
    evidence = relationship("ClinicalEvidence", back_populates="note")

class NoteTemplate(BaseModel):
    """Modelo de Nota"""
    __tablename__ = "note_templates"
    
    template_name = Column(String, unique=True)
    note_type = Column(String)
    template_content = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)

class NoteHistory(BaseModel):
    """Histórico de Modificações da Nota"""
    __tablename__ = "note_history"
    
    note_id = Column(String, ForeignKey("clinical_notes.id"), nullable=False)
    version = Column(Integer)
    modified_by = Column(String)
    modified_date = Column(DateTime, default=datetime.utcnow)
    change_summary = Column(String)

class NoteAttachment(BaseModel):
    """Anexos da Nota"""
    __tablename__ = "note_attachments"
    
    note_id = Column(String, ForeignKey("clinical_notes.id"), nullable=False)
    file_name = Column(String)
    file_path = Column(String)
    file_type = Column(String)
    uploaded_date = Column(DateTime, default=datetime.utcnow)
    
    note = relationship("ClinicalNote", back_populates="attachments")

class ClinicalEvidence(BaseModel):
    """Evidência Clínica Referenciada"""
    __tablename__ = "clinical_evidence"
    
    note_id = Column(String, ForeignKey("clinical_notes.id"), nullable=False)
    evidence_type = Column(String)  # "Lab Result", "Imaging", "Reference"
    reference_id = Column(String)
    source = Column(String)
    added_date = Column(DateTime, default=datetime.utcnow)
    
    note = relationship("ClinicalNote", back_populates="evidence")
```

---

## 5️⃣ Comunicação (Mensagens)

### Arquivo: `intellicare-comunicacao/src/comunicacao/models/`

**Modelos a Criar**:

```python
# models/messaging.py
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime

class Message(BaseModel):
    """Mensagem Individual"""
    __tablename__ = "messages"
    
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(String)
    content = Column(Text)
    message_type = Column(String)  # "Text", "File", "System"
    sent_date = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)
    read_date = Column(DateTime, nullable=True)
    
    conversation = relationship("Conversation", back_populates="messages")
    attachments = relationship("MessageAttachment", back_populates="message")

class Conversation(BaseModel):
    """Conversa/Thread"""
    __tablename__ = "conversations"
    
    participant_ids = Column(String)  # JSON array
    topic = Column(String)
    created_date = Column(DateTime, default=datetime.utcnow)
    last_message_date = Column(DateTime)
    active = Column(Boolean, default=True)
    
    messages = relationship("Message", back_populates="conversation")
    thread = relationship("MessageThread", back_populates="conversation")

class MessageAttachment(BaseModel):
    """Anexo de Mensagem"""
    __tablename__ = "message_attachments"
    
    message_id = Column(String, ForeignKey("messages.id"), nullable=False)
    file_name = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    file_type = Column(String)
    
    message = relationship("Message", back_populates="attachments")

class MessageThread(BaseModel):
    """Thread de Mensagens"""
    __tablename__ = "message_threads"
    
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    parent_message_id = Column(String)
    thread_name = Column(String)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="thread")

class NotificationPreference(BaseModel):
    """Preferências de Notificação"""
    __tablename__ = "notification_preferences"
    
    user_id = Column(String, nullable=False)
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=True)
    in_app_notifications = Column(Boolean, default=True)
    notification_frequency = Column(String)  # "Immediate", "Hourly", "Daily"
    updated_date = Column(DateTime, default=datetime.utcnow)
```

---

## 6️⃣ Auth (Autenticação)

### Arquivo: `intellicare-auth/src/auth/models/`

**Modelos a Criar**:

```python
# models/authentication.py
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime

# Tabela de Associação M:N entre User e Role
user_roles = Table(
    'user_roles',
    BaseModel.metadata,
    Column('user_id', String, ForeignKey('users.id')),
    Column('role_id', String, ForeignKey('roles.id'))
)

# Tabela de Associação M:N entre Role e Permission
role_permissions = Table(
    'role_permissions',
    BaseModel.metadata,
    Column('role_id', String, ForeignKey('roles.id')),
    Column('permission_id', String, ForeignKey('permissions.id'))
)

class User(BaseModel):
    """Usuário do Sistema"""
    __tablename__ = "users"
    
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    status = Column(String, default="Active")  # Active, Inactive, Locked
    created_date = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    password_changed_date = Column(DateTime)
    
    roles = relationship("Role", secondary=user_roles, back_populates="users")

class Role(BaseModel):
    """Função/Papel no Sistema"""
    __tablename__ = "roles"
    
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(BaseModel):
    """Permissão do Sistema"""
    __tablename__ = "permissions"
    
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    resource = Column(String)  # "patients", "notes", "messages"
    action = Column(String)  # "read", "write", "delete"
    
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class TokenBlacklist(BaseModel):
    """Token Revogado/Expirado"""
    __tablename__ = "token_blacklist"
    
    token = Column(String, unique=True, nullable=False)
    user_id = Column(String)
    revoked_date = Column(DateTime, default=datetime.utcnow)
    reason = Column(String)  # "Logout", "PasswordChange", "Manual"

class AuditLog(BaseModel):
    """Log de Auditoria"""
    __tablename__ = "audit_logs"
    
    user_id = Column(String)
    action = Column(String)
    resource = Column(String)
    resource_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)
    success = Column(Boolean)
```

---

## 7️⃣ Portal (Dashboard)

### Arquivo: `intellicare-portal/src/portal/models/`

**Modelos a Criar**:

```python
# models/dashboard.py
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

class DashboardWidget(BaseModel):
    """Widget do Dashboard"""
    __tablename__ = "dashboard_widgets"
    
    widget_name = Column(String)
    widget_type = Column(String)  # "Chart", "Table", "Metric", "Map"
    configuration = Column(JSON)  # Configuração em JSON
    created_date = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)

class UserDashboard(BaseModel):
    """Dashboard Personalizado do Usuário"""
    __tablename__ = "user_dashboards"
    
    user_id = Column(String, nullable=False, unique=True)
    dashboard_name = Column(String)
    layout = Column(JSON)  # Posição dos widgets
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow)

class Report(BaseModel):
    """Relatório"""
    __tablename__ = "reports"
    
    report_name = Column(String)
    report_type = Column(String)  # "Clinical", "Financial", "Operational"
    generated_date = Column(DateTime, default=datetime.utcnow)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    file_path = Column(String)
    status = Column(String)  # "Draft", "Generated", "Exported"

class Analytics(BaseModel):
    """Dados Analíticos"""
    __tablename__ = "analytics"
    
    metric_name = Column(String)
    metric_value = Column(String)
    measurement_date = Column(DateTime, default=datetime.utcnow)
    dimension = Column(String)  # ex: "Department", "Specialty"
    dimension_value = Column(String)

class CustomChart(BaseModel):
    """Gráfico Customizado"""
    __tablename__ = "custom_charts"
    
    chart_name = Column(String)
    chart_type = Column(String)  # "Line", "Bar", "Pie", "Area"
    data_source = Column(String)
    chart_config = Column(JSON)
    created_by = Column(String)
    created_date = Column(DateTime, default=datetime.utcnow)
```

---

## 8️⃣ Wanda (IA Assistente)

### Arquivo: `intellicare-wanda/src/wanda/models/`

**Modelos a Criar**:

```python
# models/ai_assistant.py
from sqlalchemy import Column, String, DateTime, Text, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class AISession(BaseModel):
    """Sessão de Conversa com IA"""
    __tablename__ = "ai_sessions"
    
    user_id = Column(String, nullable=False)
    session_start = Column(DateTime, default=datetime.utcnow)
    session_end = Column(DateTime)
    context = Column(Text)  # Contexto da conversa
    status = Column(String)  # "Active", "Closed"
    
    responses = relationship("AssistantResponse", back_populates="session")

class AssistantResponse(BaseModel):
    """Resposta do Assistente IA"""
    __tablename__ = "assistant_responses"
    
    session_id = Column(String, ForeignKey("ai_sessions.id"), nullable=False)
    user_query = Column(Text)
    assistant_response = Column(Text)
    confidence_score = Column(Float)  # 0-1
    response_time = Column(Integer)  # ms
    timestamp = Column(DateTime, default=datetime.utcnow)
    helpful = Column(Boolean, nullable=True)  # User feedback
    
    session = relationship("AISession", back_populates="responses")
    intents = relationship("IntentClassification", back_populates="response")

class IntentClassification(BaseModel):
    """Classificação de Intenção da Query"""
    __tablename__ = "intent_classifications"
    
    response_id = Column(String, ForeignKey("assistant_responses.id"))
    intent = Column(String)  # "ScheduleAppointment", "GetPatientInfo", "Prescription"
    confidence = Column(Float)
    sub_intent = Column(String)
    
    response = relationship("AssistantResponse", back_populates="intents")

class KnowledgeBase(BaseModel):
    """Base de Conhecimento da IA"""
    __tablename__ = "knowledge_base"
    
    topic = Column(String)
    content = Column(Text)
    category = Column(String)  # "Clinical", "Procedural", "FAQ"
    source = Column(String)
    confidence_level = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)

class AIMetrics(BaseModel):
    """Métricas de Performance da IA"""
    __tablename__ = "ai_metrics"
    
    metric_date = Column(DateTime, default=datetime.utcnow)
    total_queries = Column(Integer)
    query_success_rate = Column(Float)
    average_response_time = Column(Float)
    user_satisfaction = Column(Float)  # 1-5
    most_common_intent = Column(String)
    coverage = Column(Float)  # % de queries resolvidas
```

---

## 📋 Próximas Etapas por Módulo

Para cada módulo, após criar os **Models**:

### 1. **Criar `/api/routes`**
```
api/
├── routes/
│   ├── __init__.py
│   ├── main.py          (router principal)
│   ├── {domain}.py      (rotas específicas)
│   └── health.py        (health check)
└── main.py              (FastAPI app)
```

### 2. **Criar Schemas Pydantic**
```
schemas/
├── __init__.py
├── base.py              (BaseModel Pydantic)
├── {domain}.py          (models específicos)
└── responses.py         (padrão de resposta)
```

### 3. **Criar Services**
```
services/
├── __init__.py
├── base_service.py      (CRUD genérico)
└── {domain}_service.py  (lógica específica)
```

### 4. **Criar Testes**
```
tests/
├── conftest.py
├── test_models.py
├── test_{domain}.py
└── test_api.py
```

---

## 🚀 Próximo Comando

Comece pelo **Florence (Análise Clínica)**:

```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-florence

# Copiar arquivos base do Donabedian para customização
Copy-Item "..\intellicare-donabedian\src\donabedian\models\base.py" `
         -Destination "src\florence\models\base.py"
```

---

**Estimado por módulo: 3.5 horas**  
**Total estimado: 28 horas**

*Gerado em: 12 de Fevereiro de 2026*
