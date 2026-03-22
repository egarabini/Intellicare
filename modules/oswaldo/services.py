"""Oswaldo IA — Sugestão de CID-10 e Prescrição (Hybrid)."""
from __future__ import annotations

from intellicare_core.contracts.base import TenantContext
from modules.oswaldo.contracts import (
    OswaldoSuggestRequest, OswaldoSuggestion, PrescriptionItem,
)
from modules.shared.llm import call_llm

OSWALDO_PROMPT = """
Você é um assistente clínico. Com base nas informações abaixo, sugira:
1. O CID-10 mais provável (código e descrição curta)
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
    prompt = OSWALDO_PROMPT.format(
        chief_complaint=req.chief_complaint,
        recent_diagnoses=", ".join(req.recent_diagnoses or []) or "nenhum",
        current_medications=", ".join(req.current_medications or []) or "nenhum",
    )

    try:
        result = await call_llm(prompt)
        confidence = "high"
    except Exception:
        result = _rule_based_suggestion(req)
        confidence = "low"

    return OswaldoSuggestion(
        cid10_code=result.get("cid10_code", "Z00"),
        cid10_desc=result.get("cid10_desc", "Consulta de rotina"),
        prescription_items=[PrescriptionItem(**i) for i in result.get("items", [])],
        model=result.get("model", "rule-based"),
        confidence=confidence,
    )


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

    return render_pdf("receituario.html", context)
