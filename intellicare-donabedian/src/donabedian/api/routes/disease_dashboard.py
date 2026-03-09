"""
Disease-specific dashboard endpoints for the Gestor/Admin frontends.

Provides aggregated disease program dashboards with KPIs, trends,
stage distribution, geographic data, and patient lists.

Diseases supported: DRC, Diabetes, Hipertensão, Câncer.
"""

import logging
import random
from datetime import date, timedelta
from enum import Enum
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Enums & Constants ──────────────────────────────────────

class DiseaseCode(str, Enum):
    DRC = "drc"
    DIABETES = "diabetes"
    HIPERTENSAO = "hipertensao"
    CANCER = "cancer"


class PatientStatus(str, Enum):
    CONTROLLED = "controlled"
    ATTENTION = "attention"
    CRITICAL = "critical"
    LOST = "lost"


DISEASE_ICD_MAP = {
    DiseaseCode.DRC: ["N18", "N18.1", "N18.2", "N18.3", "N18.4", "N18.5"],
    DiseaseCode.DIABETES: ["E10", "E11", "E12", "E13", "E14"],
    DiseaseCode.HIPERTENSAO: ["I10", "I11", "I12", "I13", "I15"],
    DiseaseCode.CANCER: ["C00-C97", "D00-D09"],
}

DISEASE_STAGES = {
    DiseaseCode.DRC: [
        {"id": "G1", "label": "Estágio 1", "description": "TFG ≥ 90 ml/min"},
        {"id": "G2", "label": "Estágio 2", "description": "TFG 60-89 ml/min"},
        {"id": "G3a", "label": "Estágio 3a", "description": "TFG 45-59 ml/min"},
        {"id": "G3b", "label": "Estágio 3b", "description": "TFG 30-44 ml/min"},
        {"id": "G4", "label": "Estágio 4", "description": "TFG 15-29 ml/min"},
        {"id": "G5", "label": "Estágio 5", "description": "TFG < 15 ml/min (diálise)"},
    ],
    DiseaseCode.DIABETES: [
        {"id": "pre", "label": "Pré-diabetes", "description": "HbA1c 5.7-6.4%"},
        {"id": "controlled", "label": "Controlado", "description": "HbA1c < 7%"},
        {"id": "moderate", "label": "Moderado", "description": "HbA1c 7-8.5%"},
        {"id": "uncontrolled", "label": "Descompensado", "description": "HbA1c > 8.5%"},
        {"id": "complications", "label": "Com Complicações", "description": "Nefro/Retino/Neuropatia"},
    ],
    DiseaseCode.HIPERTENSAO: [
        {"id": "elevated", "label": "PA Elevada", "description": "PAS 120-129 / PAD <80"},
        {"id": "stage1", "label": "Estágio 1", "description": "PAS 130-139 / PAD 80-89"},
        {"id": "stage2", "label": "Estágio 2", "description": "PAS ≥140 / PAD ≥90"},
        {"id": "crisis", "label": "Crise Hipertensiva", "description": "PAS >180 / PAD >120"},
    ],
    DiseaseCode.CANCER: [
        {"id": "screening", "label": "Rastreamento", "description": "Pacientes em rastreamento ativo"},
        {"id": "early", "label": "Estágio Inicial", "description": "TNM I-II"},
        {"id": "advanced", "label": "Estágio Avançado", "description": "TNM III"},
        {"id": "metastatic", "label": "Metastático", "description": "TNM IV"},
        {"id": "remission", "label": "Remissão", "description": "Sem evidência de doença"},
    ],
}


# ─── Response Schemas ────────────────────────────────────────

class KPIItem(BaseModel):
    label: str
    value: float
    previous_value: Optional[float] = None
    unit: Optional[str] = None
    format: str = "number"
    trend: str = "stable"
    trend_is_good: Optional[bool] = None
    color: Optional[str] = None


class TrendPoint(BaseModel):
    date: str
    value: float
    target: Optional[float] = None


class TrendSeries(BaseModel):
    id: str
    label: str
    color: str
    data: list[TrendPoint]


class StageDistItem(BaseModel):
    stage: str
    label: str
    count: int
    percentage: float
    color: str


class GeoRegionItem(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    patient_count: int
    control_rate: float
    alert_count: int


class PatientIndicatorItem(BaseModel):
    name: str
    value: float
    unit: str
    reference: str
    status: str


class PatientItem(BaseModel):
    id: str
    name: str
    cpf: str
    age: int
    gender: str
    disease: str
    stage: str
    last_visit: str
    next_visit: Optional[str] = None
    status: str
    establishment: str
    indicators: list[PatientIndicatorItem]


class DiseaseDashboardResponse(BaseModel):
    """Full disease dashboard response."""
    disease: str
    period: str
    kpis: list[KPIItem]
    trends: list[TrendSeries]
    stage_distribution: list[StageDistItem] = Field(alias="stageDistribution")
    geo_data: list[GeoRegionItem] = Field(alias="geoData")
    patients: list[PatientItem]
    total_patients: int = Field(alias="totalPatients")
    total_pages: int = Field(alias="totalPages")

    model_config = {"populate_by_name": True}


# ─── Mock data generation (to be replaced by real DB queries) ──

FIRST_NAMES = [
    "Maria", "José", "Ana", "João", "Francisca", "Antonio", "Adriana", "Carlos",
    "Lúcia", "Paulo", "Juliana", "Pedro", "Fernanda", "Lucas", "Patrícia", "Marcos",
]
LAST_NAMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa", "Ferreira",
]
ESTABLISHMENTS = [
    "UBS Central", "UBS Norte", "UBS Sul", "UPA Leste", "Hospital Municipal",
    "CAPS II", "Policlínica", "UBS Vila Nova", "UBS Jardim", "CEO Regional",
]
REGIONS = [
    {"id": "centro", "name": "Centro", "lat": -15.79, "lng": -47.88},
    {"id": "norte", "name": "Zona Norte", "lat": -15.75, "lng": -47.90},
    {"id": "sul", "name": "Zona Sul", "lat": -15.83, "lng": -47.86},
    {"id": "leste", "name": "Zona Leste", "lat": -15.78, "lng": -47.82},
    {"id": "oeste", "name": "Zona Oeste", "lat": -15.80, "lng": -47.94},
    {"id": "rural", "name": "Zona Rural", "lat": -15.70, "lng": -48.00},
]


def _rand(lo: int, hi: int) -> int:
    return random.randint(lo, hi)


def _randf(lo: float, hi: float, dec: int = 1) -> float:
    return round(random.uniform(lo, hi), dec)


def _generate_kpis(disease: DiseaseCode) -> list[KPIItem]:
    base = {
        DiseaseCode.DRC: [
            KPIItem(label="Total de Pacientes", value=_rand(1200, 3500), previous_value=_rand(1100, 3400), format="number", trend="up", trend_is_good=False),
            KPIItem(label="Taxa de Controle", value=_randf(45, 72), previous_value=_randf(42, 68), unit="%", format="percent", trend="up", trend_is_good=True),
            KPIItem(label="Em Diálise", value=_rand(80, 250), previous_value=_rand(85, 260), format="number", trend="down", trend_is_good=True),
            KPIItem(label="TFG Média", value=_randf(35, 65), unit="ml/min", format="number", trend="stable", trend_is_good=True),
            KPIItem(label="Perda de Seguimento", value=_rand(30, 120), previous_value=_rand(35, 130), format="number", trend="down", trend_is_good=True, color="#f59e0b"),
            KPIItem(label="Alertas Ativos", value=_rand(5, 45), format="number", trend="down", trend_is_good=True, color="#ef4444"),
        ],
        DiseaseCode.DIABETES: [
            KPIItem(label="Total de Pacientes", value=_rand(3000, 8000), previous_value=_rand(2800, 7500), format="number", trend="up", trend_is_good=False),
            KPIItem(label="HbA1c < 7%", value=_randf(50, 68), previous_value=_randf(48, 65), unit="%", format="percent", trend="up", trend_is_good=True),
            KPIItem(label="Com Complicações", value=_rand(200, 800), previous_value=_rand(210, 820), format="number", trend="down", trend_is_good=True),
            KPIItem(label="HbA1c Média", value=_randf(6.5, 8.5), unit="%", format="number", trend="down", trend_is_good=True),
            KPIItem(label="Perda de Seguimento", value=_rand(50, 200), previous_value=_rand(55, 220), format="number", trend="down", trend_is_good=True, color="#f59e0b"),
            KPIItem(label="Alertas Ativos", value=_rand(10, 60), format="number", trend="down", trend_is_good=True, color="#ef4444"),
        ],
        DiseaseCode.HIPERTENSAO: [
            KPIItem(label="Total de Pacientes", value=_rand(5000, 15000), previous_value=_rand(4800, 14000), format="number", trend="up", trend_is_good=False),
            KPIItem(label="PA Controlada", value=_randf(40, 65), previous_value=_randf(38, 62), unit="%", format="percent", trend="up", trend_is_good=True),
            KPIItem(label="Crise Hipertensiva", value=_rand(20, 100), previous_value=_rand(25, 110), format="number", trend="down", trend_is_good=True),
            KPIItem(label="PAS Média", value=_randf(128, 155), unit="mmHg", format="number", trend="down", trend_is_good=True),
            KPIItem(label="Perda de Seguimento", value=_rand(100, 500), previous_value=_rand(120, 520), format="number", trend="down", trend_is_good=True, color="#f59e0b"),
            KPIItem(label="Alertas Ativos", value=_rand(15, 80), format="number", trend="down", trend_is_good=True, color="#ef4444"),
        ],
        DiseaseCode.CANCER: [
            KPIItem(label="Pacientes em Acompanhamento", value=_rand(400, 1500), previous_value=_rand(380, 1400), format="number", trend="up", trend_is_good=False),
            KPIItem(label="Diagnóstico Precoce", value=_randf(30, 55), previous_value=_randf(28, 50), unit="%", format="percent", trend="up", trend_is_good=True),
            KPIItem(label="Em Remissão", value=_rand(100, 400), previous_value=_rand(90, 380), format="number", trend="up", trend_is_good=True),
            KPIItem(label="Rastreamentos/mês", value=_rand(200, 800), format="number", trend="up", trend_is_good=True),
            KPIItem(label="Perda de Seguimento", value=_rand(20, 80), previous_value=_rand(25, 90), format="number", trend="down", trend_is_good=True, color="#f59e0b"),
            KPIItem(label="Alertas Ativos", value=_rand(5, 30), format="number", trend="down", trend_is_good=True, color="#ef4444"),
        ],
    }
    return base[disease]


def _generate_trends(disease: DiseaseCode, months: int = 6) -> list[TrendSeries]:
    colors = {
        DiseaseCode.DRC: ["#8b5cf6", "#06b6d4", "#f97316"],
        DiseaseCode.DIABETES: ["#f59e0b", "#06b6d4", "#f97316"],
        DiseaseCode.HIPERTENSAO: ["#ef4444", "#06b6d4", "#f97316"],
        DiseaseCode.CANCER: ["#ec4899", "#06b6d4", "#f97316"],
    }
    labels = {
        DiseaseCode.DRC: ["Taxa de Controle (%)", "TFG Média (ml/min)", "Pacientes em Diálise"],
        DiseaseCode.DIABETES: ["HbA1c < 7% (%)", "HbA1c Média (%)", "Com Complicações"],
        DiseaseCode.HIPERTENSAO: ["PA Controlada (%)", "PAS Média (mmHg)", "Crises Hipertensivas"],
        DiseaseCode.CANCER: ["Diagnóstico Precoce (%)", "Em Remissão", "Rastreamentos/mês"],
    }
    series_list = []
    for idx, label in enumerate(labels[disease]):
        data = []
        for i in range(months):
            d = date.today() - timedelta(days=(months - 1 - i) * 30)
            data.append(TrendPoint(
                date=d.isoformat(),
                value=_randf(30, 80),
                target=70.0 if idx == 0 else None,
            ))
        series_list.append(TrendSeries(
            id=f"trend-{idx}",
            label=label,
            color=colors[disease][idx],
            data=data,
        ))
    return series_list


def _generate_stages(disease: DiseaseCode) -> list[StageDistItem]:
    stages = DISEASE_STAGES.get(disease, [])
    stage_colors = ["#22c55e", "#84cc16", "#f59e0b", "#f97316", "#ef4444", "#dc2626"]
    total = _rand(1000, 5000)
    remaining = total
    items = []
    for idx, stage in enumerate(stages):
        is_last = idx == len(stages) - 1
        count = remaining if is_last else _rand(max(1, remaining // 6), max(2, remaining // 2))
        remaining -= count
        items.append(StageDistItem(
            stage=stage["id"],
            label=stage["label"],
            count=count,
            percentage=round((count / total) * 100, 1) if total > 0 else 0,
            color=stage_colors[idx % len(stage_colors)],
        ))
    return items


def _generate_geo() -> list[GeoRegionItem]:
    return [
        GeoRegionItem(
            id=r["id"], name=r["name"], lat=r["lat"], lng=r["lng"],
            patient_count=_rand(50, 800),
            control_rate=_randf(35, 75),
            alert_count=_rand(0, 20),
        )
        for r in REGIONS
    ]


def _generate_patients(disease: DiseaseCode, count: int = 20) -> list[PatientItem]:
    stages = [s["id"] for s in DISEASE_STAGES.get(disease, [])] or ["unknown"]
    statuses = ["controlled", "attention", "critical", "lost"]
    patients = []
    for i in range(count):
        patients.append(PatientItem(
            id=f"PAT-{i+1:05d}",
            name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            cpf=str(_rand(10000000000, 99999999999)),
            age=_rand(35, 85),
            gender=random.choice(["M", "F"]),
            disease=disease.value,
            stage=random.choice(stages),
            last_visit=(date.today() - timedelta(days=_rand(1, 90))).isoformat(),
            next_visit=(date.today() + timedelta(days=_rand(1, 60))).isoformat() if random.random() > 0.3 else None,
            status=random.choice(statuses),
            establishment=random.choice(ESTABLISHMENTS),
            indicators=[
                PatientIndicatorItem(
                    name="Creatinina", value=_randf(0.6, 8.0), unit="mg/dL",
                    reference="0.6-1.2", status=random.choice(["normal", "elevated", "critical"]),
                ),
            ],
        ))
    return patients


def _period_to_months(period: str) -> int:
    mapping = {"30d": 4, "90d": 6, "6m": 6, "1y": 12, "all": 24}
    return mapping.get(period, 6)


# ─── Endpoints ───────────────────────────────────────────────

@router.get(
    "/dashboard/disease/{disease_code}",
    response_model=DiseaseDashboardResponse,
    summary="Get disease-specific dashboard",
    description="Returns full dashboard with KPIs, trends, stage distribution, geo data, and patients for a specific disease program.",
)
async def get_disease_dashboard(
    disease_code: DiseaseCode,
    period: str = Query("90d", description="Time period: 30d, 90d, 6m, 1y, all"),
    establishment: Optional[str] = Query(None, description="Filter by establishment"),
    region: Optional[str] = Query(None, description="Filter by geographic region"),
    stage: Optional[str] = Query(None, description="Filter by disease stage"),
    status: Optional[str] = Query(None, description="Filter by patient status"),
    search: Optional[str] = Query(None, description="Search by name or CPF"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Full disease dashboard — mock data for now, will integrate with real DB."""
    logger.info(f"Disease dashboard requested: {disease_code.value}, period={period}")
    months = _period_to_months(period)
    total_patients = _rand(500, 5000)
    total_pages = max(1, total_patients // page_size)

    return DiseaseDashboardResponse(
        disease=disease_code.value,
        period=period,
        kpis=_generate_kpis(disease_code),
        trends=_generate_trends(disease_code, months),
        stageDistribution=_generate_stages(disease_code),
        geoData=_generate_geo(),
        patients=_generate_patients(disease_code, min(page_size, 20)),
        totalPatients=total_patients,
        totalPages=total_pages,
    )


@router.get(
    "/dashboard/disease/{disease_code}/kpis",
    response_model=list[KPIItem],
    summary="Get disease KPIs only",
)
async def get_disease_kpis(
    disease_code: DiseaseCode,
    period: str = Query("90d"),
):
    return _generate_kpis(disease_code)


@router.get(
    "/dashboard/disease/{disease_code}/trends",
    response_model=list[TrendSeries],
    summary="Get disease trend data",
)
async def get_disease_trends(
    disease_code: DiseaseCode,
    period: str = Query("90d"),
):
    return _generate_trends(disease_code, _period_to_months(period))


@router.get(
    "/dashboard/disease/{disease_code}/stages",
    response_model=list[StageDistItem],
    summary="Get disease stage distribution",
)
async def get_disease_stages(disease_code: DiseaseCode):
    return _generate_stages(disease_code)


@router.get(
    "/dashboard/disease/{disease_code}/geo",
    response_model=list[GeoRegionItem],
    summary="Get geographic distribution",
)
async def get_disease_geo(disease_code: DiseaseCode):
    return _generate_geo()


@router.get(
    "/dashboard/disease/{disease_code}/patients",
    summary="Get patient list for disease",
)
async def get_disease_patients(
    disease_code: DiseaseCode,
    stage: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    patients = _generate_patients(disease_code, page_size)
    total = _rand(500, 5000)
    return {
        "patients": [p.model_dump() for p in patients],
        "total_patients": total,
        "total_pages": max(1, total // page_size),
        "page": page,
    }
