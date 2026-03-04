# NISE — Plano de Implementacao
**Data:** 2026-03-04
**Versao:** 1.0.0
**Estimativa Total:** 7-10 dias
**Prioridade:** ONDA 3 — Inteligencia

---

## Estado Atual

Modulo documentado. Flows Flowise definidos conceitualmente.
Implementacao core a ser feita.

Pre-requisitos:
- Flowise deployado e acessivel
- COMUNICACAO funcional (para chatbot via WhatsApp)
- intellicare-conhecimento com protocolos indexados no ChromaDB

---

## Fase 1 — Setup e API Base (Dia 1-2) — ~5h

### Tarefa 1.1 — Verificar estado atual
```bash
cd intellicare-nise
pip install -e ".[dev]"
pytest tests/ --co -q
```
- [ ] Inventario do codigo existente
- [ ] Identificar o que esta funcionando

### Tarefa 1.2 — Criar/verificar API FastAPI
- [ ] app.py com lifespan
- [ ] Rotas health, info, analyze

### Tarefa 1.3 — Flowise Client
- [ ] Criar `nise/services/flowise_client.py`
- [ ] Testar conexao com Flowise
- [ ] Listar chatflows disponíveis

---

## Fase 2 — Chat e Historico (Dia 2-4) — ~6h

### Tarefa 2.1 — Modelos de conversa
- [ ] Criar `ChatSession` e `ChatMessage` no banco
- [ ] Migracoes Alembic

### Tarefa 2.2 — Endpoint POST /chat
- [ ] Proxear para Flowise com session_id
- [ ] Persistir mensagem no PostgreSQL
- [ ] Retornar resposta com sources

### Tarefa 2.3 — Historico de sessao
- [ ] GET /chat/{session_id}/history
- [ ] Paginacao de mensagens

---

## Fase 3 — Triagem (Dia 4-6) — ~5h

### Tarefa 3.1 — Triage Service
- [ ] Criar `nise/services/triage_service.py`
- [ ] Score de risco (Manchester simplificado)
- [ ] Endpoint POST /triage

### Tarefa 3.2 — Triage Flow Flowise
- [ ] Configurar flow de triagem no Flowise
- [ ] Testar via API

### Tarefa 3.3 — Integracao COMUNICACAO
- [ ] Quando triagem = "urgente": enviar alerta via COMUNICACAO
- [ ] Quando triagem = "eletivo": enviar link de agendamento

---

## Fase 4 — Testes e Release (Dia 7-10) — ~5h

### Tarefa 4.1 — Suite de testes
```bash
pytest tests/ -v --cov=nise --cov-report=term-missing
```
- [ ] Flowise mockado com respx
- [ ] Meta: >= 70% cobertura, 0 falhas

### Tarefa 4.2 — Docker smoke test
```bash
docker compose up --build -d
curl http://localhost:8013/api/v1/health
```
- [ ] Container sobe
- [ ] POST /chat retorna resposta (mesmo sem Flowise: fallback)

---

## Checklist de Entrega

| Item | Status |
|------|--------|
| POST /chat funcionando | [ ] |
| Historico persistido | [ ] |
| Triagem com score de risco | [ ] |
| Flowise mockado nos testes | [ ] |
| Fallback gracioso sem Flowise | [ ] |
| pytest >= 70% cobertura | [ ] |
| docker compose up -> healthy | [ ] |
| smoke_tests.py inclui NISE | [ ] |

---

*NISE v2.0 — Plano de Implementacao — 2026-03-04*
