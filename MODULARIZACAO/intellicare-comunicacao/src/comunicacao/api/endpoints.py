
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from intellicare_auth.fastapi import configure_auth, require_role, get_current_user


from comunicacao.routing.engine import RoutingEngine
from comunicacao.dispatchers.manager import DispatcherManager
from comunicacao.storage.intent_repository import CommunicationIntentRepository
from comunicacao.storage.delivery_repository import DeliveryResultRepository
from comunicacao.lgpd.gateway import LGPDComplianceGateway

router = APIRouter()

# Exemplo de payload para envio de mensagem
class MessageRequest(BaseModel):
    channel: str
    recipient: str
    content: str
    type: Optional[str] = "text"
    metadata: Optional[dict] = None

class MessageResponse(BaseModel):
    message_id: str
    status: str
    channel: str
    recipient: str

# Endpoint protegido: Envio de mensagem omnicanal

intent_repo = CommunicationIntentRepository()
delivery_repo = DeliveryResultRepository()
lgpd_gateway = LGPDComplianceGateway()

# Endpoint protegido: Envio de mensagem omnicanal

@router.post("/api/v1/send", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def send_message(request: MessageRequest):
    routing_engine = RoutingEngine()
    dispatcher_manager = DispatcherManager()
    # LGPD: audita evento e filtra dados sensíveis
    lgpd_gateway.audit_event(request.dict(), action="send")
    filtered_data = lgpd_gateway.filter_sensitive(request.dict())
    # Salva intent
    intent_id = intent_repo.save_intent(filtered_data)
    routing_result = routing_engine.route_intent(filtered_data)
    dispatch_result = dispatcher_manager.dispatch(routing_result["channel"], filtered_data)
    # Salva resultado de entrega
    delivery_repo.save_result({
        "message_id": dispatch_result["message_id"],
        "status": dispatch_result["status"],
        "intent_id": intent_id,
        "channel": request.channel,
        "recipient": request.recipient
    })
    return MessageResponse(
        message_id=dispatch_result["message_id"],
        status=dispatch_result["status"],
        channel=request.channel,
        recipient=request.recipient
    )

# Endpoint protegido: Consulta de status de entrega

# Endpoint protegido: Consulta de status de entrega
@router.get("/api/v1/status/{message_id}", dependencies=[Depends(get_current_user)])
async def get_status(message_id: str):
    result = delivery_repo.get_result(message_id)
    return result

# Endpoint administrativo: Listar intents (apenas admin)

# Endpoint administrativo: Listar intents (apenas admin)
@router.get("/api/v1/intents", dependencies=[Depends(require_role("admin"))])
async def list_intents():
    return intent_repo.list_intents()
