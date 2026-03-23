"""Oswaldo IA — Sugestão de CID-10 e Prescrição (Hybrid)."""
from __future__ import annotations

import json
import logging
from uuid import UUID

from intellicare_core.contracts.base import TenantContext
from modules.cuidado.service import CuidadoService
from modules.marie.client import call_marie, is_marie_enabled
from modules.oswaldo.contracts import (
    OswaldoSuggestRequest, OswaldoSuggestion, PrescriptionItem,
)
from modules.shared.llm import call_llm, get_prompt_template

logger = logging.getLogger("intellicare.oswaldo.services")
_CUIDADO_SERVICE = CuidadoService()

OSWALDO_CID10_PROMPT_FALLBACK = """
Você é um assistente clínico. Com base nas informações abaixo, sugira:
1. O CID-10 mais provável (código e descrição curta)
"""

OSWALDO_PRESCRIPTION_PROMPT_FALLBACK = """
2. Uma prescrição inicial com até 3 itens (medicamento, posologia, duração)

Queixa principal: {chief_complaint}
Diagnósticos anteriores: {recent_diagnoses}
Medicamentos em uso: {current_medications}

Responda APENAS com JSON no formato:
{{
  "cid10_code": "X00",
  "cid10_desc": "Descrição curta",
  "items": [
    {{"drug": "Nome 500mg", "posology": "1 comp 8/8h", "duration": "5 dias"}}
  ]
}}
"""


async def suggest(ctx: TenantContext, req: OswaldoSuggestRequest) -> OswaldoSuggestion:
    marie_result: dict | None = None
    patient_uuid = _coerce_patient_uuid(req.patient_id)

    if is_marie_enabled() and patient_uuid is not None:
        marie_response = await call_marie(
            workflow_slug="cid10_rag",
            inputs={
                "query": req.chief_complaint,
                "patient_history": await _get_patient_timeline_summary(ctx, patient_uuid),
            },
        )
        marie_result = _parse_marie_cid10_response(marie_response)

    result, confidence = await _local_suggestion(req)
    if marie_result:
        result["cid10_code"] = marie_result["cid10_code"]
        result["cid10_desc"] = marie_result["cid10_desc"]
        result["model"] = marie_result.get("model", "marie")
        confidence = "high"

    return OswaldoSuggestion(
        cid10_code=result.get("cid10_code", "Z00"),
        cid10_desc=result.get("cid10_desc", "Consulta de rotina"),
        prescription_items=[PrescriptionItem(**i) for i in result.get("items", [])],
        model=result.get("model", "rule-based"),
        confidence=confidence,
    )


async def _local_suggestion(req: OswaldoSuggestRequest) -> tuple[dict, str]:
    cid10_prompt = await get_prompt_template("oswaldo_cid10", OSWALDO_CID10_PROMPT_FALLBACK)
    prescription_prompt = await get_prompt_template("oswaldo_prescription", OSWALDO_PRESCRIPTION_PROMPT_FALLBACK)
    prompt = f"{cid10_prompt.strip()}\n{prescription_prompt.strip()}".format(
        chief_complaint=req.chief_complaint,
        recent_diagnoses=", ".join(req.recent_diagnoses or []) or "nenhum",
        current_medications=", ".join(req.current_medications or []) or "nenhum",
    )
    try:
        return await call_llm(prompt), "high"
    except Exception:
        return _rule_based_suggestion(req), "low"


def _coerce_patient_uuid(patient_id: str | int) -> UUID | None:
    try:
        return UUID(str(patient_id))
    except (TypeError, ValueError):
        return None


async def _get_patient_timeline_summary(ctx: TenantContext, patient_id: UUID) -> str:
    try:
        timeline = await _CUIDADO_SERVICE.clinical_timeline(ctx, patient_id, limit=8, offset=0)
    except Exception:
        logger.debug("Falha ao buscar timeline para Marie", exc_info=True)
        return ""

    lines: list[str] = []
    for item in timeline.get("items", []):
        title = item.get("title") or item.get("event_type") or "evento"
        subtitle = item.get("subtitle") or ""
        status = item.get("status") or ""
        line = f"- {title}"
        if subtitle:
            line += f": {subtitle}"
        if status:
            line += f" [{status}]"
        lines.append(line)

    summary = "\n".join(lines)
    return summary[:2000]


def _parse_marie_cid10_response(response: dict | None) -> dict | None:
    if not response:
        return None

    if isinstance(response.get("answer"), str):
        answer = response["answer"].strip()
        try:
            data = json.loads(answer)
            if data.get("cid10_code"):
                data["model"] = "marie"
                return data
        except json.JSONDecodeError:
            pass

    if response.get("cid10_code"):
        data = dict(response)
        data["model"] = "marie"
        return data

    outputs = response.get("outputs")
    if isinstance(outputs, dict) and outputs.get("cid10_code"):
        data = dict(outputs)
        data["model"] = "marie"
        return data

    return None


def _rule_based_suggestion(req: OswaldoSuggestRequest) -> dict:
    """Fallback determinístico quando LLM não está configurado."""
    return {
        "cid10_code": "Z00",
        "cid10_desc": "Consulta de rotina (preencher manualmente)",
        "items": [],
        "model": "rule-based",
    }

from modules.oswaldo.contracts import ReceituarioData, MedicationItem
from modules.oswaldo import repository
from intellicare_core.pdf.renderer import render_pdf
import qrcode
import base64
import re
from io import BytesIO

def generate_qr_base64(data: str) -> str:
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


FREQ_MAP = {
    "4/4h": "a cada 4 horas",
    "6/6h": "a cada 6 horas",
    "8/8h": "a cada 8 horas",
    "12/12h": "a cada 12 horas",
    "1x/dia": "uma vez ao dia",
    "2x/dia": "duas vezes ao dia",
    "3x/dia": "três vezes ao dia",
}

NUM_EXTENSO = {
    "1": "um", "2": "dois", "3": "três", "4": "quatro",
    "5": "cinco", "6": "seis", "7": "sete", "8": "oito",
}

ROTA_FORMA = {
    "comprimido": "via oral", "comp": "via oral",
    "cápsula": "via oral", "xarope": "via oral",
    "pomada": "uso tópico", "creme": "uso tópico",
    "colírio": "uso oftálmico", "injetável": "via intramuscular",
}


def _expand_freq(text: str) -> str:
    for abbr, full in FREQ_MAP.items():
        text = text.replace(abbr, full)
    return text


def _expand_numbers(text: str) -> str:
    def _repl(m):
        n = m.group(0)
        return f"{n} ({NUM_EXTENSO[n]})" if n in NUM_EXTENSO else n
    return re.sub(r'\b([1-8])\b', _repl, text)


def detect_route(text: str) -> str:
    """Detecta rota de administração a partir do texto da posologia."""
    lower = text.lower()
    for form, route in ROTA_FORMA.items():
        if form in lower:
            return route.title()
    return "Via Oral"


def format_posologia(item: dict) -> str:
    """Formata posologia seguindo padrão formal CFM/ANVISA."""
    posology = item.get("posology", "")
    duration = item.get("duration", "")

    text = _expand_freq(posology)
    text = _expand_numbers(text)

    if not any(text.lower().startswith(v) for v in ("tomar", "aplicar", "usar", "instilar")):
        text = f"Tomar {text}"

    if duration:
        dur = _expand_freq(duration)
        dur = _expand_numbers(dur)
        text += f" por {dur}"

    if not text.endswith("."):
        text += "."

    return text


async def generate_receituario(ctx: TenantContext, prescription_id: int, ptype: str) -> bytes:
    rx = await repository.get_prescription(ctx, prescription_id)
    if not rx:
        raise ValueError("Prescription not found")

    prof = await repository.get_professional_by_keycloak_id(ctx, ctx.user_id)
    pat = await repository.get_patient_by_id(ctx, rx.patient_id)

    prof_name = prof.get("name", ctx.email) if prof else getattr(ctx, "email", "Dr(a).")
    crm = prof.get("crm_number", "") if prof else ""
    crm_state = prof.get("crm_state", "") if prof else ""
    specialty = prof.get("specialty", "Clínico Geral") if prof else "Clínico Geral"

    pat_name = pat.get("name", "Paciente") if pat else "Paciente"
    pat_cpf = pat.get("cpf", "") if pat else ""
    
    import datetime
    pat_age = 0
    if pat and pat.get("birth_date"):
        try:
            if isinstance(pat["birth_date"], datetime.date):
                pat_age = (datetime.date.today() - pat["birth_date"]).days // 365
            else:
                bd = datetime.datetime.strptime(str(pat["birth_date"])[:10], "%Y-%m-%d").date()
                pat_age = (datetime.date.today() - bd).days // 365
        except Exception:
            pass

    meds = []
    for idx, it in enumerate(rx.items, 1):
        m = MedicationItem(
            order=idx,
            drug_name=it.drug,
            concentration="",
            pharmaceutical_form="",
            quantity=1,
            quantity_unit="unidade(s)",
            dosage_instructions=format_posologia(it.model_dump()),
            route=detect_route(it.posology)
        )
        meds.append(m)

    qr_data = f"https://intellicare.ia.br/valida/rx/{prescription_id}?tenant={ctx.tenant_id}"
    qr_b64 = generate_qr_base64(qr_data)

    data = ReceituarioData(
        prescription_id=str(rx.id),
        issued_at=rx.created_at,
        prescription_type=ptype,
        professional_name=prof_name,
        crm=crm,
        crm_state=crm_state,
        specialty=specialty,
        clinic_address="IntelliCare Saúde Digital",
        clinic_phone="(11) 99999-9999",
        patient_name=pat_name,
        patient_age=pat_age,
        patient_cpf=pat_cpf,
        cid10_code=rx.cid10_code or "",
        cid10_description=rx.cid10_desc or "",
        medications=meds,
        prescription_validity_days=30 if ptype == "special_control" else None,
        prescription_number="NT-" + str(rx.id).zfill(6) if ptype == "special_control" else None
    )

    context = {
        "data": data,
        "qr_code_b64": qr_b64,
        "issued_date_br": rx.created_at.strftime("%d/%m/%Y") if rx.created_at else "",
        "issued_date_extenso": rx.created_at.strftime("%d de %B de %Y") if rx.created_at else ""
    }

    pdf_bytes = render_pdf("receituario.html", context)

    # Assinar digitalmente se profissional tem certificado A1 cadastrado
    if prof and prof.get("id"):
        pdf_bytes = await _try_sign_pdf(ctx, pdf_bytes, prof["id"])

    # Hook DEM-081: Persistir quantidade de interações (KPI)
    try:
        from modules.oswaldo.interactions import check_interactions
        from intellicare_core.db.session import tenant_session
        from sqlalchemy import text
        medications = [item.drug for item in rx.items]
        if len(medications) > 1:
            warnings, _ = await check_interactions(medications)
            if warnings:
                async with tenant_session(ctx) as db:
                    await db.execute(
                        text("UPDATE prescriptions SET interaction_warnings_count = :count WHERE id = :id"),
                        {"count": len(warnings), "id": rx.id}
                    )
    except Exception as e:
        logger.error("Erro ao verificar interações/salvar KPI durante receituário: %s", e)

    return pdf_bytes


async def _try_sign_pdf(ctx: TenantContext, pdf_bytes: bytes, professional_id: int) -> bytes:
    """Tenta assinar o PDF se o profissional tem certificado. Nunca bloqueia a geração."""
    try:
        cert = await repository.get_professional_certificate(ctx, professional_id)
        if not cert:
            return pdf_bytes

        from intellicare_core.crypto import decrypt_bytes, decrypt_text
        from modules.oswaldo.pdf_signer import sign_pdf

        pfx_bytes = decrypt_bytes(cert["pfx_encrypted"])
        pfx_password = decrypt_text(cert["password_hash"])
        return sign_pdf(pfx_bytes=pfx_bytes, pfx_password=pfx_password, pdf_bytes=pdf_bytes)
    except Exception as e:
        logger.warning("Assinatura digital falhou para professional_id=%s: %s", professional_id, e)
        return pdf_bytes
