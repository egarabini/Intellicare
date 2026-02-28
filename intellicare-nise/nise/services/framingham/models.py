"""
Modelos Pydantic para Framingham Risk Score
"""

from pydantic import BaseModel, Field
from typing import Literal, List


class FraminghamInput(BaseModel):
    """Input para cálculo de risco Framingham"""
    
    sexo: Literal["M", "F"] = Field(..., description="Sexo do paciente (M=Masculino, F=Feminino)")
    idade: int = Field(..., ge=30, le=74, description="Idade em anos (30-74)")
    colesterol_total: float = Field(..., ge=100, le=400, description="Colesterol total em mg/dL")
    hdl: float = Field(..., ge=20, le=100, description="HDL colesterol em mg/dL")
    pa_sistolica: float = Field(..., ge=90, le=200, description="Pressão arterial sistólica em mmHg")
    tabagismo: bool = Field(..., description="Paciente é fumante")
    diabetes: bool = Field(..., description="Paciente tem diabetes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sexo": "M",
                "idade": 55,
                "colesterol_total": 220,
                "hdl": 45,
                "pa_sistolica": 140,
                "tabagismo": True,
                "diabetes": False
            }
        }


class FraminghamOutput(BaseModel):
    """Output do cálculo de risco Framingham"""
    
    risco_10_anos: float = Field(..., description="Risco cardiovascular em 10 anos (%)")
    classificacao: Literal["baixo", "intermediario", "alto"] = Field(..., description="Classificação do risco")
    pontos_totais: int = Field(..., description="Pontos totais calculados")
    recomendacoes: List[str] = Field(..., description="Recomendações clínicas")
    
    # Detalhamento dos pontos
    pontos_idade: int = Field(..., description="Pontos por idade")
    pontos_colesterol: int = Field(..., description="Pontos por colesterol total")
    pontos_hdl: int = Field(..., description="Pontos por HDL")
    pontos_pa: int = Field(..., description="Pontos por pressão arterial")
    pontos_tabagismo: int = Field(..., description="Pontos por tabagismo")
    pontos_diabetes: int = Field(..., description="Pontos por diabetes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "risco_10_anos": 18.5,
                "classificacao": "intermediario",
                "pontos_totais": 12,
                "recomendacoes": [
                    "Controle rigoroso da pressão arterial",
                    "Cessação do tabagismo urgente",
                    "Estatina de alta intensidade"
                ],
                "pontos_idade": 4,
                "pontos_colesterol": 1,
                "pontos_hdl": 1,
                "pontos_pa": 2,
                "pontos_tabagismo": 2,
                "pontos_diabetes": 0
            }
        }

