"""Router HL7v2 — Endpoint para receber mensagens HL7v2 ADT^A04.

Este módulo implementa o endpoint REST para receber mensagens HL7v2 de sistemas legados
hospitalares (Tasy, MV, Philips, etc.) e processar:
1. Parse da mensagem HL7v2
2. Validação de estrutura e campos obrigatórios
3. Conversão para recursos FHIR R4 (Patient + Encounter)
4. Publicação de eventos no Redis Stream
5. Geração de ACK (acknowledgment)

Content-Type: application/x-hl7-v2
Response: PlainTextResponse (ACK message)

Referências:
- HL7 v2.5: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=185
- FHIR R4: https://www.hl7.org/fhir/R4/
"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.hl7v2.parser import HL7v2Parser
from grahame.hl7v2.segments import MSHSegment, PIDSegment, PV1Segment
from grahame.hl7v2.messages.adt_a04 import ADTMessage
from grahame.hl7v2.converters import PatientConverter, EncounterConverter
from grahame.hl7v2.ack import ACKGenerator
from grahame.events import HL7v2EventPublisher
from grahame.api.dependencies import validate_hl7v2_api_key, update_api_key_usage, check_rate_limit, get_db_session
from grahame.models.hl7v2_api_key import HL7v2APIKey
from grahame.models.hl7v2_audit import HL7v2AuditLog

logger = logging.getLogger(__name__)

router = APIRouter(tags=["HL7v2"])

# Global event publisher (initialized on startup)
_event_publisher: Optional[HL7v2EventPublisher] = None


def init_hl7v2_publisher(redis_url: str):
    """Initialize HL7v2 event publisher.
    
    This should be called during application startup.
    
    Args:
        redis_url: Redis connection URL (e.g., "redis://localhost:6379")
    """
    global _event_publisher
    _event_publisher = HL7v2EventPublisher(redis_url)
    logger.info("HL7v2 Event Publisher initialized")


async def get_event_publisher() -> Optional[HL7v2EventPublisher]:
    """Get the global event publisher instance."""
    return _event_publisher


@router.post(
    "/hl7v2/adt-a04",
    response_class=PlainTextResponse,
    summary="Receber mensagem HL7v2 ADT^A04",
    description="""
    Endpoint para receber mensagens HL7v2 ADT^A04 (Register Patient) de sistemas legados.
    
    **Fluxo:**
    1. Parse da mensagem HL7v2
    2. Validação de estrutura e campos obrigatórios
    3. Conversão para recursos FHIR R4 (Patient + Encounter)
    4. Publicação de eventos no Redis Stream
    5. Geração de ACK (acknowledgment)
    
    **Content-Type:** `application/x-hl7-v2` ou `text/plain`
    
    **Response:** PlainTextResponse com mensagem ACK
    
    **Exemplo de mensagem:**
    ```
    MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5
    PID|1||12345^^^HOSPITAL^MR||Silva^João^Carlos||19800115|M|||Rua das Flores, 123^^São Paulo^SP^01234-567^BR
    PV1|1|I|WARD1^101^A^HOSPITAL||||||||||||||||VN123456|||||||||||||||||||HOSPITAL|||||20260224100000
    ```
    
    **Exemplo de ACK:**
    ```
    MSH|^~\\&|GRAHAME|INTELLICARE|HOSPITAL|FACILITY|20260224100001||ACK^A04|ACK00001|P|2.5
    MSA|AA|MSG00001|Message accepted
    ```
    """,
)
async def receive_adt_a04(
    request: Request,
    api_key: HL7v2APIKey = Depends(validate_hl7v2_api_key),
    db: AsyncSession = Depends(get_db_session),
    content_type: Optional[str] = Header(None),
) -> PlainTextResponse:
    """Receber e processar mensagem HL7v2 ADT^A04.

    **Autenticação:** Requer API Key no header `X-API-Key`

    Args:
        request: FastAPI request object
        api_key: Validated API Key (injected by dependency)
        content_type: Content-Type header (should be application/x-hl7-v2 or text/plain)

    Returns:
        PlainTextResponse: ACK message (success or error)

    Raises:
        HTTPException: 401 if API Key is invalid
        HTTPException: 403 if IP is not whitelisted
        HTTPException: 400 if message is invalid
        HTTPException: 500 if processing fails
    """
    # Start timing
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(request, api_key)

    # Read raw message body
    raw_message = await request.body()
    message = raw_message.decode("utf-8")

    # Get client info
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    logger.info(
        f"Received HL7v2 message from {api_key.system_identifier} "
        f"({len(message)} bytes, IP: {client_ip})"
    )
    
    try:
        # Step 1: Parse HL7v2 message
        parser = HL7v2Parser(message)
        msh = MSHSegment.from_parser(parser)
        pid = PIDSegment.from_parser(parser)
        
        # PV1 is optional for ADT^A04
        try:
            pv1 = PV1Segment.from_parser(parser)
        except Exception:
            pv1 = None
            logger.warning("PV1 segment not found or invalid, continuing without it")
        
        # Step 2: Create and validate ADT^A04 message
        adt_message = ADTMessage(msh=msh, pid=pid, pv1=pv1)
        is_valid, error_message = adt_message.validate()
        
        if not is_valid:
            logger.error(f"Message validation failed: {error_message}")
            # Generate reject ACK
            ack_generator = ACKGenerator()
            ack = ack_generator.generate_reject(msh, error_message or "Validation failed")

            # Create audit log for validation failure
            processing_time_ms = int((time.time() - start_time) * 1000)
            await create_audit_log(
                db=db,
                api_key=api_key,
                request=request,
                message=message,
                msh=msh,
                success=False,
                http_status_code=400,
                ack_code="AR",
                error_message=error_message,
                processing_time_ms=processing_time_ms,
            )

            return PlainTextResponse(content=ack, status_code=status.HTTP_400_BAD_REQUEST)
        
        # Step 3: Convert to FHIR resources
        patient_converter = PatientConverter()
        patient = patient_converter.convert(pid, msh)
        
        encounter = None
        if pv1:
            encounter_converter = EncounterConverter()
            # Use patient ID from FHIR resource if available, otherwise use HL7v2 ID
            patient_id = patient.get("id", pid.patient_id_list[0]["id"] if pid.patient_id_list else "unknown")
            encounter = encounter_converter.convert(pv1, msh, patient_id=patient_id)
        
        # Step 4: Publish events to Redis Stream
        publisher = await get_event_publisher()
        if publisher:
            await publisher.connect()
            
            # Publish patient-created event
            await publisher.publish_patient_created(
                patient=patient,
                source_system=f"{msh.sending_application}:{msh.sending_facility}",
                message_control_id=msh.message_control_id,
            )
            
            # Publish encounter-created event if PV1 exists
            if encounter:
                await publisher.publish_encounter_created(
                    encounter=encounter,
                    patient_id=patient_id,
                    source_system=f"{msh.sending_application}:{msh.sending_facility}",
                    message_control_id=msh.message_control_id,
                )

            await publisher.disconnect()

        # Step 5: Generate success ACK
        ack_generator = ACKGenerator()
        ack = ack_generator.generate_success(msh, message="Message accepted and processed")

        # Step 6: Create audit log
        processing_time_ms = int((time.time() - start_time) * 1000)
        await create_audit_log(
            db=db,
            api_key=api_key,
            request=request,
            message=message,
            msh=msh,
            success=True,
            http_status_code=200,
            ack_code="AA",
            error_message=None,
            processing_time_ms=processing_time_ms,
            patient_id=patient.get("id"),
            encounter_id=encounter.get("id") if encounter else None,
        )

        # Step 7: Update API Key usage
        await update_api_key_usage(api_key, db)

        logger.info(
            f"Successfully processed ADT^A04 message: "
            f"control_id={msh.message_control_id}, "
            f"patient_id={patient.get('id', 'unknown')}"
        )

        return PlainTextResponse(content=ack, status_code=status.HTTP_200_OK)

    except ValueError as e:
        # Parsing or validation error
        logger.error(f"Message parsing error: {e}")

        # Try to extract MSH for ACK generation and audit
        msh_for_ack = None
        try:
            parser = HL7v2Parser(message)
            msh_for_ack = MSHSegment.from_parser(parser)
            ack_generator = ACKGenerator()
            ack = ack_generator.generate_error(msh_for_ack, error_message=str(e))

            # Create audit log for parsing error
            processing_time_ms = int((time.time() - start_time) * 1000)
            await create_audit_log(
                db=db,
                api_key=api_key,
                request=request,
                message=message,
                msh=msh_for_ack,
                success=False,
                http_status_code=400,
                ack_code="AE",
                error_message=str(e),
                processing_time_ms=processing_time_ms,
            )

            return PlainTextResponse(content=ack, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception:
            # Cannot parse MSH, create audit without MSH and return generic error
            processing_time_ms = int((time.time() - start_time) * 1000)
            await create_audit_log(
                db=db,
                api_key=api_key,
                request=request,
                message=message,
                msh=None,
                success=False,
                http_status_code=400,
                ack_code="AE",
                error_message=f"Invalid HL7v2 message: {str(e)}",
                processing_time_ms=processing_time_ms,
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid HL7v2 message: {str(e)}"
            )

    except Exception as e:
        # Unexpected error
        logger.exception(f"Unexpected error processing HL7v2 message: {e}")

        # Try to generate error ACK and create audit
        msh_for_ack = None
        try:
            parser = HL7v2Parser(message)
            msh_for_ack = MSHSegment.from_parser(parser)
            ack_generator = ACKGenerator()
            ack = ack_generator.generate_error(msh_for_ack, error_message="Internal server error")

            # Create audit log for internal error
            processing_time_ms = int((time.time() - start_time) * 1000)
            await create_audit_log(
                db=db,
                api_key=api_key,
                request=request,
                message=message,
                msh=msh_for_ack,
                success=False,
                http_status_code=500,
                ack_code="AE",
                error_message=f"Internal server error: {str(e)}",
                processing_time_ms=processing_time_ms,
            )

            return PlainTextResponse(content=ack, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception:
            # Cannot parse MSH, create audit without MSH and return generic error
            processing_time_ms = int((time.time() - start_time) * 1000)
            await create_audit_log(
                db=db,
                api_key=api_key,
                request=request,
                message=message,
                msh=None,
                success=False,
                http_status_code=500,
                ack_code="AE",
                error_message=f"Internal server error: {str(e)}",
                processing_time_ms=processing_time_ms,
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error processing HL7v2 message"
            )


async def create_audit_log(
    db: AsyncSession,
    api_key: HL7v2APIKey,
    request: Request,
    message: str,
    msh: Optional[MSHSegment],
    success: bool,
    http_status_code: int,
    ack_code: Optional[str],
    error_message: Optional[str],
    processing_time_ms: int,
    patient_id: Optional[str] = None,
    encounter_id: Optional[str] = None,
) -> None:
    """Create audit log entry for HL7v2 request.

    Args:
        db: Database session
        api_key: API Key used
        request: FastAPI request
        message: Raw HL7v2 message
        msh: Parsed MSH segment (if available)
        success: Whether processing was successful
        http_status_code: HTTP status code
        ack_code: ACK code (AA, AR, AE)
        error_message: Error message (if any)
        processing_time_ms: Processing time in milliseconds
        patient_id: FHIR Patient ID (if created)
        encounter_id: FHIR Encounter ID (if created)
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    audit_log = HL7v2AuditLog(
        api_key_id=api_key.id,
        request_ip=client_ip,
        request_user_agent=user_agent,
        message_control_id=msh.message_control_id if msh else None,
        message_type=msh.message_type if msh else None,
        sending_application=msh.sending_application if msh else None,
        sending_facility=msh.sending_facility if msh else None,
        raw_message=message,
        message_size_bytes=len(message.encode("utf-8")),
        success=success,
        http_status_code=http_status_code,
        ack_code=ack_code,
        error_message=error_message,
        processing_time_ms=processing_time_ms,
        patient_id=patient_id,
        encounter_id=encounter_id,
    )

    db.add(audit_log)
    await db.commit()

    logger.info(
        f"Audit log created: {api_key.system_identifier} - "
        f"{'SUCCESS' if success else 'FAILED'} - {processing_time_ms}ms"
    )
