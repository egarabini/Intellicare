---
tipo: plano-execucao
demanda: DEM-075
titulo: Marie Bootstrap
status: em-execucao
dev: CODEX
criado: 2026-03-22
---

# DEM-075 — Plano de Execução

## Estimativa

Tempo estimado: ~5h | Complexidade: alta (infraestrutura nova + integração)

O risco principal não é o código Python — é o Dify subir corretamente no Docker Compose e o workflow `cid10_rag` ser configurado manualmente. Reservar tempo para troubleshooting do stack Dify.

---

## Ordem de execução

### Bloco 1 — Docker Compose Dify (60min)
1. Adicionar os 5 serviços ao `docker-compose.yml`: `marie-db`, `marie-redis`, `marie-api`, `marie-worker`, `marie-web`
2. Adicionar variáveis ao `.env.example` com valores placeholder
3. `docker compose up marie-db marie-redis marie-api marie-worker marie-web`
4. Aguardar containers `Up` — verificar `docker compose logs marie-api` sem erros de migração
5. Acessar `http://localhost/marie-web` — tela de setup inicial do Dify
6. Criar conta admin Dify, gerar API Key → registrar em `.env` local como `MARIE_API_KEY`

### Bloco 2 — Módulo `modules/marie/` (45min)
7. Criar `modules/marie/__init__.py`
8. Criar `modules/marie/client.py` conforme `02_TECNICA.md`
9. Adicionar settings em `shared/config.py`:
   - `marie_enabled: bool = False`
   - `marie_api_url: str = "http://marie-api:5001"`
   - `marie_api_key: str = ""`
   - `marie_timeout_seconds: int = 10`

### Bloco 3 — Workflow `cid10_rag` no Dify (45min)
10. No Dify web, criar workflow "cid10_rag" (ver `02_TECNICA.md` §Workflow)
11. Publicar workflow e anotar o `conversation_id` ou `workflow_id` gerado
12. Testar manualmente via curl:
```bash
curl -X POST http://localhost/marie-api/v1/chat-messages \
  -H "Authorization: Bearer $MARIE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"query": "dor torácica, dispneia", "patient_history": ""}, "query": "cid10", "response_mode": "blocking", "user": "test"}'
```

### Bloco 4 — Integração `oswaldo/services.py` (30min)
13. Importar `call_marie`, `is_marie_enabled` em `oswaldo/services.py`
14. Modificar `suggest_cid10()` conforme `02_TECNICA.md`
15. Adicionar `_get_patient_timeline_summary()` — helper que chama `clinical_timeline()` e formata como string para contexto RAG (máx 2000 chars)
16. Rodar testes existentes com `MARIE_ENABLED=false` — zero regressões esperadas

### Bloco 5 — Testes (45min)
17. Criar `test_marie_client.py` com os 5 testes listados em `02_TECNICA.md`
18. Usar `unittest.mock.patch` para mockar `httpx.post` — não depender do Dify rodando nos testes
19. `pytest test_marie_client.py test_oswaldo_ia.py -v` — todos passando

---

## Gotcha — Dify primeira inicialização

O container `marie-api` roda migrations do banco na primeira inicialização. Pode demorar 1-2 minutos. Se o container reiniciar em loop, verificar:

```bash
docker compose logs marie-api | grep -E "Error|error|Exception"
```

Causa mais comum: `marie-db` ainda não aceitando conexões quando `marie-api` tenta conectar. Solução: adicionar `healthcheck` no `marie-db` e `depends_on condition: service_healthy` no `marie-api`.

---

## Gotcha — `MARIE_ENABLED` deve ser `false` por default

O valor default **obrigatoriamente** deve ser `False` em `get_settings()`. Se alguém esquecer de definir a variável no `.env`, o comportamento deve ser o atual (sem Marie). Nunca inverter essa lógica.

---

## Gotcha — `call_marie` sem `patient_id`

Se `suggest_cid10()` for chamado sem `patient_id` (ex: busca rápida sem contexto de paciente), o Marie não deve ser acionado mesmo com `MARIE_ENABLED=true` — não há histórico para RAG. Usar diretamente o fallback local.

---

## Gotcha — versão do Dify

Usar `langgenius/dify-api:0.6.11` e `langgenius/dify-web:0.6.11`. Versões mais recentes (0.7.x+) alteraram a API de workflows — o contrato `POST /v1/chat-messages` pode mudar. Fixar a versão no `docker-compose.yml` com tag exata.

---

## Entrega

```
feat(marie): bootstrap Dify stack, marie_client.py, MARIE_ENABLED flag, cid10_rag proof-of-concept
```
Hash → enviar ao ARQUITETO após `git push origin HEAD:main` confirmado.
