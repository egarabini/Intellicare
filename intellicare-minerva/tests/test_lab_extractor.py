from __future__ import annotations

from minerva.engine.lab_extractor import LabResultExtractor, LabReport


# ── Fixtures de texto ───────────────────────────────────────────────────────

HEMOGRAMA_COMPLETO = """
HEMOGRAMA COMPLETO
Hemoglobina: 12.5 g/dL  (Referencia: 12.0-16.0)
Hematocrito: 38%         (Referencia: 36-46%)
Leucocitos: 8.500/mm3    (Referencia: 4.000-11.000)
Plaquetas: 250.000/mm3   (Referencia: 150.000-400.000)
"""

BIOQUIMICA = """
BIOQUIMICA
Creatinina: 1.2 mg/dL    (Referencia: 0.6-1.1)
Ureia: 45 mg/dL           (Referencia: 15-45)
Glicemia: 95 mg/dL        (Referencia: 70-99)
Potássio: 4.2 mEq/L      (Referencia: 3.5-5.5)
Sódio: 140 mEq/L          (Referencia: 135-145)
"""

VALORES_CRITICOS = """
Hemoglobina: 5.2 g/dL
Potássio: 7.1 mEq/L
Creatinina: 12.5 mg/dL
Glicemia: 650 mg/dL
"""

PERFIL_LIPIDICO = """
Colesterol Total: 245 mg/dL
HDL: 38 mg/dL
LDL: 165 mg/dL
Triglicérides: 210 mg/dL
"""

PERFIL_HEPATICO = """
TGO: 55 U/L
TGP: 78 U/L
GGT: 120 U/L
Albumina: 3.2 g/dL
Bilirrubina Total: 1.5 mg/dL
"""

PERFIL_TIREOIDIANO = """
TSH: 8.5 mUI/L
T4 Livre: 0.6 ng/dL
"""

TEXTO_SEM_EXAMES = """
Paciente apresentou-se com queixa de cefaleia há 3 dias.
Sem alterações ao exame físico.
"""


# ── Testes de compatibilidade legado (v1.0) ─────────────────────────────────

def test_lab_extractor_maps_known_exams() -> None:
    text = """
    Creatinina: 2,1 mg/dL
    Potassio 5.6 mEq/L
    Ureia 82 mg/dL
    """
    lab_results, unrecognized, confidence = LabResultExtractor().extract(text)
    assert lab_results["creatinine"] == 2.1
    assert lab_results["potassium"] == 5.6
    assert lab_results["urea"] == 82.0
    assert confidence >= 0.6
    assert unrecognized == []


def test_lab_extractor_handles_missing_numeric_value() -> None:
    text = "Creatinina: resultado indisponivel"
    lab_results, unrecognized, confidence = LabResultExtractor().extract(text)
    assert lab_results == {}
    assert len(unrecognized) >= 1
    assert confidence < 0.6


# ── Testes detalhados (v2.0) ────────────────────────────────────────────────

def test_extract_detailed_hemograma() -> None:
    report = LabResultExtractor().extract_detailed(HEMOGRAMA_COMPLETO)
    assert isinstance(report, LabReport)
    names = {r.canonical_name for r in report.results}
    assert "hemoglobin" in names
    assert "hematocrit" in names
    assert report.confidence >= 0.9
    assert report.critical_count == 0


def test_extract_detailed_bioquimica() -> None:
    report = LabResultExtractor().extract_detailed(BIOQUIMICA)
    names = {r.canonical_name for r in report.results}
    assert "creatinine" in names
    assert "glucose" in names
    assert "potassium" in names
    assert "sodium" in names
    # Creatinina 1.2 com ref 0.6-1.1 → alto
    creat = next(r for r in report.results if r.canonical_name == "creatinine")
    assert creat.value == 1.2
    assert creat.status == "alto"
    assert not creat.is_critical


def test_detect_critical_values() -> None:
    report = LabResultExtractor().extract_detailed(VALORES_CRITICOS)
    assert report.critical_count >= 3
    # Hemoglobina 5.2 < 7.0 → crítico
    hb = next(r for r in report.results if r.canonical_name == "hemoglobin")
    assert hb.is_critical
    assert hb.status == "critico"
    # Potássio 7.1 > 6.5 → crítico
    k = next(r for r in report.results if r.canonical_name == "potassium")
    assert k.is_critical
    # Creatinina 12.5 > 10.0 → crítico
    creat = next(r for r in report.results if r.canonical_name == "creatinine")
    assert creat.is_critical
    # Glicemia 650 > 500 → crítico
    glic = next(r for r in report.results if r.canonical_name == "glucose")
    assert glic.is_critical


def test_lipid_panel() -> None:
    report = LabResultExtractor().extract_detailed(PERFIL_LIPIDICO)
    names = {r.canonical_name for r in report.results}
    assert "total_cholesterol" in names
    assert "hdl" in names
    assert "ldl" in names
    assert "triglycerides" in names
    # Colesterol 245 > 200 → alto
    col = next(r for r in report.results if r.canonical_name == "total_cholesterol")
    assert col.status == "alto"
    # HDL 38 < 40 → baixo
    hdl = next(r for r in report.results if r.canonical_name == "hdl")
    assert hdl.status == "baixo"


def test_hepatic_panel() -> None:
    report = LabResultExtractor().extract_detailed(PERFIL_HEPATICO)
    names = {r.canonical_name for r in report.results}
    assert "ast" in names
    assert "alt" in names
    assert "ggt" in names
    assert "albumin" in names
    # TGO 55 > 40 → alto
    ast = next(r for r in report.results if r.canonical_name == "ast")
    assert ast.status == "alto"


def test_thyroid_panel() -> None:
    report = LabResultExtractor().extract_detailed(PERFIL_TIREOIDIANO)
    names = {r.canonical_name for r in report.results}
    assert "tsh" in names
    assert "free_t4" in names
    # TSH 8.5 > 4.0 → alto
    tsh = next(r for r in report.results if r.canonical_name == "tsh")
    assert tsh.status == "alto"
    # T4L 0.6 < 0.8 → baixo
    t4 = next(r for r in report.results if r.canonical_name == "free_t4")
    assert t4.status == "baixo"


def test_empty_text_returns_low_confidence() -> None:
    report = LabResultExtractor().extract_detailed(TEXTO_SEM_EXAMES)
    assert len(report.results) == 0
    assert report.confidence < 0.6


def test_report_to_dict() -> None:
    report = LabResultExtractor().extract_detailed(BIOQUIMICA)
    d = report.to_dict()
    assert "results" in d
    assert "critical_count" in d
    assert "total_results" in d
    assert d["total_results"] == len(report.results)
    # Each result should have the expected keys
    for r in d["results"]:
        assert "exam_name" in r
        assert "canonical_name" in r
        assert "value" in r
        assert "status" in r
        assert "is_critical" in r


def test_normal_values_status() -> None:
    text = """
    Glicemia: 85 mg/dL
    Sódio: 140 mEq/L
    Potássio: 4.0 mEq/L
    """
    report = LabResultExtractor().extract_detailed(text)
    for r in report.results:
        assert r.status == "normal"
        assert not r.is_critical
    assert report.critical_count == 0

