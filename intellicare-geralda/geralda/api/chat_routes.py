"""Rotas de chat com a Geralda AI."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from geralda.ai.geralda_agent import create_geralda_agent
from geralda.database.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    patient_id: str
    session_id: Optional[str] = None
    role: str = "patient"  # "patient" ou "professional"
    patient_context: Optional[str] = None
    history: Optional[list[dict]] = None


class ChatResponse(BaseModel):
    success: bool
    response: str
    actions_taken: list[dict]
    patient_id: str
    session_id: Optional[str]
    mode: str  # "ai" ou "fallback"


class CreatePlanRequest(BaseModel):
    patient_id: str
    patient_name: str = ""
    conditions: list = []
    goals: list = []


# Agente Geralda (singleton)
_geralda_agent = None


def get_geralda_agent():
    """Obtém instância singleton do agente Geralda."""
    global _geralda_agent

    if _geralda_agent is None:
        from geralda.config import GeraldaConfig
        from geralda.database.base import get_session_factory

        config = GeraldaConfig()

        # Obtém session_factory (deve estar configurado no lifespan)
        try:
            session_factory = get_session_factory(config.database_url)
        except Exception:
            # Fallback: sem database
            session_factory = None

        _geralda_agent = create_geralda_agent(
            llm_provider=getattr(config, "llm_provider", "none"),
            ollama_url=getattr(config, "ollama_url", "http://localhost:11434"),
            ollama_model=getattr(config, "ollama_model", "mistral:7b"),
            session_factory=session_factory,
        )

    return _geralda_agent


def get_agent():
    """Alias legado para compatibilidade com testes existentes."""
    return get_geralda_agent()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    """
    Endpoint de chat com a Geralda.

    Processa mensagens de pacientes ou profissionais usando IA
    (quando disponível) ou respostas de fallback.
    """
    try:
        agent = get_agent()

        # Obtém contexto do paciente se não fornecido
        patient_context = request.patient_context or ""
        if not patient_context:
            # TODO: Buscar contexto do paciente no banco/FHIR
            patient_context = f"Paciente ID: {request.patient_id}"

        # Processa mensagem
        result = await agent.chat(
            message=request.message,
            patient_id=request.patient_id,
            patient_context=patient_context,
            history=request.history,
            role=request.role,
        )

        return ChatResponse(
            success=True,
            response=result["response"],
            actions_taken=result.get("actions_taken", []),
            patient_id=request.patient_id,
            session_id=request.session_id,
            mode=result.get("mode", "fallback"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar mensagem: {str(e)}",
        )


@router.post("/create-plan")
async def create_care_plan_ai(
    request: CreatePlanRequest,
):
    """
    Cria plano de cuidado assistido por IA.

    Usa o LLM para sugerir tarefas baseadas nas condições e metas.
    """
    try:
        agent = get_agent()

        result = await agent.create_care_plan(
            patient_id=request.patient_id,
            patient_name=request.patient_name,
            conditions=request.conditions,
            goals=request.goals,
        )

        return {
            "success": True,
            "patient_id": request.patient_id,
            "suggestions": result.get("suggestions"),
            "mode": result.get("mode", "fallback"),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar plano: {str(e)}",
        )
