"""
Event models para integração com Florence (RabbitMQ).

Define os 3 tipos de eventos que Florence publica:
1. ExameResultado - Novo resultado de exame (glicemia, creatinina, PA, etc)
2. PacienteDados - Dados básicos do paciente (atualização)
3. RequestConsulta - Solicitação para agendar acompanhamento
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum


class TipoExame(str, Enum):
    """Tipos de exames que Florence envia"""
    GLICEMIA = "glicemia"
    HBA1C = "hba1c"
    PA = "pressao_arterial"
    CREATININA = "creatinina"
    COLESTEROL = "colesterol"
    OUTROS = "outros"


class ExameResultadoEvent(BaseModel):
    """
    Evento: Florence → Oswaldo quando novo exame está disponível.
    
    Exemplo:
    {
        "event_type": "exame_resultado",
        "paciente_cpf_hash": "abc123xyz",
        "data_coleta": "2026-02-13T10:30:00Z",
        "tipo_exame": "glicemia",
        "valor": 250.5,
        "unidade": "mg/dL",
        "valor_referencia": "70-100",
        "laboratorio": "Lab Central",
        "medico_solicitante": "Dr. Silva",
        "timestamp": "2026-02-13T12:00:00Z"
    }
    """
    event_type: str = "exame_resultado"
    paciente_cpf_hash: str = Field(..., description="Hash do CPF do paciente")
    data_coleta: datetime = Field(..., description="Data/hora da coleta")
    tipo_exame: TipoExame = Field(..., description="Tipo de exame")
    valor: float = Field(..., description="Valor do resultado")
    unidade: str = Field(..., description="Unidade de medida (mg/dL, mmHg, etc)")
    valor_referencia: str = Field(..., description="Intervalo de referência")
    laboratorio: str = Field(..., description="Nome do laboratório")
    medico_solicitante: str = Field(..., description="Médico que solicitou")
    dados_adicionais: Optional[Dict] = Field(None, description="Dados extras (critério, protocolo, etc)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "exame_resultado",
                "paciente_cpf_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "data_coleta": "2026-02-13T10:30:00Z",
                "tipo_exame": "glicemia",
                "valor": 250.5,
                "unidade": "mg/dL",
                "valor_referencia": "70-100",
                "laboratorio": "Lab Central",
                "medico_solicitante": "Dr Silva"
            }
        }


class PacienteDadosEvent(BaseModel):
    """
    Evento: Florence → Oswaldo com atualização de dados do paciente.
    
    Exemplo:
    {
        "event_type": "paciente_dados",
        "paciente_cpf_hash": "abc123xyz",
        "idade": 65,
        "sexo": "M",
        "peso_kg": 80.5,
        "altura_cm": 175,
        "imc": 26.3,
        "timestamp": "2026-02-13T12:00:00Z"
    }
    """
    event_type: str = "paciente_dados"
    paciente_cpf_hash: str = Field(..., description="Hash do CPF do paciente")
    idade: int = Field(..., ge=0, le=150)
    sexo: str = Field(..., description="M ou F")
    peso_kg: Optional[float] = Field(None, description="Peso em kg")
    altura_cm: Optional[float] = Field(None, description="Altura em cm")
    imc: Optional[float] = Field(None, description="Índice de Massa Corporal")
    comorbidades: Optional[List[str]] = Field(None, description="Lista de comorbidades")
    medicacoes_ativas: Optional[List[Dict]] = Field(None, description="Medicações atuais")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "paciente_dados",
                "paciente_cpf_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "idade": 65,
                "sexo": "M",
                "peso_kg": 80.5,
                "altura_cm": 175,
                "imc": 26.3
            }
        }


class RequestConsultaEvent(BaseModel):
    """
    Evento: Florence → Oswaldo solicitando agendar acompanhamento.
    
    Exemplo:
    {
        "event_type": "request_consulta",
        "paciente_cpf_hash": "abc123xyz",
        "motivo": "Acompanhamento hipertensão",
        "urgencia": "normal",
        "periodo_preferido": "proximas_2_semanas",
        "medico_solicitante": "Dr. Silva",
        "timestamp": "2026-02-13T12:00:00Z"
    }
    """
    event_type: str = "request_consulta"
    paciente_cpf_hash: str = Field(..., description="Hash do CPF do paciente")
    motivo: str = Field(..., description="Motivo da solicitação")
    urgencia: str = Field(..., description="baixa, normal, alta, critica")
    periodo_preferido: str = Field(None, description="proximas_2_semanas, proximo_mes, etc")
    medico_solicitante: str = Field(..., description="Médico que solicitou")
    observacoes: Optional[str] = Field(None, description="Observações adicionais")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "request_consulta",
                "paciente_cpf_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "motivo": "Acompanhamento hipertensão",
                "urgencia": "normal",
                "medico_solicitante": "Dr Silva"
            }
        }


# Union type para qualquer evento
FlorenzeEvent = ExameResultadoEvent | PacienteDadosEvent | RequestConsultaEvent
