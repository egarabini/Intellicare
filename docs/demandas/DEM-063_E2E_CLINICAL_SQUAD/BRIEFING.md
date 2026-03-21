# DEM-063 — E2E Clinical Squad (Florence + Oswaldo + Portal)

> **Dev:** CODEX
> **Estimativa:** ~3h
> **Dependência:** DEM-055, DEM-057, DEM-058, DEM-059, DEM-062

---

## Contexto

As DEMs 055–062 entregaram o Clinical Squad completo: Florence notas + IA,
Oswaldo prescrições + IA, Portal do paciente e PDF clínico. Esta DEM fecha
o ciclo com cobertura de testes E2E — Playwright para os fluxos do clínico e
do paciente, e pytest de integração para os endpoints críticos.

Seguir o padrão estabelecido em DEM-050 (E2E multi-canal) e DEM-036 (E2E atualizado).

---

## Fase A — Pytest de integração

### STEP-001 — `test_florence_e2e.py`

```python
async def test_create_and_retrieve_soap_note(async_client_clinico):
    """Fluxo completo: criar nota SOAP → buscar por encontro → verificar campos."""
    # Criar nota SOAP
    create = await async_client_clinico.post("/florence/notes", json={
        "encounter_id": 1, "patient_id": 1, "note_type": "SOAP",
        "soap_s": "Dor abdominal", "soap_o": "Abdome tenso",
        "soap_a": "Gastrite aguda provável", "soap_p": "Omeprazol 20mg 1x/dia",
    })
    assert create.status_code == 200
    note_id = create.json()["id"]

    # Buscar por encontro
    listing = await async_client_clinico.get("/florence/notes/encounter/1")
    assert any(n["id"] == note_id for n in listing.json())

async def test_florence_suggest_fills_fields(async_client_clinico, monkeypatch):
    """Sugestão rule-based retorna os 4 campos SOAP."""
    monkeypatch.delenv("FLORENCE_LLM_URL", raising=False)
    resp = await async_client_clinico.post("/florence/notes/suggest", json={
        "encounter_id": 1, "patient_id": 1, "chief_complaint": "Febre há 2 dias",
    })
    assert resp.status_code == 200
    data = resp.json()
    for field in ("soap_s", "soap_o", "soap_a", "soap_p"):
        assert field in data
```

### STEP-002 — `test_oswaldo_e2e.py`

```python
async def test_cid10_search_returns_results(async_client_clinico):
    resp = await async_client_clinico.get("/oswaldo/cid10/search?q=gastrite")
    assert resp.status_code == 200
    # Lista pode estar vazia se seed não tiver CID-10 — aceitar ambos
    assert isinstance(resp.json(), list)

async def test_create_and_list_prescription(async_client_clinico):
    create = await async_client_clinico.post("/oswaldo/prescriptions", json={
        "encounter_id": 1, "patient_id": 1,
        "cid10_code": "K21", "cid10_desc": "Doença do refluxo",
        "items": [{"drug": "Omeprazol 20mg", "posology": "1 cp em jejum", "duration": "30 dias"}],
    })
    assert create.status_code == 200

    listing = await async_client_clinico.get("/oswaldo/prescriptions/encounter/1")
    assert len(listing.json()) >= 1

async def test_oswaldo_suggest_rule_based(async_client_clinico, monkeypatch):
    monkeypatch.delenv("FLORENCE_LLM_URL", raising=False)
    resp = await async_client_clinico.post("/oswaldo/suggest", json={
        "encounter_id": 1, "patient_id": 1, "chief_complaint": "Dor de garganta",
    })
    assert resp.status_code == 200
    assert resp.json()["model"] == "rule-based"
```

### STEP-003 — `test_portal_clinical_e2e.py`

```python
async def test_patient_sees_journeys(async_client_paciente, seed_journey):
    resp = await async_client_paciente.get("/cuidado/paciente/me/journeys")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

async def test_patient_notes_no_soap_a(async_client_paciente, seed_soap_note):
    resp = await async_client_paciente.get("/cuidado/paciente/me/clinical-notes")
    assert resp.status_code == 200
    for note in resp.json():
        assert "soap_a" not in note
        assert "Avaliação" not in note.get("summary", "")

async def test_clinical_role_cannot_access_patient_portal(async_client_clinico):
    resp = await async_client_clinico.get("/cuidado/paciente/me/journeys")
    assert resp.status_code == 403
```

---

## Fase B — Playwright E2E

### STEP-004 — `clinico_florence.spec.ts`

```typescript
test('Clínico cria nota SOAP no EncounterView', async ({ page }) => {
  await loginAs(page, 'dr.silva', 'Demo@1234')
  await page.goto('/clinico-ui/agenda')
  await page.click('[data-testid="btn-open-encounter"]')
  await page.click('[data-testid="tab-florence"]')

  // Selecionar modo SOAP
  await page.click('button:has-text("SOAP")')
  await page.fill('[data-testid="florence-soap-s"]', 'Dor de cabeça há 3 dias')
  await page.fill('[data-testid="florence-soap-p"]', 'Analgésico + repouso')
  await page.click('button:has-text("Salvar nota")')

  await expect(page.locator('[data-testid="florence-note-list"]')).toContainText('Dor de cabeça')
})

test('Botão Sugerir SOAP com IA preenche campos', async ({ page }) => {
  await loginAs(page, 'dr.silva', 'Demo@1234')
  // navegar até EncounterView → aba Florence → modo SOAP
  await page.fill('[data-testid="florence-chief-complaint"]', 'Febre e tosse')
  await page.click('button:has-text("Sugerir SOAP com IA")')
  // aguarda preenchimento (rule-based é síncrono no staging sem LLM)
  await expect(page.locator('[data-testid="florence-soap-s"]')).not.toBeEmpty()
})
```

### STEP-005 — `clinico_oswaldo.spec.ts`

```typescript
test('Clínico cria prescrição com CID-10 no EncounterView', async ({ page }) => {
  await loginAs(page, 'dr.silva', 'Demo@1234')
  // navegar até EncounterView → aba Prescrição
  await page.click('[data-testid="tab-oswaldo"]')
  await page.fill('[data-testid="oswaldo-cid10-search"]', 'gastrite')
  await page.click('[data-testid="oswaldo-cid10-option"]:first-child')
  await page.fill('[data-testid="oswaldo-drug-0"]', 'Omeprazol 20mg')
  await page.fill('[data-testid="oswaldo-posology-0"]', '1 cp em jejum')
  await page.click('button:has-text("Salvar prescrição")')
  await expect(page.locator('[data-testid="oswaldo-prescription-list"]')).toContainText('Omeprazol')
})
```

### STEP-006 — `paciente_portal_clinical.spec.ts`

```typescript
test('Paciente vê jornadas no portal', async ({ page }) => {
  await loginAs(page, 'paciente.alfa', 'Demo@1234')
  await page.goto('/paciente-ui/jornadas')
  await expect(page.locator('h1')).toContainText('Minhas Jornadas')
  // Pode estar vazia em staging — verificar que a página carrega sem erro
  await expect(page.locator('[data-testid="page-error"]')).not.toBeVisible()
})

test('Paciente vê histórico clínico sem soap_a', async ({ page }) => {
  await loginAs(page, 'paciente.alfa', 'Demo@1234')
  await page.goto('/paciente-ui/historico')
  await expect(page.locator('body')).not.toContainText('Avaliação')
  await expect(page.locator('body')).not.toContainText('soap_a')
})
```

---

## Critérios de Aceite

- [ ] `test_florence_e2e.py` — 2 testes passando
- [ ] `test_oswaldo_e2e.py` — 3 testes passando
- [ ] `test_portal_clinical_e2e.py` — 3 testes passando
- [ ] `clinico_florence.spec.ts` — 2 testes Playwright passando
- [ ] `clinico_oswaldo.spec.ts` — 1 teste Playwright passando
- [ ] `paciente_portal_clinical.spec.ts` — 2 testes Playwright passando
- [ ] Nenhuma regressão nos testes anteriores (contagem total não cai)
