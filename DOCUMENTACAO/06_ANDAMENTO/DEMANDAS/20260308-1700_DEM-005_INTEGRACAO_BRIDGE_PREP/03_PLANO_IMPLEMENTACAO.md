# DEM-005 — Portas de Integração HIS: Plano de Implementação

**Demanda:** DEM-005
**Dev:** dev3
**Branch:** `feature/bridge-integration-prep`
**Depende de:** DEM-002 (auth estável — realm `intellicare` funcionando)
**Estimativa:** 5–7 dias úteis

---

## Antes de começar

**Ler obrigatoriamente:**
- `intellicare-core/docs/DEM-005_ESPECIFICACAO_FUNCIONAL.md`
- `intellicare-core/docs/DEM-005_ESPECIFICACAO_TECNICA.md`
- `DOCUMENTACAO/06_ANDAMENTO/DEMANDAS/20260308-1700_DEM-005_INTEGRACAO_BRIDGE_PREP.md`

**Pré-requisitos:**
- DEM-002 concluída (Keycloak com realm `intellicare`, roles `PLATFORM_ADMIN` e `TENANT_GESTOR` criadas)
- `intellicare-grahame` rodando em `http://localhost:8012` com auth funcionando
- `intellicare-wanda` rodando em `http://localhost:8004`
- Redis rodando em `localhost:6379`

**Setup da branch:**
```bash
cd C:\Users\egara\INTELLICARE
git checkout staging
git pull
git checkout -b feature/bridge-integration-prep
```

---

## Sprint 1 — intellicare-core: pacote `bridge` (2 dias)

### Passo 1 — Criar o pacote `bridge` no core

```bash
cd intellicare-core
mkdir intellicare_core/bridge
```

Criar os 4 arquivos conforme `DEM-005_ESPECIFICACAO_TECNICA.md` (seção FASE 1):
- `intellicare_core/bridge/__init__.py`
- `intellicare_core/bridge/context.py`
- `intellicare_core/bridge/adapter.py`
- `intellicare_core/bridge/registry.py`

### Passo 2 — Testes unitários do HISContext

Criar `intellicare-core/tests/test_bridge_context.py`:

```python
import pytest
from intellicare_core.bridge.context import HISContext, HISSystem


def test_his_context_roundtrip():
    """HISContext serializa e desserializa corretamente do header base64."""
    ctx = HISContext(
        his_system=HISSystem.FEEGOW,
        his_patient_id="PAC-001",
        fhir_patient_id="fhir-uuid-001",
        tenant_id="tenant-hospital-abc",
    )
    header_value = ctx.to_header()
    assert isinstance(header_value, str)
    assert len(header_value) > 0

    recovered = HISContext.from_header(header_value)
    assert recovered.his_system == HISSystem.FEEGOW
    assert recovered.his_patient_id == "PAC-001"
    assert recovered.tenant_id == "tenant-hospital-abc"


def test_his_context_invalid_header():
    """from_header com base64 inválido deve lançar exceção."""
    with pytest.raises(Exception):
        HISContext.from_header("not-valid-base64!!!")
```

### Passo 3 — Reinstalar o core em todos os módulos afetados

Após adicionar o pacote `bridge`, reinstalar o core no GRAHAME e WANDA:

```bash
cd intellicare-grahame && pip install -e ../intellicare-core
cd intellicare-wanda   && pip install -e ../intellicare-core
```

### Entrega do Sprint 1

- [ ] `intellicare_core/bridge/__init__.py` criado
- [ ] `intellicare_core/bridge/context.py` criado com `HISContext` e `HISSystem`
- [ ] `intellicare_core/bridge/adapter.py` criado com `BaseHISAdapter`
- [ ] `intellicare_core/bridge/registry.py` criado com `HISAdapterRegistry`
- [ ] `pytest intellicare-core/tests/test_bridge_context.py` — todos passando
- [ ] `from intellicare_core.bridge import HISContext` funciona no Python REPL

---

## Sprint 2 — GRAHAME: endpoint `$process-message` (2 dias)

### Passo 1 — Criar `bridge_routes.py`

Copiar o código da `DEM-005_ESPECIFICACAO_TECNICA.md` (seção FASE 2) para:
```
intellicare-grahame/grahame/api/routes/bridge_routes.py
```

### Passo 2 — Adicionar `require_his_adapter` em `deps.py`

```python
# grahame/api/deps.py — adicionar ao final
from intellicare_auth.fastapi import require_role

async def require_his_adapter(payload: dict = Depends(require_role("HIS_ADAPTER"))) -> dict:
    return payload
```

### Passo 3 — Registrar o router no `app.py`

```python
# grahame/api/app.py — adicionar após outros include_router:
from grahame.api.routes.bridge_routes import router as bridge_router
app.include_router(bridge_router)
```

### Passo 4 — Implementar o corpo do `$process-message`

O código gerado em Sprint 2 tem `TODO` marcado para o upsert FHIR. Verificar como o GRAHAME processa recursos individuais hoje (procurar por `FHIRService` ou equivalente) e reusar a mesma lógica no loop de entries.

### Passo 5 — Implementar publicação no Redis

No `_publish_his_ingestion_event`, usar o cliente Redis existente no GRAHAME:
```python
# Verificar como GRAHAME acessa Redis hoje (app.state.redis, injeção por Depends, etc.)
# e usar o mesmo padrão para publicar no stream intellicare:events:his_ingestion
```

### Passo 6 — Testar `$process-message` com service account bridge-dev

Antes de testar, criar a role e o service account no Keycloak (ver FAQ abaixo).

```bash
# 1. Obter token do service account bridge-dev
TOKEN=$(curl -s -X POST \
  http://localhost:8080/realms/intellicare/protocol/openid-connect/token \
  -d "client_id=intellicare-bridge-dev" \
  -d "client_secret=SEU_SECRET" \
  -d "grant_type=client_credentials" \
  | jq -r .access_token)

# 2. Criar HISContext de teste
HIS_CTX=$(python3 -c "
from intellicare_core.bridge.context import HISContext, HISSystem
ctx = HISContext(his_system=HISSystem.FEEGOW, his_patient_id='P001', tenant_id='test-tenant')
print(ctx.to_header())
")

# 3. Enviar bundle de teste
curl -s -X POST http://localhost:8012/api/v1/fhir/\$process-message \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-HIS-Context: $HIS_CTX" \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Bundle",
    "type": "transaction",
    "entry": [
      {"resource": {"resourceType": "Patient", "id": "fhir-P001", "name": [{"family": "Teste"}]}}
    ]
  }'
# Esperado: 202 com Bundle transaction-response
```

### Entrega do Sprint 2

- [ ] `grahame/api/routes/bridge_routes.py` criado e registrado
- [ ] `require_his_adapter` adicionado em `deps.py`
- [ ] `GET /api/v1/fhir/$process-message` sem token → 403
- [ ] `GET /api/v1/fhir/$process-message` com token `PLATFORM_ADMIN` → 403
- [ ] `POST /api/v1/fhir/$process-message` com token `HIS_ADAPTER` + bundle válido → 202
- [ ] Evento publicado no Redis stream (verificar com `redis-cli XREAD COUNT 1 STREAMS intellicare:events:his_ingestion 0`)

---

## Sprint 3 — WANDA: propagação de HISContext + consumer Redis (1–2 dias)

### Passo 1 — Leitura do header no WANDA

Localizar o ponto de injeção de contexto no WANDA (middleware ou dependência base). Adicionar leitura de `X-HIS-Context` conforme spec técnica (seção FASE 3).

```bash
# Para encontrar onde o WANDA lida com contexto hoje:
grep -r "request.state" intellicare-wanda/wanda/api/
grep -r "TenantContext\|tenant_id" intellicare-wanda/wanda/api/
```

### Passo 2 — Propagação no intent router

Localizar onde o WANDA monta `AnalysisRequest` para enviar aos agentes. Adicionar propagação do `HISContext` conforme spec técnica.

### Passo 3 — Consumer Redis `his_bundle_ingested`

Localizar onde o WANDA registra consumers de Redis Streams (provavelmente no `lifespan` do app.py). Adicionar consumer para `intellicare:events:his_ingestion`.

### Entrega do Sprint 3

- [ ] WANDA lê `X-HIS-Context` e injeta em `request.state.his_context`
- [ ] `AnalysisRequest` com `HISContext` tem `parameters["his_context"]` preenchido
- [ ] Consumer `his_bundle_ingested` registrado e logando evento ao receber
- [ ] Teste end-to-end: POST `$process-message` → evento no Redis → WANDA loga o evento

---

## Sprint 4 — Módulo stub `intellicare-bridge` + Docker (1 dia)

### Passo 1 — Criar estrutura do diretório

```bash
mkdir -p intellicare-bridge/bridge/api
mkdir -p intellicare-bridge/bridge/adapters/feegow
touch intellicare-bridge/bridge/__init__.py
touch intellicare-bridge/bridge/adapters/__init__.py
touch intellicare-bridge/bridge/adapters/feegow/__init__.py
```

### Passo 2 — Criar os arquivos do stub

Copiar da spec técnica (seção FASE 5):
- `intellicare-bridge/bridge/api/app.py`
- `intellicare-bridge/bridge/adapters/base.py`
- `intellicare-bridge/bridge/config.py` (vazio por ora — apenas `GRAHAME_BASE_URL` e `WANDA_BASE_URL`)
- `intellicare-bridge/pyproject.toml`
- `intellicare-bridge/Dockerfile`

### Passo 3 — Testar o stub localmente

```bash
cd intellicare-bridge
pip install -e ../intellicare-core -e ../intellicare-auth -e .
uvicorn bridge.api.app:app --reload --port 8014
```

Verificar:
```bash
curl http://localhost:8014/api/v1/health
# Esperado: {"status": "healthy", "module": "intellicare-bridge", "details": {"mode": "stub", ...}}
curl http://localhost:8014/api/v1/bridge/adapters
# Esperado: {"registered": [], "planned": ["feegow", "philips_tasy", ...]}
```

### Passo 4 — Adicionar ao docker-compose.full.yml

Copiar o bloco `intellicare-bridge` da spec técnica (seção FASE 5 — docker-compose).

### Passo 5 — Adicionar ao smoke_test.sh

```bash
# Em scripts/smoke_test.sh, adicionar:
check_health "intellicare-bridge" "http://localhost:8014/api/v1/health"
```

### Entrega do Sprint 4

- [ ] `intellicare-bridge/` criado com estrutura completa
- [ ] `uvicorn bridge.api.app:app --port 8014` sobe sem erro
- [ ] `GET /api/v1/health` → 200 com `"mode": "stub"`
- [ ] `GET /api/v1/bridge/adapters` → 200 com `"registered": []`
- [ ] Serviço adicionado ao `docker-compose.full.yml`
- [ ] Adicionado ao `scripts/smoke_test.sh`

---

## Sprint 5 — Keycloak: role HIS_ADAPTER + service account (0.5 dia)

Executar no Keycloak Admin Console em `http://localhost:8080` (ou `auth.intellicare.ia.br` se disponível):

1. **Criar role realm:**
   - `Realm Settings > Roles > Add Role`
   - Name: `HIS_ADAPTER`
   - Description: `Permite ingerir FHIR Bundles via bridge`

2. **Criar client service account:**
   - `Clients > Create`
   - Client ID: `intellicare-bridge-dev`
   - Access Type: `confidential`
   - Standard Flow: OFF
   - Service Accounts Enabled: ON
   - Salvar → aba `Credentials` → copiar secret

3. **Atribuir role ao service account:**
   - `Clients > intellicare-bridge-dev > Service Account Roles`
   - Adicionar `HIS_ADAPTER`

4. **Salvar secret:**
   ```bash
   # Criar arquivo (não commitar — adicionar ao .gitignore se não estiver)
   cat > intellicare-bridge/keycloak_client_secrets.json << 'EOF'
   {
     "client_id": "intellicare-bridge-dev",
     "client_secret": "SEU_SECRET_AQUI",
     "realm": "intellicare",
     "auth_server_url": "http://localhost:8080"
   }
   EOF
   ```

### Entrega do Sprint 5

- [ ] Role `HIS_ADAPTER` criada no realm `intellicare`
- [ ] Client `intellicare-bridge-dev` criado com service account
- [ ] Service account tem role `HIS_ADAPTER`
- [ ] Token obtido com sucesso:
  ```bash
  curl -s -X POST http://localhost:8080/realms/intellicare/protocol/openid-connect/token \
    -d "client_id=intellicare-bridge-dev" \
    -d "client_secret=SEU_SECRET" \
    -d "grant_type=client_credentials" | jq .access_token
  # Deve retornar string de token (não null)
  ```
- [ ] `keycloak_client_secrets.json` salvo em `intellicare-bridge/`

---

## FAQ

**P: Devo criar os adaptadores Feegow, Tasy, etc. nesta demanda?**
R: Não. Esta demanda cria apenas o esqueleto. O diretório `bridge/adapters/feegow/` fica com `__init__.py` vazio. Os adaptadores reais são demanda futura.

**P: Em qual ordem criar os arquivos?**
R: Sprint 1 → Sprint 5 → Sprint 2 → Sprint 3 → Sprint 4. O core precisa existir antes do GRAHAME e do WANDA, e o Keycloak precisa ter a role antes de testar o endpoint.

**P: E se o WANDA não tiver middleware de contexto ainda?**
R: Procurar por `TenantResolver` ou `init_tenant_resolver()` — esses já injetam contexto. Adicionar a leitura do `X-HIS-Context` no mesmo ponto. Se não existir middleware, criar um simples que só lê o header e injeta em `request.state`.

**P: O `$process-message` deve processar TODOS os tipos de recurso FHIR?**
R: Não. Processar com lógica real apenas: `Patient`, `Observation`, `Condition`, `MedicationRequest`. Para outros tipos, aceitar (retornar 202), guardar o recurso raw se possível, e logar. Nunca retornar 400 por tipo desconhecido — o bundle pode conter recursos que ainda não processamos.

**P: O HISContext precisa ser válido para o $process-message aceitar?**
R: Não. O header `X-HIS-Context` é opcional. Se vier malformado, ignorar e continuar sem contexto (não retornar erro). O que é obrigatório é o token com role `HIS_ADAPTER`.

**P: Qual Redis usar no GRAHAME?**
R: Verificar como o GRAHAME acessa Redis hoje (provavelmente `app.state.redis` ou injeção via `Depends`). Usar exatamente o mesmo padrão — não criar uma segunda conexão Redis.

**P: `intellicare-bridge` precisa de banco de dados?**
R: Não no stub. Quando adaptadores reais forem implementados, o bridge provavelmente usará o GRAHAME como seu storage FHIR (via API) — não terá banco próprio.

---

## Checklist de entrega final

### intellicare-core
- [ ] `intellicare_core/bridge/__init__.py` ✓
- [ ] `intellicare_core/bridge/context.py` ✓
- [ ] `intellicare_core/bridge/adapter.py` ✓
- [ ] `intellicare_core/bridge/registry.py` ✓
- [ ] `pytest tests/test_bridge_context.py` — verde

### intellicare-grahame
- [ ] `grahame/api/routes/bridge_routes.py` ✓
- [ ] `require_his_adapter` em `deps.py` ✓
- [ ] Router registrado em `app.py` ✓
- [ ] `POST /fhir/$process-message` com token HIS_ADAPTER → 202 ✓
- [ ] Evento publicado no Redis Stream ✓

### intellicare-wanda
- [ ] Leitura de `X-HIS-Context` injetando em `request.state` ✓
- [ ] Propagação em `AnalysisRequest.parameters` ✓
- [ ] Consumer Redis `his_bundle_ingested` registrado ✓

### intellicare-auth (Keycloak)
- [ ] Role `HIS_ADAPTER` criada ✓
- [ ] Client `intellicare-bridge-dev` criado com service account + role ✓
- [ ] Token obtido com sucesso ✓

### intellicare-bridge (stub)
- [ ] Estrutura de diretórios criada ✓
- [ ] `bridge/api/app.py` stub funcional ✓
- [ ] `/api/v1/health` → 200 ✓
- [ ] `/api/v1/bridge/adapters` → 200 ✓
- [ ] Adicionado ao `docker-compose.full.yml` ✓
- [ ] Adicionado ao `scripts/smoke_test.sh` ✓

### Qualidade
- [ ] `make lint` passando em intellicare-core (novos arquivos)
- [ ] `make typecheck` passando em intellicare-core
- [ ] `make lint` passando em intellicare-grahame
- [ ] `make lint` passando em intellicare-wanda

---

## Ao terminar

1. **Preencher o log de execução** no ANDAMENTO_DEMANDA:
   `DOCUMENTACAO/06_ANDAMENTO/DEMANDAS/20260308-1700_DEM-005_INTEGRACAO_BRIDGE_PREP.md`
   — uma entrada por sprint concluído, com data/hora e o que foi feito

2. **Avisar Eduardo** que a implementação está completa e aguarda revisão

3. **Não abrir PR** — Claude abrirá o PR após revisão com Eduardo

4. **Se encontrar algo errado ou conflitante na spec**, parar, documentar a dúvida e avisar Eduardo antes de prosseguir
