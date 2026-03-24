"""Testes unitarios do modulo Cuidado."""
from __future__ import annotations

import pytest
from datetime import date, datetime
from uuid import uuid4

from modules.cuidado.schemas import (
    ClinicalAskRequest,
    EncounterCreate,
    EncounterResponse,
    NoteCreate,
    NoteResponse,
    PatientCreate,
    PatientResponse,
)


# ------------------------------------------------------------------
# PatientCreate validation
# ------------------------------------------------------------------

def test_patient_create_minimal():
    p = PatientCreate(full_name="João Silva")
    assert p.full_name == "João Silva"
    assert p.cpf is None
    assert p.sex is None


def test_patient_create_full():
    p = PatientCreate(
        full_name="Maria Oliveira",
        cpf="12345678901",
        birth_date=date(1990, 5, 15),
        sex="F",
        phone="11999999999",
        email="maria@email.com",
        address="Rua A, 123",
    )
    assert p.sex == "F"
    assert p.birth_date == date(1990, 5, 15)
    assert p.email == "maria@email.com"


def test_patient_create_sex_literal():
    for s in ("M", "F", "O"):
        p = PatientCreate(full_name="Test", sex=s)
        assert p.sex == s


def test_patient_create_invalid_sex():
    with pytest.raises(ValueError):
        PatientCreate(full_name="Test", sex="X")


# ------------------------------------------------------------------
# PatientResponse
# ------------------------------------------------------------------

def test_patient_response():
    uid = uuid4()
    r = PatientResponse(
        id=uid, name="Ana", active=True,
        created_at=datetime(2026, 1, 1, 12, 0, 0),
    )
    assert r.id == uid
    assert r.active is True


# ------------------------------------------------------------------
# EncounterCreate
# ------------------------------------------------------------------

def test_encounter_create_defaults():
    pid = uuid4()
    e = EncounterCreate(patient_id=pid)
    assert e.priority == "normal"
    assert e.chief_complaint is None


def test_encounter_create_custom():
    pid = uuid4()
    e = EncounterCreate(patient_id=pid, chief_complaint="Cefaleia intensa", priority="urgent")
    assert e.priority == "urgent"
    assert e.chief_complaint == "Cefaleia intensa"


def test_encounter_create_invalid_priority():
    with pytest.raises(ValueError):
        EncounterCreate(patient_id=uuid4(), priority="critical")


# ------------------------------------------------------------------
# EncounterResponse
# ------------------------------------------------------------------

def test_encounter_response():
    uid = uuid4()
    r = EncounterResponse(
        id=uid, patient_id=uuid4(), clinician_id="user-1",
        status="open", chief_complaint="Dor", priority="normal",
        opened_at=datetime.now(), closed_at=None,
    )
    assert r.status == "open"
    assert r.closed_at is None


# ------------------------------------------------------------------
# NoteCreate / NoteResponse
# ------------------------------------------------------------------

def test_note_create_defaults():
    n = NoteCreate()
    assert n.subjective is None
    assert n.objective is None
    assert n.assessment is None
    assert n.plan is None


def test_note_create_soap():
    n = NoteCreate(
        subjective="Paciente relata dor de cabeça há 2 dias",
        objective="PA 140/90, FC 80",
        assessment="Cefaleia tensional",
        plan="Paracetamol 750mg 6/6h",
    )
    assert "dor de cabeça" in n.subjective
    assert "140/90" in n.objective


def test_note_response():
    r = NoteResponse(
        id=1, encounter_id=uuid4(), clinician_id="doc-1",
        created_at=datetime.now(),
        subjective="Queixa", objective="Exame",
        assessment="Hipótese", plan="Conduta",
    )
    assert r.id == 1
    assert r.plan == "Conduta"


# ------------------------------------------------------------------
# ClinicalAskRequest
# ------------------------------------------------------------------

def test_clinical_ask_defaults():
    r = ClinicalAskRequest(query="Protocolo hipertensão")
    assert r.limit == 5
    assert r.min_similarity == 0.5


def test_clinical_ask_custom():
    r = ClinicalAskRequest(query="Manejo diabetes", limit=10, min_similarity=0.7)
    assert r.limit == 10
    assert r.min_similarity == 0.7

