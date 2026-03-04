# ZILDA — Plano de Implementacao
**Data:** 2026-03-04
**Versao:** 1.0.0
**Estimativa Total:** 1-2 dias
**Prioridade:** ONDA 1 — Quick Win

---

## Status Atual

O ZILDA ja tem estrutura base implementada (health, info, unit-types, consultas basicas).
O objetivo desta versao e **fechar os gaps** para entrega standalone e adicionar
integracao com fonte de dados real (DATASUS API publica).

---

## Fase 1 — Hardening (Dia 1, manha) — ~3h

### Tarefa 1.1 — Verificar e corrigir testes existentes
```bash
cd intellicare-zilda
pip install -e ".[dev]"
pytest tests/ -v --tb=short
```
- [ ] Identificar testes falhando
- [ ] Corrigir fixtures e imports quebrados
- [ ] Meta: `pytest -q` com 0 falhas

### Tarefa 1.2 — Validar health check e info
```bash
uvicorn zilda.api.app:app --port 8007
curl http://localhost:8007/api/v1/health
curl http://localhost:8007/api/v1/info
```
- [ ] Health retorna `{"status": "healthy"}`
- [ ] Info retorna `{"module": "zilda", "version": "..."}`

### Tarefa 1.3 — Testar endpoints CNES existentes
```bash
curl "http://localhost:8007/api/v1/unit-types"
curl "http://localhost:8007/api/v1/cnes/2077485"
```
- [ ] unit-types retorna lista valida
- [ ] Busca por CNES retorna dados ou 404 claro

---

## Fase 2 — Integracao DATASUS (Dia 1, tarde) — ~4h

### Tarefa 2.1 — Implementar datasus_client.py
```python
# zilda/services/datasus_client.py
class DATASUSClient:
    def __init__(self, base_url: str, redis_client, http_timeout: int = 30):
        ...

    async def get_establishment(self, cnes: str) -> dict | None:
        # 1. Checar cache Redis (key: "zilda:cnes:{cnes}")
        # 2. Se miss: GET https://apidadosabertos.saude.gov.br/cnes/estabelecimentos/{cnes}
        # 3. Persistir no cache com TTL 24h
        # 4. Se DATASUS offline: retornar cache vencido se disponivel (graceful)

    async def list_establishments(self, uf: str, municipio: str = None,
                                  tipo: str = None, limit: int = 50) -> list[dict]:
        # Cache key: "zilda:establishments:{uf}:{municipio}:{tipo}"
        # TTL: 86400 (24h)
```

- [ ] Criar `zilda/services/datasus_client.py`
- [ ] Implementar cache Redis com TTL configuravel
- [ ] Implementar graceful degradation (retornar cache mesmo vencido se API offline)

### Tarefa 2.2 — Integrar territorio com IBGE
```python
# zilda/services/territory_service.py
class TerritoryService:
    async def get_municipal_profile(self, uf: str, municipio: str) -> PerfilTerritorial:
        # IBGE: https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{cod}
        # Combinar: populacao + estabelecimentos CNES + calculo cobertura ESF
```

- [ ] Criar `zilda/services/territory_service.py`
- [ ] Endpoint `GET /api/v1/territory/{uf}/{municipio}` respondendo

### Tarefa 2.3 — Endpoint analyze (BaseAgent)
```python
# zilda/api/routes/analyze.py
# POST /api/v1/analyze
# Aceita AnalysisRequest do intellicare-core
# Extrai: query_type (cnes_lookup, territorial_context, network_mapping)
# Retorna: AnalysisResponse com dados relevantes
```

- [ ] Implementar `analyze.py` seguindo contrato BaseAgent
- [ ] Testar via WANDA simulada

---

## Fase 3 — Testes e Empacotamento (Dia 2, manha) — ~3h

### Tarefa 3.1 — Testes unitarios completos
```bash
pytest tests/ -v --cov=zilda --cov-report=term-missing
```
- [ ] `test_cnes_service.py` — 8 testes minimos (ver spec tecnica)
- [ ] `test_territory_service.py` — 3 testes minimos
- [ ] `test_routes.py` — testar todos os endpoints com mocks
- [ ] Meta: >= 80% cobertura, 0 falhas

### Tarefa 3.2 — Docker smoke test
```bash
docker compose up --build -d
sleep 30
curl http://localhost:8007/api/v1/health
docker compose logs zilda | tail -20
```
- [ ] Container sobe sem erros
- [ ] Health check passa
- [ ] Logs sem excecoes criticas

### Tarefa 3.3 — Adicionar ao smoke_tests.py global
```python
# scripts/smoke_tests.py
# Adicionar: {"name": "zilda", "url": "http://localhost:8007/api/v1/health"}
```
- [ ] ZILDA incluido no smoke test global
- [ ] `python scripts/smoke_tests.py` retorna ZILDA como healthy

---

## Fase 4 — Documentacao e Release (Dia 2, tarde) — ~2h

### Tarefa 4.1 — Atualizar README.md do modulo
- [ ] Documentar todos os endpoints com exemplos curl
- [ ] Documentar variaveis de ambiente
- [ ] Documentar dependencias de infra (Redis opcional para cache)

### Tarefa 4.2 — CHANGELOG.md
```markdown
## v2.0.0 — 2026-03-XX
### Adicionado
- Integracao com DATASUS API publica
- Cache Redis para dados externos
- Endpoint territorial com dados IBGE
- Endpoint analyze compativel com BaseAgent
### Corrigido
- Testes unitarios estabilizados
```

---

## Checklist de Entrega

| Item | Status |
|------|--------|
| `pytest -q` → 0 falhas, >= 80% cobertura | [ ] |
| `docker compose up` → container healthy | [ ] |
| `GET /api/v1/health` → 200 OK | [ ] |
| `GET /api/v1/cnes/{codigo}` → dados CNES | [ ] |
| `GET /api/v1/territory/{uf}/{municipio}` → perfil | [ ] |
| `POST /api/v1/analyze` → resposta BaseAgent | [ ] |
| smoke_tests.py inclui ZILDA | [ ] |
| README atualizado com exemplos | [ ] |
| CHANGELOG.md criado | [ ] |

---

## Riscos e Mitigacoes

| Risco | Probabilidade | Mitigacao |
|-------|--------------|-----------|
| API DATASUS instavel/lenta | Media | Cache Redis + graceful degradation |
| Dados CNES desatualizados | Baixa | TTL de 24h para refresh |
| IBGE muda formato de resposta | Baixa | Pydantic validation com campos opcionais |

---

*ZILDA v2.0 — Plano de Implementacao — 2026-03-04*
