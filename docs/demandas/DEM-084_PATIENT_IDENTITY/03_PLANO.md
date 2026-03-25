---
tipo: plano-execucao
demanda: DEM-084
titulo: Patient Identity Integration
status: planejada
dev: DEV-2
sprint: 2026-05-16
criado: 2026-03-23
---

# DEM-084 — Plano de Execução

## Estimativa

Tempo estimado: ~4h | Complexidade: alta

A complexidade está em injetar corretamente dois AsyncSession no mesmo handler sem introduzir regressões nas rotas existentes (timeline, prescrições, notas Florence dependem de `cuidado/patients`).

## Pré-condição

DEM-083 commitada e em `origin/main`. Os módulos `modules/identity/` e `platform.pessoa*` precisam existir antes desta DEM começar.

---

## Ordem de execução

### Bloco 1 — Migration tenant (20min)
1. Criar `db/tenant_migrations/022_paciente_pessoa_id.sql`
2. Verificar que `pessoa_id UUID` não existe ainda em `{schema}.paciente`
3. Testar: `psql ... -c "\d demo.paciente"` → coluna `pessoa_id` presente, nullable

### Bloco 2 — Backend integration (90min)
4. Adaptar `create_patient()` em `cuidado/services.py` (ver `02_TECNICA.md §2`)
5. Adicionar `register_tenant_link()` em `modules/identity/repository.py`
6. Atualizar `cuidado/routes.py`: injetar `platform_db` no endpoint `POST /patients`
7. Adaptar `get_patient()` para merge com dados canônicos (ver `02_TECNICA.md §5`)
8. Atualizar `PatientOut` schema: adicionar campo `pessoa_id` opcional

### Bloco 3 — Portal do Paciente (45min)
9. Adaptar `GET /me/profile` para retornar dados canônicos quando `pessoa_id` disponível
10. Garantir fallback legado funcionando (sem `pessoa_id`)

### Bloco 4 — Testes e regressão (45min)
11. Criar `tests/test_patient_identity.py` com 7 cenários
12. `pytest tests/test_patient_identity.py -v` → 7/7 passed
13. `pytest tests/test_linha_do_tempo.py tests/test_oswaldo_receituario.py tests/test_florence_marie.py -v` → zero regressões nas funcionalidades dependentes de `cuidado/patients`

---

## Gotcha — DEM-083 deve estar em main antes desta DEM

Se DEM-083 ainda não chegou em `origin/main`, fazer `git pull` antes de iniciar. O import de `modules.identity.services` vai falhar sem a DEM-083.

---

## Gotcha — call sites de `create_patient()`

Buscar todos os lugares que chamam `create_patient()` no código e adicionar o parâmetro `platform_db`:
```bash
grep -r "create_patient(" modules/ --include="*.py"
```
Atualizar cada call site com a nova assinatura.

---

## Gotcha — testes mockam `platform_db`

Os testes existentes que testam `POST /cuidado/patients` não injetam `platform_db`. Atualizar os fixtures de teste para mockar `get_platform_db`:
```python
@pytest.fixture
def mock_platform_db(mocker):
    return mocker.AsyncMock()

# No test:
app.dependency_overrides[get_platform_db] = lambda: mock_platform_db
```

---

## Entrega

```
feat(identity): patient identity integration — pessoa_id em paciente, find-or-create CPF, vínculo LGPD
```
Hash → enviar ao ARQUITETO após `git push origin HEAD:main` confirmado.
