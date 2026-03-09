import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from gestor.api.deps import get_db, require_tenant_gestor
from gestor.models.patient import Patient
from gestor.schemas.patient import PatientCreate, PatientResponse, PatientFhirLink
from gestor.config import settings
from gestor.services.kestra_client import KestraClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])


async def dispatch_sync_to_fhir(patient_id: str, tenant_id: str, patient_name: str, patient_cpf: str):
    """
    Background Task que engatilha o Kestra para o Workflow de Sincronização.
    Dessa forma a API do sistema não fica travada aguardando o FHIR/Grahame.
    """
    logger.info(f"Disparando Workflow Kestra para sinc do paciente {patient_id}")
    try:
        client = KestraClient(
            base_url=settings.KESTRA_URL,
            api_key=settings.KESTRA_API_KEY,
            timeout=settings.KESTRA_TIMEOUT
        )
        await client.execute_flow(
            namespace="intellicare",
            flow_id="sync-fhir-patient",
            inputs={
                "postgresql_patient_id": patient_id,
                "tenant_id": tenant_id,
                "nome": patient_name,
                "cpf": patient_cpf
            },
            wait=False
        )
        await client.close()
    except Exception as e:
        logger.error(f"Falha ao acionar o orquestrador (Kestra) para paciente {patient_id}: {str(e)}")


@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(
    *,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_tenant_gestor),
    patient_in: PatientCreate,
    background_tasks: BackgroundTasks
) -> Any:
    """
    Cria um novo paciente operacional no Gestor (PostgreSQL).
    Isso é extremamente rápido para a UI (SaaS).
    Em paralelo, dispara evento de orquestração via Kestra para gravar no FHIR e devolver o 'fhir_patient_id'.
    """
    # 1. Checagens de Duplicidade no banco do Gestor
    if patient_in.cpf:
        stmt = select(Patient).where(Patient.cpf == patient_in.cpf)
        result = await db.execute(stmt)
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Paciente com esse CPF já existe")
            
    # 2. Salva no banco Operacional Rápido
    db_patient = Patient(
        nome=patient_in.nome,
        cpf=patient_in.cpf,
        cns=patient_in.cns,
        data_nascimento=patient_in.data_nascimento,
        telefone=patient_in.telefone,
        sexo=patient_in.sexo,
        active=patient_in.active,
        default_sector_id=patient_in.default_sector_id
    )
    
    db.add(db_patient)
    await db.commit()
    await db.refresh(db_patient)
    
    # 3. KESTRA TRIGGER (Asynchronously sync this Patient into FHIR)
    background_tasks.add_task(
        dispatch_sync_to_fhir,
        patient_id=str(db_patient.id),
        tenant_id=payload.get("tenant_id", ""),
        patient_name=db_patient.nome,
        patient_cpf=db_patient.cpf or ""
    )
    
    return db_patient


@router.get("", response_model=list[PatientResponse])
async def get_patients(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_tenant_gestor),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retorna pacientes operacionais da Base PostgreSQL nativa do Gestor.
    Utilizando métricas ultra-rápidas para Dashboards.
    """
    # No futuro, podemos filtrar pelo "default_sector_id" usando o user_payload
    stmt = select(Patient).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/{patient_id}/fhir-link", response_model=PatientResponse)
async def link_fhir_patient(
    patient_id: str,
    link_in: PatientFhirLink,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_tenant_gestor),
) -> Any:
    """
    Endpoint chamado pelo Kestra para atualizar a referência oficial do recurso FHIR 
    (GRAHAME) na tabela local do PostgreSQL após a criação ser concluída assincronamente.
    """
    stmt = select(Patient).where(Patient.id == patient_id)
    result = await db.execute(stmt)
    db_patient = result.scalars().first()
    
    if not db_patient:
        raise HTTPException(status_code=404, detail="Paciente operacional não encontrado")
        
    db_patient.fhir_patient_id = link_in.fhir_patient_id
    
    db.add(db_patient)
    await db.commit()
    await db.refresh(db_patient)
    
    return db_patient

