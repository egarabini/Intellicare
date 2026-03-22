import pytest
from modules.oswaldo.interactions import check_interactions, _load_db

@pytest.fixture(autouse=True)
def ensure_db_loaded():
    # Garante que o DB foi carregado se estiver vazio no contexto de testes
    _load_db()

async def test_grave_interaction_detected():
    warnings, count = await check_interactions(["varfarina", "AAS"])
    assert count == 1
    assert len(warnings) == 1
    w = warnings[0]
    assert w.severity == "GRAVE"
    assert "varfarina" in [w.drug_a.lower(), w.drug_b.lower()]
    assert "aas" in [w.drug_a.lower(), w.drug_b.lower()]
    assert w.source == "static"

async def test_moderate_interaction_detected():
    warnings, count = await check_interactions(["ESPIRONOLACTONA", "Enalapril"])
    assert count == 1
    assert len(warnings) == 1
    w = warnings[0]
    assert w.severity == "MODERADO"
    assert w.source == "static"

async def test_no_interaction():
    warnings, count = await check_interactions(["atenolol", "amoxicilina"])
    assert count == 1
    # Lista pode estar vazia ou a IA mockada pode dar exception local
    assert len(warnings) == 0

async def test_case_insensitive_matching():
    warnings1, count1 = await check_interactions(["VARFARINA", "AAS"])
    warnings2, count2 = await check_interactions(["varfarina", "aas"])
    assert len(warnings1) == 1
    assert len(warnings2) == 1
    assert warnings1[0].severity == "GRAVE"
    assert warnings2[0].severity == "GRAVE"

async def test_multiple_pairs():
    warnings, count = await check_interactions(["varfarina", "AAS", "amiodarona"])
    assert count == 3
    assert len(warnings) >= 2
    gravs = [w for w in warnings if w.severity == "GRAVE" and w.source == "static"]
    assert len(gravs) == 2
