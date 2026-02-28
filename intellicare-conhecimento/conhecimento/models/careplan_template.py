from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CarePlanActivityFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    AS_NEEDED = "as_needed"


class CarePlanActivity(BaseModel):
    code: str = Field(..., description="Código da atividade")
    category: str = Field(..., description="Categoria (medicação, exame, consulta, educação)")
    title: str = Field(..., description="Título da atividade")
    description: str = Field(..., description="Descrição detalhada")
    frequency: CarePlanActivityFrequency = Field(default=CarePlanActivityFrequency.AS_NEEDED)
    duration: Optional[str] = Field(None, description="Duração (ex: '3 meses')")
    instructions: Optional[str] = Field(None, description="Instruções específicas")
    monitoring: Optional[str] = Field(None, description="Parâmetros de monitoramento")


class CarePlanGoal(BaseModel):
    code: str = Field(..., description="Código do objetivo")
    description: str = Field(..., description="Descrição do objetivo")
    target_value: Optional[str] = Field(None, description="Valor alvo (ex: 'HbA1c < 7%')")
    target_date: Optional[str] = Field(None, description="Data alvo")
    priority: str = Field(default="medium", description="high, medium, low")


class CarePlanTemplate(BaseModel):
    id: str = Field(..., description="Identificador único do template")
    condition: str = Field(..., description="Condição clínica (ex: ckd, ic, dm2)")
    title: str = Field(..., description="Título do template")
    description: str = Field(..., description="Descrição do template")
    specialty: str = Field(..., description="Especialidade")
    stage: Optional[str] = Field(None, description="Estágio da condição (ex: G3a, NYHA II)")
    goals: List[CarePlanGoal] = Field(default_factory=list)
    activities: List[CarePlanActivity] = Field(default_factory=list)
    education_materials: List[str] = Field(default_factory=list, description="Materiais educativos")
    triggers: List[str] = Field(default_factory=list, description="Gatilhos para ativação")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "careplan-ckd-g3a",
                "condition": "ckd",
                "title": "Plano de Cuidado DRC G3a",
                "description": "Template para pacientes com DRC estágio G3a (eGFR 45-59)",
                "specialty": "nefrologia",
                "stage": "G3a",
                "goals": [
                    {
                        "code": "goal-egfr",
                        "description": "Manter função renal estável",
                        "target_value": "eGFR > 45 mL/min/1.73m²",
                        "priority": "high"
                    }
                ],
                "activities": [
                    {
                        "code": "lab-creatinine",
                        "category": "exame",
                        "title": "Dosagem de creatinina",
                        "description": "Monitoramento da função renal",
                        "frequency": "quarterly"
                    }
                ]
            }
        }


class CarePlanGenerateRequest(BaseModel):
    patient_id: str = Field(..., description="ID do paciente")
    condition: str = Field(..., description="Condição clínica")
    stage: Optional[str] = Field(None, description="Estágio da condição")
    comorbidities: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Preferências do paciente")


class CarePlanGenerateResponse(BaseModel):
    careplan_id: str
    patient_id: str
    template_id: str
    condition: str
    goals: List[CarePlanGoal]
    activities: List[CarePlanActivity]
    generated_at: datetime = Field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None
