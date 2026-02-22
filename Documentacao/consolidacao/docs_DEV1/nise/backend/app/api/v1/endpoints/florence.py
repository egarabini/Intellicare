"""
============================================================================
NISE TRAINING MODULE - FLORENCE AI ASSISTANT ENDPOINTS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Florence (Dr. Nise) Chatbot Integration
Versão: 1.0
Data: 24/03/2026
Responsável: DEV1
============================================================================
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import httpx

from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.rag_service import rag_service

# ============================================================================
# CONFIGURATION
# ============================================================================

router = APIRouter(prefix="/florence", tags=["Florence"])
logger = logging.getLogger(__name__)

# Flowise configuration (from environment)
FLOWISE_URL = "http://flowise:3000"
FLOWISE_CHATFLOW_ID = "dr-nise-chatbot"

# RAG configuration
USE_RAG = True  # Enable RAG by default

# ============================================================================
# MODELS
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User message", min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context (patient data, etc.)")


class ChatResponse(BaseModel):
    """Chat response model."""
    message: str = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources: Optional[List[str]] = Field(None, description="Knowledge sources used")
    confidence: Optional[float] = Field(None, description="Response confidence (0-1)")


class ConversationHistory(BaseModel):
    """Conversation history model."""
    session_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat_with_florence(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with Florence (Dr. Nise) AI Assistant.
    
    Florence is an AI-powered medical assistant that helps healthcare
    professionals learn about FHIR resources, clinical scenarios, and
    best practices.
    
    Args:
        request: Chat request with message and optional context
        db: Database session
    
    Returns:
        ChatResponse: Assistant response with sources and confidence
    
    Example:
        ```json
        {
            "message": "Como criar um recurso Patient FHIR R4?",
            "session_id": "session-123",
            "context": {
                "user_role": "medical_student",
                "specialty": "cardiology"
            }
        }
        ```
    """
    try:
        session_id = request.session_id or f"session-{datetime.utcnow().timestamp()}"

        # Use RAG service for enhanced responses
        if USE_RAG:
            system_message = """Você é Dr. Nise, um assistente de IA especializado em
            treinamento médico e recursos FHIR R4. Você ajuda profissionais de saúde a
            aprender sobre interoperabilidade em saúde, padrões FHIR, e melhores práticas
            clínicas. Seja educativo, preciso e empático."""

            # Generate response using RAG
            rag_response = await rag_service.generate_response(
                query=request.message,
                system_message=system_message,
                use_rag=True
            )

            assistant_message = rag_response.get("text", "")
            sources = rag_response.get("sources", [])
            context_used = rag_response.get("context_used", 0)

            # Calculate confidence based on context used
            confidence = 0.95 if context_used >= 2 else (0.85 if context_used == 1 else 0.7)

            logger.info(f"Florence RAG chat: session={session_id}, context_used={context_used}, confidence={confidence}")

            return ChatResponse(
                message=assistant_message,
                session_id=session_id,
                sources=sources,
                confidence=confidence
            )

        else:
            # Fallback to Flowise (legacy mode)
            flowise_request = {
                "question": request.message,
                "sessionId": session_id,
                "overrideConfig": {
                    "systemMessage": """Você é Dr. Nise, um assistente de IA especializado em
                    treinamento médico e recursos FHIR R4. Você ajuda profissionais de saúde a
                    aprender sobre interoperabilidade em saúde, padrões FHIR, e melhores práticas
                    clínicas. Seja educativo, preciso e empático."""
                }
            }

            # Add context if provided
            if request.context:
                flowise_request["overrideConfig"]["context"] = request.context

            # Call Flowise API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{FLOWISE_URL}/api/v1/prediction/{FLOWISE_CHATFLOW_ID}",
                    json=flowise_request,
                    timeout=30.0
                )
                response.raise_for_status()
                flowise_response = response.json()

            # Extract response
            assistant_message = flowise_response.get("text", "")
            sources = flowise_response.get("sourceDocuments", [])

            # Calculate confidence (simplified)
            confidence = 0.9 if sources else 0.7

            logger.info(f"Florence Flowise chat: session={session_id}, confidence={confidence}")

            return ChatResponse(
                message=assistant_message,
                session_id=session_id,
                sources=[s.get("metadata", {}).get("source", "") for s in sources],
                confidence=confidence
            )
        
    except httpx.HTTPError as e:
        logger.error(f"Flowise API error: {str(e)}")
        raise HTTPException(status_code=503, detail="Florence is temporarily unavailable")
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=ConversationHistory)
async def get_conversation_history(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session ID
        db: Database session
    
    Returns:
        ConversationHistory: Full conversation history
    """
    # TODO: Implement database storage for conversation history
    # For now, return empty history
    return ConversationHistory(
        session_id=session_id,
        messages=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.post("/feedback")
async def submit_feedback(
    session_id: str,
    message_id: str,
    rating: int = Field(..., ge=1, le=5),
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback for a Florence response.
    
    Args:
        session_id: Session ID
        message_id: Message ID
        rating: Rating (1-5)
        comment: Optional feedback comment
        db: Database session
    
    Returns:
        dict: Confirmation message
    """
    logger.info(f"Feedback received: session={session_id}, rating={rating}")
    
    # TODO: Store feedback in database
    
    return {
        "status": "success",
        "message": "Feedback received. Thank you!"
    }


@router.get("/health")
async def florence_health():
    """
    Check Florence service health.
    
    Returns:
        dict: Health status
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FLOWISE_URL}/api/v1/health", timeout=5.0)
            response.raise_for_status()
        
        return {
            "status": "healthy",
            "service": "Florence (Dr. Nise)",
            "flowise_status": "connected"
        }
    except Exception as e:
        logger.error(f"Florence health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "Florence (Dr. Nise)",
            "flowise_status": "disconnected",
            "error": str(e)
        }

